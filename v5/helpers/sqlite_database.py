import sqlite3
import logging
from helpers.redis import *
from helpers.common import *

QUERY = {}
QUERY['get_next_active_rule'] = (
    "SELECT l.id, l.line_id, l.rule_id, l.timer as \"[timestamp]\", l.interval_id, l.time, li.name "
    "FROM life AS l, lines as li "
    "WHERE l.state = 1 AND l.active=1 AND l.line_id={0} AND li.number = l.line_id AND timer>=datetime('now', 'localtime') "
    "ORDER BY timer LIMIT 1")

QUERY['get_last_start_rule'] = (
    "SELECT l.id, l.line_id, l.rule_id, l.timer as \"[timestamp]\", l.interval_id "
    "FROM life AS l "
    "WHERE l.state = 2 AND l.active=1 AND l.rule_id = 1 AND l.line_id={0} AND timer<=datetime('now', 'localtime') "
    "ORDER BY timer DESC LIMIT 1")

QUERY['get_table_body_only'] = (
    "SELECT l.id, li.name, rule_type.name, l.state, l.date, l.timer as \"[timestamp]\", l.active, rule_state.full_name, l.interval_id "
    "FROM life as l, type_of_rule as rule_type, lines as li, state_of_rule as rule_state "
    "WHERE l.rule_id = rule_type.id AND l.line_id = li.number AND l.state = rule_state.id "
    "order by l.id, l.timer desc, l.interval_id")

QUERY['ongoing_rules_table'] = (
    "SELECT w.id, dw.name, li.name, rule_type.name, \"time\" as \"[timestamp]\", \"interval\", w.active "
    "FROM week_schedule as w, day_of_week as dw, lines as li, type_of_rule as rule_type "
    "WHERE  w.day_number = dw.num AND w.line_id = li.number AND w.rule_id = rule_type.id "
    "ORDER BY w.day_number, w.time")

QUERY['history'] = (
    "SELECT l.id, li.name, rule_type.name, l.state, l.date, l.timer as \"[timestamp]\", l.active, rule_state.full_name, l.time "
    "FROM life as l, type_of_rule as rule_type, lines as li, state_of_rule as rule_state "
    "WHERE l.rule_id = rule_type.id AND l.line_id = li.number AND l.timer >= datetime('now', 'localtime', '-{0} day') AND l.state = rule_state.id "
    "ORDER BY l.timer desc")

QUERY['get_timetable_list_1'] = (
    "SELECT l.id, li.name, rule_type.name, l.state, l.date, l.timer as \"[timestamp]\", l.active, rule_state.full_name, l.time "
    "FROM life as l, type_of_rule as rule_type, lines as li, state_of_rule as rule_state "
    "WHERE l.rule_id = rule_type.id AND l.line_id = li.number AND l.timer<=datetime('now', 'localtime','+{0} day') AND l.state = rule_state.id "
    "ORDER BY l.timer desc")

QUERY['get_timetable_list_2'] = (
    "SELECT l.id, li.name, rule_type.name, l.state, l.date, l.timer as \"[timestamp]\", l.active, rule_state.full_name, l.time "
    "FROM life as l, type_of_rule as rule_type, lines as li, state_of_rule as rule_state "
    "WHERE l.rule_id = rule_type.id AND l.line_id = li.number AND l.timer>= datetime('now', 'localtime', '-{0} hour') AND l.timer<=datetime('now', 'localtime', '+{0} hour') AND l.state = rule_state.id "
    "ORDER BY l.timer desc")

QUERY['ongoing_rules'] = (
    "SELECT r.id, r.line_id, r.time, r.intervals, r.time_wait, r.repeat_value, "
    "r.date_time_start, r.end_date, r.active, l.name "
    "FROM ongoing_rules as r, lines as l "
    "WHERE r.line_id = l.number "
    "ORDER BY r.date_time_start")

