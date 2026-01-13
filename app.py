from flask import Flask, render_template, request, jsonify
from attendance import attendance
from public import public
from user import user

app = Flask(__name__)
app.secret_key = 'smart-attendance'

app.register_blueprint(public)
app.register_blueprint(attendance,url_prefix='/attendance')
app.register_blueprint(user,url_prefix='/user')


@app.route('/')
def index():
    return render_template('login.html')

@app.route('/attendance/mark_attendance', methods=['POST'])
def mark_attendance():
    
    return jsonify({"status": "success", "message": "Attendance marked"})

if __name__ == '__main__':
    app.run(debug=True, ssl_context='adhoc') # SSL required for Webcam access