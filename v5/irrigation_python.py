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

eventlet.monkey_patch()
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.INFO)

logging.getLogger('socketio').setLevel(logging.ERROR)
logging.getLogger('engineio').setLevel(logging.ERROR)

app = Flask(__name__)
socketio = SocketIO(app, async_mode='eventlet', engineio_logger=False)
redis_db = redis.StrictRedis(host="localhost", port=6379, db=0)

DEBUG = False

ARDUINO_WEATHER_IP = 'http://192.168.1.10'
ARDUINO_IP = 'http://185.20.216.94:5555' if DEBUG else 'http://192.168.1.10'
VIBER_BOT_IP = 'https://mozart.hopto.org:7443'

USERS = [
{'name':'Сергей', 'id': 'cHxBN+Zz1Ldd/60xd62U/w=='}
# {'name':'Сергей', 'id': 'cHxBN+Zz1Ldd/60xd62U/w=='}, 
# {'name':'Сергей', 'id': 'cHxBN+Zz1Ldd/60xd62U/w=='}
]

# ARDUINO_IP = 'http://192.168.1.144'
# ARDUINO_IP = 'http://butenko.asuscomm.com:5555'

HUMIDITY_MAX = 1000
RULES_FOR_BRANCHES = [None] * 18
SENSORS = {'time': datetime.datetime.now(), 'data': {'temperature': 0, 'humidity': 0, 'rain': False, 'daylight': False},
'user_message': '', 'allow_irrigation': False, 'rule_status': 0}


# For get function name intro function. Usage mn(). Return string with current function name. Instead 'query' will be QUERY[mn()].format(....)
mn = lambda: inspect.stack()[1][3]

