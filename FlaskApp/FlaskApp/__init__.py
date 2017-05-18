from threading import Timer
from flask import Flask
import subprocess
import datetime

app = Flask(__name__)
DATA = "datetime:"

def update_data(interval):
    Timer(interval, update_data, [interval]).start()
    global DATA
    DATA = DATA + datetime.datetime.now()

# update data every 5 seconds
update_data(5)

@app.route("/")
def hello():
	return DATA

@app.route('/gitwebhook', methods=['POST'])
def git_post():
	try: 
		#subprocess.call(['sudo', 'sh', '/var/repo_update.sh'])
	except subprocess.CalledProcessError as e:
		return "An error occurred while trying to update git repo."
	return "Done!"

@app.route('/gitwebhook', methods=['GET'])
def git_get():
	return "Webhooks work! Now3"

@app.route('/active_branch', methods=['GET'])
def get_active_branch():
	return [0,1,0,0,0,0,1]


@app.route('/activate_branch', methods=['POST'])
def activate_branch():
	return "OK"



if __name__ == "__main__":
	app.run()
