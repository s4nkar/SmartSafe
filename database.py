import mysql.connector

user = "root"
password = ""
database = "attendance_db"
host = "localhost"
port = 3306

def get_connection():
    return mysql.connector.connect(user=user,password=password,host=host,database=database,port=port)

def select(q):
	con=mysql.connector.connect(user=user,password=password,host=host,database=database,port=port)
	cur=con.cursor(dictionary=True)
	cur.execute(q)
	result=cur.fetchall()
	cur.close()
	con.close()
	return result

def select_one(q, params=None):
    con = get_connection()
    cur = con.cursor(dictionary=True)
    cur.execute(q, params)
    result = cur.fetchone()
    cur.close()
    con.close()
    return result

def insert(q, params=None):
	con=mysql.connector.connect(user=user,password=password,host=host,database=database,port=port)
	cur=con.cursor(dictionary=True)
	cur.execute(q, params)
	con.commit()
	result=cur.lastrowid
	cur.close()
	con.close()
	return result

def update(q):
	con=mysql.connector.connect(user=user,password=password,host=host,database=database,port=port)
	cur=con.cursor(dictionary=True)
	cur.execute(q)
	con.commit()
	res=cur.rowcount
	cur.close()
	con.close()
	return res

def delete(q):
	con=mysql.connector.connect(user=user,password=password,host=host,database=database,port=port)
	cur=con.cursor(dictionary=True)
	cur.execute(q)
	con.commit()
	result=cur.rowcount
	cur.close()
	con.close()
	return result

def execute(q, params=None):
    """
    Generic executor for UPDATE / DELETE / anything else
    Returns affected row count
    """
    con = get_connection()
    cur = con.cursor()
    cur.execute(q, params)
    con.commit()
    count = cur.rowcount
    cur.close()
    con.close()
    return count