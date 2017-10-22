#!/usr/bin/python3
# -*- coding: utf-8 -*-
from flask import Flask
from flask import jsonify, request, render_template
from flask import abort
from eventlet import wsgi
import eventlet
from flask_socketio import SocketIO
from flask_socketio import emit
import datetime
import json
import requests
import inspect
import sqlite3
import logging
import uuid
import redis
import pytemperature
import time
from controllers import relay_controller as garden_controller

eventlet.monkey_patch()
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.INFO)

logging.getLogger('socketio').setLevel(logging.ERROR)
logging.getLogger('engineio').setLevel(logging.ERROR)

app = Flask(__name__)
socketio = SocketIO(app, async_mode='eventlet', engineio_logger=False)
redis_db = redis.StrictRedis(host="localhost", port=6379, db=0)

DEBUG = False

VIBER_BOT_IP = 'https://mozart.hopto.org:7443'
ARDUINO_SMALL_H_IP = 'http://butenko.asuscomm.com:5555'

# For get function name intro function. Usage mn(). Return string with current function name. Instead 'query' will be QUERY[mn()].format(....)
mn = lambda: inspect.stack()[1][3]

BRANCHES_LENGTH = 18
RULES_FOR_BRANCHES = [None] * BRANCHES_LENGTH
BRANCHES_SETTINGS = [None] * BRANCHES_LENGTH


QUERY = {}
QUERY['get_next_active_rule'] = "SELECT l.id, l.line_id, l.rule_id, l.timer as \"[timestamp]\", l.interval_id, l.time, li.name  FROM life AS l, lines as li WHERE l.state = 1 AND l.active=1 AND l.line_id={0} AND li.number = l.line_id AND timer>=datetime('now', 'localtime') ORDER BY timer LIMIT 1"
QUERY['get_last_start_rule'] = "SELECT l.id, l.line_id, l.rule_id, l.timer as \"[timestamp]\", l.interval_id  FROM life AS l WHERE l.state = 2 AND l.active=1 AND l.rule_id = 1 AND l.line_id={0} AND timer<=datetime('now', 'localtime') ORDER BY timer DESC LIMIT 1"
QUERY['get_table_body_only'] = "SELECT l.id, li.name, rule_type.name, l.state, l.date, l.timer as \"[timestamp]\", l.active, rule_state.full_name, l.interval_id FROM life as l, type_of_rule as rule_type, lines as li, state_of_rule as rule_state WHERE l.rule_id = rule_type.id AND l.line_id = li.number and l.state = rule_state.id order by l.id, l.timer desc, l.interval_id"

QUERY['ongoing_rules_table'] = "SELECT w.id, dw.name, li.name, rule_type.name, \"time\" as \"[timestamp]\", \"interval\", w.active FROM week_schedule as w, day_of_week as dw, lines as li, type_of_rule as rule_type WHERE  w.day_number = dw.num AND w.line_id = li.number and w.rule_id = rule_type.id ORDER BY w.day_number, w.time"

QUERY['branch_settings'] = "SELECT number, name, time, intervals, time_wait, start_time from lines where line_type='irrigation' order by number"

QUERY['lighting'] = "SELECT number, name, time from lines where line_type='lighting' order by number"
QUERY['lighting_settings'] = QUERY['lighting']

QUERY['history'] = "SELECT l.id, li.name, rule_type.name, l.state, l.date, l.timer as \"[timestamp]\", l.active, rule_state.full_name, l.time FROM life as l, type_of_rule as rule_type, lines as li, state_of_rule as rule_state WHERE l.rule_id = rule_type.id AND l.line_id = li.number AND l.timer >= datetime('now', 'localtime', '-{0} day') and l.state = rule_state.id order by l.timer desc"

QUERY['ongoing_rules'] = "SELECT w.id, dw.name, li.name, rule_type.name, \"time\" as \"[timestamp]\", \"interval\", w.active FROM week_schedule as w, day_of_week as dw, lines as li, type_of_rule as rule_type WHERE  w.day_number = dw.num AND w.line_id = li.number and w.rule_id = rule_type.id ORDER BY w.day_number, w.time"

QUERY['get_timetable_list_1'] = "SELECT l.id, li.name, rule_type.name, l.state, l.date, l.timer as \"[timestamp]\", l.active, rule_state.full_name, l.time FROM life as l, type_of_rule as rule_type, lines as li, state_of_rule as rule_state WHERE l.rule_id = rule_type.id AND l.line_id = li.number AND l.timer<=datetime('now', 'localtime','+{0} day') and l.state = rule_state.id  order by l.timer desc"
QUERY['get_timetable_list_2'] = "SELECT l.id, li.name, rule_type.name, l.state, l.date, l.timer as \"[timestamp]\", l.active, rule_state.full_name, l.time FROM life as l, type_of_rule as rule_type, lines as li, state_of_rule as rule_state WHERE l.rule_id = rule_type.id AND l.line_id = li.number AND l.timer>= datetime('now', 'localtime', '-{0} hour') and l.timer<=datetime('now', 'localtime', '+{0} hour') and l.state = rule_state.id  order by l.timer desc"

