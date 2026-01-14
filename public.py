from flask import *
from database import *
import base64
import numpy as np
import cv2
import pickle
from deepface import DeepFace

from werkzeug.security import check_password_hash, generate_password_hash

public=Blueprint('public',__name__)

@public.route('/login',methods=['get','post'])
def login():

	if 'submit' in request.form:
		username=request.form['username']
		password=request.form['password']
		
		# Fetch by username first
		q="SELECT * FROM `login` WHERE `username`='%s'"%(username)
		res=select(q)
		
		if res:
			stored_password = res[0]['password']
			# Check hash or plaintext (legacy)
			password_ok = False
			try:
				if check_password_hash(stored_password, password):
					password_ok = True
			except:
				pass
			
			# Fallback for plain text
			if not password_ok and stored_password == password:
				password_ok = True
				
			if password_ok:
				usertype=res[0]['usertype']
				login_id=res[0]['login_id']
				session['lid']=login_id
				
				if usertype=='user':
					return redirect(url_for('user.user_home'))
			else:
				flash("Invalid Password", "danger")
		else:
			flash("User not found", "danger")

	return render_template('login.html')


@public.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('public.login'))


# from werkzeug.security import generate_password_hash # Duplicate removed, imported at top

@public.route('/register', methods=['GET', 'POST'])
def register():
    if 'submit' in request.form:
        name = request.form['name']
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']

        hashed_password = generate_password_hash(password)

        q_login = """
        INSERT INTO login (username, password, usertype)
        VALUES (%s, %s, 'user')
        """
        login_id = insert(q_login, (username, hashed_password))

        q_user = """
        INSERT INTO user (login_id, full_name, email, created_at)
        VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
        """
        user_id = insert(q_user, (login_id, name, email))

        session['enroll_user_id'] = user_id
        return redirect(url_for('public.enroll_biometrics'))

    return render_template("register.html")


# --- 2. New Biometric Enrollment Route ---
@public.route('/enroll_biometrics', methods=['GET', 'POST'])
def enroll_biometrics():
    user_id = session.get('enroll_user_id')
    if not user_id:
        return redirect(url_for('public.login'))

    if request.method == 'POST':
        try:
            data = request.json
            image_data = data.get('face_image')
            audio_data = data.get('voice_audio')

            if not image_data or not audio_data:
                return jsonify({"status": "error", "message": "Face and voice required"})

            # ---- Image Decode ----
            encoded_img = image_data.split(',')[1]
            img_arr = np.frombuffer(base64.b64decode(encoded_img), np.uint8)
            img = cv2.imdecode(img_arr, cv2.IMREAD_COLOR)

            if img is None:
                return jsonify({"status": "error", "message": "Invalid image data"})

            # ---- Audio Decode ----
            encoded_audio = audio_data.split(',')[1]
            audio_bytes = base64.b64decode(encoded_audio)

            if len(audio_bytes) < 8000:
                return jsonify({"status": "error", "message": "Audio too short"})

            # ---- Face Embedding ----
            try:
                face_obj = DeepFace.represent(
                    img_path=img,
                    model_name="ArcFace",
                    enforce_detection=True
                )
            except Exception:
                return jsonify({"status": "error", "message": "No face detected"})

            embedding_blob = pickle.dumps(face_obj[0]["embedding"])

            # ---- Prevent duplicate enrollment ----
            exists = select_one(
                "SELECT id FROM user_biometrics WHERE user_id=%s",
                (user_id,)
            )
            if exists:
                return jsonify({"status": "error", "message": "Biometrics already enrolled"})

            # ---- Insert ----
            q = """
            INSERT INTO user_biometrics (user_id, face_embedding, voice_embedding)
            VALUES (%s, %s, %s)
            """
            insert(q, (user_id, embedding_blob, audio_bytes))

            session.pop('enroll_user_id', None)
            return jsonify({"status": "success"})

        except Exception as e:
            return jsonify({"status": "error", "message": str(e)})

    import random
    phrases = ["Red Apple", "Green Grass", "Blue Sky", "Yellow Sun", "Purple Rain"]
    phrase = random.choice(phrases)
    return render_template("enroll_biometrics.html", phrase=phrase)