QUERY['add_ongoing_rule'] = (
    "INSERT INTO date_time_start(line_id, time, intervals, time_wait, repeat_value, date_time_start, "
    "end_date, active, rule_id) "
    "VALUES ({0}, {1}, {2}, {3}, {4}, '{5}', '{6}', {7}, '{8}')")

QUERY['add_rule'] = (
    "INSERT INTO life(line_id, rule_id, state, date, timer, interval_id, time) "
    "VALUES ({0}, {1}, {2}, '{3}', '{4}', '{5}', {6})")

QUERY['activate_branch_1'] = (
    "INSERT INTO life(line_id, rule_id, state, date, timer, interval_id, time) "
    "VALUES ({0}, {1}, {2}, '{3}', '{4}', '{5}', {6})")

QUERY['activate_branch_2'] = (
    "SELECT l.id, l.line_id, l.rule_id, l.timer, l.interval_id, l.time, li.name "
    "FROM life as l, lines as li "
    "WHERE l.id = {0} AND li.number = l.line_id")

QUERY['deactivate_branch_1'] = (
    "UPDATE life "
    "SET state=4 "
    "WHERE interval_id = '{0}' AND state = 1")

QUERY['deactivate_branch_2'] = (
    "INSERT INTO life(line_id, rule_id, state, date, timer, interval_id) "
    "VALUES ({0}, {1}, {2}, '{3}', '{4}', '{5}')")

QUERY['enable_rule'] = "UPDATE life SET state=2 WHERE id={0}"
QUERY['enable_rule_state_6'] = "UPDATE life SET state=6 WHERE id={0}"

QUERY['activate_ongoing_rule'] = "UPDATE week_schedule SET active=1 WHERE id={0}"

QUERY['deactivate_ongoing_rule'] = "UPDATE week_schedule SET active=0 WHERE id={0}"

QUERY['remove_rule'] = "DELETE from life WHERE id={0}"

QUERY['remove_ongoing_rule'] = "DELETE from week_schedule WHERE id={0}"

QUERY['edit_ongoing_rule'] = "DELETE from week_schedule WHERE id={0}"

QUERY['cancel_rule_1'] = "SELECT l.interval_id, li.name FROM life AS l, lines AS li WHERE l.id = {0} AND l.line_id = li.number"
QUERY['cancel_rule_2'] = "UPDATE life SET state = 4 WHERE interval_id = '{0}' AND state = 1"

QUERY['temperature_1'] = "SELECT * FROM temperature_statistics limit 1"
QUERY['temperature_2'] = (
    "INSERT INTO temperature_statistics (temperature_street, humidity_street, temperature_small_h_1_fl, humidity_small_h_1_fl, temperature_small_h_2_fl, humidity_small_h_2_fl, temperature_big_h_1_fl, humidity_big_h_1_fl, temperature_big_h_2_fl, humidity_big_h_2_fl) "
    "VALUES ('{0}', '{1}', '{2}', '{3}', '{4}', '{5}', '{6}', '{7}', '{8}', '{9}')")

QUERY['get_settings'] = "SELECT number, name, time, intervals, time_wait, start_time, line_type, base_url, pump_enabled FROM lines ORDER BY number"

QUERY['enable_rule_cancel_interval'] = "UPDATE life SET state={1} WHERE state=1 AND interval_id={0}"


# executes query and returns fetch* result
def select(query, method='fetchall'):
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
def update(query):
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
    res = select(query, 'fetchone')
    if res is None:
        return None

    logging.info("Next active rule retrieved for line id {0}".format(line_id))
    return {'id': res[0], 'line_id': res[1], 'rule_id': res[2], 'user_friendly_name': res[6], 'timer': res[3], 'interval_id': res[4], 'time': res[5]}


def get_last_start_rule(line_id):
    """Return last compeled start irrigation rule."""
    query = QUERY[mn()].format(line_id)
    res = select(query, 'fetchone')
    if res is None:
        return None

    logging.debug("Last completed rule retrieved for line id {0}".format(line_id))
    return {'id': res[0], 'line_id': res[1], 'rule_id': res[2], 'timer': res[3], 'interval_id': res[4]}
