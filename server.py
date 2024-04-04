#!/usr/bin/env python3
import os
import os.path
import time
import secrets
import subprocess
import mimetypes
import ssl
import ftransc
import requests
import json
from operator import itemgetter
import asyncio
import time
from random import *
import re
from threading import Timer
import queue

from flask import request, session, Flask, send_file, jsonify
from flask_socketio import SocketIO, Namespace, disconnect


history = []

##
# Danomation
# GitHub: https://github.com/danomation
# Patreon https://www.patreon.com/Wintermute310
##

#set the storage location for your drawings
history_file_path = "/var/www/html/history.txt"

app = Flask("shared_canvas")
socketio = SocketIO(app, cors_allowed_origins="*")

from flask_cors import CORS
CORS(app, resources={r"/*": {"origins": "*"}})

#requires https with cert
ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
ssl_context.check_hostname = False
ssl_cert = "/etc/letsencrypt/live/**YOURDOMAIN**/fullchain.pem"
ssl_key = "/etc/letsencrypt/live/**YOURDOMAIN**/privkey.pem"
ssl_context.load_cert_chain(ssl_cert, keyfile=ssl_key)

@app.errorhandler(Exception)
def handle_exception(e):
    if isinstance(e, HTTPException):
        return e
    return render_template("500_generic.html", e=e), 500


user_sessions = {}

def loadhistory():
    filePath = history_file_path
    if os.path.exists(filePath):
        f = open(filePath, "r")
        f_lines = f.readlines()
        for line in f_lines:
            history.append(line)
        f.close()
    else:
        print("no history.txt to load")

def writehistory():
    filePath = history_file_path
    f = open(filePath, "w")
    for line in history:
        if "," in line:
            stripped = line.replace("\n", "")
            f.write(stripped + "\n")
    f.close()

class CanvasNamespace(Namespace):
    def __init__(self, namespace=None):
        super().__init__(namespace)
        self.user_sessions = {}

    def on_connect(self):
        session['sid'] = request.sid
        session['color'] = str(secrets.token_hex(3))
        print('-- Session ' + str(session['sid']) + ' connected to /shared_canvas')
        for data in history:
            self.emit("draw", {'type': 'text', 'data': data}, room=session['sid'])

    def on_disconnect(self):
        writehistory()
        print('-- Session ' + str(session['sid']) + ' disconnected from /shared_canvas')

    def on_canvas(self, data):
        current_session = self.user_sessions[request.sid]

    def on_draw(self, data):
        dataToSend = {'type': 'text', 'data': data}
        history.append(data)
        self.emit("draw", dataToSend)

loadhistory()

socketio.on_namespace(CanvasNamespace('/shared_canvas'))
socketio.run(app, host='0.0.0.0', port=6979, ssl_context=ssl_context, allow_unsafe_werkzeug=True)
