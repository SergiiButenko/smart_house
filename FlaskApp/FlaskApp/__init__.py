from threading import Timer
from flask import Flask
from flask import jsonify, request

import datetime
import json, requests

app = Flask(__name__)

ARDUINO_IP='http://192.168.1.10'
#ARDUINO_IP='http://185.20.216.94:5555'

RULES_FOR_BRANCHES=[None,None,None,None,None,None,None]

def update_data(interval):
    Timer(interval, update_data, [interval]).start()    
    
    global RULES_FOR_BRANCHES
    for rule in RULES_FOR_BRANCHES: 
        if (rule is not None) and (datetime.datetime.now() >= rule['finish']):            
            response = requests.get(url=ARDUINO_IP+'/off', params={"params":rule['id']})
            json_data = json.loads(response.text)
            if (json_data['returned_value'] == 0 ):
                print("Turned off {0} branch".format(rule['id']))
                RULES_FOR_BRANCHES[rule['id']]=None
                print(str(RULES_FOR_BRANCHES))

            if (json_data['returned_value'] == 1 ):
                print("Can't turn off {0} branch".format(rule['id']))
        
# update data every 5 seconds
update_data(10)

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE')
    return response

@app.route("/")
def hello():
    return str(RULES_FOR_BRANCHES)

@app.route('/arduino_status', methods=['GET'])
def arduino_status():
    response = requests.get(url=ARDUINO_IP)
    return (response.text, response.status_code, response.headers.items())

@app.route('/activate_branch', methods=['GET'])
def activate_branch():
    id=int(request.args.get('id'))
    time_min=int(request.args.get('time'))
    
    response = requests.get(url=ARDUINO_IP+'/on', params={"params":id}) 

    now = datetime.datetime.now()
    now_plus = now + datetime.timedelta(minutes = time_min)
    
    global RULES_FOR_BRANCHES
    RULES_FOR_BRANCHES[id]={'id':id, 'start':now, 'finish': now_plus}
    
    return (response.text, response.status_code, response.headers.items())

@app.route('/deactivate_branch', methods=['GET'])
def deactivate_branch():
    id=request.args.get('id')
    
    global RULES_FOR_BRANCHES
    RULES_FOR_BRANCHES[id]=None

    response = requests.get(url=ARDUINO_IP+'/off', params={"params":id})    
    return (response.text, response.status_code, response.headers.items())

@app.route("/weather")
def weather():
    url = 'http://apidev.accuweather.com/currentconditions/v1/360247.json?language=en&apikey=hoArfRosT1215'
    response = requests.get(url=url)
    json_data = json.loads(response.text)
    return jsonify(
        temperature=str(json_data[0]['Temperature']['Metric']['Value'])
    )

@app.route('/gitwebhook', methods=['POST'])
def git_post():
    return "Done!"

if __name__ == "__main__":
    app.run(debug=True)
