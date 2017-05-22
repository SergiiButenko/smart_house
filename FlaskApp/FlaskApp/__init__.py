from threading import Timer
from flask import Flask
from flask import jsonify, request

import datetime
import json, requests

app = Flask(__name__)
DATA = ""

ARDUINO_IP='http://192.168.1.10'
#ARDUINO_IP='http://185.20.216.94:5555'


def update_data(interval):
    Timer(interval, update_data, [interval]).start()
    global DATA
    DATA = str(datetime.datetime.now())
 
# update data every 5 seconds
update_data(3)

@app.route("/")
def hello():
	return DATA


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

@app.route('/gitwebhook', methods=['GET'])
def git_get():
	return "Webhooks work! Now3"

@app.route('/active_branch', methods=['GET'])
def get_active_branch():
	return [0,1,0,0,0,0,1]

@app.route('/arduino_status', methods=['GET'])
def arduino_status():
	response = requests.get(url=ARDUINO_IP)
	return response.text

@app.route('/activate_branch', methods=['PUT'])
def activate_branch():
	response = requests.get(url=ARDUINO_IP+'/off', params={"params":request.form['id']})	
	return response.text

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE')
    return response


if __name__ == "__main__":
	app.run(debug=True)
