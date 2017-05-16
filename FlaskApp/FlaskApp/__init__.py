from flask import Flask
import subprocess

app = Flask(__name__)
@app.route("/")
def hello():
	return "Hello, I love Digital Ocean!"

@app.route('/gitwebhook', methods=['POST'])
def git_post():
	try: 
		subprocess.call(['sh', '/var/repo_update.sh'])
	except subprocess.CalledProcessError as e:
		return "An error occurred while trying to update git repo."
	return "Done!"

@app.route('/gitwebhook', methods=['GET'])
def git_get():
	return "Webhooks work! Now2"

if __name__ == "__main__":
	app.run()