QUERY['add_rule'] = "INSERT INTO life(line_id, rule_id, state, date, timer, interval_id, time) VALUES ({0}, {1}, {2}, '{3}', '{4}', '{5}', {6})"
QUERY['add_rule_endpoint_v2'] = "INSERT INTO life(line_id, rule_id, state, date, timer, interval_id, time) VALUES ({0}, {1}, {2}, '{3}', '{4}', '{5}', {6})"

QUERY['add_ongoing_rule'] = "INSERT INTO week_schedule(day_number, line_id, rule_id, \"time\", \"interval\", active) VALUES ({0}, {1}, {2}, '{3}', {4}, 1)"

QUERY['activate_branch_1'] = "INSERT INTO life(line_id, rule_id, state, date, timer, interval_id, time) VALUES ({0}, {1}, {2}, '{3}', '{4}', '{5}', {6})"
QUERY['activate_branch_2'] = "SELECT l.id, l.line_id, l.rule_id, l.timer, l.interval_id, l.time, li.name FROM life as l, lines as li where l.id = {0} and li.number = l.line_id"

QUERY['deactivate_branch_1'] = "UPDATE life SET state=4 WHERE interval_id = '{0}' and state = 1 and rule_id = 1"
QUERY['deactivate_branch_2'] = "INSERT INTO life(line_id, rule_id, state, date, timer, interval_id) VALUES ({0}, {1}, {2}, '{3}', '{4}', '{5}')"

QUERY['enable_rule'] = "UPDATE life SET state=2 WHERE id={0}"
QUERY['enable_rule_state_6'] = "UPDATE life SET state=6 WHERE id={0}"

QUERY['activate_rule'] = "UPDATE life SET active=1 WHERE id={0}"

QUERY['deactivate_rule'] = "UPDATE life SET active=0 WHERE id={0}"
QUERY['deactivate_all_rules_1'] = "UPDATE life SET active=0 WHERE timer >= datetime('now', 'localtime') AND timer <= datetime('now', 'localtime', '+1 day')"
QUERY['deactivate_all_rules_2'] = "UPDATE life SET active=0 WHERE timer >= datetime('now', 'localtime')  AND timer <= datetime('now', 'localtime', '+7 days')"

QUERY['activate_ongoing_rule'] = "UPDATE week_schedule SET active=1 WHERE id={0}"

QUERY['deactivate_ongoing_rule'] = "UPDATE week_schedule SET active=0 WHERE id={0}"

QUERY['remove_rule'] = "DELETE from life WHERE id={0}"

QUERY['remove_ongoing_rule'] = "DELETE from week_schedule WHERE id={0}"

QUERY['edit_ongoing_rule'] = "DELETE from week_schedule WHERE id={0}"

QUERY['cancel_rule_1'] = "SELECT l.interval_id, li.name FROM life AS l, lines AS li WHERE l.id = {0} AND l.line_id = li.number"
QUERY['cancel_rule_2'] = "UPDATE life SET state=4 WHERE interval_id = '{0}' and state = 1 and rule_id = 1"

QUERY['temperature_1'] = "SELECT * FROM temperature_statistics limit 1"
QUERY['temperature_2'] = "INSERT INTO temperature_statistics (temperature_street, humidity_street, temperature_small_h_1_fl, humidity_small_h_1_fl, temperature_small_h_2_fl, humidity_small_h_2_fl, temperature_big_h_1_fl, humidity_big_h_1_fl, temperature_big_h_2_fl, humidity_big_h_2_fl) VALUES ('{0}', '{1}', '{2}', '{3}', '{4}', '{5}', '{6}', '{7}', '{8}', '{9}')"

QUERY['power_outlets'] = "SELECT number, name, time from lines where line_type='power_outlet' order by number"
QUERY['power_outlets_settings'] = QUERY['power_outlets']

QUERY['get_settings'] = "SELECT number, name, time, intervals, time_wait, start_time, line_type, base_url, pump_enabled from lines order by number"


@socketio.on_error_default
def error_handler(e):
    """Handle error for websockets."""
    logging.error('error_handler for socketio. An error has occurred: ' + str(e))


@socketio.on('connect')
def connect():
    """Log info if user is connected to websocket."""
    logging.info('Client connected')


@socketio.on('disconnect')
def disconnect():
    """Log info if user is disconnected to websocket."""
    logging.info('Client disconnected')


def date_handler(obj):
    """Convert datatime to string format."""
    if hasattr(obj, 'isoformat'):
        return obj.isoformat()
    else:
        raise TypeError


def convert_to_obj(data):
    try:
        data = json.loads(data)
    except:
        pass
    return data


def date_hook(json_dict):
    """Convert str to datatime object."""
    for (key, value) in json_dict.items():
        try:
            json_dict[key] = datetime.datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%f")
        except:
            pass
        try:
            json_dict[key] = datetime.datetime.strptime(value, "%Y-%m-%dT%H:%M:%S")
        except:
            pass
    return json_dict


