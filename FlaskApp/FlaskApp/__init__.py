from flask import Flask
app = Flask(__name__)
@app.route("/")
def hello():
    return "Hello, I love Digital Ocean!"

@app.route("/test")
def hi():
    return "Second endpoint!"

if __name__ == "__main__":
    app.run()
