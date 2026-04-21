import os
import sys
import numpy as np
import datetime
from flask import Flask, request, jsonify

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(SCRIPT_DIR)

from local_agent.app import generate_fridge, characters
import local_agent.app as agent_app

app = Flask(__name__)

def change_character(idx):
    agent_app.change_character(idx)

@app.route("/request_reply", methods=['POST'])
def request_reply():
    package = {}

    try :
        message = request.json["message"]
        steps = request.json["steps"]
        char_idx = request.json["char_idx"]
        model_idx = request.json["model_idx"]
        fridge = request.json["fridge"]
        injected_prompt = f"""[System Information: The fridge currently contains: {fridge}]
        Player says: "{message}"
        """
        
        if char_idx != agent_app.character_index or model_idx != agent_app.model_index:
            change_character(char_idx, model_idx)
        
        if fridge != agent_app.global_fridge:
            agent_app.global_fridge = fridge

        agent_app.agent.memory.steps = steps
        response = agent_app.agent.run(injected_prompt, reset=False)
        steps = agent_app.agent.memory.steps

        if agent_app.global_ended :
             _ = end_convo()

        package["response"] = response
        package["fridge"] = agent_app.global_fridge
        package["points"] = agent_app.global_points
        package["ended"] = agent_app.global_ended
        package["steps"] = steps
    except Exception as e:
        return jsonify({"error": f"Python Exception: {str(e)}"})
    
    return jsonify(package)

@app.route("/start_convo", methods=['GET'])
def start_convo():
    package = {}

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
        steps = agent_app.agent.memory.steps
        
    except Exception as e:
        return jsonify({"error": f"Python Exception: {str(e)}"})
    
    package["response"] = response
    package["fridge"] = agent_app.global_fridge
    package["points"] = agent_app.global_points
    package["ended"] = agent_app.global_ended
    package["steps"] = steps
    package["model_idx"] = agent_app.model_index
    package["char_idx"] = agent_app.character_index
    return jsonify(package)

@app.route("/end_convo")
def end_convo():

    model_idx = request.json["model_idx"]
    char_idx = request.json["char_idx"]
    log = request.json["log"]

    with open(f"{SCRIPT_DIR}/log/{agent_app.global_models[model_idx]['key']}_{characters[char_idx]['name']}_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M')}.csv", "a") as f:
        np.savetxt(f, [["Request", "Response"]] + log, fmt="%s", delimiter=",")

    return jsonify([])

@app.route("/ping")
def ping():
    return jsonify(["pong"])

@app.route("/")
def home():
    return jsonify(["Hello from Azure"])

if __name__ == '__main__' :
    app.run(debug=True)