def set_next_rule_to_redis(branch_id, data):
    """Set next rule in redis."""
    res = False
    try:
        data = json.dumps(data, default=date_handler)
        res = redis_db.set(branch_id, data)
    except Exception as e:
        logging.error("Can't save data to redis. Exception occured {0}".format(e))

    return res


def get_next_rule_from_redis(branch_id):
    """Get next rule from redis."""
    json_to_data = None
    try:
        data = redis_db.get(branch_id)
        if data is None:
            return None

        json_to_data = json.loads(data.decode("utf-8"), object_hook=date_hook)
    except Exception as e:
        logging.error("Can't get data from redis. Exception occured {0}".format(e))

    return json_to_data


def send_message(channel, data):
    """Enclose emit method into try except block."""
    try:
        socketio.emit(channel, data)
        logging.info('Message was sent.')
        logging.debug(data)
    except Exception as e:
        logging.error(e)
        logging.error("Can't send message. Exeption occured")


# executes query and returns fetch* result
def execute_request(query, method='fetchall'):
    """Use this method in case you need to get info from database."""
    conn = None
    try:
        conn = sqlite3.connect('/var/sqlite_db/test_v4', detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        # conn = sqlite3.connect('/home/sergey/repos/irrigation_peregonivka/test_v4', detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        # conn = sqlite3.connect('C:\\repos\\irrigation_peregonivka\\test_v4', detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)

        # conn.cursor will return a cursor object, you can use this cursor to perform queries
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        # execute our Query
        cursor.execute(query)
        logging.debug("db request '{0}' executed".format(query))
        return getattr(cursor, method)()
    except Exception as e:
        logging.error("Error while performing operation with database: '{0}'. query: '{1}'".format(e, query))
        return None
    finally:
        try:
            if conn is not None:
                conn.close()
        except Exception as e:
            logging.error("Error while closing connection with database: {0}".format(e))


# executes query and returns fetch* result
def update_db_request(query):
    """Doesn't have fetch* methods. Returns lastrowid after database insert command."""
    conn = None
    lastrowid = -1
    try:
        conn = sqlite3.connect('/var/sqlite_db/test_v4', detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        # conn = sqlite3.connect('/home/sergey/repos/irrigation_peregonivka/test_v4', detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        # conn = sqlite3.connect('C:\\repos\\irrigation_peregonivka\\test_v4', detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)

        # conn.cursor will return a cursor object, you can use this cursor to perform queries
        cursor = conn.cursor()
        # execute our Query
        cursor.execute(query)
        conn.commit()
        logging.debug("db request '{0}' executed".format(query))
        lastrowid = cursor.lastrowid
        return lastrowid
    except Exception as e:
        logging.error("Error while performing operation with database: '{0}'. query: '{1}'".format(e, query))
    finally:
        try:
            if conn is not None:
                conn.close()
        except Exception as e:
            logging.error("Error while closing connection with database: {0}".format(e))
            return None


def get_next_active_rule(line_id):
    """Return nex active rule."""
    query = QUERY[mn()].format(line_id)
    res = execute_request(query, 'fetchone')
    if res is None:
        return None

    logging.info("Next active rule retrieved for line id {0}".format(line_id))
    return {'id': res[0], 'line_id': res[1], 'rule_id': res[2], 'user_friendly_name': res[6], 'timer': res[3], 'interval_id': res[4], 'time': res[5]}


def get_last_start_rule(line_id):
    """Return last compeled start irrigation rule."""
    query = QUERY[mn()].format(line_id)
    res = execute_request(query, 'fetchone')
    if res is None:
        return None

    logging.debug("Last completed rule retrieved for line id {0}".format(line_id))
    return {'id': res[0], 'line_id': res[1], 'rule_id': res[2], 'timer': res[3], 'interval_id': res[4]}


def update_all_rules():
    """Set next active rules for all branches."""
    try:
        for i in range(1, len(RULES_FOR_BRANCHES)):
            set_next_rule_to_redis(i, get_next_active_rule(i))
        logging.info("Rules updated")
    except Exception as e:
        logging.error("Exeption occured while updating all rules. {0}".format(e))


def get_settings():
    """Fills up settings array to save settings for branches"""
    try:
        branches = execute_request(QUERY[mn()])
        # QUERY['get_settings'] = "SELECT number, name, time, intervals, time_wait, start_time, line_type, base_url, pump_enabled from lines where line_type='power_outlet' order by number"
        for row in branches:
            branch_id = row[0]
            name = row[1]
            time = row[2]
            intervals = row[3]
            time_wait = row[4]
            start_time = row[5]
            line_type = row[6]
            base_url = row[7]
            pump_enabled = row[8]

            BRANCHES_SETTINGS[branch_id] = {
                'branch_id': branch_id,
                'name': name,
                'time': time,
                'intervals': intervals,
                'time_wait': time_wait,
                'start_time': start_time,
                'line_type': line_type,
                'base_url': base_url,
                'pump_enabled': True if pump_enabled == 1 else False
            }
            logging.debug("{0} added to settings".format(str(BRANCHES_SETTINGS[branch_id])))
    except Exception as e:
        logging.error("Exceprion occured when trying to get settings for all branches. {0}".format(e))


@app.route("/update_all_rules")
def update_rules():
    """Synchronize rules with database."""
    update_all_rules()
    return "OK"


@app.route("/branch_settings")
def branch_settings():
    """Return branch names."""
    branch_list = []
    res = execute_request(QUERY[mn()], 'fetchall')
    if res is None:
        logging.error("Can't get branches settings from database")
        abort(500)

    for row in res:
        branch_list.append({'id': row[0], 'name': row[1], 'default_time': row[2], 'default_interval': row[3], 'default_time_wait': row[4],
            'start_time': row[5]})

    return jsonify(list=branch_list)


@app.route("/lighting")
def lighting():
    """Return branch names."""
    light_list = []
    res = execute_request(QUERY[mn()], 'fetchall')
    if res is None:
        logging.error("Can't get light names from database")
        abort(500)

    for row in res:
        light_list.append({'id': row[0], 'name': row[1], 'default_time': row[2]})

    return render_template('lighting.html', my_list=light_list)


@app.route("/lighting_settings")
def lighting_settings():
    """Return branch names."""
    light_list = []
    res = execute_request(QUERY[mn()], 'fetchall')
    if res is None:
        logging.error("Can't get light settings from database")
        abort(500)

    for row in res:
        light_list.append({'id': row[0], 'name': row[1], 'default_time': row[2]})

    return jsonify(list=light_list)


@app.route("/power_outlets")
def power_outlets():
    """Return branch names."""
    light_list = []
    res = execute_request(QUERY[mn()], 'fetchall')
    if res is None:
        logging.error("Can't get light names from database")
        abort(500)

    for row in res:
        light_list.append({'id': row[0], 'name': row[1], 'default_time': row[2]})

    return render_template('power_outlets.html', my_list=light_list)


@app.route("/power_outlets_settings")
def power_outlets_settings():
    """Return branch names."""
    light_list = []
    res = execute_request(QUERY[mn()], 'fetchall')
    if res is None:
        logging.error("Can't get power outlet settings from database")
        abort(500)

    for row in res:
        light_list.append({'id': row[0], 'name': row[1], 'default_time': row[2]})

    return jsonify(list=light_list)



@app.route("/")
def index():
    """Index page."""
    return render_template('index.html')


@app.route("/add_rule")
def add_rule_page():
    """add rule page."""
    return render_template('add_rule.html')


def get_table_body_only(query=None):
    """If no query is passed returns all entries from life table."""
    if (query is None):
        query = QUERY[mn()]

    list_arr = execute_request(query, 'fetchall')

    rows = []
    if list_arr is not None:
        for row in list_arr:
            id = row[0]
            branch_name = row[1]
            rule_name = row[2]
            state = row[3]
            timer = row[5]
            active = row[6]
            rule_state = row[7]
            time = row[8]
            outdated = 0
            if (state == 1 and timer < datetime.datetime.now() - datetime.timedelta(minutes=1)):
                outdated = 1

            rows.append({'id': id, 'branch_name': branch_name, 'rule_name': rule_name, 'state': state, 'time': time,
                'timer': "{:%A, %d-%m-%y %R}".format(timer), 'outdated': outdated, 'active': active, 'rule_state': rule_state})

    template = render_template('timetable_table_only.html', my_list=rows)
    return template


@app.route("/history")
def history():
    """Return history page if no parameters passed and only table body if opposite."""
    if 'days' in request.args:
        days = int(request.args.get('days'))
    else:
        days = 60

    list_arr = execute_request(QUERY[mn()].format(days), 'fetchall')
    rows = []
    if list_arr is not None:
        for row in list_arr:
            id = row[0]
            branch_name = row[1]
            rule_name = row[2]
            state = row[3]
            timer = row[5]
            active = row[6]
            rule_state = row[7]
            time = row[8]
            outdated = 0
            if (state == 1 and timer < datetime.datetime.now() - datetime.timedelta(minutes=1)):
                outdated = 1

            rows.append({'id': id, 'branch_name': branch_name, 'rule_name': rule_name, 'state': state, 'time': time,
                'timer': "{:%A, %d-%m-%y %R}".format(timer), 'outdated': outdated, 'active': active, 'rule_state': rule_state})

    template = render_template('history.html', my_list=rows)
    return template


@app.route("/add_rule", methods=['POST'])
def add_rule_endpoint():
    """Used in add rule modal window."""
    content = request.json['list']

    for rule in content:
        rule = content[rule]
        print(rule)
        branch_id = int(rule['branch_id'])
        time_min = int(rule['time'])
        start_time = datetime.datetime.strptime(rule['datetime_start'], "%Y-%m-%d %H:%M")
        time_wait = int(rule['time_wait'])
        num_of_intervals = int(rule['interval'])

        interval_id = str(uuid.uuid4())

        now = datetime.datetime.now()
        stop_time = start_time + datetime.timedelta(minutes=time_min)

        update_db_request(QUERY[mn()].format(branch_id, 1, 1, now.date(), start_time, interval_id, time_min))
        update_db_request(QUERY[mn()].format(branch_id, 2, 1, now.date(), stop_time, interval_id, 0))

        # first interval is executed
        for x in range(2, num_of_intervals + 1):
            start_time = stop_time + datetime.timedelta(minutes=time_wait)
            stop_time = start_time + datetime.timedelta(minutes=time_min)
            update_db_request(QUERY[mn()].format(branch_id, 1, 1, now.date(), start_time, interval_id, time_min))
            update_db_request(QUERY[mn()].format(branch_id, 2, 1, now.date(), stop_time, interval_id, 0))
            logging.info("Start time: {0}. Stop time: {1} added to database".format(str(start_time), str(stop_time)))

    update_all_rules()
    return json.dumps({'status': 'OK'})


@app.route("/cancel_rule")
def cancel_rule():
    """User can remove rule from ongoing rules table."""
    if ('id' not in request.args):
        logging.error("No id param in request")
        abort(500)

    id = int(request.args.get('id'))
    # select l.interval_id, li.name from life as l, lines as li where id = {0} and l.line_id = li.number
    res = execute_request(QUERY[mn() + "_1"].format(id), 'fetchone')
    if (res is None):
        logging.error("No {0} rule id in database".format(id))

    interval_id = res[0]
    branch_name = res[1]
    # "UPDATE life SET state=4 WHERE interval_id = '{0}' and state = 1 and rule_id = 1"
    update_db_request(QUERY[mn() + '_2'].format(interval_id))
    update_all_rules()

    try:
        response_status = garden_controller.branch_status()

        arr = form_responce_for_branches(response_status)
        send_message('branch_status', {'data': json.dumps({'branches': arr}, default=date_handler)})
    except Exception as e:
        logging.error(e)
        logging.error("Can't get Raspberri Pi pin status. Exception occured")
        abort(500)

    logging.info("Rule {0} canceled".format(id))
    return render_template('index.html')


def ongoing_rules_table():
    """Return only table for ongoing rules page."""
    list_arr = execute_request(QUERY[mn()], 'fetchall')
    if (list_arr is None):
        list_arr = []

    rows = []
    for row in list_arr:
        id = row[0]
        day_number = row[1]
        branch_name = row[2]
        rule_name = row[3]
        time = row[4]
        minutes = row[5]
        active = row[6]
        rule_state = row[7]
        rows.append({'id': id, 'branch_name': branch_name, 'dow': day_number, 'rule_name': rule_name,
                'time': time, 'minutest': minutes, 'active': active, 'rule_state': rule_state})

    template = render_template('ongoing_rules_table_only.html', my_list=rows)
    return template


@app.route("/ongoing_rules")
def ongoing_rules():
    """Return ongoing_rules.html."""
    list_arr = execute_request(QUERY[mn()], 'fetchall')
    if (list_arr is None):
        list_arr = []

    rows = []
    for row in list_arr:
        id = row[0]
        day_number = row[1]
        branch_name = row[2]
        rule_name = row[3]
        time = row[4]
        minutes = row[5]
        active = row[6]
        rule_state = row[7]
        rows.append({'id': id, 'branch_name': branch_name, 'dow': day_number, 'rule_name': rule_name,
                    'time': time, 'minutest': minutes, 'active': active, 'rule_state': rule_state})

    template = render_template('ongoing_rules.html', my_list=rows)
    return template


@app.route("/add_ongoing_rule")
def add_ongoing_rule():
    """User can add ongoing rule from ui."""
    branch_id = int(request.args.get('branch_id'))
    time_min = int(request.args.get('time_min'))
    time_start = request.args.get('datetime_start')
    dow = int(request.args.get('dow'))

    update_db_request(QUERY[mn()].format(dow, branch_id, 1, time_start, time_min))
    update_all_rules()
    template = ongoing_rules_table()
    send_message('ongoind_rules_update', {'data': template})
    return template


@app.route("/remove_ongoing_rule")
def remove_ongoing_rule():
    """User can remove ongoing rule from ui."""
    id = int(request.args.get('id'))
    update_db_request(QUERY[mn()].format(id))
    update_all_rules()
    template = ongoing_rules_table()
    send_message('ongoind_rules_update', {'data': template})
    return template


@app.route("/edit_ongoing_rule")
def edit_ongoing_rule():
    """User can edit ongoing rule from ui."""
    id = int(request.args.get('id'))
    # update_db_request(QUERY[mn()].format(id))
    update_all_rules()
    template = ongoing_rules_table()
    send_message('ongoind_rules_update', {'data': template})
    return template


@app.route("/activate_ongoing_rule")
def activate_ongoing_rule():
    """User can activate ongoing rule from ui."""
    id = int(request.args.get('id'))
    update_db_request(QUERY[mn()].format(id))
    update_all_rules()
    template = ongoing_rules_table()
    send_message('ongoind_rules_update', {'data': template})
    return template


@app.route("/deactivate_ongoing_rule")
def deactivate_ongoing_rule():
    """User can deactivate ongoing rule from ui."""
    id = int(request.args.get('id'))
    update_db_request(QUERY[mn()].format(id))
    update_all_rules()
    template = ongoing_rules_table()
    send_message('ongoind_rules_update', {'data': template})
    return template


@app.route("/get_timetable_list")
def get_timetable_list():
    """Blablbal."""
    if 'days' in request.args:
        days = int(request.args.get('days'))
        return get_table_body_only(QUERY[mn() + '_1'].format(days))

    if 'before' in request.args and 'after' in request.args:
        before = int(request.args.get('before'))
        after = int(request.args.get('after'))
        return get_table_body_only(QUERY[mn() + '_2'].format(before, after))


def form_responce_for_branches(payload):
    """Return responce with rules."""
    try:
        res = [None] * BRANCHES_LENGTH
        payload = convert_to_obj(payload)
        for branch in payload:            
            status = branch['state']
            branch_id = branch['id']

            last_rule = get_last_start_rule(branch_id)
            next_rule = get_next_active_rule(branch_id)

            res[int(branch_id)] = {'id': branch_id, 'status': status, 'next_rule': next_rule, 'last_rule': last_rule}
        return res
    except Exception as e:
        logging.error(e)
        logging.error("Can't form responce. Exception occured")
        raise e


@app.route('/irrigation_lighting_status', methods=['GET'])
def irrigation_status():
    """Return status of raspberry_pi relay."""
    try:
        response_status = garden_controller.branch_status()

        arr = form_responce_for_branches(response_status)
        send_message('branch_status', {'data': json.dumps({'branches': arr}, default=date_handler)})
        return jsonify(branches=arr)
    except Exception as e:
        logging.error(e)
        logging.error("Can't get Raspberri Pi pin status. Exception occured")
        abort(500)


@app.route('/power_outlets_status', methods=['GET'])
def arduino_small_house_status():
    """Return status of arduino relay."""
    try:
        response_status_small_house = requests.get(url='http://butenko.asuscomm.com:5555/branch_status', timeout=(5, 5))
        response_status_small_house.raise_for_status()

        arr = form_responce_for_branches(response_status_small_house.text)
        send_message('power_outlet_status', {'data': json.dumps({'branches': arr}, default=date_handler)})

        response_status_big_house = requests.get(url='http://butenko.asuscomm.com:5555/branch_status', timeout=(5, 5))
        response_status_big_house.raise_for_status()

        arr2 = form_responce_for_branches(response_status_big_house.text)
        send_message('power_outlet_status', {'data': json.dumps({'branches': arr2}, default=date_handler)})

        return jsonify(branches=arr.contat(arr2))

    except Exception as e:
        logging.error(e)
        logging.error("Can't get arduino small_house status. Exception occured")
        abort(500)


def retry_branch_on(branch_id, time_min):
    """Use to retry turn on branch in case of any error."""    
    base_url = BRANCHES_SETTINGS[branch_id]['base_url']
    pump_enabled = BRANCHES_SETTINGS[branch_id]['pump_enabled']
    # If branch is not deactivated. It will be stoped by internal process in 2 minutes
    time_min = time_min + 2

    try:
        for attempt in range(2):
            try:
                if base_url is None:
                    response_off = garden_controller.branch_on(branch_id=branch_id, pump_enable=pump_enabled, branch_alert=time_min)
                    logging.info('response {0}'.format(response_off))

                    if (response_off[branch_id]['state'] != 1):
                        logging.error('Branch {0} cant be turned on. response {1}'.format(branch_id, str(response_off)))
                        time.sleep(2)
                        continue
                    else:
                        return response_off
                else:
                    response_off = requests.get(url=base_url, params={'branch_id': branch_id, 'branch_alert': time_min})
                    logging.info('response {0}'.format(str(response_off)))

                    if (response_off[branch_id]['state'] != 0):
                        logging.error('Branch {0} cant be turned on. response {1}'.format(branch_id, response_off))
                        time.sleep(2)
                        continue
                    else:
                        return response_off

            except Exception as e:
                logging.error(e)
                logging.error("Can't turn on {0} branch. Exception occured. {1} try out of 2".format(branch_id, attempt))
                time.sleep(2)
                continue

        raise Exception("Can't turn on {0} branch. Retries limit reached".format(branch_id))
    except Exception as e:
        logging.error(e)
        logging.error("Can't turn on branch id={0}. Exception occured".format(branch_id))
        raise Exception("Can't turn on {0} branch".format(branch_id))


@app.route('/activate_branch', methods=['GET'])
def activate_branch():
    """Blablbal."""
    # ============ check input params =======================
    mode = request.args.get('mode')
    if (mode is None):
        logging.error("no 'mode' parameter passed")
        abort(500)

    if (mode == 'single'):
        branch_id = int(request.args.get('id'))
        time_min = int(request.args.get('time_min'))
    elif (mode == 'interval'):
        branch_id = int(request.args.get('id'))
        time_min = int(request.args.get('time_min'))
        time_wait = int(request.args.get('time_wait'))
        num_of_intervals = int(request.args.get('quantity'))
    elif (mode == 'auto'):
        branch_id = int(request.args.get('id'))
        time_min = int(request.args.get('time_min'))
    else:
        logging.error("incorrect mode parameter passed: {0}".format(mode))
        abort(500)
    # ============ check input params =======================

    try:
        response_arr = retry_branch_on(branch_id=branch_id, time_min=time_min)
    except Exception as e:
        logging.error(e)
        logging.error("Can't turn on branch id={0}. Exception occured".format(branch_id))
        abort(500)

    # needs to be executed in both cases single and interval, but in in auto
    if (mode != 'auto'):
        interval_id = str(uuid.uuid4())
        now = datetime.datetime.now()
        stop_time = now + datetime.timedelta(minutes=time_min)

        update_db_request(QUERY[mn() + '_1'].format(branch_id, 1, 2, now.date(), now, interval_id, time_min))
        lastid = update_db_request(QUERY[mn() + '_1'].format(branch_id, 2, 1, now.date(), stop_time, interval_id, 0))
        logging.debug("lastid:{0}".format(lastid))

        res = execute_request(QUERY[mn() + '_2'].format(lastid), 'fetchone')
        logging.debug("res:{0}".format(res[0]))

        set_next_rule_to_redis(branch_id, {'id': res[0], 'line_id': res[1], 'rule_id': res[2], 'user_friendly_name': res[6], 'timer': res[3], 'interval_id': res[4], 'time': res[5]})
        logging.info("Rule '{0}' added".format(str(get_next_active_rule(branch_id))))

    if (mode == 'interval'):
        # first interval is already added
        for x in range(2, num_of_intervals + 1):
            start_time = stop_time + datetime.timedelta(minutes=time_wait)
            stop_time = start_time + datetime.timedelta(minutes=time_min)
            update_db_request(QUERY[mn() + '_1'].format(branch_id, 1, 1, now.date(), start_time, interval_id, time_min))
            update_db_request(QUERY[mn() + '_1'].format(branch_id, 2, 1, now.date(), stop_time, interval_id, 0))
            logging.info("Start time: {0}. Stop time: {1} added to database".format(str(start_time), str(stop_time)))

    if (mode == 'auto'):
        logging.info("Branch '{0}' activated from rules service".format(branch_id))
    else:
        logging.info("Branch '{0}' activated manually".format(branch_id))

    arr = form_responce_for_branches(response_arr)
    send_message('branch_status', {'data': json.dumps({'branches': arr}, default=date_handler)})

    return jsonify(branches=arr)


def retry_branch_off(branch_id):
    """Use to retry turn off branch in case of any error."""
    base_url = BRANCHES_SETTINGS[branch_id]['base_url']
    pump_enabled = BRANCHES_SETTINGS[branch_id]['pump_enabled']

    try:
        for attempt in range(2):
            try:
                if base_url is None:
                    response_off = garden_controller.branch_off(branch_id=branch_id, pump_enable=pump_enabled)
                    logging.info('response {0}'.format(response_off))

                    if (response_off[branch_id]['state'] != 0):
                        logging.error('Branch {0} cant be turned off. response {1}'.format(branch_id, str(response_off)))
                        time.sleep(2)
                        continue
                    else:
                        logging.info('Branch {0} is turned off by rule'.format(branch_id))
                        return response_off
                else:
                    response_off = requests.get(url=base_url, params={'branch_id': branch_id})
                    logging.info('response {0}'.format(str(response_off)))

                    if (response_off[branch_id]['state'] != 0):
                        logging.error('Branch {0} cant be turned off. response {1}'.format(branch_id, response_off))
                        time.sleep(2)
                        continue
                    else:
                        logging.info('Branch {0} is turned off by rule'.format(branch_id))
                        return response_off
            except Exception as e:
                logging.error(e)
                logging.error("Can't turn off {0} branch. Exception occured. {1} try out of 2".format(branch_id, attempt))
                time.sleep(2)
                continue

        raise Exception("Can't turn off {0} branch. Retries limit reached".format(branch_id))
    except Exception as e:
        logging.error(e)
        logging.error("Can't turn off branch id={0}. Exception occured".format(branch_id))
        raise Exception("Can't turn off {0} branch".format(branch_id))


@app.route('/deactivate_branch', methods=['GET'])
def deactivate_branch():
    """Route is used to disable branch."""
    """Can be executed manaully - row will be added to database
    or with rules service - no new row will be added to database"""
    branch_id = int(request.args.get('id'))
    mode = request.args.get('mode')
    if (mode is None):
        logging.error("no 'mode' parameter passed")
        abort(500)

    try:
        response_off = retry_branch_off(branch_id=branch_id)
    except Exception as e:
        logging.error(e)
        logging.error("Can't turn off branch id={0}. Exception occured".format(branch_id))
        abort(500)

    if (mode == 'manually'):
        now = datetime.datetime.now()
        if get_next_rule_from_redis(branch_id) is not None:
            update_db_request(QUERY[mn() + '_1'].format(get_next_rule_from_redis(branch_id)['interval_id']))
        else:
            update_db_request(QUERY[mn() + '_2'].format(id, 2, 4, now.date(), now, None))

        set_next_rule_to_redis(branch_id, get_next_active_rule(branch_id))
        logging.info("Rule '{0}' added".format(str(get_next_rule_from_redis(branch_id))))

        logging.info("Branch '{0}' deactivated manually".format(branch_id))
    else:
        logging.info('No new entries is added to database.')

    arr = form_responce_for_branches(response_off)
    send_message('branch_status', {'data': json.dumps({'branches': arr}, default=date_handler)})

    return jsonify(branches=arr)


@app.route("/weather")
def weather():
    """Blablbal."""
    url = 'http://api.openweathermap.org/data/2.5/weather?id=698782&appid=319f5965937082b5cdd29ac149bfbe9f'
    try:
        response = requests.get(url=url, timeout=(3, 3))
        response.raise_for_status()
        json_data = convert_to_obj(response.text)
        return jsonify(temperature=str(round(pytemperature.k2c(json_data['main']['temp']), 2)), humidity=str(round(json_data['main']['humidity'], 2)))
    except requests.exceptions.RequestException as e:
        logging.error(e)
        logging.error("Can't get weather info Exception occured")
        return jsonify(temperature="0")


@app.route("/temperature")
def temperature():
    mode = request.args.get('force')
    if (mode is not None):
        temperature_street = 0
        humidity_street = 0

        temperature_small_h_1_fl = 0
        humidity_small_h_1_fl = 0

        temperature_small_h_2_fl = 0
        humidity_small_h_2_fl = 0

        temperature_big_h_1_fl = 0
        humidity_big_h_1_fl = 0

        temperature_big_h_2_fl = 0
        humidity_big_h_2_fl = 0

        url = 'http://api.openweathermap.org/data/2.5/weather?id=698782&appid=319f5965937082b5cdd29ac149bfbe9f'
        try:
            response = requests.get(url=url, timeout=(3, 3))
            response.raise_for_status()
            json_data = convert_to_obj(response.text)
            temperature_street = str(round(pytemperature.k2c(json_data['main']['temp']), 2)), 
            humidity_street = str(round(json_data['main']['humidity'], 2))
        except requests.exceptions.RequestException as e:
            logging.error(e)
            logging.error("Can't get weather info Exception occured")
            humidity_street = 0
            temperature_street = 0

        try:
            response = requests.get(url=ARDUINO_SMALL_H_IP + '/temperature', timeout=(3, 3))
            response.raise_for_status()
            json_data = convert_to_obj(response.text)

            temperature_small_h_1_fl = json_data['1_floor_temperature']
            humidity_small_h_1_fl = json_data['1_floor_humidity']

            temperature_small_h_2_fl = json_data['2_floor_temperature']
            humidity_small_h_2_fl = json_data['2_floor_humidity']
        except requests.exceptions.RequestException as e:
            logging.error(e)
            logging.error("Can't get temp info Exception occured")

            temperature_small_h_1_fl = 0
            humidity_small_h_1_fl = 0

            temperature_small_h_2_fl = 0
            humidity_small_h_2_fl = 0

        update_db_request(QUERY[mn() + '_2'].format(
            temperature_street, humidity_street,
            temperature_small_h_1_fl, humidity_small_h_1_fl,
            temperature_small_h_2_fl, humidity_small_h_2_fl,
            temperature_big_h_1_fl, humidity_big_h_1_fl,
            temperature_big_h_2_fl, humidity_big_h_2_fl)
        )

    res = execute_request(QUERY[mn() + '_1'], 'fetchone')
    return jsonify( 
        datetime=res[0],
        temperature_street=res[1],
        humidity_street=res[2],

        temperature_small_h_1_fl=res[3],
        humidity_small_h_1_fl=res[4],

        temperature_small_h_2_fl=res[5],
        humidity_small_h_2_fl=res[6],

        temperature_big_h_1_fl=res[7],
        humidity_big_h_1_fl=res[8],

        temperature_big_h_2_fl=res[9],
        humidity_big_h_2_fl=res[10]
    )


@app.route("/sensors")
def sensors():
    """Blablbal."""
    return app.send_static_file('sensors.html')


@app.route("/.well-known/acme-challenge/caIBL2nKjk9nIX_Earqy9Qy4vttNvOcXA_TEgfNLcUk")
def sensors2():
    """Blablbal."""
    return app.send_static_file('caIBL2nKjk9nIX_Earqy9Qy4vttNvOcXA_TEgfNLcUk')


if __name__ == "__main__":
    get_settings()
    socketio.run(app, host='0.0.0.0', port=7542, debug=DEBUG)
