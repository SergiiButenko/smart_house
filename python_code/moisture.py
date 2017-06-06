#! /usr/bin/python3

import requests
import json
from threading import Timer
import time
import datetime

f_name = '/home/sprinkler/moisture.txt'
def fname(arg):
    return open(arg, "a")

def record():
    response = requests.get(url='http://185.20.216.94:5555/analog/0')
    m_data = json.loads(response.text)
    out = fname(f_name)
    print(time.strftime("%d-%m %R", time.localtime()) + "  " + str(m_data['return_value']), file=out)
    out.close()
    Timer(1800, record).start()

record()

while 1:
    pass
