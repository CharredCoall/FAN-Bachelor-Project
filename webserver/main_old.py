from flask import Flask, render_template, request, jsonify
import os
import sys
import numpy as np
import time
import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(SCRIPT_DIR)

from local_agent.app import agent, global_model, global_fridge, global_points, generate_fridge, characters

app = Flask(__name__)

log = [["Request", "Response"]]

dict_package = {
    "Response": str,
    "Fridge": dict[str,int],
    "Points": int
}

def update_package(package, model_response):
    package["Response"] = model_response
    package["Fridge"] = global_fridge
    package["Points"] = global_points
    return package

def reset_points(package):
    package["Points"] = int
    return package

def reset_package(package):
    package["Response"] = str
    package["Fridge"] = dict[str,int]
    package["Points"] = int
    return package


@app.route("/")
def show_home():
    return render_template("index.html")

@app.route("/request_reply", methods=['POST'])
def request_reply():
    global dict_package
    try :
        dict_package = reset_points(dict_package)
        message = request.json["message"]
        response = agent.run(message)

        log.append(['"' + message + '"', '"' + response + '"'])
    except:
        return jsonify("Something didn't work")
    dict_package = update_package(dict_package, response)
    return jsonify(dict_package)

@app.route("/start_convo", methods=['GET'])
def start_convo():
    global dict_package
    try :
        character_difficulty = characters[0]["difficulty"]

        generate_fridge(character_difficulty)
        
        message = """This is a prompt telling you that you have connected to the player. 
        You can now write a message to them as you need their help reducing waste from your fridge. 
        So start by introducing yourself to them and telling them that you need help making a meal!"""
        response = agent.run(message)
        
        log.append(['"' + message + '"', '"' + response + '"'])
    except:
        return jsonify("Something didn't work")
    dict_package = update_package(dict_package, response)
    return jsonify(dict_package)

@app.route("/end_convo")
def end_convo():
    global dict_package
    with open(f"{SCRIPT_DIR}/log/{global_model}_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M')}.csv", "ab") as f:
        np.savetxt(f, log, fmt="%s", delimiter=",")
    log = [["Request", "Response"]]
    dict_package = reset_package(dict_package)
    return jsonify()

if __name__ == '__main__' :
    app.run(debug=True)