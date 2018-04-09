#!/usr/bin/env python

import rospy
import setproctitle
import signal
from std_msgs.msg import String
from std_srvs.srv import SetBool
from flask import Flask, render_template
from flask_sockets import Sockets
from gevent import pywsgi
from geventwebsocket.handler import WebSocketHandler

setproctitle.setproctitle('ros_speech_recognition')

topic_name = 'saam_speech_to_text'

app = Flask(__name__)
app.latest_connection = None
sockets = Sockets(app)

rospy.init_node(topic_name)
pub = rospy.Publisher('/{}/result'.format(topic_name), String, queue_size=10)


def service_handler(req):
    if not app.latest_connection:
        return False, 'ws is not available'

    req = 'stop' if req.data else 'start'
    rospy.loginfo("Speech controller : " + req)
    app.latest_connection.send(req)
    return True, 'ok'


service = rospy.Service('/{}/controller'.format(topic_name), SetBool, service_handler)


@sockets.route('/ws')
def socket_handler(ws):
    rospy.loginfo("New client on websocket connected ...")
    app.latest_connection = ws

    while not ws.closed:
        message = ws.receive()
        if type(message) is not unicode:
            continue
        message = message.strip()
        rospy.loginfo("New speech detected, " + message)
        pub.publish(message)

    app.latest_connection = None
    rospy.loginfo("Websocket client has been closed !")


@app.route('/')
def hello():
    return render_template('index.html')


rospy.loginfo("Server is running ...")


def stop_server(*args, **kwargs):
    rospy.loginfo("Stopping server ...")
    server.stop(3)


signal.signal(signal.SIGINT, stop_server)

server = pywsgi.WSGIServer(('localhost', 8081), app, handler_class=WebSocketHandler)
server.serve_forever()
