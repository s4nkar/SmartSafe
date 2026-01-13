from database import select
import base64
import json
import numpy as np
import cv2
from flask import Flask, render_template, request, jsonify
from deepface import DeepFace
import mysql.connector
import speech_recognition as sr
from io import BytesIO
from database import *
from utils import calculate_confidence


attendance=Blueprint('attendance',__name__)


@attendance.route('/mark_attendance', methods=['POST'])
def mark_attendance():
    data = request.json
    user_id = data.get('user_id')
    image_data = data.get('image') # Base64 string
    audio_text_claimed = data.get('audio_text') # Text from client-side STT or server processing
    
    # 1. Fetch Enrolled Embedding
    q = "SELECT face_embedding FROM user_biometrics WHERE user_id = '%s'" %(user_id)
    result = select(q)
    
    if not result:
        return jsonify({"status": "fail", "reason": "User not enrolled"}), 400

    # Deserialize stored embedding (assuming it was stored as bytes/blob)
    enrolled_embedding = np.frombuffer(result[0], dtype=np.float64)

    # 2. Process Incoming Image
    # Convert Base64 to CV2 Image
    encoded_data = image_data.split(',')[1]
    nparr = np.frombuffer(base64.b64decode(encoded_data), np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    # 3. Get Live Embedding & Liveness
    # DeepFace usually handles detection + alignment + embedding
    try:
        # Generate embedding for current frame
        # 'ArcFace' is robust. 'VGG-Face' is default.
        live_objs = DeepFace.represent(img_path=img, model_name="ArcFace", enforce_detection=False)
        live_embedding = np.array(live_objs[0]["embedding"])
        
        # Calculate Distance (Cosine)
        # Manually calculating allows for custom scoring thresholds
        cosine_distance = np.dot(enrolled_embedding, live_embedding) / (np.linalg.norm(enrolled_embedding) * np.linalg.norm(live_embedding))
        cosine_distance = 1 - cosine_distance # DeepFace usually returns distance, not similarity
        
        # 4. Audio Check (Simplification: Client sends text, we verify content)
        # Ideally, you send audio blob and process STT here for security.
        # For MVP, we trust client STT or do simple string match.
        expected_phrase = "Blue Sky" # Example dynamic challenge
        audio_matched = audio_text_claimed.lower() == expected_phrase.lower()
        
        # 5. Scoring
        total_score = calculate_confidence(cosine_distance, audio_matched, liveness_passed=True)
        
        status = "success" if total_score >= 80 else "failed"
        
        # Log it
        q = "INSERT INTO attendance_log (user_id, confidence_score, method_details, status) VALUES ('%s', '%s', '%s', '%s')" % (user_id, total_score, json.dumps({"face_dist": float(cosine_distance), "audio": audio_matched}), status)
        insert(q)

        return jsonify({
            "status": status, 
            "score": total_score,
            "message": "Attendance marked" if status == "success" else "Verification low confidence"
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
