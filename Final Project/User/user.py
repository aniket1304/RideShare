#libraries
from flask_api import status
from datetime import datetime
from flask import Flask, render_template,jsonify,request,abort
from flask_sqlalchemy import SQLAlchemy
import requests
import json

#Counter
count=0

#IP address of Orchestrator
ip="http://34.207.157.150/"

#validate password-SHA1
def is_sha1(x):

    if len(x) != 40:
        return 0
    try:
        y = int(x, 16)
    except ValueError:
        return 0
    return 1



app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///user.db'
db = SQLAlchemy(app)
# Ensure FOREIGN KEY for sqlite3
if 'sqlite' in app.config['SQLALCHEMY_DATABASE_URI']:
    def _fk_pragma_on_connect(dbapi_con, con_record):  # noqa
        dbapi_con.execute('pragma foreign_keys=ON')

    with app.app_context():
        from sqlalchemy import event
        event.listen(db.engine, 'connect', _fk_pragma_on_connect)


class User(db.Model):
	username = db.Column(db.Text(), unique=True, primary_key=True)
	password = db.Column(db.Text(), nullable=False)
	#ride= db.relationship("Ride", back_populates="user")

	def __repr__(self):
		return '<User %r>' % self.username
	def __init__(self, Name,passw):
		self.username = Name
		self.password= passw





@app.route("/api/v1/users",methods=["PUT","POST"])
def create_user():
		global count
		count+=1
		if(request.method!="PUT"):
			abort(405)
		
	

		try:
			#formatting data in specific format
			data={'table':'User','insert':[request.get_json()['username'],request.get_json()['password']]}

		except:

			return ("Invalid Request",status.HTTP_400_BAD_REQUEST)

		#Validate password
		x = is_sha1(request.get_json()['password'])

		if x==0:

			return ("Password format Invalid",status.HTTP_400_BAD_REQUEST)

		#sending write request to orchestrator
		r=requests.post(ip+'api/v1/db/write',json=data )

		if r.status_code==500:

			return ("Not Unique Username",status.HTTP_400_BAD_REQUEST)

		return (jsonify(),status.HTTP_201_CREATED)


@app.route("/api/v1/users",methods=["GET"])
def listusers():

	global count
	count+=1

	if(1):

		#changing to specific format for read request
		data={"table": "User","columns": ["username"]}

		#sending read request to orchestrator
		r=requests.post(ip+'api/v1/db/read',json=data )
		
		d=r.json()


		if(len(d)==0):#if users are not present

			return ("",status.HTTP_204_NO_CONTENT)

		l=[]

		for i in d:#saving all users

			l+=[i['username']]

		return (jsonify(l))	
	
'''
@app.route("/api/v1/users/<username>",methods=["DELETE"])
def del_user(username):

	global count
	count+=1

	a=User.query.filter(User.username==username).first()


	if(a==None):
		return('Username Not found',status.HTTP_400_BAD_REQUEST)
	db.session.delete(a)
	db.session.commit()	
	return(jsonify())
'''


	
@app.route("/api/v1/db/clear",methods=["POST"])
def clr_db():

	#sending clear request to orchestrator
	r=requests.post(ip+'api/v1/db/clear')

	return {}

@app.route("/api/v1/_count",methods=["GET"])
def get_count():

		#number of requests
		global count

		return (jsonify([count]))	



@app.route("/api/v1/_count",methods=["DELETE"])
def zer_count():

		global count
		count=0
		return (jsonify())	





if __name__ == '__main__':	
	app.run(host='0.0.0.0',port=80)
