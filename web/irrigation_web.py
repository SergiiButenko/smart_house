#!/usr/bin/python3
# -*- coding: utf-8 -*-
from flask import Flask
from flask import jsonify, request, render_template
from flask import abort
from flask.ext.cache import Cache
from eventlet import wsgi
import eventlet
from flask_socketio import SocketIO
from flask_socketio import emit
import datetime
import json
import requests
import logging
import uuid
import pytemperature
import time
from itertools import groupby
from operator import itemgetter
from controllers import relay_controller as garden_controller
from helpers import sqlite_database as database
from helpers.redis import *
from helpers.common import *

eventlet.monkey_patch()
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.DEBUG)

logging.getLogger('socketio').setLevel(logging.ERROR)
logging.getLogger('engineio').setLevel(logging.ERROR)

app = Flask(__name__)
socketio = SocketIO(app, async_mode='eventlet', engineio_logger=False)
cache = Cache(app,config={'CACHE_TYPE': 'simple'})

DEBUG = False

CACHE_TIMEOUT = 600

def update_all_rules():
    """Set next active rules for all branches."""
    try:
        for i in range(1, len(RULES_FOR_BRANCHES)):
            set_next_rule_to_redis(i, database.get_next_active_rule(i))
        logging.info("Rules updated")
    except Exception as e:
        logging.error("Exeption occured while updating all rules. {0}".format(e))


def get_settings():
    """Fill up settings array to save settings for branches."""
    try:
        branches = database.select(database.QUERY[mn()])
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


def send_message(channel, data):
    """Enclose emit method into try except block."""
    try:
        socketio.emit(channel, data)
        logging.info('Message was sent.')
        logging.debug(data)
    except Exception as e:
        logging.error(e)
        logging.error("Can't send message. Exeption occured")


def send_branch_status_message(channel, data):
    """Convert data in order to send data object."""
    send_message(channel, {'data': json.dumps({'branches': data}, default=date_handler)})


def send_ongoing_rule_message(channel, data):
    """Convert data in order to send data object."""
    send_message(channel, {'data': json.dumps({'rule': data}, default=date_handler)})


@app.route("/update_all_rules")
def update_rules():
    """Synchronize rules with database."""
    update_all_rules()
    return "OK"


@app.route("/")
@cache.cached(timeout=CACHE_TIMEOUT)
def index():
    """Index page."""
    branch_list = []
    for item in BRANCHES_SETTINGS:
        if item is not None and item['branch_id'] != 17 and item['line_type'] == 'irrigation':
            branch_list.append({
                'id': item['branch_id'],
                'name': item['name'],
                'default_time': item['time'],
                'default_interval': item['intervals'],
                'default_time_wait': item['time_wait'],
                'start_time': item['start_time']})
    return render_template('index.html', my_list=branch_list)


@app.route("/branch_settings")
@cache.cached(timeout=CACHE_TIMEOUT)
def branch_settings():
    """Return branch names."""
    branch_list = []
    for item in BRANCHES_SETTINGS:
        if item is not None and item['line_type'] == 'irrigation':
            branch_list.append({
                'id': item['branch_id'],
                'name': item['name'],
                'default_time': item['time'],
                'default_interval': item['intervals'],
                'default_time_wait': item['time_wait'],
                'start_time': item['start_time']})

    return jsonify(list=branch_list)


@app.route("/lighting")
@cache.cached(timeout=CACHE_TIMEOUT)
def lighting():
    """Return branch names."""
    branch_list = []
    for item in BRANCHES_SETTINGS:
        if item is not None and item['line_type'] == 'lighting':
            branch_list.append({
                'id': item['branch_id'],
                'name': item['name'],
                'default_time': item['time']})

    return render_template('lighting.html', my_list=branch_list)


@app.route("/lighting_settings")
@cache.cached(timeout=CACHE_TIMEOUT)
def lighting_settings():
    """Return branch names."""
    branch_list = []
    for item in BRANCHES_SETTINGS:
        if item is not None and item['line_type'] == 'lighting':
            branch_list.append({
                'id': item['branch_id'],
                'name': item['name'],
                'default_time': item['time']})

    return jsonify(list=branch_list)


