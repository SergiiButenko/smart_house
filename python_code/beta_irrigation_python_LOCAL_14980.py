#!/usr/bin/python3
# -*- coding: utf-8 -*- 

from threading import Timer
from flask import Flask
from flask import jsonify, request, render_template
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
import os
import os.path
import psycopg2

app = Flask(__name__)
socketio = SocketIO(app, async_mode='eventlet')

ARDUINO_IP='http://192.168.1.10'
#ARDUINO_IP='http://185.20.216.94:5555'
RULES_FOR_BRANCHES=[None] * 10
RULES_ENABLED=True

@socketio.on_error_default
def error_handler(e):
    print('An error has occurred: ' + str(e))

def branch_on(id):
    try:
        response = requests.get(url=ARDUINO_IP+'/on', params={"params":line_id})
        json_data = json.loads(response.text)
    except requests.exceptions.RequestException as e:  # This is the correct syntax
        print(e)
        print("Can't turn on {0} branch. Exception occured".format(line_id))
    
    # this request returns status for all branches
    try:
        response_status = requests.get(url=ARDUINO_IP) 
        socketio.emit('branch_status', {'data':response_status.text})
    except requests.exceptions.RequestException as e:  # This is the correct syntax
        print(e)
        print("Can't get arduino status. Exception occured")

    return response_status

def branch_off(line_id):
    try:
        response = requests.get(url=ARDUINO_IP+'/off', params={"params":line_id})
        json_data = json.loads(response.text)
    except requests.exceptions.RequestException as e:  # This is the correct syntax
        print(e)
        print("Can't turn off {0} branch. Exception occured".format(line_id))
    
    try:
        response_status = requests.get(url=ARDUINO_IP) 
        socketio.emit('branch_status', {'data':response_status.text})
    except requests.exceptions.RequestException as e:  # This is the correct syntax
        print(e)
        print("Can't get arduino status. Exception occured")
        return None

    return response_status

#executes query and returns fetch* result
def execute_request(query, method='fetchall'):
    dir = os.path.dirname(__file__)
    sql_file = os.path.join(dir, '..','sql', query)
    conn=None
    try:
        conn = psycopg2.connect("dbname='test' user='sprinkler' host='185.20.216.94' port='35432' password='drop#'")
        # conn.cursor will return a cursor object, you can use this cursor to perform queries
        cursor = conn.cursor()
        # execute our Query
        if os.path.isfile(sql_file):
            cursor.execute(open(sql_file, "r").read())
        else:   
            cursor.execute(query)
        conn.commit()
        return getattr(cursor, method)()
    except BaseException as e:
        print("Error while performing operation with database")
        print(e)
        return None
    finally:
        if conn is not None:
            conn.close()

def get_next_active_rule(line_id):
    query="SELECT l.id, l.line_id, l.rule_id, l.timer FROM life AS l WHERE l.state = 0 AND l.active=1 AND l.line_id={0} AND timer>=now() ORDER BY date, timer LIMIT 1".format(line_id)
    res = execute_request(query, 'fetchone')
    if res is None:
        return None

    return {'id':res[0], 'line_id':res[1], 'rule_id':res[2], 'timer':res[3]}

def enable_rule():
    while True:
        time.sleep(10)
        if (RULES_ENABLED==False):
            continue

        for rule in RULES_FOR_BRANCHES: 
            if rule is None:
                continue

            if (datetime.datetime.now() >= rule['timer']): 

                if (rule['line_id'] == 7):                    
                    arduino_branch_name='pump'
                else:
                    arduino_branch_name=rule['line_id']

                if rule['rule_id'] == 1:
                    response=branch_on(rule['line_id'])
                    if response is None:
                        print("Can't turn on {0} branch".format(rule['line_id']))
                        continue
                    
                    json_data = json.loads(response.text)
                    if (json_data['variables'][str(arduino_branch_name)] == 0 ):
                        print("Can't turn on {0} branch".format(rule['line_id']))
                        continue

                    if (json_data['variables'][str(arduino_branch_name)] == 1 ):
                        print("Turned on {0} branch".format(rule['line_id']))
                        execute_request("UPDATE life SET state=1 WHERE id={0}".format(rule['id']))
                        RULES_FOR_BRANCHES[rule['line_id']]=get_next_active_rule(rule['line_id'])

                if rule['rule_id'] == 2:
                    response=branch_off(rule['line_id'])
                    if response is None:
                        print("Can't turn off {0} branch".format(rule['line_id']))
                        continue
                    
                    json_data = json.loads(response.text)
                    if (json_data['variables'][str(arduino_branch_name)] == 1 ):
                        print("Can't turn off {0} branch".format(rule['line_id']))
                        continue

                    if (json_data['variables'][str(arduino_branch_name)] == 0 ):
                        print("Turned off {0} branch".format(rule['line_id']))
                        execute_request("UPDATE life SET state=1 WHERE id={0}".format(rule['id']))
                        RULES_FOR_BRANCHES[rule['line_id']]=get_next_active_rule(rule['line_id'])
                    
thread = threading.Thread(name='enable_rule', target=enable_rule)
thread.setDaemon(True)
thread.start() 

def update_all_rules():
    for i in range(1,len(RULES_FOR_BRANCHES), 1):
        RULES_FOR_BRANCHES[i]=get_next_active_rule(i)    


def update_all_rules_daemon():
    while True:
        for i in range(1,len(RULES_FOR_BRANCHES), 1):
            RULES_FOR_BRANCHES[i]=get_next_active_rule(i)    
        time.sleep(60*60)

