#libraries
from flask_api import status
from datetime import datetime
from flask import Flask, render_template,jsonify,request,abort
from flask_sqlalchemy import SQLAlchemy
import requests
import json
import datetime
import time
# import time
import os
import socket
from kazoo.client import KazooClient
from kazoo.client import KazooState
import logging

#connecting Zookeeper
logging.basicConfig()

zk = KazooClient(hosts='zoo:2181')


def zk_listener(state):
	if(state == KazooState.LOST):
		logging.warning("Zookeeper connection lost")
	elif(state == KazooState.SUSPENDED):
		logging.warning("Zookeeper connection suspended")
	else:
		logging.info("Zookeeper connected")



zk.add_listener(zk_listener)
zk.start()

#ensuring nodal path /workers/
zk.ensure_path("/Workers/")


cid = socket.gethostname()
print(cid)
path = "/Workers/"+cid

#creating node for this slave
if zk.exists(path):
    print("Node already exists")
else:
    zk.create(path, b"slave node")
    print("node created")


print(os.environ['HOSTNAME'])

#creating database
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///'+os.environ['HOSTNAME']+'.db'
db = SQLAlchemy(app)

#creating table
db.create_all()



if 'sqlite' in app.config['SQLALCHEMY_DATABASE_URI']:
    def _fk_pragma_on_connect(dbapi_con, con_record):
        dbapi_con.execute('pragma foreign_keys=ON')

    with app.app_context():
        from sqlalchemy import event
        event.listen(db.engine, 'connect', _fk_pragma_on_connect)


#table definitions for User, Ride and ridetake

class User(db.Model):
	username = db.Column(db.Text(), unique=True, primary_key=True)
	password = db.Column(db.Text(), nullable=False)
	#ride= db.relationship("Ride", back_populates="user")

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
	created_by= db.Column(db.Text(),nullable=False)
	#user= db.relationship("User",back_populates="ride")
#db foreign Key contrain to be added
	def __repr__(self):
		return '<rideid %r>' % self.rideid
	def __init__(self,s,d,t,c):
		self.source= s
		self.destination= d
		datetime_object = datetime.datetime.strptime(t, '%d-%m-%Y:%S-%M-%H')
		self.timestamp = datetime_object
		self.created_by= c
class Ridetake(db.Model):
	rideid = db.Column(db.Integer,db.ForeignKey('ride.rideid'),nullable=False, primary_key=True)
	user=db.Column(db.Text(),nullable=False, primary_key=True)
	def __repr__(self):
		return '<rideid %r>' % self.rideid
	def __init__(self,r,u):
		self.rideid= r
		self.user= u



import pika

#creating tables
db.create_all()

#connecting to rabbitmq
connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='rmq',heartbeat=0))

channel = connection.channel()

#declaring readQ
channel.queue_declare(queue='readQ',durable=True)



def on_request(ch, method, props, body):

    dataDict = json.loads(body)
    print(dataDict)
    print(User.query.all())
    

    #for read requests
    if method.routing_key == 'read':
 
        try:
         with app.test_request_context():
            print(User.query.all())
            request = json.loads(body)
            print(request)


            try:

                me =("global us;us="+request["table"]+".query.filter"+"("+request["where"]+").all()")
            
            except:
            	
                me =("global us;us="+request["table"]+".query.all()")

            exec(me)

            lis=[]
            
            for i in us:
             global res
             res={}
            #  print(REcolumns)
             for j in request["columns"]:
                if (j=="timestamp"):
                    print("intimestamp")
                    exec("res[j]=str(i."+j+")")
                else:
                    exec("res[j]=i."+j)
             lis+=[res]
            print(lis)
            retResponse = (lis)
        except Exception as e:
            print(e)
            print(User.query.all())
            retResponse=json.dumps(500)
        ch.basic_publish(exchange='response_exchange1',
                     routing_key='response',
                     properties=pika.BasicProperties(correlation_id = \
                                                         props.correlation_id),
                     body= json.dumps(retResponse))
        ch.basic_ack(delivery_tag=method.delivery_tag)
    else:
        n = json.loads(body)
        if (n=="clear"):
            print(User.query.all())
            db.drop_all()
            db.create_all()
            # response="a"
        else:
    	    exec(n)	
    	    db.session.add(us)
    	    db.session.commit()
    	    response="a"
	# channel.basic_qos(prefetch_count=1)
try:

        connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='rmq'))
except:
        time.sleep(30)
finally:
        connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='rmq'))
channel = connection.channel()

channel.exchange_declare(exchange='read_exchange1', exchange_type='direct')
channel.exchange_declare(exchange='response_exchange1', exchange_type='direct')
channel.exchange_declare(exchange = 'sync_exchange1', exchange_type = 'direct')
channel.exchange_declare(exchange='write_exchange', exchange_type='direct')

channel.queue_declare(queue='readQ', durable = True)
channel.queue_bind(exchange = 'read_exchange1', queue = 'readQ', routing_key = 'read')

channel.queue_declare(queue='syncQ', durable = True)
channel.queue_bind(exchange = 'sync_exchange1', queue = 'syncQ', routing_key = 'synchronize1')

channel.queue_declare(queue='writeQ', durable=True)
channel.queue_bind(exchange = 'write_exchange', queue = 'writeQ', routing_key = 'write')


channel.basic_qos(prefetch_count=0)
master = 0
if master == 1:
	#channel.basic_consume(queue= 'writeQ', on_message_callback=callback, auto_ack=True)
	pass
else:
	channel.basic_consume(queue='readQ', on_message_callback=on_request)
	channel.basic_consume(queue='syncQ', on_message_callback=on_request, auto_ack = True)

	print(" [x] Awaiting RPC requests")
	channel.start_consuming()