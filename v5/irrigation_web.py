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
import logging
import uuid
import pytemperature
import time
from controllers import relay_controller as garden_controller
from helpers import sqlite_database as database
from helpers.redis import *
from helpers.common import *

eventlet.monkey_patch()
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.INFO)

logging.getLogger('socketio').setLevel(logging.ERROR)
logging.getLogger('engineio').setLevel(logging.ERROR)

app = Flask(__name__)
socketio = SocketIO(app, async_mode='eventlet', engineio_logger=False)

DEBUG = False

VIBER_BOT_IP = 'https://mozart.hopto.org:7443'
ARDUINO_SMALL_H_IP = 'http://butenko.asuscomm.com:5555'

BRANCHES_LENGTH = 18
RULES_FOR_BRANCHES = [None] * BRANCHES_LENGTH
BRANCHES_SETTINGS = [None] * BRANCHES_LENGTH


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


@app.route("/update_all_rules")
def update_rules():
    """Synchronize rules with database."""
    update_all_rules()
    return "OK"


@app.route("/")
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
    """Add rule page."""
    return render_template('add_rule.html')


def get_table_body_only(query=None):
    """If no query is passed returns all entries from life table."""
    if (query is None):
        query = database.QUERY[mn()]

    list_arr = database.select(query, 'fetchall')

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

            rows.append({
                'id': id,
                'branch_name': branch_name,
                'rule_name': rule_name,
                'state': state,
                'time': time,
                'timer': "{:%A, %d-%m-%y %R}".format(timer),
                'outdated': outdated,
                'active': active,
                'rule_state': rule_state})

    template = render_template('timetable_table_only.html', my_list=rows)
    return template


@app.route("/history")
def history():
    """Return history page if no parameters passed and only table body if opposite."""
    if 'days' in request.args:
        days = int(request.args.get('days'))
    else:
        days = 60

    list_arr = database.select(database.QUERY[mn()].format(days), 'fetchall')
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

            rows.append({
                'id': id,
                'branch_name': branch_name,
                'rule_name': rule_name,
                'state': state,
                'time': time,
                'timer': "{:%A, %d-%m-%y %R}".format(timer),
                'outdated': outdated,
                'active': active,
                'rule_state': rule_state})

    template = render_template('history.html', my_list=rows)
    return template


@app.route("/add_rule", methods=['POST'])
def add_rule():
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
    requester = request.args.get('requester')

    # select l.interval_id, li.name from life as l, lines as li where id = {0} and l.line_id = li.number
    res = database.select(database.QUERY[mn() + "_1"].format(id), 'fetchone')
    if (res is None):
        logging.error("No {0} rule id in database".format(id))
        abort(500)

    interval_id = res[0]
    # branch_name = res[1]
    # "UPDATE life SET state=4 WHERE interval_id = '{0}' and state = 1 and rule_id = 1"
    database.update(database.QUERY[mn() + '_2'].format(interval_id))
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
    return render_template('index.html')


def ongoing_rules_table():
    """Return only table for ongoing rules page."""
    list_arr = database.select(database.QUERY[mn()], 'fetchall')
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
        rows.append({
            'id': id,
            'branch_name': branch_name,
            'dow': day_number,
            'rule_name': rule_name,
            'time': time,
            'minutest': minutes,
            'active': active,
            'rule_state': rule_state})

    template = render_template('ongoing_rules_table_only.html', my_list=rows)
    return template


@app.route("/ongoing_rules")
def ongoing_rules():
    """Return ongoing_rules.html."""
    list_arr = database.select(database.QUERY[mn()], 'fetchall')
    if (list_arr is None):
        list_arr = []

    rows = []
    # SELECT id, line_id, time, intervals, time_wait, repeat_value, dow, date_start, time_start, end_value, end_date, end_repeat_quantity 
    for row in list_arr:
        rule_id = row[0]
        line_id = row[1]
        time = row[2]
        intervals = row[3]
        time_wait = row[4]
        repeat_value = row[5]
        date_time_start = row[6]
        end_date = row[7]
        active = row[8]
        name = row[9]
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
            'name': name})
    template = render_template('ongoing_rules.html', my_list=rows)
    return template


