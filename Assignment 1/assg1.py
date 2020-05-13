from datetime import datetime
from flask import Flask, render_template,jsonify,request,abort
from flask_sqlalchemy import SQLAlchemy
import requests

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
db = SQLAlchemy(app)
# app.run(debug=False)
#dictionary containing book names
# and quantities

class User(db.Model):
	username = db.Column(db.Text(), unique=True, primary_key=True)
	password = db.Column(db.Text(), nullable=False)

	def __repr__(self):
		return '<User %r>' % self.username
	def __init__(self, Name,passw):
		self.username = Name
		self.password= passw

class Ride(db.Model):
	rideid = db.Column(db.Integer,primary_key=True)
	source = db.Column(db.Text(),nullable=False)
	destination = db.Column(db.Text(),nullable=False)
	timestamp = db.Column(db.DateTime(),nullable=False)
	created_by= db.Column(db.Text(),db.ForeignKey('user.username'),nullable=False)
#db foreign Key contrain to be added
	def __repr__(self):
		return '<rideid %r>' % self.rideid
	def __init__(self,s,d,t,c):
		self.source= s
		self.destination= d
		datetime_object = datetime.strptime(t, '%d-%m-%Y:%S-%M-%H')
		self.timestamp = datetime_object
		self.created_by= c

class Ridetake(db.Model):
	rideid = db.Column(db.Integer,nullable=False,primary_key=True)
	user=db.Column(db.Text(),nullable=False,primary_key=True)
	
	def __repr__(self):
		return '<rideid %r>' % self.rideid
	def __init__(self,r,u):
		self.rideid= r
		self.user= u
		

@app.route("/api/v1/db/write",methods=["POST"])
def write_db(db=db):
#“column name” : “data”,
#“column” : “column name”,
#“table” : “table name”
	print(request.get_json())
	l=request.get_json()['insert']
	me =("global us;us="+request.get_json()["table"]+"("+ str(l)[1:-1]+")")
	# print(type(me))
	exec(me)	
	print(us)
	#User("a","b")
	db.session.add(us)
	db.session.commit()
	return (jsonify())


@app.route("/api/v1/db/read",methods=["POST"])
def read_db():
# 	{
# “table”: “table name”,
# “columns”: [“column name”,],
# “where”: “[column=='value',"fhgf>=yu"]”
# }
	me =("global us;us="+request.get_json()["table"]+".query.filter"+"("+request.get_json()["where"]+").all()")
	print(me)
	exec(me)
	print(us)
	lis=[]
	for i in us:
		global res
		res={}
		for j in request.get_json()["columns"]:
			exec("res[j]=i."+j)
		lis+=[res]
	print()
	return (jsonify(lis))
	# db.session.add(me)
	# db.session.commit()
@app.route("/api/v1/users",methods=["PUT"])
def create_user():
	try:
		ur=request.url_root
		#IF SHA1 TO BE DONE case insensitive
		print(request.get_json()['username'],request.get_json()['password'])
		data={'table':'User','insert':[request.get_json()['username'],request.get_json()['password']]}
		print(data)
		r=requests.post(ur+'api/v1/db/write',json=data )
		print(r.status_code)
		if r.status_code==500:
			abort (405)
		return (jsonify())	
	except:
		abort(400)
@app.route("/api/v1/rides",methods=["POST"])
def create_ride():
	#try:
		ur=request.url_root
		#datetime_object = datetime.strptime(request.get_json()['timestamp'], '%d-%m-%Y:%S-%M-%H')
		#print(request.gset_json()['username'],request.get_json()['password'])
		data={'table':'Ride','insert':[request.get_json()['source'],request.get_json()['destination'],request.get_json()['timestamp'],request.get_json()['created_by']]}
		print(data)
		r=requests.post(ur+'api/v1/db/write',json=data )
		
		print(r.status_code)
#		if r.status_code==500:
#			abort (405)
		return (jsonify())	
	#except:
	#	abort(400)

	#
	# me = exec(request.get_json()["table"]+"("+request.get_json()["table"]+")")
	# db.session.add(me)
	# db.session.commit()
@app.route("/api/v1/rides",methods=["GET"])
def get_rides():
	#try:
		ur=request.url_root
		#datetime_object = datetime.strptime(request.get_json()['timestamp'], '%d-%m-%Y:%S-%M-%H')
		#print(request.gset_json()['username'],request.get_json()['password'])
		print(request.args.get('source'))
		data={"table": "Ride","columns": ["created_by","rideid","timestamp"],"where": "Ride.timestamp>='"+str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))+"',Ride.source=="+request.args.get('source')+",Ride.destination=="+request.args.get('destination')}
		print(data)
		r=requests.post(ur+'api/v1/db/read',json=data )
		d=r.json()
		for i in d:
			i["username"]=i.pop("created_by")
			i['timestamp'] = datetime.strptime(i['timestamp'], '%a, %d %b %Y %H:%M:%S %Z').strftime('%d-%m-%Y:%S-%M-%H')
		print(d)
		return (jsonify(d))	
	#except:
	#	abort(400)

	#
	# me = exec(request.get_json()["table"]+"("+request.get_json()["table"]+")")
	# db.session.add(me)
	# db.session.commit()
	

@app.route("/api/v1/rides/<rideId>",methods=["POST"])
def join_rides(rideId):
		ur=request.url_root
		#datetime_object = datetime.strptime(request.get_json()['timestamp'], '%d-%m-%Y:%S-%M-%H')
		#print(request.gset_json()['username'],request.get_json()['password'])
		data={'table':'Ridetake','insert':[rideId,request.get_json()['username']]}
		print(data)
		r=requests.post(ur+'api/v1/db/write',json=data )
		
		print(r.status_code)
#		if r.status_code==500:
#			abort (405)
		return (jsonify())	
	#except:
	#	abort(400)

	

if __name__ == '__main__':	
	app.debug=True
	app.run()