@app.route("/power_outlets")
@cache.cached(timeout=CACHE_TIMEOUT)
def power_outlets():
    """Return branch names."""
    branch_list = []
    for item in BRANCHES_SETTINGS:
        if item is not None and item['line_type'] == 'power_outlet':
            branch_list.append({
                'id': item['branch_id'],
                'name': item['name'],
                'default_time': item['time']})

    return render_template('power_outlets.html', my_list=branch_list)


@app.route("/power_outlets_settings")
@cache.cached(timeout=CACHE_TIMEOUT)
def power_outlets_settings():
    """Return branch names."""
    branch_list = []
    for item in BRANCHES_SETTINGS:
        if item is not None and item['line_type'] == 'power_outlet':
            branch_list.append({
                'id': item['branch_id'],
                'name': item['name'],
                'default_time': item['time']})

    return jsonify(list=branch_list)


@app.route("/add_rule")
def add_rule_page():
    if 'add_to_date' in request.args:
        days = int(request.args.get('add_to_date'))

    branch_list = []
    for item in BRANCHES_SETTINGS:
        if item is not None and item['line_type'] == 'irrigation' and item['name'] != 'Насос':
            start_time = convert_to_datetime(item['start_time'])
            branch_list.append({
                'line_id': item['branch_id'],
                'line_name': item['name'],
                'default_time': item['time'],
                'default_interval': item['intervals'],
                'default_time_wait': item['time_wait'],
                'start_time': ("%s:%s" % (start_time.strftime("%H"), start_time.strftime("%M"))),
                'start_date': str(datetime.date.today() + datetime.timedelta(days=days))
            })

    """Add rule page."""
    return render_template('add_rule.html', my_list=branch_list)


@app.route("/history")
def history():
    """Return history page if no parameters passed and only table body if opposite."""
    if 'days' in request.args:
        days = int(request.args.get('days'))
    else:
        days = 7

    # SELECT l.interval_id, li.name, l.date, l.timer as \"[timestamp]\", l.active, l.time 
    list_arr = database.select(database.QUERY[mn()].format(days), 'fetchall')
    if list_arr is not None:
        list_arr.sort(key=itemgetter(0))
        grouped = []
        groups = groupby(list_arr, itemgetter(0))

        for key, group in groups:
            grouped.append(list([list(thing) for thing in group]))

        rules = []
        for intervals in grouped:
            intervals.sort(key=itemgetter(3))
            interval = len(intervals)

            row = intervals[0]
            id = row[0]

            rules.append(dict(line_name=row[1],
                                date=row[2].strftime('%m/%d/%Y'),
                                timer=date_handler(row[3]),
                                ative=row[4],
                                time=row[5],
                                intervals=interval,
                                interval_id=row[0]),
                                time_wait=15)

    return render_template('history.html', my_list=rules)


# @app.route("/add_rule", methods=['POST'])
# def add_rule():
#     """Used in add rule modal window."""
#     content = request.json['list']

#     for rule in content:
#         rule = content[rule]
#         branch_id = int(rule['branch_id'])
#         time_min = int(rule['time'])
#         start_time = datetime.datetime.strptime(rule['datetime_start'], "%Y-%m-%d %H:%M")
#         time_wait = int(rule['time_wait'])
#         num_of_intervals = int(rule['interval'])

#         interval_id = str(uuid.uuid4())

#         now = datetime.datetime.now()
#         stop_time = start_time + datetime.timedelta(minutes=time_min)

#         database.update(database.QUERY[mn()].format(branch_id, 1, 1, now.date(), start_time, interval_id, time_min))
#         database.update(database.QUERY[mn()].format(branch_id, 2, 1, now.date(), stop_time, interval_id, 0))

#         # first interval is executed
#         for x in range(2, num_of_intervals + 1):
#             start_time = stop_time + datetime.timedelta(minutes=time_wait)
#             stop_time = start_time + datetime.timedelta(minutes=time_min)
#             database.update(database.QUERY[mn()].format(branch_id, 1, 1, now.date(), start_time, interval_id, time_min))
#             database.update(database.QUERY[mn()].format(branch_id, 2, 1, now.date(), stop_time, interval_id, 0))
#             logging.info("Start time: {0}. Stop time: {1} added to database".format(str(start_time), str(stop_time)))