QUERY = {}
QUERY['get_next_active_rule'] = "SELECT l.id, l.line_id, l.rule_id, l.timer as \"[timestamp]\", l.interval_id, l.time, li.name  FROM life AS l, lines as li WHERE l.state = 1 AND l.active=1 AND l.line_id={0} AND li.number = l.line_id AND timer>=datetime('now', 'localtime') ORDER BY timer LIMIT 1"
QUERY['get_last_start_rule'] = "SELECT l.id, l.line_id, l.rule_id, l.timer as \"[timestamp]\", l.interval_id  FROM life AS l WHERE l.state = 2 AND l.active=1 AND l.rule_id = 1 AND l.line_id={0} AND timer<=datetime('now', 'localtime') ORDER BY timer DESC LIMIT 1"
QUERY['get_table_body_only'] = "SELECT l.id, li.name, rule_type.name, l.state, l.date, l.timer as \"[timestamp]\", l.active, rule_state.full_name, l.interval_id FROM life as l, type_of_rule as rule_type, lines as li, state_of_rule as rule_state WHERE l.rule_id = rule_type.id AND l.line_id = li.number and l.state = rule_state.id order by l.id, l.timer desc, l.interval_id"
QUERY['ongoing_rules_table'] = "SELECT w.id, dw.name, li.name, rule_type.name, \"time\" as \"[timestamp]\", \"interval\", w.active FROM week_schedule as w, day_of_week as dw, lines as li, type_of_rule as rule_type WHERE  w.day_number = dw.num AND w.line_id = li.number and w.rule_id = rule_type.id ORDER BY w.day_number, w.time"
QUERY['branches_names'] = "SELECT number, name, time, intervals, time_wait, start_time from lines order by number"
# QUERY['timetable'] = "SELECT l.id, li.name, rule_type.name, l.state, l.date, l.timer as \"[timestamp]\", l.active, rule_state.full_name, l.interval_id, l.time FROM life as l, type_of_rule as rule_type, lines as li, state_of_rule as rule_state WHERE l.rule_id = rule_type.id AND l.line_id = li.number AND l.timer>= datetime('now', 'localtime', '-{0} hours') AND l.timer<=datetime('now', 'localtime', '+{0} hours') and l.state = rule_state.id order by l.timer desc"
QUERY['history'] = "SELECT l.id, li.name, rule_type.name, l.state, l.date, l.timer as \"[timestamp]\", l.active, rule_state.full_name, l.time FROM life as l, type_of_rule as rule_type, lines as li, state_of_rule as rule_state WHERE l.rule_id = rule_type.id AND l.line_id = li.number AND l.timer >= datetime('now', 'localtime', '-{0} day') and l.state = rule_state.id order by l.timer desc"
QUERY['ongoing_rules'] = "SELECT w.id, dw.name, li.name, rule_type.name, \"time\" as \"[timestamp]\", \"interval\", w.active FROM week_schedule as w, day_of_week as dw, lines as li, type_of_rule as rule_type WHERE  w.day_number = dw.num AND w.line_id = li.number and w.rule_id = rule_type.id ORDER BY w.day_number, w.time"
QUERY['get_timetable_list_1'] = "SELECT l.id, li.name, rule_type.name, l.state, l.date, l.timer as \"[timestamp]\", l.active, rule_state.full_name, l.time FROM life as l, type_of_rule as rule_type, lines as li, state_of_rule as rule_state WHERE l.rule_id = rule_type.id AND l.line_id = li.number AND l.timer<=datetime('now', 'localtime','+{0} day') and l.state = rule_state.id  order by l.timer desc"
QUERY['get_timetable_list_2'] = "SELECT l.id, li.name, rule_type.name, l.state, l.date, l.timer as \"[timestamp]\", l.active, rule_state.full_name, l.time FROM life as l, type_of_rule as rule_type, lines as li, state_of_rule as rule_state WHERE l.rule_id = rule_type.id AND l.line_id = li.number AND l.timer>= datetime('now', 'localtime', '-{0} hour') and l.timer<=datetime('now', 'localtime', '+{0} hour') and l.state = rule_state.id  order by l.timer desc"
QUERY['add_rule'] = "INSERT INTO life(line_id, rule_id, state, date, timer, interval_id, time) VALUES ({0}, {1}, {2}, '{3}', '{4}', '{5}', {6})"
QUERY['add_rule_endpoint_v2'] = "INSERT INTO life(line_id, rule_id, state, date, timer, interval_id, time) VALUES ({0}, {1}, {2}, '{3}', '{4}', '{5}', {6})"
QUERY['add_ongoing_rule'] = "INSERT INTO week_schedule(day_number, line_id, rule_id, \"time\", \"interval\", active) VALUES ({0}, {1}, {2}, '{3}', {4}, 1)"
QUERY['activate_branch_1'] = "INSERT INTO life(line_id, rule_id, state, date, timer, interval_id, time) VALUES ({0}, {1}, {2}, '{3}', '{4}', '{5}', {6})"
QUERY['activate_branch_2'] = "SELECT l.id, l.line_id, l.rule_id, l.timer, l.interval_id, l.time, li.name FROM life as l, lines as li where id = {0} and li.number = l.line_id"
QUERY['deactivate_branch_1'] = "UPDATE life SET state=4 WHERE interval_id = '{0}' and state = 1 and rule_id = 1"
QUERY['deactivate_branch_2'] = "INSERT INTO life(line_id, rule_id, state, date, timer, interval_id) VALUES ({0}, {1}, {2}, '{3}', '{4}', '{5}')"
QUERY['enable_rule'] = "UPDATE life SET state=2 WHERE id={0}"
QUERY['enable_rule_state_6'] = "UPDATE life SET state=6 WHERE id={0}"
QUERY['activate_rule'] = "UPDATE life SET active=1 WHERE id={0}"
QUERY['deactivate_rule'] = "UPDATE life SET active=0 WHERE id={0}"
QUERY['deactivate_all_rules_1'] = "UPDATE life SET active=0 WHERE timer>= datetime('now', 'localtime') AND timer<=datetime('now', 'localtime', '+1 day')"
QUERY['deactivate_all_rules_2'] = "UPDATE life SET active=0 WHERE timer>= datetime('now', 'localtime')  AND timer<=datetime('now', 'localtime', '+7 days')"
QUERY['activate_ongoing_rule'] = "UPDATE week_schedule SET active=1 WHERE id={0}"
QUERY['deactivate_ongoing_rule'] = "UPDATE week_schedule SET active=0 WHERE id={0}"
QUERY['remove_rule'] = "DELETE from life WHERE id={0}"
QUERY['remove_ongoing_rule'] = "DELETE from week_schedule WHERE id={0}"
QUERY['edit_ongoing_rule'] = "DELETE from week_schedule WHERE id={0}"

QUERY['cancel_rule_1'] = "SELECT l.interval_id, li.name FROM life AS l, lines AS li WHERE l.id = {0} AND l.line_id = li.number"
QUERY['cancel_rule_2'] = "UPDATE life SET state=4 WHERE interval_id = '{0}' and state = 1 and rule_id = 1"


@socketio.on_error_default
def error_handler(e):
    """Used to handle error for websockets."""
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
    try:
        data = json.dumps(data, default=date_handler)
        res = redis_db.set(branch_id, data)
    except Exception as e:
        logging.error("Can't save data to redis. Exception occured {0}".format(e))

    return res


