from flask import Flask
import subprocess

app = Flask(__name__)
@app.route("/")
def hello():
	return "Hello, I love Digital Ocean!"

@app.route('/gitwebhook', methods=['POST'])
def git_post():
	res = ''
	try: 
		command = "sh /var/www/bash_scripts/repo_update.sh"
		res = subprocess.check_output( [cmd], shell=True) 
	except subprocess.CalledProcessError as e:
		return "An error occurred while trying to update git repo. {0}".format(res)
	return "Result: {0}".format(res)

@app.route('/gitwebhook', methods=['GET'])
def git_get():
	return "Webhooks work! Now2"

if __name__ == "__main__":
	app.run()
