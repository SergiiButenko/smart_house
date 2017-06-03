#! /usr/bin/python3
import os
import time
import psycopg2
import sched
import datetime

class Rshed(object):
    """docstring for Rshed."""
    def __init__(self):
        super(Rshed, self).__init__()
#        self.arg = arg
    rules_dict = {}
    def execute_request(self, query, method):
        dir = os.path.dirname(__file__)
        sql_file = os.path.join(dir, '..','sql', query)
        conn=None
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
            if conn is not None:
                conn.close()
