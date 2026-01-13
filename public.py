from flask import *
from database import *
import base64
import numpy as np
import cv2
import pickle
from deepface import DeepFace

public=Blueprint('public',__name__)

@public.route('/login',methods=['get','post'])
def login():

	if 'submit' in request.form:
		username=request.form['username']
		password=request.form['password']
		q="SELECT usertype, login_id FROM `login` WHERE `username`='%s' AND `password`='%s'"%(username,password)
		res=select(q)
		if res:
			usertype=res[0]['usertype']
			login_id=res[0]['login_id']
			session['lid']=login_id
			
			if usertype=='user':
				return redirect(url_for('user.user_home'))

	return render_template('login.html')


@public.route('/register', methods=['GET', 'POST'])
def register():
    if 'submit' in request.form:
        name = request.form['name']
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']
        
        # 1. Insert Login
        q_login = "INSERT INTO `login` VALUES(NULL, '%s', '%s', 'user')" % (username, password)
        login_id = insert(q_login) 
        
        # 2. Insert User (Table name is 'user')
        q_user = "INSERT INTO `user` VALUES(NULL, '%s', '%s', '%s', current_timestamp)" % (login_id, name, email)
        user_id = insert(q_user)
        
        # 3. Store user_id in session so we know who we are enrolling next
        session['enroll_user_id'] = user_id
        
        # 4. Redirect to Biometric Enrollment instead of Login
        return redirect(url_for('public.enroll_biometrics'))

    return render_template("register.html")

# --- 2. New Biometric Enrollment Route ---
@public.route('/enroll_biometrics', methods=['GET', 'POST'])
def enroll_biometrics():
    # Security: Ensure we are in the middle of a registration flow
    user_id = session.get('enroll_user_id')
    if not user_id:
        return redirect(url_for('public.login'))

    if request.method == 'POST':
        try:
            # 1. Get the image and audio from JSON
            data = request.json
            image_data = data.get('face_image') # Base64 string
            audio_data = data.get('voice_audio') # Base64 string
            
            if not image_data or not audio_data:
                return jsonify({"status": "error", "message": "Missing face or voice data"})

            # 2. Convert Base64 -> OpenCV Image
            encoded_data = image_data.split(',')[1]
            nparr = np.frombuffer(base64.b64decode(encoded_data), np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            # Process Audio (Decode Base64 to bytes)
            # Format usually: "data:audio/wav;base64,UklGRi..."
            if ',' in audio_data:
                audio_encoded = audio_data.split(',')[1]
            else:
                audio_encoded = audio_data
            
            audio_bytes = base64.b64decode(audio_encoded)

            # 3. Generate Embedding using DeepFace
            # We use 'ArcFace' for best balance of speed/accuracy
            # enforce_detection=True ensures we don't save a wall as a face
            embedding_objs = DeepFace.represent(
                img_path=img, 
                model_name="ArcFace", 
                enforce_detection=True
            )
            embedding = embedding_objs[0]["embedding"]
            
            # 4. Serialize the embedding to bytes for BLOB storage
            # We use pickle or simple bytes conversion
            embedding_blob = pickle.dumps(embedding)
            
            # 5. Save to DB
            import mysql.connector
            # Note: Hardcoded creds should be replaced with config imports in production
            conn = mysql.connector.connect(user='root', password='', host='localhost', database='attendance_db', port=3306)
            cursor = conn.cursor()
            
            # Update query to include voice_embedding
            sql = "INSERT INTO user_biometrics (user_id, face_embedding, voice_embedding) VALUES (%s, %s, %s)"
            cursor.execute(sql, (user_id, embedding_blob, audio_bytes))
            conn.commit()
            conn.close()

            # Clear session and finish
            session.pop('enroll_user_id', None)
            return jsonify({"status": "success", "redirect": url_for('public.login')})

        except ValueError:
            return jsonify({"status": "error", "message": "No face detected! Please ensure good lighting."})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)})

    return render_template("enroll_biometrics.html")