def update_rules_from_ongoing_rules(rule):
    """Form rules from ongoing rule."""
    # select * from ongoing_rule where rule_id = rule['rule_id']
    if len(res) > 0:
        # update
        # delete from life where ongoing_rule_id = rule['rule_id'] and timer >= now('localime', 'utc')
        print('s')

    if rule['end_value'] in (1, 3):
        now = datetime.datetime.now()
        end_date = rule['end_date']

    


    if rule['end_value'] == 3:
        end_date = rule['']

    if rule['end_value'] == 3:
        end_date = rule['']


    # insert


@app.route("/add_ongoing_rule", methods=['POST'])
def add_ongoing_rule():
    """Used in add rule modal window."""
    rule = request.json['rule']
    rule['line_id'] = int(rule['line_id'])
    rule['time'] = convert_to_datetime(rule['time'])
    rule['intervals'] = int(rule['intervals'])
    rule['time_wait'] = int(rule['time_wait'])
    rule['repeat_value'] = int(rule['repeat_value'])
    rule['date_start'] = convert_to_datetime(rule['date_start'])
    rule['time_start'] = convert_to_datetime(rule['time_start'])
    rule['date_time_start'] = datetime.datetime.combine(
        rule['date_start'], rule['time_start'].time()
        )
    rule['end_date'] = convert_to_datetime(rule['end_date'])
    rule['active'] = 1
    rule['rule_id'] = str(uuid.uuid4())

    # "INSERT INTO life(line_id, time, intervals, time_wait, repeat_value, date_start, "
    # "time_start, end_date, active, rule_id) "
    # "VALUES ({0}, '{1}', {2}, '{3}', {4}, {5}, '{6}', {7}, {8}, {9}")
    # insert into ongoing table
    database.update(database.QUERY[mn()].format(
        rule['line_id'], rule['time'], rule['intervals'], rule['time_wait'],
        rule['repeat_value'], rule['date_time_start'],
        rule['end_date'], rule['active'], rule['rule_id']))

    # update rules;
    # update_rules_from_ongoing_rules(rule['rule_id'])
    update_all_rules()
    logging.info("Rule added. {0}".format(str(rule)))
    return json.dumps({'status': 'OK'})


@app.route("/remove_ongoing_rule")
def remove_ongoing_rule():
    """User can remove ongoing rule from ui."""
    id = int(request.args.get('id'))
    database.update(database.QUERY[mn()].format(id))
    update_all_rules()
    template = ongoing_rules_table()
    send_message('ongoind_rules_update', {'data': template})
    return template


@app.route("/edit_ongoing_rule")
def edit_ongoing_rule():
    """User can edit ongoing rule from ui."""
    # id = int(request.args.get('id'))
    # database.update(database.QUERY[mn()].format(id))
    update_all_rules()
    template = ongoing_rules_table()
    send_message('ongoind_rules_update', {'data': template})
    return template


@app.route("/activate_ongoing_rule")
def activate_ongoing_rule():
    """User can activate ongoing rule from ui."""
    id = int(request.args.get('id'))
    database.update(database.QUERY[mn()].format(id))
    update_all_rules()
    template = ongoing_rules_table()
    send_message('ongoind_rules_update', {'data': template})
    return template


@app.route("/deactivate_ongoing_rule")
def deactivate_ongoing_rule():
    """User can deactivate ongoing rule from ui."""
    id = int(request.args.get('id'))
    database.update(database.QUERY[mn()].format(id))
    update_all_rules()
    template = ongoing_rules_table()
    send_message('ongoind_rules_update', {'data': template})
    return template


@app.route("/get_timetable_list")
def get_timetable_list():
    """Blablbal."""
    if 'days' in request.args:
        days = int(request.args.get('days'))
        return get_table_body_only(database.QUERY[mn() + '_1'].format(days))

    if 'before' in request.args and 'after' in request.args:
        before = int(request.args.get('before'))
        after = int(request.args.get('after'))
        return get_table_body_only(database.QUERY[mn() + '_2'].format(before, after))


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
    """Collect temperature from each station."""
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

        database.update(database.QUERY[mn() + '_2'].format(
            temperature_street, humidity_street,
            temperature_small_h_1_fl, humidity_small_h_1_fl,
            temperature_small_h_2_fl, humidity_small_h_2_fl,
            temperature_big_h_1_fl, humidity_big_h_1_fl,
            temperature_big_h_2_fl, humidity_big_h_2_fl)
        )

    res = database.select(database.QUERY[mn() + '_1'], 'fetchone')
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
