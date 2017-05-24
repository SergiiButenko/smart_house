from threading import Timer
from flask import Flask
from flask import jsonify, request

from flask_socketio import SocketIO
from flask_socketio import send, emit

import datetime
import json, requests
import threading
import time

app = Flask(__name__)
socketio = SocketIO(app)

ARDUINO_IP='http://192.168.1.10'
#ARDUINO_IP='http://185.20.216.94:5555'

RULES_FOR_BRANCHES=[None,None,None,None,None,None,None,None]

def update_data():
    while True:
        time.sleep(10)
        for rule in RULES_FOR_BRANCHES: 
            print(rule)
            if (rule is not None) and (datetime.datetime.now() >= rule['finish']):            
                response = requests.get(url=ARDUINO_IP+'/off', params={"params":rule['id']})
                json_data = json.loads(response.text)
                if (json_data['return_value'] == 0 ):
                    print("Turned off {0} branch".format(rule['id']))
                    RULES_FOR_BRANCHES[rule['id']]=None
                    
                if (json_data['return_value'] == 1 ):
                    print("Can't turn off {0} branch".format(rule['id']))
        
                response_status = requests.get(url=ARDUINO_IP) 
                socketio.emit('branch_status', {'data':response_status.text})

thread = threading.Thread(name='update_data', target=update_data)
thread.setDaemon(True)
thread.start()

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE')
    return response

@app.route("/")
def hello():
    return str(RULES_FOR_BRANCHES)

@app.route('/arduino_status', methods=['GET'])
def arduino_status():
    response = requests.get(url=ARDUINO_IP)
    return (response.text, response.status_code)

@app.route('/activate_branch', methods=['GET'])
def activate_branch():
    id=int(request.args.get('id'))
    time_min=int(request.args.get('time'))
    
    response_on = requests.get(url=ARDUINO_IP+'/on', params={"params":id}) 

    now = datetime.datetime.now()
    now_plus = now + datetime.timedelta(minutes = time_min)
    
    RULES_FOR_BRANCHES[id]={'id':id, 'start':now, 'finish': now_plus}
    
    response_status = requests.get(url=ARDUINO_IP)
    socketio.emit('branch_status', {'data':response_status.text})

    return (response_on.text, response_on.status_code)

@app.route('/deactivate_branch', methods=['GET'])
def deactivate_branch():
    id=int(request.args.get('id'))
    
    response_off = requests.get(url=ARDUINO_IP+'/off', params={"params":id})

    RULES_FOR_BRANCHES[id]=None

    response_status = requests.get(url=ARDUINO_IP)         
    socketio.emit('branch_status', {'data':response_status.text})

    return (response_off.text, response_off.status_code)

@app.route("/weather")
def weather():
    url = 'http://apidev.accuweather.com/currentconditions/v1/360247.json?language=en&apikey=hoArfRosT1215'
    response = requests.get(url=url)
    json_data = json.loads(response.text)
    return jsonify(
        temperature=str(json_data[0]['Temperature']['Metric']['Value'])
    )

@app.route('/gitwebhook', methods=['POST'])
def git_post():
    return "Done!"

if __name__ == "__main__":
    socketio.run(app)