#     update_all_rules()

#     try:
#         response_status = garden_controller.branch_status()

#         arr = form_responce_for_branches(response_status)
#         send_branch_status_message('branch_status', arr)
#     except Exception as e:
#         logging.error(e)
#         logging.error("Can't send updated rules. Exception occured")
#     return json.dumps({'status': 'OK'})


@app.route("/cancel_rule")
def cancel_rule():
    """User can remove rule from ongoing rules table."""
    if ('id' not in request.args):
        logging.error("No id param in request")
        abort(500)

    id = int(request.args.get('id'))

    # select l.interval_id, li.name from life as l, lines as li where id = {0} and l.line_id = li.number
    res = database.select(database.QUERY[mn() + "_1"].format(id), 'fetchone')
    if (res is None):
        logging.error("No {0} rule id in database".format(id))
        abort(500)

    interval_id = res[0]
    ongoing_rule_id = res[2]
    # branch_name = res[1]
    # "UPDATE life SET state=4 WHERE interval_id = '{0}' and state = 1 and rule_id = 1"
    database.update(database.QUERY[mn() + '_2'].format(interval_id))

    res = database.select(database.QUERY[mn() + "_select_ongoing_rule"].format(ongoing_rule_id), 'fetchone')
    if res is None:
        logging.info('No intervals for {0} ongoing rule. Remove it'.format(ongoing_rule_id))
        database.update(database.QUERY[mn() + "_delete_ongoing_rule"].format(ongoing_rule_id))

    update_all_rules()

    try:
        response_status = garden_controller.branch_status()

        arr = form_responce_for_branches(response_status)
        send_branch_status_message('branch_status', arr)
    except Exception as e:
        logging.error(e)
        logging.error("Can't get Raspberri Pi pin status. Exception occured")
        abort(500)

    logging.info("Rule {0} canceled".format(id))
    return {'status': 'OK'}


@app.route("/ongoing_rules")
def ongoing_rules():
    """Return ongoing_rules.html."""
    list_arr = database.select(database.QUERY[mn()], 'fetchall')
    if (list_arr is None):
        list_arr = []

    rows = []
    now = datetime.datetime.now()
    # SELECT id, line_id, time, intervals, time_wait, repeat_value, dow, date_start, time_start, end_value, end_date, end_repeat_quantity
    for row in list_arr:
        rule_id = row[10]
        line_id = row[1]
        time = row[2]
        intervals = row[3]
        time_wait = row[4]
        repeat_value = row[5]
        date_time_start = row[6]
        end_date = row[7]
        active = row[8]
        name = row[9]
        days = -1

        start_dt = convert_to_datetime(date_time_start)
        end_dt = convert_to_datetime(end_date)
        
        if start_dt.date() == end_dt.date():
            date_delta = end_dt.date() - now.date()
            if date_delta.days == 0:
                days = 0
            if date_delta.days == 1:
                days = 1

        rows.append({
            'rule_id': rule_id,
            'line_id': line_id,
            'time': time,
            'intervals': intervals,
            'time_wait': time_wait,
            'repeat_value': repeat_value,
            'date_time_start': str(date_time_start),
            'end_date': str(end_date),
            'active': active,
            'line_name': name,
            'days': days})
    template = render_template('ongoing_rules.html', my_list=rows)
    return template