def get_next_rule_from_redis(branch_id):
    """Get next rule from redis."""
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


def get_weather(force_update='false', ignore_sensors='false'):
    """Use data from weather station. Refresh data per hour."""
    if (force_update == 'true' or datetime.datetime.now() > (datetime.datetime.now() + datetime.timedelta(minutes=60))):
        json_data = ''
        try:
            response = requests.get(url=ARDUINO_WEATHER_IP + "/weather", timeout=(3, 3))
            json_data = json.loads(response.text)
        except Exception as e:
            logging.error(e)
            logging.error("Can't get weather status. Exeption occured")
            return None

        SENSORS['time'] = datetime.datetime.now()
        SENSORS['data']['temperature'] = json_data['temperature']
        SENSORS['data']['humidity'] = json_data['humidity']
        SENSORS['data']['rain'] = json_data['rain']
        SENSORS['data']['daylight'] = json_data['daylight']

    SENSORS['data']['allow_irrigation'] = True
    SENSORS['data']['user_message'] = 'Автоматический полив разрешен.'

    if (ignore_sensors == 'false' and SENSORS['data']['rain'] is True):
        SENSORS['data']['allow_irrigation'] = False
        SENSORS['data']['user_message'] = 'Автоматический полив запрещен из-за дождя.'
        SENSORS['data']['rule_status'] = 5

    if (ignore_sensors == 'false' and SENSORS['data']['humidity'] > HUMIDITY_MAX):
        SENSORS['data']['allow_irrigation'] = False
        SENSORS['data']['user_message'] = 'Автоматический полив запрещен датчиком влажности.'
        SENSORS['data']['rule_status'] = 6

    return SENSORS


@app.route("/weather2")
def weather_station():
    """Synchronize with weather station."""
    force_update = request.args.get('force_update')
    if (force_update is None):
        force_update = 'false'

    ignore_sensors = request.args.get('ignore_sensors')
    if (ignore_sensors is None):
        ignore_sensors = 'false'

    get_weather(force_update, ignore_sensors)
    return str(SENSORS)


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
        logging.error("Error while performing operation with database: {0}".format(e))
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
    lastrowid = 0
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
        logging.error("Error while performing operation with database: {0}".format(e))
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


@app.route("/update_all_rules")
def update_rules():
    """Synchronize rules with database."""
    update_all_rules()
    return "OK"


@app.route("/branches_names")
def branches_names():
    """Return branch names."""
    branch_list = []
    res = execute_request(QUERY[mn()], 'fetchall')
    if res is None:
        logging.error("Can't get branches names from database")
        abort(500)

    for row in res:
        branch_list.append({'id': row[0], 'name': row[1], 'default_time': row[2], 'default_interval': row[3], 'default_time_wait': row[4],
            'start_time': row[5]})

    return jsonify(list=branch_list)


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


@app.route("/v2/add_rule", methods=['POST'])
def add_rule_endpoint_v2():
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
        response_status = requests.get(url=ARDUINO_IP + '/branch_status', timeout=(3, 3))
        response_status.raise_for_status()

        arr = form_responce_for_branches(response_status.text)
        send_message('branch_status', {'data': json.dumps({'branches': arr}, default=date_handler)})
    except Exception as e:
        logging.error(e)
        logging.error("Can't get arduino status. Exception occured")
        abort(500)

    if ('sender' not in request.args):
        logging.info("No sender param in request. No message will be send")
    else:
        sender = request.args.get('sender')
        try:
            payload = {'user_name': sender, 'branch_name': branch_name, 'users': USERS}
            response = requests.post(VIBER_BOT_IP + '/notify_users', json=payload, timeout=(3, 3))
            response.raise_for_status()
        except Exception as e:
            logging.error(e)
            logging.error("Can't send rule to viber. Ecxeption occured")

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
        res = [None] * 18
        payload = json.loads(payload)
        for branch_id in payload:
            status = payload[branch_id]
            if branch_id == 'pump':
                branch_id = 17

            last_rule = get_last_start_rule(branch_id)
            next_rule = get_next_active_rule(branch_id)

            res[int(branch_id)] = {'id': branch_id, 'status': status, 'next_rule': next_rule, 'last_rule': last_rule}
        return res
    except Exception as e:
        logging.error(e)
        logging.error("Can't form responce. Exception occured")
        raise e


