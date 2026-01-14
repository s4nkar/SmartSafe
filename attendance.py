import base64
import json
import numpy as np
import cv2
import pickle
import time
from io import BytesIO

from flask import Blueprint, request, jsonify
from deepface import DeepFace
import speech_recognition as sr

from database import select_one, execute
from utils import calculate_confidence

attendance = Blueprint("attendance", __name__)

FACE_SIMILARITY_THRESHOLD = 0.75
CHALLENGE_EXPIRY_SECONDS = 60


@attendance.route("/attendance/mark_attendance", methods=["POST"])
def mark_attendance():
    data = request.json

    user_id = data.get("user_id")
    image_data = data.get("image")           # base64 image
    audio_blob_b64 = data.get("audio")       # base64 audio
    liveness_passed = data.get("liveness_passed", False)

    if not user_id or not image_data:
        return jsonify({"status": "fail", "reason": "Missing data"}), 400

    # ------------------------------------------------------------------
    # 1. Fetch enrolled face embedding
    # ------------------------------------------------------------------
    row = select_one(
        "SELECT face_embedding FROM user_biometrics WHERE user_id = %s",
        (user_id,)
    )

    if not row:
        return jsonify({"status": "fail", "reason": "User not enrolled"}), 400

    enrolled_embedding = pickle.loads(row["face_embedding"])

    # ------------------------------------------------------------------
    # 2. Decode incoming image
    # ------------------------------------------------------------------
    try:
        encoded = image_data.split(",")[1]
        img_bytes = base64.b64decode(encoded)
        nparr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    except Exception:
        return jsonify({"status": "fail", "reason": "Invalid image"}), 400

    # ------------------------------------------------------------------
    # 3. Face recognition (ArcFace)
    # ------------------------------------------------------------------
    try:
        objs = DeepFace.represent(
            img_path=img,
            model_name="ArcFace",
            enforce_detection=True
        )
        live_embedding = np.array(objs[0]["embedding"])
    except Exception:
        return jsonify({"status": "fail", "reason": "Face not detected"}), 400

    # Cosine similarity (−1 to 1, higher is better)
    cosine_similarity = np.dot(enrolled_embedding, live_embedding) / (
        np.linalg.norm(enrolled_embedding) * np.linalg.norm(live_embedding)
    )

    is_face_match = cosine_similarity >= FACE_SIMILARITY_THRESHOLD

    # ------------------------------------------------------------------
    # 4. Fetch active challenge (DO NOT rely on flask session)
    # ------------------------------------------------------------------
    challenge = select_one(
        """
        SELECT phrase, expires_at
        FROM attendance_challenges
        WHERE user_id = %s
        ORDER BY created_at DESC
        LIMIT 1
        """,
        (user_id,)
    )

    audio_matched = False
    challenge_status = "missing"

    if challenge:
        if time.time() > challenge["expires_at"]:
            challenge_status = "expired"
        else:
            challenge_status = "valid"

    # ------------------------------------------------------------------
    # 5. Audio verification (server-side STT)
    # ------------------------------------------------------------------
    recognized_text = None
    challenge_text = challenge["phrase"] if challenge else None

    if challenge_status == "valid" and audio_blob_b64:
        try:
            # Clean Base64 string (remove data URL header if present)
            if "," in audio_blob_b64:
                audio_blob_b64 = audio_blob_b64.split(",")[1]
                
            recognizer = sr.Recognizer()
            audio_bytes = base64.b64decode(audio_blob_b64)
            
            # Use AudioFile with the in-memory bytes
            audio_file = sr.AudioFile(BytesIO(audio_bytes))

            with audio_file as source:
                audio = recognizer.record(source)

            recognized_text = recognizer.recognize_google(audio)

            audio_matched = (
                recognized_text.lower().strip()
                == challenge_text.lower().strip()
            )

        except sr.UnknownValueError:
            audio_matched = False
            recognized_text = "<Unintelligible>"
        except sr.RequestError as e:
            audio_matched = False
            recognized_text = f"<API Error: {e}>"
        except Exception as e:
            audio_matched = False
            recognized_text = f"<STT Error: {str(e)}>"

    # ------------------------------------------------------------------
    # 6. Confidence scoring
    # ------------------------------------------------------------------
    total_score = calculate_confidence(
        face_similarity=cosine_similarity,
        face_match=is_face_match,
        audio_matched=audio_matched,
        liveness_passed=liveness_passed
    )

    # Map to DB ENUM values ('success', 'failed', 'flagged')
    db_status = "success" if total_score >= 80 else "failed"

    # ------------------------------------------------------------------
    # 7. Persist attendance log
    # ------------------------------------------------------------------
    method_details = {
        "face_similarity": float(cosine_similarity),
        "face_match": bool(is_face_match),
        "audio_matched": audio_matched,
        "liveness_passed": liveness_passed,
        "challenge_status": challenge_status,
        "challenge_text": challenge_text,
        "recognized_text": recognized_text
    }

    execute(
        """
        INSERT INTO attendance_log
        (user_id, confidence_score, method_details, status)
        VALUES (%s, %s, %s, %s)
        """,
        (
            user_id,
            total_score,
            json.dumps(method_details),
            db_status
        )
    )

    return jsonify({
        "status": db_status,
        "score": total_score,
        "face_similarity": round(float(cosine_similarity), 3),
        "message": "Attendance marked" if db_status == "success" else "Low confidence"
    })
