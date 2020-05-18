#!/usr/bin/env python
#libraries
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


#creating watch on workers
@zk.ChildrenWatch("/Workers/",send_event = True)
def watch_children(children,event):
    print("Children are now: %s" % children)
    print("Slave Event",event)
    if(event == None):
        pass
    elif(event.type is DELETED):
        print("Slave deleted")


class reading_response(object):

    def __init__(self):
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host='rmq'))

        self.channel = self.connection.channel()
        self.channel.basic_qos(prefetch_count = 0)

        #exchange declaration
        self.channel.exchange_declare(exchange='read_exchange1', exchange_type='direct')
        self.channel.exchange_declare(exchange='response_exchange1', exchange_type='direct')
        self.channel.exchange_declare(exchange='write_exchange', exchange_type='direct')

        #queue declaration
        self.channel.queue_declare(queue='responseQ', durable= True)
        self.channel.queue_bind(exchange = 'response_exchange1', queue = 'responseQ', routing_key = 'response')

        #basic consume definition
        self.channel.basic_consume(
            queue='responseQ',
            on_message_callback=self.on_response,
            auto_ack=True)


    #defining response function which sets response variable to the response received
    def on_response(self, ch, method, props, body):
        print("#####", body)
        if self.corr_id == props.correlation_id:#matching correlation ID
            print("@@@@", body)
            self.response = json.loads(body)


    def call(self, n):
        self.response = None
        self.corr_id = str(uuid.uuid4())  #generating correlation ID


        #publish configuration
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

#starting timer
time_start=time.time()
counter=0  #to keep track of number of requests

sl=2

#to count number of active slaves
def no_of_slaves():
    client = docker.from_env()
    pc=0
    
    for i in client.containers.list():
        if(i.name.split("_")[1]=="producer"):#naming convention for slave - zookeeperamqp_producer_slavenumber
            pc+=1
    return pc

#creating slave
def create_slave():
    global sl
    sl+=1
    client = docker.from_env()

    #creating a slave container with name zookeeperamqp_producer_<sl>
    c=client.containers.run(image='zookeeperamqp_producer:latest',command= ['python','slave.py'],links = {'zookeeperamqp_rmq_1':'rmq'},detach=True,name="zookeperamqp_producer_"+str(sl),network="zookeeperamqp_default")
    print(c.name,c.id)



#killing slaves
def slavekill():
    client = docker.from_env()
    pidmax=-3
    pname=""
    for i in client.containers.list():
        if(i.name.split("_")[1]=="producer"):

                pid = int(i.top()['Processes'][0][1])#getting pid of the container

                if(pid>pidmax):
                    pidmax=pid
                    pname=i.name

    a=client.containers.get(pname)
    a.kill()
    a.remove()


#adjusting slaves
def adjust_slaves(count):

    #calculating number of required slaves
    target_slaves = int(math.ceil(count/20))

    #number of active slaves
    slaves = no_of_slaves()

    if (target_slaves>slaves):

        #need to increase slave

        for i in range(slaves, target_slaves):
            print("increasing slaves")
            create_slave()

    elif (slaves>target_slaves):

        #need to decrease slave

        for i in range(target_slaves,slaves):
            slavekill()



#keeping count of number of read requests for an interval of 120s and adjusting the slaves accordingly
def count_track():
    global counter
    global time_start
    time_end = time.time()

    print("counter",counter,time_end - time_start)

    #checking if time interval > 120s
    if time_end - time_start >= 120:
        val = counter
        counter=0
        time_start = time.time()
        time_end = time.time()

        #adjusting slave
        adjust_slaves(val)


#libraries
from flask_api import status
from datetime import datetime
from flask import Flask, render_template,jsonify,request,abort
from flask_sqlalchemy import SQLAlchemy
import requests
app = Flask(__name__)



#writing to database
@app.route("/api/v1/db/write",methods=["POST"])
def write_db():

    l=request.get_json()['insert']

    #command to create object of class tablename ex - User("anand","password")
    me =("global us;us="+request.get_json()["table"]+"("+ str(l)[1:-1]+")")

    #publishing me variable to writeQ
    connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='rmq'))
    channel = connection.channel()
    channel.basic_publish(exchange='write_exchange', routing_key = 'write', body= json.dumps(me))
    return {}


#crash slave api
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

#crash master api
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


#list of PIDs of workers-master+slave
@app.route("/api/v1/worker/list",methods=["GET"])
def pid():
    count_track()
    client = docker.from_env()
    print("client created")
    pids=[]
    for i in client.containers.list():

        #if master or slave i.e. name is zookeeperamqp_consumer_number or zookeeperamqp_producer_number
        if(i.name.split("_")[1]=="consumer" or i.name.split("_")[1]=="producer"):
                print(i.name,i.top()['Processes'][0][1])
                pid = int(i.top()['Processes'][0][1])
                print(pid)
                pids+=[pid]
    print(pids)

    #returning sorted list of PIDs
    return (json.dumps(sorted(pids)))


#read request
@app.route("/api/v1/db/read",methods=["POST"])
def read_db():

    global counter
    counter+=1

    #increasing number of request counter and adjusting number of slaves accordingly
    count_track()

    #creating reading_response() object
    response_rpc = reading_response()

    #publishing json received to readQ
    response = (response_rpc.call(request.get_json()))

    print("global a;a="+response[:])

    #changing the response received into proper json
    exec(("global a;a="+response[:]))


    print(jsonify(a))

    print(json.dumps(a))

    #if internal error occurs at slave
    if(response=="\"500\""):

        #return status code 500
        return("",status.HTTP_500_INTERNAL_SERVER_ERROR)

    return (jsonify(a))


#clear database
@app.route("/api/v1/db/clear",methods=["POST"])
def clr_db():

    
    connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='rmq'))
    channel = connection.channel()
    
    #publishing 'clear' to writeQ as body
    channel.basic_publish(exchange='write_exchange', routing_key = 'write', body= json.dumps("clear"))
    
    return {}
	


if __name__ == '__main__':	
    app.run(host='0.0.0.0',port=80)
    