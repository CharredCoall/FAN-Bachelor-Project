import os
import sys
import numpy as np
import datetime
import json
from flask import Flask, request, jsonify

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(SCRIPT_DIR)

from local_agent.app import generate_fridge, characters
import local_agent.app as agent_app

app = Flask(__name__)

log = []

dict_package = {
    "Response": "",
    "Fridge": {"":0},
    "Points": 0,
    "Ended": True
}

def update_package(package, model_response):
    package["Response"] = model_response
    package["Fridge"] = agent_app.global_fridge
    package["Points"] = agent_app.global_points
    package["Ended"] = agent_app.global_ended
    return package

def reset_points(package):
    agent_app.global_points = 0
    package["Points"] = agent_app.global_points
    return package

def reset_package(package):
    package["Response"] = ""
    package["Fridge"] = {"":0}
    agent_app.global_points = 0
    package["Points"] = agent_app.global_points
    return package

def change_character(idx):
    agent_app.change_character(idx)

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

        response = agent_app.agent.run(injected_prompt, reset=False)

        if agent_app.global_ended :
             _ = end_convo()

        log.append(['"' + message + '"', '"' + response + '"'])
        dict_package = update_package(dict_package, response)
    except:
        return json.dumps("Something didn't work")
    
    return json.dumps(dict_package)

@app.route("/start_convo", methods=['GET'])
def start_convo():
    global dict_package
    global log

    agent_app.global_ended = False

    char_idx = request.json["char_idx"]

    if char_idx != None:
        agent_app.change_character(char_idx)
    
    try :
        agent_app.global_ended = False
        character_difficulty = characters[agent_app.character_index]["difficulty"]
        generate_fridge(character_difficulty)

        message = f"""[System Information: The fridge currently contains: {agent_app.global_fridge}]
        [System Event: The conversation has just started, and you are speaking first. 
        Generate your opening message to the player strictly based on your character's persona, current mood, and constraints. Do not break character.]"""
        
        response = agent_app.agent.run(message, reset=True)
        
        log = []
        log.append(['"' + message + '"', '"' + response + '"'])
    except:
        return json.dumps("Something didn't work")
    dict_package = update_package(dict_package, response)
    return json.dumps(dict_package)

@app.route("/end_convo")
def end_convo():
    global dict_package
    global log

    with open(f"{SCRIPT_DIR}/log/{agent_app.global_models[agent_app.model_index]['key']}_{characters[agent_app.character_index]['name']}_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M')}.csv", "a") as f:
        np.savetxt(f, [["Request", "Response"]] + log, fmt="%s", delimiter=",")
    
    log = []
    dict_package = reset_package(dict_package)

if __name__ == '__main__' :
    app.run(debug=True)


