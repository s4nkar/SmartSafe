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

