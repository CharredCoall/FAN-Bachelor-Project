import os
import sys
import numpy as np
import datetime
from flask import Flask, request, jsonify, json
from smolagents.memory import TaskStep, ActionStep, MemoryStep, PlanningStep, FinalAnswerStep, SystemPromptStep, Timing, ChatMessage, ToolCall, AgentError, TokenUsage
from github import Github, Auth
import io

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(SCRIPT_DIR)

from local_agent.app import generate_fridge, characters
import local_agent.app as agent_app

app = Flask(__name__)

step_classes = {
    "MemoryStep": MemoryStep,
    "ActionStep": ActionStep,
    "PlanningStep": PlanningStep,
    "TaskStep": TaskStep,
    "SystemPromptStep": SystemPromptStep,
    "FinalAnswerStep": FinalAnswerStep
}    

def steps_to_dict(steps):
    return [{"class": step.__class__.__name__, "state": step.dict()} for step in steps if step.__class__.__name__ in step_classes]

def steps_from_dict(raw):
    steps = []
    
    for item in raw:
        state = item["state"]

        step = MemoryStep.__new__(MemoryStep)

        match item["class"]:
            case "MemoryStep":
                step = MemoryStep.__new__(MemoryStep)
            case "ActionStep":
                step = ActionStep.__new__(ActionStep)
                step.step_number = state["step_number"] if "step_number" in state else 0
                if "timing" in state and state["timing"] != None:
                    timing = Timing(start_time=state["timing"]["start_time"], end_time=state["timing"]["end_time"])
                    step.timing = timing
                if "model_input_messages" in state and state["model_input_messages"] != None:
                    step.model_input_messages = [ChatMessage.from_dict(msg) for msg in state["model_input_messages"]]
                if "tool_calls" in state and state["tool_calls"] != None:
                    step.tool_calls = [ToolCall(name=tool_call["function"]["name"], arguments=tool_call["function"]["arguments"], id= tool_call["id"]) for tool_call in state["tool_calls"]]
                step.error = AgentError(state["error"]["message"]) if "error" in state and state["error"] != None else None
                step.model_output_message = ChatMessage.from_dict(state["model_output_message"]) if "model_output_message" in state and state["model_output_message"] != None else None
                step.model_output = state["model_output"] if "model_output" in state else None
                step.code_action = state["code_action"] if "code_action" in state else None
                step.observations = state["observations"] if "observations" in state else None
                step.observations_images = state["observation_images"] if "observation_images" in state else None
                step.action_output = state["action_output"] if "action_output" in state else None
                step.token_usage = TokenUsage(state["token_usage"]["input_tokens"], state["token_usage"]["output_tokens"]) if "token_usage" in state and state["token_usage"] != None else None
                step.is_final_answer = state["is_final_answer"] if "is_final_answer" in state else False
            case "PlanningStep":
                step = PlanningStep.__new__(PlanningStep)
                if "model_input_messages" in state and state["model_input_messages"] != None:
                    step.model_input_messages = [ChatMessage.from_dict(msg) for msg in state["model_input_messages"]]
                step.model_output_message = ChatMessage.from_dict(state["model_output_message"]) if "model_output_message" in state and state["model_output_message"] != None else None
                step.plan = state["plan"] if "plan" in state else None
                if "timing" in state and state["timing"] != None:
                    timing = Timing(start_time=state["timing"]["start_time"], end_time=state["timing"]["end_time"])
                    step.timing = timing
                step.token_usage = TokenUsage(state["token_usage"]["input_tokens"], state["token_usage"]["output_tokens"]) if "token_usage" in state and state["token_usage"] != None else None
            case "TaskStep":
                step = TaskStep.__new__(TaskStep)
                step.task = state["task"] if "task" in state else None
                step.task_images = state ["task_images"] if "task_images" in state else None
            case "SystemPromptStep":
                step = SystemPromptStep.__new__(SystemPromptStep)
                step.system_prompt = state["system_prompt"] if "system_prompt" in state else None
            case "FinalAnswerStep":
                step = FinalAnswerStep.__new__(FinalAnswerStep) 
                step.output = state["output"] if "output" in state else None
            case _:
                print(f"""Error in step. Unknown Class: {item["class"]}""")

        steps.append(step)
    return steps

@app.route("/request_reply", methods=['POST'])
def request_reply():
    package = {}

    try :
        agent_app.global_ended = False
        message = request.json["message"]
        steps = request.json["steps"]
        char_idx = request.json["char_idx"]
        model_idx = request.json["model_idx"]
        fridge = request.json["fridge"]
        injected_prompt = f"""[System Information: The fridge currently contains: {fridge}]
        Player says: "{message}"
        """
        
        if char_idx != agent_app.character_index or model_idx != agent_app.model_index:
            agent_app.change_character(char_idx, model_idx)
        
        if fridge != agent_app.global_fridge:
            agent_app.global_fridge = fridge

        agent_app.agent.memory.steps = steps_from_dict(steps)
        response = agent_app.agent.run(injected_prompt, reset=False)
        steps = steps_to_dict(agent_app.agent.memory.steps)

        if agent_app.global_ended :
             request.json["log"].append(['"' + message.replace('"', "'") + '"', '"' + response.replace('"', "'") + '"'])
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
        steps = steps_to_dict(agent_app.agent.memory.steps)
        
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

    #Initializing github and getting repo
    repo_id = 1149716740
    g = Github(auth=Auth.Token(os.environ["GITHUB_TOKEN"]))
    repo = g.get_repo(repo_id)

    s = io.BytesIO()
    f = f"models/log/{agent_app.global_models[model_idx]['key']}_{characters[char_idx]['name']}_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M')}.csv"
    np.savetxt(s, [["Request", "Response"]] + log, fmt="%s", delimiter=",")
    repo.create_file(f, f"Added log for {characters[char_idx]['name']} produced by model {agent_app.global_models[model_idx]['key']}",  s.getvalue())

    return jsonify()

@app.route("/ping")
def ping():
    return jsonify(["pong"])

@app.route("/")
def home():
    return jsonify(["Hello from Azure"])

if __name__ == '__main__' :
    
    app.run(debug=True)
