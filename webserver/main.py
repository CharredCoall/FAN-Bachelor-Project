from flask import Flask, render_template, request, jsonify
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(SCRIPT_DIR)

from local_agent.app import agent

app = Flask(__name__)

@app.route("/")
def show_home():
    return render_template("index.html")

@app.route("/request_reply", methods=['POST'])
def request_reply():
    try :
        message = request.json["message"]
        print("The recieved message was: " + message)
        response = agent.run(message)
    except:
        return jsonify("Something didn't work")
    return jsonify(response)


if __name__ == '__main__' :
    app.run(debug=True)