@app.route('/arduino_status', methods=['GET'])
def arduino_status():
    """Return status of arduino relay."""
    try:
        response_status = requests.get(url=ARDUINO_IP + '/branch_status', timeout=(3, 3))
        response_status.raise_for_status()

        arr = form_responce_for_branches(response_status.text)
        send_message('branch_status', {'data': json.dumps({'branches':arr}, default=date_handler)})

        return jsonify(branches=arr)

    except requests.exceptions.RequestException as e:
        logging.error(e)
        logging.error("Can't get arduino status. Exception occured")
        abort(500)


def retry_branch_on(id, time_min):
    """Use to retry turn on branch in case of any error."""
    try:
        for attempt in range(2):
            try:
                payload = (('branch_id', id), ('branch_alert', time_min + 2))
                response_on = requests.get(url=ARDUINO_IP + '/branch_on', params=payload, timeout=(3, 3))
                response_on.raise_for_status()
                logging.info('response {0}'.format(response_on.text))

                if (id == 17):
                    arduino_branch_name = 'pump'
                else:
                    arduino_branch_name = id

                resp = json.loads(response_on.text)
                if (resp[str(arduino_branch_name)] != "1"):
                    logging.error('Branch {0} cant be turned on. response {1}'.format(id, response_on.text))
                    time.sleep(2)
                    continue
                else:
                    logging.info('Branch {0} is turned on by rule'.format(id))
                    return response_on
            except requests.exceptions.Timeout as e:
                logging.error(e)
                logging.error("Can't turn on {0} branch. Timeout Exception occured  {1} try out of 2".format(id, attempt))
                time.sleep(2)
                continue
            except Exception as e:
                logging.error(e)
                logging.error("Can't turn on {0} branch. Exception occured. {1} try out of 2".format(id, attempt))
                time.sleep(2)
                continue

        raise Exception("Can't turn on {0} branch. Retries limit reached".format(id))
    except Exception as e:
        logging.error(e)
        logging.error("Can't turn on branch id={0}. Exception occured".format(id))
        raise Exception("Can't turn on {0} branch".format(id))


@app.route('/activate_branch', methods=['GET'])
def activate_branch():
    """Blablbal."""
    mode = request.args.get('mode')
    if (mode is None):
        logging.error("no 'mode' parameter passed")
        abort(500)

    if (mode == 'single'):
        id = int(request.args.get('id'))
        time_min = int(request.args.get('time_min'))
    elif (mode == 'interval'):
        id = int(request.args.get('id'))
        time_min = int(request.args.get('time_min'))
        time_wait = int(request.args.get('time_wait'))
        num_of_intervals = int(request.args.get('quantity'))
    elif (mode == 'auto'):
        id = int(request.args.get('id'))
        time_min = int(request.args.get('time_min'))
    else:
        logging.error("incorrect mode parameter passed: {0}".format(mode))
        abort(500)

    try:
        response_on = retry_branch_on(id, time_min)
        response_on.raise_for_status()
    except Exception as e:
        logging.error(e)
        logging.error("Can't turn on branch id={0}. Exception occured".format(id))
        abort(500)

    # needs to be executed in both cases single and interval, but in in auto
    if (mode != 'auto'):
        interval_id = str(uuid.uuid4())
        now = datetime.datetime.now()
        stop_time = now + datetime.timedelta(minutes=time_min)

        update_db_request(QUERY[mn() + '_1'].format(id, 1, 2, now.date(), now, interval_id, time_min))
        lastid = update_db_request(QUERY[mn() + '_1'].format(id, 2, 1, now.date(), stop_time, interval_id, 0))
        logging.debug("lastid:{0}".format(lastid))

        res = execute_request(QUERY[mn() + '_2'].format(lastid), 'fetchone')
        logging.debug("res:{0}".format(res[0]))

        set_next_rule_to_redis(id, {'id': res[0], 'line_id': res[1], 'rule_id': res[2], 'user_friendly_name': res[6], 'timer': res[3], 'interval_id': res[4], 'time': res[5]})
        logging.info("Rule '{0}' added".format(str(get_next_active_rule(id))))

    if (mode == 'interval'):
        # first interval is already added
        for x in range(2, num_of_intervals + 1):
            start_time = stop_time + datetime.timedelta(minutes=time_wait)
            stop_time = start_time + datetime.timedelta(minutes=time_min)
            update_db_request(QUERY[mn() + '_1'].format(id, 1, 1, now.date(), start_time, interval_id, time_min))
            update_db_request(QUERY[mn() + '_1'].format(id, 2, 1, now.date(), stop_time, interval_id, 0))
            logging.info("Start time: {0}. Stop time: {1} added to database".format(str(start_time), str(stop_time)))

    if (mode == 'auto'):
        logging.info("Branch '{0}' activated from rules service".format(id))
    else:
        logging.info("Branch '{0}' activated manually".format(id))

    arr = form_responce_for_branches(response_on.text)
    send_message('branch_status', {'data': json.dumps({'branches': arr}, default=date_handler)})

    return jsonify(branches=arr)