def update_rules_from_ongoing_rules(rule):
    """Form rules from ongoing rule."""
    database.update(database.QUERY[mn() + '_remove_from_life'].format(rule['rule_id']))

    _delta = rule['end_date'] - rule['date_time_start']
    _days = _delta.days + 1
    logging.info("number of days: {0}".format(_days))

    ongoing_rule_id = rule['rule_id']

    for days_to_add in range(0, _days + 1, rule['repeat_value']):
        date_datetime = rule['date_time_start'] + datetime.timedelta(days=days_to_add)

        # start_time = rule['date_time_start']
        branch_id = int(rule['line_id'])
        time_min = int(rule['time'])
        time_wait = int(rule['time_wait'])
        num_of_intervals = int(rule['intervals'])
        interval_id = str(uuid.uuid4())

        stop_datetime = date_datetime + datetime.timedelta(minutes=time_min)

        database.update(database.QUERY[mn() + '_add_rule_to_life'].format(
            branch_id, START_RULE, ENABLED_RULE,
            date_datetime.date(), date_datetime,
            interval_id, time_min, ongoing_rule_id))
        database.update(database.QUERY[mn() + '_add_rule_to_life'].format(
            branch_id, STOP_RULE, ENABLED_RULE,
            date_datetime.date(), stop_datetime,
            interval_id, 0, ongoing_rule_id))

        logging.info("Start time: {0}. Stop time: {1} added to database".format(str(date_datetime), str(stop_datetime)))

        # first interval is executed
        for x in range(2, num_of_intervals + 1):
            date_datetime = stop_datetime + datetime.timedelta(minutes=time_wait)
            stop_datetime = date_datetime + datetime.timedelta(minutes=time_min)

            database.update(database.QUERY[mn() + '_add_rule_to_life'].format(
                branch_id, START_RULE, ENABLED_RULE,
                date_datetime.date(), date_datetime,
                interval_id, time_min, ongoing_rule_id))
            database.update(database.QUERY[mn() + '_add_rule_to_life'].format(
                branch_id, STOP_RULE, ENABLED_RULE,
                date_datetime.date(), stop_datetime,
                interval_id, 0, ongoing_rule_id))

            logging.info("Start time: {0}. Stop time: {1} added to database".format(str(date_datetime), str(stop_datetime)))


@app.route("/add_ongoing_rule", methods=['POST'])
def add_ongoing_rule():
    """Used in add rule modal window."""
    rules = request.json['rules']
    now = datetime.datetime.now()

    for rule in rules:
        rule['line_id'] = int(rule['line_id'])
        rule['line_name'] = rule['line_name']
        rule['time'] = convert_to_datetime(rule['time'])
        rule['intervals'] = int(rule['intervals'])
        rule['time_wait'] = int(rule['time_wait'])
        rule['repeat_value'] = int(rule['repeat_value'])
        rule['date_start'] = convert_to_datetime(rule['date_start'])
        rule['time_start'] = convert_to_datetime(rule['time_start'])
        rule['date_time_start'] = datetime.datetime.combine(
            rule['date_start'], rule['time_start'].time())
        rule['end_date'] = convert_to_datetime(rule['end_date'])
        rule['active'] = 1
        rule['rule_id'] = str(uuid.uuid4())
        rule['days'] = -1

        if rule['date_start'].date() == rule['end_date'].date():
            date_delta = rule['end_date'].date() - now.date()
            if date_delta.days == 0:
                rule['days'] = 0
            if date_delta.days == 1:
                rule['days'] = 1

        # "INSERT INTO life(line_id, time, intervals, time_wait, repeat_value, date_start, "
        # "time_start, end_date, active, rule_id) "
        # "VALUES ({0}, '{1}', {2}, '{3}', {4}, {5}, '{6}', {7}, {8}, {9}")
        # insert into ongoing table
        database.update(database.QUERY[mn()].format(
            rule['line_id'], rule['time'], rule['intervals'], rule['time_wait'],
            rule['repeat_value'], rule['date_time_start'],
            rule['end_date'], rule['active'], rule['rule_id']))

        # update rules;
        update_rules_from_ongoing_rules(rule)
        logging.info("Ongoing rule added. {0}".format(str(rule)))

        template = render_template('ongoing_rule_single.html', n=rule)
        send_ongoing_rule_message(
            'add_ongoing_rule',
            {'template': template, 'rule_id': rule['rule_id'], 'days': rule['days']})

    update_all_rules()
    try:
        response_status = garden_controller.branch_status()

        arr = form_responce_for_branches(response_status)
        send_branch_status_message('branch_status', arr)
    except Exception as e:
        logging.error(e)
        logging.error("Can't send updated rules. Exception occured")

    return json.dumps({'status': 'OK'})


@app.route("/remove_ongoing_rule")
def remove_ongoing_rule():
    """User can remove ongoing rule from ui."""
    rule_id = request.args.get('id')
    database.update(database.QUERY[mn() + '_remove_from_life'].format(rule_id))
    database.update(database.QUERY[mn() + '_delete_ongoing_rule'].format(rule_id))
    update_all_rules()

    send_ongoing_rule_message('remove_ongoing_rule', {'rule_id': rule_id})

    return json.dumps({'status': 'OK'})


