from flask import *
from database import *

user=Blueprint('user',__name__)

@user.route('/user_home')
def user_home():
    return render_template('user_home.html')

@user.route('/mark_attendance_view')
def mark_attendance_view():
    q = "SELECT * FROM user WHERE login_id = '%s'" %(session['lid'])
    result = select(q)
    return render_template('attendance.html',user_id=result[0]["user_id"])

import random
import time
from datetime import datetime

@user.route('/view_history')
def view_history():
    if 'lid' not in session:
        return redirect(url_for('public.login'))
        
    # Get user_id first
    q_user = "SELECT user_id FROM user WHERE login_id = '%s'" % (session['lid'])
    res_user = select(q_user)
    
    if not res_user:
        return redirect(url_for('public.login'))
        
    user_id = res_user[0]['user_id']
    
    # Get logs
    q_log = "SELECT * FROM attendance_log WHERE user_id = '%s' ORDER BY check_in_time DESC" % (user_id)
    logs = select(q_log)
    
    return render_template('history.html', logs=logs)

@user.route('/get_challenge')
def get_challenge():
    if 'lid' not in session:
        return jsonify({"phrase": "Login Required", "expiry_seconds": 0}), 401

    # Get user_id
    q_user = "SELECT user_id FROM user WHERE login_id = '%s'" % (session['lid'])
    res_user = select(q_user)
    if not res_user:
        return jsonify({"phrase": "User Not Found", "expiry_seconds": 0}), 404
    user_id = res_user[0]['user_id']

    phrases = [
        "Red Apple", "Green Grass", "Blue Sky", "Yellow Sun", 
        "Purple Rain", "White Snow", "Black Night", "Orange Fruit",
        "Golden Star", "Silver Moon", "Fast Car", "Quiet Lake",
        "Ocean Wave", "Mountain Peak", "River Flow", "Desert Sand"
    ]
    phrase = random.choice(phrases)
    expiry = time.time() + 60
    
    # Store in DB
    q_ins = "INSERT INTO attendance_challenges (user_id, phrase, expires_at) VALUES ('%s', '%s', '%s')" % (user_id, phrase, expiry)
    insert(q_ins)
    
    return jsonify({"phrase": phrase, "expiry_seconds": 60})
