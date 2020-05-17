#!/usr/bin/env python
import pika
import uuid
import docker
import json
import time
import math   
import logging
from kazoo.client import KazooClient
from kazoo.client import KazooState
import socket
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

# if(zk.exists("/Workers")):
# 	zk.delete("/Workers", recursive=True)

@zk.ChildrenWatch("/Workers/",send_event = True)
def watch_children(children,event):
    print("Children are now: %s" % children)
    print("Slave Event",event)
    if(event == None):
        pass
    elif(event.type is DELETED):
        print("Slave deleted")

# connection = pika.BlockingConnection(
#             pika.ConnectionParameters(host='rmq'))
# channel = connection.channel()
class reading_response(object):

    def __init__(self):
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host='rmq'))

        self.channel = self.connection.channel()
        self.channel.basic_qos(prefetch_count = 0)

        self.channel.exchange_declare(exchange='read_exchange1', exchange_type='direct')
        self.channel.exchange_declare(exchange='response_exchange1', exchange_type='direct')
        self.channel.exchange_declare(exchange='write_exchange', exchange_type='direct')

        self.channel.queue_declare(queue='responseQ', durable= True)
        self.channel.queue_bind(exchange = 'response_exchange1', queue = 'responseQ', routing_key = 'response')
        # self.callback_queue = result.method.queue

        self.channel.basic_consume(
            queue='responseQ',
            on_message_callback=self.on_response,
            auto_ack=True)

    def on_response(self, ch, method, props, body):
        print("#####", body)
        if self.corr_id == props.correlation_id:
            print("@@@@", body)
            self.response = json.loads(body)

    def call(self, n):
        self.response = None
        self.corr_id = str(uuid.uuid4())
        # print(n, type(n))
        self.channel.basic_publish(
            exchange='read_exchange1',
            routing_key='read',
            properties=pika.BasicProperties(
                reply_to='responseQ',
                correlation_id=self.corr_id,
            ),
            body= json.dumps(n))
        print("here already!")
        while self.response is None:
            self.connection.process_data_events()
        self.connection.close()
        return json.dumps(self.response)

'''
class RRpcClient(object):

    def __init__(self):
        # self.channel.queue_declare(queue='readQ',durable=True)
        result = channel.queue_declare(queue='responseQ', exclusive=True)
        self.callback_queue = result.method.queue

        channel.basic_consume(
            queue=self.callback_queue,
            on_message_callback=self.on_response,
            auto_ack=True)

    def on_response(self, ch, method, props, body):
        if self.corr_id == props.correlation_id:
            self.response = body

    def call(self, n):
        self.response = None
        self.corr_id = str(uuid.uuid4())
        print("before publish")
        channel.basic_publish(
            exchange='',
            routing_key='ReadQ',
            properties=pika.BasicProperties(
                reply_to=self.callback_queue,
                correlation_id=self.corr_id,
                content_type="text/plain",
            ),
            body=str(n))
        print("data pushed")
        while self.response is None:
            connection.process_data_events()
        # self.connection.close()
        return (self.response)


class WRpcClient(object):

    def __init__(self):
        # self.channel.queue_declare(queue='writeQ',durable=True)

        result = channel.queue_declare(queue='', exclusive=True)
        self.callback_queue = result.method.queue

        channel.basic_consume(
            queue=self.callback_queue,
            on_message_callback=self.on_response,
            auto_ack=True)

    def on_response(self, ch, method, props, body):
        if self.corr_id == props.correlation_id:
            self.response = body

    def call(self, n):
        self.response = None
        self.corr_id = str(uuid.uuid4())
        print("before publish")
        channel.basic_publish(
            exchange='',
            routing_key='WriteQ',
            properties=pika.BasicProperties(
                reply_to=self.callback_queue,
                correlation_id=self.corr_id,
                content_type="text/plain",
            ),
            body=str(n))
        while self.response is None:
            connection.process_data_events()
        # self.connection.close()
        return (self.response)

'''
time_start=time.time()
counter=0
counti=0
sl=2
def no_of_slaves():
    client = docker.from_env()
    pc=0
    
    for i in client.containers.list():
        if(i.name.split("_")[1]=="producer"):
            pc+=1
    return pc
def create_slave():
    global sl
    sl+=1
    client = docker.from_env()
    c=client.containers.run(image='zookeeperamqp_producer:latest',command= ['python','slave.py'],links = {'zookeeperamqp_rmq_1':'rmq'},detach=True,name="zookeperamqp_producer_"+str(sl),network="zookeeperamqp_default")
    print(c.name,c.id)
# create_slave()
print("slave_created")
def slavekill():
    client = docker.from_env()
    pidmax=-3
    pname=""
    for i in client.containers.list():
        if(i.name.split("_")[1]=="producer"):
                pid = int(i.top()['Processes'][0][1])
                if(pid>pidmax):
                    pidmax=pid
                    pname=i.name
    a=client.containers.get(pname)
    a.kill()
    a.remove()
