from flask import Flask
app = Flask(__name__)
@app.route("/")
def hello():
    return "Hello, I love Digital Ocean!"

@app.route('/gitwebhook', methods=['POST'])
def git_post():
    return "POST"

@app.route('/gitwebhook', methods=['GET'])
def git_get():
    return "GET"

if __name__ == "__main__":
    app.run()
