#!/usr/bin/python3

from threading import Timer
from flask import Flask
from flask import jsonify, request
from flask import abort

# for socketio
from eventlet import wsgi
import eventlet
eventlet.monkey_patch()

from flask_socketio import SocketIO
from flask_socketio import send, emit

import datetime
import json, requests
import threading
import time

app = Flask(__name__)
db = SQLAlchemy(app)

socketio = SocketIO(app, async_mode='eventlet')

ARDUINO_IP='http://192.168.1.10'
#ARDUINO_IP='http://185.20.216.94:5555'
RULES_FOR_BRANCHES=[None] * 8

def enable_rule():
    while True:
        time.sleep(10)
        for rule in RULES_FOR_BRANCHES: 
            if (rule is not None) and (datetime.datetime.now() >= rule['finish']):            
                try:
                    response = requests.get(url=ARDUINO_IP+'/off', params={"params":rule['id']})
                    json_data = json.loads(response.text)
                    if (json_data['return_value'] == 0 ):
                        print("Turned off {0} branch".format(rule['id']))
                        RULES_FOR_BRANCHES[rule['id']]=None
                        
                    if (json_data['return_value'] == 1 ):
                        print("Can't turn off {0} branch".format(rule['id']))
                except requests.exceptions.RequestException as e:  # This is the correct syntax
                    print(e)
                    print("Can't turn off {0} branch. Exception occured".format(rule['id']))

                
                try:
                    response_status = requests.get(url=ARDUINO_IP) 
                    socketio.emit('branch_status', {'data':response_status.text})
                except requests.exceptions.RequestException as e:  # This is the correct syntax
                    print(e)
                    print("Can't get arduino status. Exception occured")
                    
thread = threading.Thread(name='enable_rule', target=enable_rule)
thread.setDaemon(True)
thread.start() 

#executes query and returns fetch* result
def execute_request(query, method):
    dir = os.path.dirname(__file__)
    sql_file = os.path.join(dir, '..','sql', query)
    try:
        conn = psycopg2.connect("dbname='test' user='sprinkler' host='185.20.216.94' port='35432' password='drop#'")
        # conn.cursor will return a cursor object, you can use this cursor to perform queries
        cursor = conn.cursor()
        # execute our Query
        cursor.execute(open(sql_file, "r").read())
        return getattr(cursor, method)()
    except BaseException:
        print("Unable to connect to the database")
        return None
    finally:
        if conn:
            conn.close()

@app.route("/update_rules")
def update_rules(): 
    return 1

@app.route("/")
def hello():
    return str(RULES_FOR_BRANCHES)

@app.route('/arduino_status', methods=['GET'])
def arduino_status():
    try:
        response_status = requests.get(url=ARDUINO_IP) 
        return (response.text, response.status_code)
    except requests.exceptions.RequestException as e:  # This is the correct syntax
        print(e)
        print("Can't get arduino status. Exception occured")
        abort(404)
    
@app.route('/activate_branch', methods=['GET'])
def activate_branch():
    id=int(request.args.get('id'))
    time_min=int(request.args.get('time'))
    
    try:
        response_on = requests.get(url=ARDUINO_IP+'/on', params={"params":id}) 
    except requests.exceptions.RequestException as e:  # This is the correct syntax   
        print(e)
        print("Can't turn on branch id={0}. Exception occured".format(id))
        abort(404)

    now = datetime.datetime.now()
    now_plus = now + datetime.timedelta(minutes = time_min)
    
    RULES_FOR_BRANCHES[id]={'id':id, 'start':now, 'finish': now_plus}
    
    try:
        response_status = requests.get(url=ARDUINO_IP)
        socketio.emit('branch_status', {'data':response_status.text})
    except requests.exceptions.RequestException as e:  # This is the correct syntax   
        print(e)
        print("Can't get arduino status. Exception occured")
        abort(404)

    return (response_status.text, response_status.status_code)

@app.route('/deactivate_branch', methods=['GET'])
def deactivate_branch():
    id=int(request.args.get('id'))
    
    try:
        response_off = requests.get(url=ARDUINO_IP+'/off', params={"params":id})
    except requests.exceptions.RequestException as e:  # This is the correct syntax   
        print(e)
        print("Can't turn on branch id={0}. Exception occured".format(id))
        abort(404)
        
    RULES_FOR_BRANCHES[id]=None

    try:
        response_status = requests.get(url=ARDUINO_IP)
        socketio.emit('branch_status', {'data':response_status.text})
    except requests.exceptions.RequestException as e:  # This is the correct syntax   
        print(e)
        print("Can't get arduino status. Exception occured")
        abort(404)

    return (response_status.text, response_status.status_code)

@app.route("/weather")
def weather():
    url = 'http://apidev.accuweather.com/currentconditions/v1/360247.json?language=en&apikey=hoArfRosT1215'
    response = requests.get(url=url)
    json_data = json.loads(response.text)
    return jsonify(
        temperature=str(json_data[0]['Temperature']['Metric']['Value'])
    )

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE')
    return response


if __name__ == "__main__":
    socketio.run(app, host='0.0.0.0', port=7543, debug=True)

    