def retry_branch_off(id):
    """Use to retry turn off branch in case of any error."""
    try:
        for attempt in range(2):
            try:
                response_off = requests.get(url=ARDUINO_IP + '/branch_off', params={"branch_id": id}, timeout=(3, 3))
                response_off.raise_for_status()
                logging.info('response {0}'.format(response_off.text))

                if (id == 17):
                    arduino_branch_name = 'pump'
                else:
                    arduino_branch_name = id

                resp = json.loads(response_off.text)
                if (resp[str(arduino_branch_name)] != "0"):
                    logging.error('Branch {0} cant be turned off. response {1}'.format(id, response_off.text))
                    time.sleep(2)
                    continue
                else:
                    logging.info('Branch {0} is turned off by rule'.format(id))
                    return response_off
            except requests.exceptions.Timeout as e:
                logging.error(e)
                logging.error("Can't turn off {0} branch. Timeout Exception occured  {1} try out of 2".format(id, attempt))
                time.sleep(2)
                continue
            except Exception as e:
                logging.error(e)
                logging.error("Can't turn off {0} branch. Exception occured. {1} try out of 2".format(id, attempt))
                time.sleep(2)
                continue

        raise Exception("Can't turn off {0} branch. Retries limit reached".format(id))
    except Exception as e:
        logging.error(e)
        logging.error("Can't turn off branch id={0}. Exception occured".format(id))
        raise Exception("Can't turn off {0} branch".format(id))


@app.route('/deactivate_branch', methods=['GET'])
def deactivate_branch():
    """Route is used to disable branch."""
    """Can be executed manaully - row will be added to database
    or with rules service - no new row will be added to database"""
    id = int(request.args.get('id'))
    mode = request.args.get('mode')
    if (mode is None):
        logging.error("no 'mode' parameter passed")
        abort(500)

    try:
        response_off = retry_branch_off(id)
        response_off.raise_for_status()
    except Exception as e:
        logging.error(e)
        logging.error("Can't turn on branch id={0}. Exception occured".format(id))
        abort(500)

    if (mode == 'manually'):
        now = datetime.datetime.now()
        if get_next_rule_from_redis(id) is not None:
            update_db_request(QUERY[mn() + '_1'].format(get_next_rule_from_redis(id)['interval_id']))
        else:
            update_db_request(QUERY[mn() + '_2'].format(id, 2, 4, now.date(), now, None))

        set_next_rule_to_redis(id, get_next_active_rule(id))
        logging.info("Rule '{0}' added".format(str(get_next_rule_from_redis(id))))

        logging.info("Branch '{0}' deactivated manually".format(id))
    else:
        logging.info('No new entries is added to database.')

    arr = form_responce_for_branches(response_off.text)
    send_message('branch_status', {'data': json.dumps({'branches':arr}, default=date_handler)})

    return jsonify(branches=arr)


@app.route("/weather")
def weather():
    """Blablbal."""
    # url = 'http://apidev.accuweather.com/currentconditions/v1/360247.json?language=en&apikey=hoArfRosT1215'
    url = 'http://api.openweathermap.org/data/2.5/weather?id=698782&appid=319f5965937082b5cdd29ac149bfbe9f'
    try:
        response = requests.get(url=url, timeout=(3, 3))
        response.raise_for_status()
        json_data = json.loads(response.text)
        return jsonify(temperature=str(round(pytemperature.k2c(json_data['main']['temp']), 2)), humidity=str(round(json_data['main']['humidity'], 2)))
    except requests.exceptions.RequestException as e:
        logging.error(e)
        logging.error("Can't get weather info Exception occured")
        return jsonify(temperature="0")


@app.route("/sensors")
def sensors():
    """Blablbal."""
    return app.send_static_file('sensors.html')


@app.route("/.well-known/acme-challenge/caIBL2nKjk9nIX_Earqy9Qy4vttNvOcXA_TEgfNLcUk")
def sensors2():
    """Blablbal."""
    return app.send_static_file('caIBL2nKjk9nIX_Earqy9Qy4vttNvOcXA_TEgfNLcUk')


@app.after_request
def after_request(response):
    """Blablbal."""
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE')
    return response


if __name__ == "__main__":
    socketio.run(app, host='0.0.0.0', port=7542, debug=DEBUG)
