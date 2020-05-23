#Libraries
from flask_api import status
from datetime import datetime
from flask import Flask, render_template,jsonify,request,abort
from flask_sqlalchemy import SQLAlchemy
import requests


ip='http://34.207.157.150/'  #IP of Orchestrator/DBaaS
ipu="http://52.55.28.15/" #IP of Users

count=0  #for counter


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


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
db = SQLAlchemy(app)
# Ensure FOREIGN KEY for sqlite3
if 'sqlite' in app.config['SQLALCHEMY_DATABASE_URI']:
    def _fk_pragma_on_connect(dbapi_con, con_record):  # noqa
        dbapi_con.execute('pragma foreign_keys=ON')

    with app.app_context():
        from sqlalchemy import event
        event.listen(db.engine, 'connect', _fk_pragma_on_connect)




#defining DataBase structure
class Ride(db.Model):
	rideid = db.Column(db.Integer,primary_key=True)
	source = db.Column(db.Text(),nullable=False)
	destination = db.Column(db.Text(),nullable=False)
	timestamp = db.Column(db.DateTime(),nullable=False)
	created_by= db.Column(db.Text(),nullable=False)



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
	#A table definition for a user joining a ride
	rideid = db.Column(db.Integer,db.ForeignKey('ride.rideid'),nullable=False, primary_key=True)
	user=db.Column(db.Text(),nullable=False, primary_key=True)
	def __repr__(self):
		return '<rideid %r>' % self.rideid
	def __init__(self,r,u):
		self.rideid= r
		self.user= u
		




@app.route("/api/v1/rides",methods=["POST","PUT"])
def create_ride():
	#try:
		global count
		count+=1
		if(request.method!="POST"):
			abort(405)
		ur=request.url_root



		try:

			#Creating data in specific format for write database request
			data={'table':'Ride','insert':[request.get_json()['source'],request.get_json()['destination'],request.get_json()['timestamp'],request.get_json()['created_by']]}
		
		except:
			
			#if any data is missing return 400
			return ("Invalid Request",status.HTTP_400_BAD_REQUEST)
		



		#Requesting User to get all the users
		q=requests.get(ipu+'api/v1/users',json=data )
		if(q.status_code!=204):#204=no user
			
			z=(q.json())


			#To check if user creating ride exists
			if(request.get_json()['created_by'] in z):

					#requesting write to DBaaS
					r=requests.post(ip+'api/v1/db/write',json=data )
			

					return (jsonify(),status.HTTP_201_CREATED)	
		return ("USER NOT FOUND",status.HTTP_400_BAD_REQUEST)
		



@app.route("/api/v1/rides/count",methods=["GET"])
def count_rides():
		global count
		count+=1


		ur=request.url_root

		try:

			#creating data in specific format
			data={"table": "Ride","columns": ["created_by","rideid","timestamp"]}

		except:

			#if missing value
			return ('Missing Parameter',status.HTTP_400_BAD_REQUEST)
		
		#requesting Read to DBaaS
		r=requests.post(ip+'api/v1/db/read',json=data )

		d=r.json()

		return (jsonify(len(d)))	#returning Count
		



@app.route("/api/v1/rides",methods=["GET"])
def get_rides():

		global count
		count+=1

		ur=request.url_root


		try:

			#data in specific format for read request for upcoming rides
			data={"table": "Ride","columns": ["created_by","rideid","timestamp"],"where": "Ride.timestamp>='"+str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))+"',Ride.source=="+request.args.get('source')+",Ride.destination=="+request.args.get('destination')}

		except:

			return ('Missing Parameter',status.HTTP_400_BAD_REQUEST)



		#Source and destination should be in valid range	
		if int(request.args.get('source')) in range(1,199) and int(request.args.get('destination')) in range(1,199):
			
			#read request to Orchestrator
			r=requests.post(ip+'api/v1/db/read',json=data )
			d=r.json()

			#check if atleast one ride is available
			if(len(d)==0):
				return ("",status.HTTP_204_NO_CONTENT)

			#
			for i in d:


				#changing read data into specified format
				i['username']=i.pop("created_by")
				i['timestamp'] = datetime.strptime(i['timestamp'], '%Y-%m-%d %H:%M:%S').strftime('%d-%m-%Y:%S-%M-%H')


			return (jsonify(d))


		else:


			#if source or destination is out of range
			return ('Source/destination invalid',status.HTTP_400_BAD_REQUEST)
		


	

@app.route("/api/v1/rides/<rideId>",methods=["POST"])
def join_rides(rideId):


		global count
		count+=1

		ur=request.url_root


		try:

			#to insert data changing into specific format
			data={'table':'Ridetake','insert':[rideId,request.get_json()['username']]}

		except:


			return ('Missing Parameter',status.HTTP_400_BAD_REQUEST)

		#getting users
		q=requests.get(ipu+'api/v1/users')	


		if(q.status_code!=204):#204=no users

			z=(q.json())

			if(request.get_json()['username'] in z):#user creating ride exists

				r=requests.post(ip+'api/v1/db/write',json=data )

				return (jsonify())

		return ("USER NOT FOUND",status.HTTP_400_BAD_REQUEST)
		

		

@app.route("/api/v1/rides/<rideId>")
def ride_detail(rideId):
		global count
		count+=1

	#try:
		ur=request.url_root
		try:

			#data into specific format for read request
			data={"table": "Ride","columns": ["created_by","rideid","timestamp","source","destination"],"where": "Ride.rideid=="+rideId}
		
		except:

			return ('Missing Parameter',status.HTTP_400_BAD_REQUEST)

		#Sending read request to DBaaS to fetch ride details
		r=requests.post(ip+'api/v1/db/read',json=data )

		d=r.json()[0]

		#Sending read request to fetch users associated with the ride
		data={"table": "Ridetake","columns": ["user"],"where": "Ride.rideid=="+rideId}
		
		#Sending read request to DBaaS to fetch users associated with the ride
		r=requests.post(ip+'api/v1/db/read',json=data )

		user=(r.json())

		#users taking the ride
		d["users"]=[x["user"] for x in user ]

		if r.status_code==500:

			return ("Ride Not Found",status.HTTP_400_BAD_REQUEST)
		
		return (jsonify(d))

'''


@app.route("/api/v1/rides/<rideId>",methods=["DELETE"])
def del_ride(rideId):

	global count
	
	count+=1

	
	b=Ride.query.filter(Ride.rideid==rideId).first()
	if(b==None):
		return('Ride Not found',status.HTTP_400_BAD_REQUEST)
	

	db.session.delete(b)

	db.session.commit()

	return(jsonify())

'''


	
@app.route("/api/v1/db/clear",methods=["POST"])
def clr_db():

	#sending clear request to DBaaS
	r=requests.post(ip+'api/v1/db/clear')

	return(jsonify())



@app.route("/api/v1/_count",methods=["GET"])
def get_count():

		#counting number of requests
		global count

		return (jsonify([count]))	
		

@app.route("/api/v1/_count",methods=["DELETE"])
def zer_count():

		#to reset counter
		global count

		count=0

		return (jsonify())
	




if __name__ == '__main__':
	
	app.run(host='0.0.0.0',port=80)