@app.route("/edit_ongoing_rule", methods=['PUT'])
def edit_ongoing_rule():
    """User can edit ongoing rule from ui."""
    rules = request.json['rules']
    now = datetime.datetime.now()

    for rule in rules:
        rule['line_id'] = int(rule['line_id'])
        rule['time'] = convert_to_datetime(rule['time'])
        rule['intervals'] = int(rule['intervals'])
        rule['time_wait'] = int(rule['time_wait'])
        rule['repeat_value'] = int(rule['repeat_value'])
        rule['date_start'] = convert_to_datetime(rule['date_start'])
        rule['time_start'] = convert_to_datetime(rule['time_start'])
        rule['date_time_start'] = datetime.datetime.combine(
            rule['date_start'], rule['time_start'].time())
        rule['end_date'] = convert_to_datetime(rule['end_date'])
        rule['rule_id'] = rule['rule_id']
        rule['days'] = -1

        if rule['date_start'].date() == rule['end_date'].date():
            date_delta = rule['end_date'].date() - now.date()
            if date_delta.days == 0:
                rule['days'] = 0
            if date_delta.days == 1:
                rule['days'] = 1

        # "UPDATE ongoing_rules
        # SET line_id = {0}, time = {1}, intervals = {2}, time_wait = {3}, repeat_value={4}, date_time_start='{5}'"
        # end_date = '{6}' WHERE rule_id = '{7}'"
        database.update(database.QUERY[mn() + '_ongoing'].format(
            rule['line_id'], rule['time'], rule['intervals'], rule['time_wait'],
            rule['repeat_value'], rule['date_time_start'],
            rule['end_date'], rule['rule_id']))

        # update rules;
        update_rules_from_ongoing_rules(rule)
        # update_all_rules()
        logging.info("Ongoing rule modified. {0}".format(str(rule)))

        send_ongoing_rule_message('edit_ongoing_rule', rule)

    return json.dumps({'status': 'OK'})


@app.route("/activate_ongoing_rule")
def activate_ongoing_rule():
    """User can activate ongoing rule from ui."""
    rule_id = request.args.get('id')
    database.update(database.QUERY[mn() + '_ongoing'].format(rule_id))
    database.update(database.QUERY[mn() + '_life'].format(rule_id))
    update_all_rules()

    send_ongoing_rule_message('ongoing_rule_state', {'rule_id': rule_id, 'status': 1})
    return json.dumps({'status': 'OK'})


@app.route("/deactivate_ongoing_rule")
def deactivate_ongoing_rule():
    """User can deactivate ongoing rule from ui."""
    rule_id = request.args.get('id')
    database.update(database.QUERY[mn() + '_ongoing'].format(rule_id))
    database.update(database.QUERY[mn() + '_life'].format(rule_id))
    update_all_rules()

    send_ongoing_rule_message('ongoing_rule_state', {'rule_id': rule_id, 'status': 0})
    return json.dumps({'status': 'OK'})


def form_responce_for_branches(payload):
    """Return responce with rules."""
    try:
        res = [None] * BRANCHES_LENGTH
        payload = convert_to_obj(payload)
        for branch in payload:
            status = branch['state']
            branch_id = branch['id']

            last_rule = database.get_last_start_rule(branch_id)
            next_rule = database.get_next_active_rule(branch_id)

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
        send_branch_status_message('branch_status', arr)
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
        send_branch_status_message('power_outlet_status', arr)

        response_status_big_house = requests.get(url='http://butenko.asuscomm.com:5555/branch_status', timeout=(5, 5))
        response_status_big_house.raise_for_status()

        arr2 = form_responce_for_branches(response_status_big_house.text)
        send_branch_status_message('power_outlet_status', arr2)

        return jsonify(branches=arr.contat(arr2))

    except Exception as e:
        logging.error(e)
        logging.error("Can't get arduino small_house status. Exception occured")
        abort(500)


