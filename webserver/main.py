from flask import Flask, render_template, request, jsonify
import os
import sys
import numpy as np
import time
import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(SCRIPT_DIR)

from local_agent.app import agent

app = Flask(__name__)

log = [["Request", "Response"]]

@app.route("/")
def show_home():
    return render_template("index.html")

@app.route("/request_reply", methods=['POST'])
def request_reply():
    try :
        message = request.json["message"]
        response = agent.run(message)

        log.append(['"' + message + '"', '"' + response + '"'])
    except:
        return jsonify("Something didn't work")
    return jsonify(response)

@app.route("/start_convo", methods=['GET'])
def start_convo():
    try :
        message = """This is a prompt telling you that you have connected to the player. 
        You can now write a message to them as you need their help reducing waste from your fridge. 
        So start by introducing yourself to them and telling them that you need help making a meal!"""
        response = agent.run(message)
        
        log.append(['"' + message + '"', '"' + response + '"'])
    except:
        return jsonify("Something didn't work")
    return jsonify(response)

@app.route("/end_convo")
def end_convo():
    with open(f"{SCRIPT_DIR}/log/{datetime.datetime.now().strftime('%Y-%m-%d %H_%M')}.csv", "ab") as f:
        np.savetxt(f, log, fmt="%s", delimiter=",")
    return jsonify()

if __name__ == '__main__' :
    app.run(debug=True)