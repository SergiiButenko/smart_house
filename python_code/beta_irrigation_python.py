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
from locale import setlocale, LC_ALL
from time import strftime

# added logging
import logging
logging.basicConfig(format='%(asctime)s - %(process)d - %(processName)s - %(threadName)s - %(levelname)s - %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.INFO)


app = Flask(__name__)
socketio = SocketIO(app, async_mode='eventlet', engineio_logger=True)


ARDUINO_IP='http://192.168.1.10'
#ARDUINO_IP='http://185.20.216.94:5555'

RULES_FOR_BRANCHES=[None] * 10
threadErrors = [] #global list

RULES_ENABLED=True
setlocale(LC_ALL, 'ru_UA.utf-8')

@socketio.on_error_default
def error_handler(e):
	logging.error('error_handler for socketio. An error has occurred: ' + str(e))

@socketio.on('connect')
def connect():
    logging.info('Client connected')

@socketio.on('disconnect')
def disconnect():
    logging.info('Client disconnected')


def send_message(channel, data):
	try:
		socketio.emit(channel, data)
		logging.info('Message was sent')
	except Exception as e:
		logging.error(e)
		logging.error("Can't send message. Exeption occured")

def branch_on(line_id):
	try:
		response = requests.get(url=ARDUINO_IP+'/on', params={"params":line_id})
		json_data = json.loads(response.text)

		logging.info('Branch {0} is turned on by rule'.format(line_id))
	except requests.exceptions.RequestException as e:  # This is the correct syntax
		logging.error(e)
		logging.error("Can't turn on {0} branch by rule. Exception occured".format(line_id))
		
		time.sleep(1)
	# this request returns status for all branches
	try:
		response_status = requests.get(url=ARDUINO_IP)
		send_message('branch_status', {'data':response_status.text})
		logging.info("Arudino status retreived. by rule")
	except requests.exceptions.RequestException as e:  # This is the correct syntax
		logging.error(e)
		logging.error("Can't get arduino status. by rule. Exception occured")

	return response_status

def branch_off(line_id):
	try:
		response = requests.get(url=ARDUINO_IP+'/off', params={"params":line_id})
		json_data = json.loads(response.text)

		logging.info('Branch {0} is turned off by rule'.format(line_id))
	#except requests.exceptions.RequestException as e:  # This is the correct syntax
	except Exception as e:
		logging.error(e)
		logging.error("Can't turn off {0} branch by rule. Exception occured".format(line_id))

		time.sleep(1)
	try:
		response_status = requests.get(url=ARDUINO_IP)
		send_message('branch_status', {'data':response_status.text})
		logging.info("Arudino status retreived. by rule")
	#except requests.exceptions.RequestException as e:  # This is the correct syntax
	except Exception as e:  # This is the correct syntax
		logging.error(e)
		logging.error("Can't get arduino status. by rule. Exception occured")
		return None

	return response_status

#executes query and returns fetch* result
def execute_request(query, method='fetchall'):
	conn=None
	try:
		conn = psycopg2.connect("dbname='test' user='sprinkler' host='185.20.216.94' port='35432' password='drop#'")
		# conn.cursor will return a cursor object, you can use this cursor to perform queries
		cursor = conn.cursor()
		# execute our Query
		cursor.execute(query)
		conn.commit()
		logging.debug("db request '{0}' executed".format(query))
		return getattr(cursor, method)()
	except Exception as e:
		logging.error("Error while performing operation with database: {0}".format(e))
		return None
	finally:
		try:
			if conn is not None:
				conn.close()
		except Exception as e:
			logging.error("Error while closing connection with database: {0}".format(e))

def get_next_active_rule(line_id):
	query="SELECT l.id, l.line_id, l.rule_id, l.timer FROM life AS l WHERE l.state = 0 AND l.active=1 AND l.line_id={0} AND timer>=now() ORDER BY timer LIMIT 1".format(line_id)
	res = execute_request(query, 'fetchone')
	if res is None:
		return None

	logging.info("Next active rule retrieved for line id {0}".format(line_id))
	return {'id':res[0], 'line_id':res[1], 'rule_id':res[2], 'timer':res[3]}

def update_all_rules():
	try:
		global RULES_FOR_BRANCHES
		for i in range(1,len(RULES_FOR_BRANCHES), 1):
			RULES_FOR_BRANCHES[i]=get_next_active_rule(i)
		logging.info("Rules updated")
	except Exception as e:
		logging.error("Exeption occured while updating all rules. {0}".format(e))

def update_all_rules_daemon():
	global RULES_FOR_BRANCHES
	logging.info("update_all_rules_daemon started")
	while True:
		time.sleep(60*10)
		try:
			for i in range(1,len(RULES_FOR_BRANCHES), 1):
				RULES_FOR_BRANCHES[i]=get_next_active_rule(i)
			logging.info("Rules updated by deamon")
		except Exception as e:
			logging.error("Exeption occured while updating all rules by deamon. {0}".format(e))

	logging.info("update_all_rules_daemon stoped")

thread2 = threading.Thread(name='update_all_rules_daemon', target=update_all_rules_daemon)
thread2.setDaemon(True)
thread2.start()

def enable_rule():
	global RULES_FOR_BRANCHES
	try:
		logging.info("enable rule thread started.")
		while True:
			logging.info("enable_rule_daemon heartbeat")	
			logging.info("RULES_FOR_BRANCHES from deamon: {0}".format(str(RULES_FOR_BRANCHES)))	
			time.sleep(10)
			
			if (RULES_ENABLED==False):
				logging.warn("All rules are disabled on demand")
				continue

			for rule in RULES_FOR_BRANCHES:
				if rule is None:
					continue

				logging.info("Rule '{0}' is going to be executed".format(str(rule)))

				if (datetime.datetime.now() >= rule['timer']):

					if (rule['line_id'] == 7):
						arduino_branch_name='pump'
					else:
						arduino_branch_name=rule['line_id']

					if rule['rule_id'] == 1:
						response=branch_on(rule['line_id'])
						if response is None:
							logging.error("Can't turn on {0} branch".format(rule['line_id']))
							continue

						json_data = json.loads(response.text)
						if (json_data['variables'][str(arduino_branch_name)] == 0 ):
							logging.error("Can't turn on {0} branch".format(rule['line_id']))
							continue

						if (json_data['variables'][str(arduino_branch_name)] == 1 ):
							logging.info("Turned on {0} branch".format(rule['line_id']))
							execute_request("UPDATE life SET state=1 WHERE id={0}".format(rule['id']))
							RULES_FOR_BRANCHES[rule['line_id']]=get_next_active_rule(rule['line_id'])
							logging.info("Rule '{0}' is done. Removing".format(str(rule)))

					if rule['rule_id'] == 2:
						response=branch_off(rule['line_id'])
						if response is None:
							logging.error("Can't turn off {0} branch".format(rule['line_id']))
							continue

						json_data = json.loads(response.text)
						if (json_data['variables'][str(arduino_branch_name)] == 1 ):
							logging.error("Can't turn off {0} branch".format(rule['line_id']))
							continue

						if (json_data['variables'][str(arduino_branch_name)] == 0 ):
							logging.info("Turned off {0} branch".format(rule['line_id']))
							execute_request("UPDATE life SET state=1 WHERE id={0}".format(rule['id']))
							RULES_FOR_BRANCHES[rule['line_id']]=get_next_active_rule(rule['line_id'])
							logging.info("Rule '{0}' is done. Removing".format(str(rule)))
							
		logging.info("enable rule thread stoped.")						
	except Exception as e:
		logging.error("enable rule thread exception occured. {0}".format(e))	
		threadErrors.append([repr(e), current_thread.name])	
		raise 

thread = threading.Thread(name='enable_rule', target=enable_rule)
#thread.setDaemon(True)
thread.start()

@app.route("/error")
def errorlist():
	return str(threadErrors)

@app.route("/branches_names")
def branches_names():
	branch_list=[]
	res = execute_request("select number, name from lines order by number", 'fetchall')
	if res == None:
		logging.error("Can't get branches names from database")
		abort(500)

	for row in res:
		branch_list.append( {'id':row[0], 'name':row[1]})

	return jsonify(
			list=branch_list
		)


@app.route("/beta")
def beta():
	return app.send_static_file('index.html')


@app.route("/")
def hello():
	global RULES_FOR_BRANCHES
	return str(RULES_FOR_BRANCHES)

def get_table_template(query="SELECT l.id, li.name, rule_type.name, l.state, l.date, l.timer, l.active FROM life as l, type_of_rule as rule_type, lines as li WHERE l.rule_id = rule_type.id AND l.line_id = li.number order by timer desc"):
	list_arr = execute_request(query, 'fetchall')

	rows=[]
	if list_arr is not None:
		for row in list_arr:
			id=row[0]
			branch_name=row[1]
			rule_name=row[2]
			state=row[3]
			timer=row[5]
			active=row[6]
			outdated=0
			if (state==0 and timer<datetime.datetime.now() - datetime.timedelta(minutes=1)):
				outdated=1

			rows.append({'id':id, 'branch_name':branch_name, 'rule_name':rule_name, 'state':state,
				'timer':"{:%A, %H:%M, %d %b %Y}".format(timer), 'outdated':outdated, 'active':active})

	template=render_template('table_only.html', my_list=rows)
	return template

@app.route("/list")
def list():
	list_arr = execute_request("SELECT l.id, li.name, rule_type.name, l.state, l.date, l.timer, l.active FROM life as l, type_of_rule as rule_type, lines as li WHERE l.rule_id = rule_type.id AND l.line_id = li.number AND l.timer>= now() - interval '{0} hour' AND l.timer<=now()+ interval '{1} hour' order by l.timer desc".format(12, 24), 'fetchall')
	rows=[]
	for row in list_arr:
		id=row[0]
		branch_name=row[1]
		rule_name=row[2]
		state=row[3]
		timer=row[5]
		active=row[6]
		outdated=0
		if (state==0 and timer<datetime.datetime.now() - datetime.timedelta(minutes=1)):
			outdated=1

		rows.append({'id':id, 'branch_name':branch_name, 'rule_name':rule_name, 'state':state,
			'timer':"{:%A, %H:%M, %d %b %Y}".format(timer), 'outdated':outdated, 'active':active})

	template=render_template('list.html', my_list=rows)
	return template

@app.route("/list_all")
def list_all():
	if 'days' in request.args:
		days=int(request.args.get('days'))
		return get_table_template("SELECT l.id, li.name, rule_type.name, l.state, l.date, l.timer, l.active FROM life as l, type_of_rule as rule_type, lines as li WHERE l.rule_id = rule_type.id AND l.line_id = li.number AND l.timer>=now()- interval '{0} day' AND l.timer <=now() order by l.timer desc".format(days))

	list_arr = execute_request("SELECT l.id, li.name, rule_type.name, l.state, l.date, l.timer, l.active FROM life as l, type_of_rule as rule_type, lines as li WHERE l.rule_id = rule_type.id AND l.line_id = li.number AND l.timer <= now() order by l.timer desc", 'fetchall')
	rows=[]
	for row in list_arr:
		id=row[0]
		branch_name=row[1]
		rule_name=row[2]
		state=row[3]
		timer=row[5]
		active=row[6]
		outdated=0
		if (state==0 and timer<datetime.datetime.now() - datetime.timedelta(minutes=1)):
			outdated=1

		rows.append({'id':id, 'branch_name':branch_name, 'rule_name':rule_name, 'state':state,
			'timer':strftime("%A %d-%m-%y %R", timer.timetuple()).capitalize(), 'outdated':outdated, 'active':active})

	template=render_template('history.html', my_list=rows)
	return template

@app.route("/add_rule")
def add_rule():
	branch_id=int(request.args.get('branch_id'))
	time_min=int(request.args.get('time_min'))
	datetime_start=datetime.datetime.strptime(request.args.get('datetime_start'), "%Y-%m-%d %H:%M")

	datetime_stop=datetime_start + datetime.timedelta(minutes = time_min)
	now = datetime.datetime.now()

	execute_request("INSERT INTO public.life(line_id, rule_id, state, date, timer) VALUES ({0}, {1}, {2}, '{3}', '{4}') RETURNING id,line_id, rule_id, timer".format(branch_id, 1, 0, now.date(), datetime_start))
	execute_request("INSERT INTO public.life(line_id, rule_id, state, date, timer) VALUES ({0}, {1}, {2}, '{3}', '{4}') RETURNING id,line_id, rule_id, timer".format(branch_id, 2, 0, now.date(), datetime_stop))
	update_all_rules()
	template=get_table_template()
	socketio.emit('list_update', {'data':template})
	return template

@app.route("/remove_rule")
def remove_rule():
	id=int(request.args.get('id'))
	execute_request("DELETE from life WHERE id={0}".format(id))
	update_all_rules()
	template=get_table_template()
	socketio.emit('list_update', {'data':template})
	return template

# @app.route("/modify_rule")
# def modify_rule():


@app.route("/activate_rule")
def activate_rule():
	id=int(request.args.get('id'))
	execute_request("UPDATE life SET active=1 WHERE id={0}".format(id))
	update_all_rules()
	template=get_table_template()
	socketio.emit('list_update', {'data':template})
	return template

@app.route("/deactivate_rule")
def deactivate_rule():
	id=int(request.args.get('id'))
	execute_request("UPDATE life SET active=0 WHERE id={0}".format(id))
	update_all_rules()
	template=get_table_template()
	socketio.emit('list_update', {'data':template})
	return template

@app.route("/deactivate_all_rules")
def deactivate_all_rules():
	id=int(request.args.get('id'))
	#1-24h;2-7d;3-on demand
	if (id==1):
		execute_request("UPDATE life SET active=0 WHERE timer>= now() AND timer<=now()::date+1")
		update_all_rules()
		template=get_table_template()
		socketio.emit('list_update', {'data':template})
		return template

	if (id==2):
		execute_request("UPDATE life SET active=0 WHERE timer>= now() AND timer<=now()::date+7")
		update_all_rules()
		template=get_table_template()
		socketio.emit('list_update', {'data':template})
		return template

	if (id==3):
		logging.warn("Is not implemented yet")
		#RULES_ENABLED=False

	return 'OK'

def ongoing_rules_table(query="SELECT w.id, dw.name, li.name, rule_type.name, \"time\", \"interval\", w.active FROM week_schedule as w, day_of_week as dw, lines as li, type_of_rule as rule_type WHERE  w.day_number = dw.num AND w.line_id = li.number and w.rule_id = rule_type.id ORDER BY w.day_number, w.time"):
	list_arr = execute_request(query, 'fetchall')
	rows=[]
	for row in list_arr:
		id=row[0]
		day_number=row[1]
		branch_name=row[2]
		rule_name=row[3]
		time=row[4]
		minutes=row[5]
		active=row[6]
		rows.append({'id':id, 'branch_name':branch_name, 'dow': day_number, 'rule_name':rule_name, 'time':time, 'minutest': minutes, 'active':active})

	template=render_template('ongoing_rules_table_only.html', my_list=rows)
	return template


@app.route("/ongoing_rules")
def ongoing_rules():
	list_arr = execute_request("SELECT w.id, dw.name, li.name, rule_type.name, \"time\", \"interval\", w.active FROM week_schedule as w, day_of_week as dw, lines as li, type_of_rule as rule_type WHERE  w.day_number = dw.num AND w.line_id = li.number and w.rule_id = rule_type.id ORDER BY w.day_number, w.time", 'fetchall')
	rows=[]
	for row in list_arr:
		id=row[0]
		day_number=row[1]
		branch_name=row[2]
		rule_name=row[3]
		time=row[4]
		minutes=row[5]
		active=row[6]
		rows.append({'id':id, 'branch_name':branch_name, 'dow': day_number, 'rule_name':rule_name, 'time':time, 'minutest': minutes, 'active':active})

	template=render_template('ongoing_rules.html', my_list=rows)
	return template

@app.route("/add_ongoing_rule")
def add_ongoing_rule():
	branch_id=int(request.args.get('branch_id'))
	time_min=int(request.args.get('time_min'))
	time_start=request.args.get('datetime_start')
	dow=int(request.args.get('dow'))

	execute_request("INSERT INTO week_schedule(day_number, line_id, rule_id, \"time\", \"interval\", active) VALUES ({0}, {1}, {2}, '{3}', {4}, 1)".format(dow, branch_id, 1, time_start, time_min))
	update_all_rules()
	template=ongoing_rules_table()
	socketio.emit('ongoind_rules_update', {'data':template})
	return template

@app.route("/remove_ongoing_rule")
def remove_ongoing_rule():
	id=int(request.args.get('id'))
	execute_request("DELETE from week_schedule WHERE id={0}".format(id))
	update_all_rules()
	template=ongoing_rules_table()
	socketio.emit('ongoind_rules_update', {'data':template})
	return template

@app.route("/edit_ongoing_rule")
def edit_ongoing_rule():
	id=int(request.args.get('id'))
	#execute_request("DELETE from week_schedule WHERE id={0}".format(id))
	update_all_rules()
	template=ongoing_rules_table()
	socketio.emit('ongoind_rules_update', {'data':template})
	return template

@app.route("/activate_ongoing_rule")
def activate_ongoing_rule():
	id=int(request.args.get('id'))
	execute_request("UPDATE week_schedule SET active=1 WHERE id={0}".format(id))
	update_all_rules()
	template=ongoing_rules_table()
	socketio.emit('ongoind_rules_update', {'data':template})
	return template

@app.route("/deactivate_ongoing_rule")
def deactivate_ongoing_rule():
	id=int(request.args.get('id'))
	execute_request("UPDATE week_schedule SET active=0 WHERE id={0}".format(id))
	update_all_rules()
	template=ongoing_rules_table()
	socketio.emit('ongoind_rules_update', {'data':template})
	return template

@app.route("/get_list")
def get_list():
	if 'days' in request.args:
		days=int(request.args.get('days'))
		return get_table_template("SELECT l.id, li.name, rule_type.name, l.state, l.date, l.timer, l.active FROM life as l, type_of_rule as rule_type, lines as li WHERE l.rule_id = rule_type.id AND l.line_id = li.number AND l.timer<=now()::date+{0} order by l.timer desc".format(days))

	if 'before' in request.args and 'after' in request.args:
		before=int(request.args.get('before'))
		after=int(request.args.get('after'))
		return get_table_template("SELECT l.id, li.name, rule_type.name, l.state, l.date, l.timer, l.active FROM life as l, type_of_rule as rule_type, lines as li WHERE l.rule_id = rule_type.id AND l.line_id = li.number AND l.timer>= now() - interval '{0} hour' and l.timer<=now()+ interval '{1} hour' order by l.timer desc".format(before, after))

@app.route('/arduino_status', methods=['GET'])
def arduino_status():
	try:
		response_status = requests.get(url=ARDUINO_IP)
		return (response_status.text, response_status.status_code)
	except requests.exceptions.RequestException as e:  # This is the correct syntax
		logging.error(e)
		logging.error("Can't get arduino status. Exception occured")
		abort(404)

@app.route('/activate_branch', methods=['GET'])
def activate_branch():
	global RULES_FOR_BRANCHES
	id=int(request.args.get('id'))
	time_min=int(request.args.get('time'))

	try:
		response_on = requests.get(url=ARDUINO_IP+'/on', params={"params":id})
	except requests.exceptions.RequestException as e:  # This is the correct syntax
		logging.error(e)
		logging.error("Can't turn on branch id={0}. Exception occured".format(id))
		abort(404)

	now = datetime.datetime.now()
	now_plus = now + datetime.timedelta(minutes = time_min)

	execute_request("INSERT INTO public.life(line_id, rule_id, state, date, timer) VALUES ({0}, {1}, {2}, '{3}', '{4}')".format(id, 1, 1, now.date(), now), 'fetchone')
	res=execute_request("INSERT INTO public.life(line_id, rule_id, state, date, timer) VALUES ({0}, {1}, {2}, '{3}', '{4}') RETURNING id,line_id, rule_id, timer".format(id, 2, 0, now.date(), now_plus), 'fetchone')
	RULES_FOR_BRANCHES[id]={'id':res[0], 'line_id':res[1], 'rule_id':res[2], 'timer':res[3]}
	logging.info("Rule '{0}' added".format(str(RULES_FOR_BRANCHES[id])))

	try:
		response_status = requests.get(url=ARDUINO_IP)
		socketio.emit('branch_status', {'data':response_status.text})
	except requests.exceptions.RequestException as e:  # This is the correct syntax
		logging.error(e)
		logging.error("Can't get arduino status. Exception occured")
		abort(404)

	logging.info("Branch '{0}' activated manually".format(id))
	return (response_status.text, response_status.status_code)

@app.route('/deactivate_branch', methods=['GET'])
def deactivate_branch():
	global RULES_FOR_BRANCHES
	id=int(request.args.get('id'))

	try:
		response_off = requests.get(url=ARDUINO_IP+'/off', params={"params":id})
	except requests.exceptions.RequestException as e:  # This is the correct syntax
		logging.error(e)
		logging.error("Can't turn on branch id={0}. Exception occured".format(id))
		abort(404)

	now = datetime.datetime.now()
	if RULES_FOR_BRANCHES[id] is not None:
		execute_request("UPDATE public.life SET state=1 WHERE id = {0}".format(RULES_FOR_BRANCHES[id]['id']), 'fetchone')
	else:
		execute_request("INSERT INTO public.life(line_id, rule_id, state, date, timer) VALUES ({0}, {1}, {2}, '{3}', '{4}')".format(id, 2, 1, now.date(), now), 'fetchone')

	RULES_FOR_BRANCHES[id]=get_next_active_rule(id)
	logging.info("Rule '{0}' added".format(str(RULES_FOR_BRANCHES[id])))

	try:
		response_status = requests.get(url=ARDUINO_IP)
		socketio.emit('branch_status', {'data':response_status.text})
	except requests.exceptions.RequestException as e:  # This is the correct syntax
		logging.error(e)
		logging.error("Can't get arduino status. Exception occured")
		abort(404)
	
	logging.info("Branch '{0}' deactivated manually".format(id))
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
	socketio.run(app, host='0.0.0.0', port=7543, debug=False)
