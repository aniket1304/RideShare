from flask_api import status
from datetime import datetime
from flask import Flask, render_template,jsonify,request,abort
from flask_sqlalchemy import SQLAlchemy
import requests
import time
import json
import os
print(os.environ['HOSTNAME'])
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///'+os.environ['HOSTNAME']+'.db'
db = SQLAlchemy(app)
# Ensure FOREIGN KEY for sqlite3
if 'sqlite' in app.config['SQLALCHEMY_DATABASE_URI']:
    def _fk_pragma_on_connect(dbapi_con, con_record):  # noqa
        dbapi_con.execute('pragma foreign_keys=ON')

    with app.app_context():
        from sqlalchemy import event
        event.listen(db.engine, 'connect', _fk_pragma_on_connect)
# app.run(debug=True)
#dictionary containing book names
# and quantities

class User(db.Model):
	username = db.Column(db.Text(),unique=True,primary_key=True)
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
		datetime_object = datetime.strptime(t, '%d-%m-%Y:%S-%M-%H')
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
db.create_all()
'''connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='rmq',heartbeat=0))

channel = connection.channel()

channel.queue_declare(queue='writeQ')

def on_request(ch, method, props, body):
    n = str(body)
    if (n=="clear"):
            db.drop_all()
            db.create_all()
            response="a"
            ch.basic_publish(exchange='',
                        routing_key=props.reply_to,
                        properties=pika.BasicProperties(correlation_id = \
                                                            props.correlation_id),
                        body=str(response))
            ch.basic_ack(delivery_tag=method.delivery_tag)

    else:
        exec(n)	
        db.session.add(us)
        db.session.commit()
        response="a"
        ch.basic_publish(exchange='',
                        routing_key=props.reply_to,
                        properties=pika.BasicProperties(correlation_id = \
                                                            props.correlation_id),
                        body=str(response))
        ch.basic_ack(delivery_tag=method.delivery_tag)

# channel.basic_qos(prefetch_count=1)
channel.basic_consume(queue='writeQ', on_message_callback=on_request)

print(" [x] Awaiting RPC requests")
channel.start_consuming()'''
def callback(ch, method, properties, body):
    print(User.query.all())
            
    print(" [x] %r:%r" % (method.routing_key, body))
    n = json.loads(body)
    try:
     if (n=="clear"):
            print(User.query.all())
            db.drop_all()
            db.create_all()
            response="a"
            # ch.basic_publish(exchange='',
            #             routing_key=props.reply_to,
            #             properties=pika.BasicProperties(correlation_id = \
            #                                                 props.correlation_id),
            #             body=str(response))
            # ch.basic_ack(delivery_tag=method.delivery_tag)

     else:
        print(User.query.all())
        exec(n)	
        db.session.add(us)
        db.session.commit()
        response="a"
        # ch.basic_publish(exchange='',
        #                 routing_key=props.reply_to,
        #                 properties=pika.BasicProperties(correlation_id = \
        #                                                     props.correlation_id),
        #                 body=str(response))
    except:
        return{'notsuccefull'}
    channel.basic_publish(exchange='sync_exchange1',routing_key = 'synchronize1', body = json.dumps(n))
    return {}
try:
 connection = pika.BlockingConnection(
 pika.ConnectionParameters(host='rmq')) #!localhost to rabbitmq
 channel = connection.channel()
except:
    time.sleep(30)
finally:
 connection = pika.BlockingConnection(
 pika.ConnectionParameters(host='rmq')) #!localhost to rabbitmq
 channel = connection.channel()

channel.exchange_declare(exchange='write_exchange', exchange_type='direct')

channel.exchange_declare(exchange='sync_exchange1', exchange_type='direct')

channel.queue_declare(queue='writeQ', durable=True)

channel.queue_bind(exchange = 'write_exchange', queue = 'writeQ', routing_key = 'write')

print(' [*] Waiting for logs. To exit press CTRL+C')
channel.basic_consume(queue= 'writeQ', on_message_callback=callback, auto_ack=True)

channel.start_consuming()