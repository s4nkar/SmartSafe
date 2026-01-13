from flask import *
from database import *

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


@public.route('/register',methods=['get','post'])
def register():
	if 'submit' in request.form:
		name=request.form['name']
		email=request.form['email']
		username=request.form['username']
		password=request.form['password']
		
		q= "insert into `login` values(null,'%s','%s', 'user')"%(username,password)
		login_id = insert(q)
		q="INSERT INTO `user` VALUES(null,'%s', '%s', '%s', current_timestamp)"%(login_id, name, email)
		insert(q)
		return redirect(url_for('public.login'))

	return render_template("register.html")
