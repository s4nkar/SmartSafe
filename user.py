from flask import *
from database import *

user=Blueprint('user',__name__)

@user.route('/user_home')
def user_home():
    return render_template('user_home.html')

@user.route('/mark_attendance_view')
def mark_attendance_view():
    return render_template('attendance.html')