def retry_branch_on(branch_id, time_min):
    """Retry turn on branch in case of any error."""
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
                    response_off = requests.get(url=base_url, params={'branch_id': branch_id, 'branch_alert': time_min}, timeout=(5, 5))
                    logging.info('response {0}'.format(str(response_off.text)))
                    response_off = json.loads(response_off.text)

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

        database.update(database.QUERY[mn() + '_1'].format(branch_id, 1, 2, now.date(), now, interval_id, time_min))
        lastid = database.update(database.QUERY[mn() + '_1'].format(branch_id, 2, 1, now.date(), stop_time, interval_id, 0))
        logging.debug("lastid:{0}".format(lastid))

        res = database.select(database.QUERY[mn() + '_2'].format(lastid), 'fetchone')
        logging.debug("res:{0}".format(res[0]))

        set_next_rule_to_redis(branch_id, {'id': res[0], 'line_id': res[1], 'rule_id': res[2], 'user_friendly_name': res[6], 'timer': res[3], 'interval_id': res[4], 'time': res[5]})
        logging.info("Rule '{0}' added".format(str(database.get_next_active_rule(branch_id))))

    if (mode == 'interval'):
        # first interval is already added
        for x in range(2, num_of_intervals + 1):
            start_time = stop_time + datetime.timedelta(minutes=time_wait)
            stop_time = start_time + datetime.timedelta(minutes=time_min)
            database.update(database.QUERY[mn() + '_1'].format(branch_id, 1, 1, now.date(), start_time, interval_id, time_min))
            database.update(database.QUERY[mn() + '_1'].format(branch_id, 2, 1, now.date(), stop_time, interval_id, 0))
            logging.info("Start time: {0}. Stop time: {1} added to database".format(str(start_time), str(stop_time)))

    if (mode == 'auto'):
        logging.info("Branch '{0}' activated from rules service".format(branch_id))
    else:
        logging.info("Branch '{0}' activated manually".format(branch_id))

    arr = form_responce_for_branches(response_arr)
    send_branch_status_message('branch_status', arr)

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
            database.update(database.QUERY[mn() + '_1'].format(get_next_rule_from_redis(branch_id)['interval_id']))
        else:
            database.update(database.QUERY[mn() + '_2'].format(branch_id, 2, 4, now.date(), now, None))

        set_next_rule_to_redis(branch_id, database.get_next_active_rule(branch_id))
        logging.info("Rule '{0}' added".format(str(get_next_rule_from_redis(branch_id))))

        logging.info("Branch '{0}' deactivated manually".format(branch_id))
    else:
        logging.info('No new entries is added to database.')

    arr = form_responce_for_branches(response_off)
    send_branch_status_message('branch_status', arr)

    return jsonify(branches=arr)


@app.route("/weather")
@cache.cached(timeout=CACHE_TIMEOUT)
def weather():
    """Blablbal."""
    rain = database.select(database.QUERY[mn()])[0][0]
    if rain is None:
        rain = 0

    rain_status = 0
    if rain < RAIN_MAX:
        rain_status = 1

    wurl = 'http://api.openweathermap.org/data/2.5/weather?id=698782&appid=319f5965937082b5cdd29ac149bfbe9f'
    try:
        response = requests.get(url=wurl, timeout=(10, 10))
        response.raise_for_status()
        json_data = json.loads(response.text)
        return jsonify(
            temperature=str(round(pytemperature.k2c(json_data['main']['temp']), 2)),
            humidity=str(round(json_data['main']['humidity'], 2)),
            rain=str(rain),
            rain_status=rain_status)
    except Exception as e:
        logging.error(e)
        logging.error("Can't get weather info Exception occured")
        return jsonify(
            temperature=0,
            humidity=0,
            rain=str(rain),
            rain_status=rain_status)


@app.route("/.well-known/acme-challenge/caIBL2nKjk9nIX_Earqy9Qy4vttNvOcXA_TEgfNLcUk")
def sensors2():
    """Blablbal."""
    return app.send_static_file('caIBL2nKjk9nIX_Earqy9Qy4vttNvOcXA_TEgfNLcUk')


if __name__ == "__main__":
    get_settings()
    socketio.run(app, host='0.0.0.0', port=7542, debug=DEBUG)
