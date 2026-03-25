from flask import Flask, render_template, request, jsonify
import os
import sys
import numpy as np
import time
import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(SCRIPT_DIR)

from local_agent.app import agent, generate_fridge, characters
import local_agent.app as agent_app

app = Flask(__name__)

log = []

dict_package = {
    "Response": str,
    "Fridge": dict[str,int],
    "Points": int
}

def update_package(package, model_response):
    package["Response"] = model_response
    package["Fridge"] = agent_app.global_fridge
    package["Points"] = agent_app.global_points
    package["Ended"] = agent_app.global_ended
    return package

def reset_points(package):
    package["Points"] = int
    agent_app.global_points = 0.0
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
    global log
    
    try :
        dict_package = reset_points(dict_package)

        message = request.json["message"]
        
        injected_prompt = f"""[System Information: The fridge currently contains: {dict_package["Fridge"]}]
        Player says: "{message}"
        """

        response = agent.run(injected_prompt)

        if agent_app.global_ended :
             _ = end_convo()

        log.append(['"' + message + '"', '"' + response + '"'])
        dict_package = update_package(dict_package, response)
    except:
        return jsonify("Something didn't work")
    
    return jsonify(dict_package)

@app.route("/start_convo", methods=['GET'])
def start_convo():
    global dict_package
    global log

    agent_app.global_ended = False
    try :
        agent_app.global_ended = False
        character_difficulty = characters[0]["difficulty"]
        generate_fridge(character_difficulty)

        message = f"""[System Information: The fridge currently contains: {agent_app.global_fridge}]
        This is a prompt telling you that you have connected to the player. 
        You can now write a message to them as you need their help reducing waste from your fridge. 
        So start by introducing yourself to them and telling them that you need help making a meal!"""
        
        response = agent.run(message)
        
        log = []
        log.append(['"' + message + '"', '"' + response + '"'])
    except:
        return jsonify("Something didn't work")
    dict_package = update_package(dict_package, response)
    return jsonify(dict_package)

@app.route("/end_convo")
def end_convo():
    global dict_package
    global log

    with open(f"{SCRIPT_DIR}/log/{agent_app.global_model}_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M')}.csv", "a") as f:
        np.savetxt(f, [["Request", "Response"]] + log, fmt="%s", delimiter=",")
    
    log = []
    dict_package = reset_package(dict_package)
    return jsonify()

if __name__ == '__main__' :
    app.run(debug=True)