thread2 = threading.Thread(name='update_all_rules_daemon', target=update_all_rules_daemon)
thread2.setDaemon(True)
thread2.start() 

@app.route("/branches_names")
def branches_names():
    branch_list=[]
    res = execute_request("get_branches_names.sql", 'fetchall')
    if res == None:
        print("Can't get branches names from database")
        abort(500)

    for row in res:
        branch_list.append( {'id':row[0], 'name':row[1]})

    return jsonify(
            list=branch_list
        )

@app.route("/beta")
def beta():
    return app.send_static_file('index.html')


@app.route("/list")
def list():
    list_arr = execute_request("select_all_records.sql", 'fetchall')
    rows=[]
    #rules=['',"Начать полив","Остановить полив","Неактивно"]
    rules=['',"Start","Stop","Deactivated"]
    
    for row in list_arr:
        id=row[0]
        branch_id=row[1]
        rule_id=row[2]        
        state=row[3]
        timer=row[5]
        active=row[6]
        outdated=0
        if (state==0 and timer<datetime.datetime.now() - datetime.timedelta(minutes=1)):
            outdated=1

        rows.append({'id':row[0], 'branch_id':row[1], 'rule_id':row[2], 'rule_text':rules[row[2]], 'state':row[3], 
            'timer':"{:%A, %H:%M, %d %b %Y}".format(row[5]), 'outdated':outdated, 'active':active})
    return render_template('list.html', my_list=rows)

@app.route("/")
def hello():
    return str(RULES_FOR_BRANCHES)

@app.route("/activate_rule")
def activate_rule():
    id=int(request.args.get('id'))
    execute_request("UPDATE life SET active=1 WHERE id={0}".format(id))
    update_all_rules()

    list_arr = execute_request("select_all_records.sql", 'fetchall')
    rows=[]
    #rules=['',"Начать полив","Остановить полив","Неактивно"]
    rules=['',"Start","Stop","Deactivated"]
    
    for row in list_arr:
        id=row[0]
        branch_id=row[1]
        rule_id=row[2]        
        state=row[3]
        timer=row[5]
        active=row[6]
        outdated=0
        if (state==0 and timer<datetime.datetime.now() - datetime.timedelta(minutes=1)):
            outdated=1

        rows.append({'id':row[0], 'branch_id':row[1], 'rule_id':row[2], 'rule_text':rules[row[2]], 'state':row[3], 
            'timer':"{:%A, %H:%M, %d %b %Y}".format(row[5]), 'outdated':outdated, 'active':active})
    
    template=render_template('table_only.html', my_list=rows)
    socketio.emit('list_update', {'data':template})
    return template

@app.route("/deactivate_rule")
def deactivate_rule():
    id=int(request.args.get('id'))
    execute_request("UPDATE life SET active=0 WHERE id={0}".format(id))
    update_all_rules()

    list_arr = execute_request("select_all_records.sql", 'fetchall')
    rows=[]
    #rules=['',"Начать полив","Остановить полив","Неактивно"]
    rules=['',"Start","Stop","Deactivated"]
    
    for row in list_arr:
        id=row[0]
        branch_id=row[1]
        rule_id=row[2]        
        state=row[3]
        timer=row[5]
        active=row[6]
        outdated=0
        if (state==0 and timer<datetime.datetime.now() - datetime.timedelta(minutes=1)):
            outdated=1

        rows.append({'id':row[0], 'branch_id':row[1], 'rule_id':row[2], 'rule_text':rules[row[2]], 'state':row[3], 
            'timer':"{:%A, %H:%M, %d %b %Y}".format(row[5]), 'outdated':outdated, 'active':active})
    
    template=render_template('table_only.html', my_list=rows)
    socketio.emit('list_update', {'data':template})
    return template

@app.route("/deactivate_all_rules")
def deactivate_all_rules():
    id=int(request.args.get('id'))
    #1-24h;2-7d;3-on demand
    if (id==1):
        execute_request("UPDATE life SET active=0 WHERE timer>= now() AND timer<=now()::date+1".format(id))
        update_all_rules()    

    if (id==2):
        execute_request("UPDATE life SET active=0 WHERE timer>= now() AND timer<=now()::date+7".format(id))        
        update_all_rules()

    if (id==3):
        RULES_ENABLED=False

    return 'OK'

@app.route('/arduino_status', methods=['GET'])
def arduino_status():
    try:
        response_status = requests.get(url=ARDUINO_IP) 
        return (response_status.text, response_status.status_code)
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
    
    execute_request("INSERT INTO public.life(line_id, rule_id, state, date, timer) VALUES ({0}, {1}, {2}, '{3}', '{4}')".format(id, 1, 1, now.date(), now), 'fetchone')
    res=execute_request("INSERT INTO public.life(line_id, rule_id, state, date, timer) VALUES ({0}, {1}, {2}, '{3}', '{4}') RETURNING id,line_id, rule_id, timer".format(id, 2, 0, now.date(), now_plus), 'fetchone')
    RULES_FOR_BRANCHES[id]={'id':res[0], 'line_id':res[1], 'rule_id':res[2], 'timer':res[3]}
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
    
    now = datetime.datetime.now()
    if RULES_FOR_BRANCHES[id] is not None:
        execute_request("UPDATE public.life SET state=2 WHERE id = {0}".format(RULES_FOR_BRANCHES[id]['id']), 'fetchone')
    else:
        execute_request("INSERT INTO public.life(line_id, rule_id, state, date, timer) VALUES ({0}, {1}, {2}, '{3}', '{4}')".format(id, 2, 1, now.date(), now), 'fetchone')

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

    
