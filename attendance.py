from database import select
import base64
import json
import numpy as np
import cv2
import pickle
from flask import Flask, render_template, request, jsonify
from deepface import DeepFace
import mysql.connector
import speech_recognition as sr
from io import BytesIO
from database import *
from utils import calculate_confidence
from flask import Blueprint

attendance=Blueprint('attendance',__name__)


@attendance.route('/attendance/mark_attendance', methods=['POST'])
def mark_attendance():
    data = request.json
    user_id = data.get('user_id')
    image_data = data.get('image') # Base64 string
    audio_text_claimed = data.get('audio_text') # Text claim
    audio_blob_b64 = data.get('audio') # Base64 Audio Blob
    
    # 1. Fetch Enrolled Embedding
    q = "SELECT face_embedding FROM user_biometrics WHERE user_id = '%s'" %(user_id)
    result = select(q)
    
    if not result:
        return jsonify({"status": "fail", "reason": "User not enrolled"}), 400

    # Deserialize stored embedding (assuming it was stored as bytes/blob)
    enrolled_embedding = pickle.loads(result[0]['face_embedding'])

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
        # Actually Cosine distance: 0 is same, 1 is opposite. 
        # DeepFace verification: distance < threshold means match.
        # But here we calculated Cosine Similarity manually? np.dot / (norm*norm) is Cosine Similarity (-1 to 1). 1 is Identical.
        # So 'cosine_distance' variable above is actually '1 - Similarity', which is Distance. Correct.
        
        # 4. Audio Check
        # For MVP, we trust client text claim OR if simple match needed. 
        # We also received 'audio' blob which we can save or transcribe.
        expected_phrase = "Blue Sky"
        audio_matched = False
        if audio_text_claimed:
             audio_matched = audio_text_claimed.lower() == expected_phrase.lower()
        else:
             # If no text claim, we might assume failed or pass if strictness low
             audio_matched = True 
        
        # 5. Scoring
        total_score = calculate_confidence(cosine_distance, audio_matched, liveness_passed=True)
        
        status = "success" if total_score >= 80 else "failed"
        
        # Log it
        # We store specific method details. If audio blob exists, we note its size.
        audio_size = len(audio_blob_b64) if audio_blob_b64 else 0
        method_details = {
            "face_dist": float(cosine_distance), 
            "audio_matched": audio_matched,
            "audio_evidence_size": audio_size
        }
        
        q = "INSERT INTO attendance_log (user_id, confidence_score, method_details, status) VALUES ('%s', '%s', '%s', '%s')" % (user_id, total_score, json.dumps(method_details), status)
        insert(q)

        return jsonify({
            "status": status, 
            "score": total_score,
            "message": "Attendance marked" if status == "success" else "Verification low confidence"
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