def adjust_slaves(count):
    target_slaves = int(math.ceil(count/20))
    slaves = no_of_slaves()
    if (target_slaves>slaves):
        print("less slaves")
    #     print("Initial Container", list_container)
        for i in range(slaves, target_slaves):
            print("increasing slaves")
            create_slave()
    # else:
        # print("more slaves")
        # for i in range(target_slaves, slaves):
            # print("decreasing slaves")
            # slavekill()

def count_track():
    global counter
    global time_start
    time_end = time.time()

    print("counter",counter,time_end - time_start)
    if time_end - time_start >= 120:
        val = counter
        counter=0
        time_start = time.time()
        time_end = time.time()

        adjust_slaves(val)

from flask_api import status
from datetime import datetime
from flask import Flask, render_template,jsonify,request,abort
from flask_sqlalchemy import SQLAlchemy
import requests
app = Flask(__name__)
# write_rpc=WRpcClient()
# read_rpc=RRpcClient()

# channel.queue_declare(queue='task_queue', durable=True)

@app.route("/a",methods=["GET"])
def don():
#     connection = pika.BlockingConnection(
#     pika.ConnectionParameters(host='rmq'))
# channel = connection.channel()

    # for i in range(15):
    #     message = "Hello World! " + str(i)
    #     channel.basic_publish(
    #         exchange='',
    #         routing_key='task_queue',
    #         body=message,
    #         properties=pika.BasicProperties(
    #             delivery_mode=2,  # make message persistent
    #         ))

    #     print(" [x] Sent %r" % message)
    # # connection.close()
    return(jsonify())

@app.route("/api/v1/db/write",methods=["POST"])
def write_db():
    l=request.get_json()['insert']
    me =("global us;us="+request.get_json()["table"]+"("+ str(l)[1:-1]+")")
    # write_rpc.call(me)
    # print("Sent to server")
    
    connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='rmq'))
    channel = connection.channel()
    channel.basic_publish(exchange='write_exchange', routing_key = 'write', body= json.dumps(me))
    return {}
    '''
	exec(me)	
	db.session.add(us)
	db.session.commit()
    '''
    # return (jsonify())

@app.route("/api/v1/crash/slave",methods=["POST"])
def slave():
    client = docker.from_env()
    pidmax=-3
    pname=""
    for i in client.containers.list():
        if(i.name.split("_")[1]=="producer"):
                pid = int(i.top()['Processes'][0][1])
                if(pid>pidmax):
                    pidmax=pid
                    pname=i.name
    a=client.containers.get(pname)
    a.kill()
    a.remove()
 
    time.sleep(5)
    create_slave()
    return (jsonify())   
@app.route("/api/v1/crash/master",methods=["POST"])
def master():
    client = docker.from_env()
    pidmax=-3
    pname=""
    for i in client.containers.list():
        if(i.name.split("_")[1]=="consumer"):
                pid = int(i.top()['Processes'][0][1])
                if(pid>pidmax):
                    pidmax=pid
                    pname=i.name
    print(pidmax,pname)
    a=client.containers.get(pname)
    a.kill()
    a.remove()
    return (jsonify())    

@app.route("/api/v1/worker/list",methods=["GET"])
def pid():
    count_track()
    client = docker.from_env()
    print("client created")
    pids=[]
    for i in client.containers.list():
        if(i.name.split("_")[1]=="consumer" or i.name.split("_")[1]=="producer"):
                print(i.name,i.top()['Processes'][0][1])
                pid = int(i.top()['Processes'][0][1])
                print(pid)
                pids+=[pid]
    print(pids)
    return (json.dumps(sorted(pids)))

@app.route("/api/v1/db/read",methods=["POST"])
def read_db():
# 	{
# “table”: “table name”,
# “columns”: [“column name”,],
# “where”: “[column=='value',"fhgf>=yu"]”
# }
    '''try:
        me =("global us;us="+request.get_json()["table"]+".query.filter"+"("+request.get_json()["where"]+").all()")
    except:
        me =("global us;us="+request.get_json()["table"]+".query.all()")
    print(me)'''
    # response=read_rpc.call(me)
    # print("Sent to server")
    # return (response.decode("utf-8"))
	# # db.session.add(me)
	# db.session.commit()
    global counter
    counter+=1
    count_track()
    response_rpc = reading_response()
    response = (response_rpc.call(request.get_json()))
    print("global a;a="+response[:])
    exec(("global a;a="+response[:]))
    print(jsonify(a))
    print(json.dumps(a))
    if(response=="\"500\""):
        return("",status.HTTP_500_INTERNAL_SERVER_ERROR)
    return (jsonify(a))

@app.route("/api/v1/db/clear",methods=["POST"])
def clr_db():
    
    connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='rmq'))
    channel = connection.channel()
    channel.basic_publish(exchange='write_exchange', routing_key = 'write', body= json.dumps("clear"))
    return {}
	


if __name__ == '__main__':	
    app.run(host='0.0.0.0',port=80)
    