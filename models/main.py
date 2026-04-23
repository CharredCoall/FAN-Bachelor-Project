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

#Initialize Flask app
app = Flask(__name__)

#Dictionary over available step classes
step_classes = {
    "MemoryStep": MemoryStep,
    "ActionStep": ActionStep,
    "PlanningStep": PlanningStep,
    "TaskStep": TaskStep,
    "SystemPromptStep": SystemPromptStep,
    "FinalAnswerStep": FinalAnswerStep
}    

def steps_to_dict(steps):
    """
    This function returns a list of the supported steps as dictionaries of the class and the output dictionary of the step.
    Args: 
        steps: The steps as output from agent : list[Any]

    Returns:
        list of supported steps : List[Dict[str, Dict[Any, Any]]]
    """
    return [{"class": step.__class__.__name__, "state": step.dict()} for step in steps if step.__class__.__name__ in step_classes]

def steps_from_dict(raw):
    """
    This function reads a list of dictionary steps and converts each step to its original class
    Args:
        raw: List with dictionaries of steps: List[Dict[str, Dict[Any, Any]]]

    Returns:
        list of Steps: List[Any]
    """
    #Initializes list of steps
    steps = []
    
    #Iterates through all steps
    for item in raw:
        state = item["state"]

        #Initialize empty step
        step = MemoryStep.__new__(MemoryStep)

        #Match class and set all necessary variables for each step
        match item["class"]:
            case "MemoryStep":
                step = MemoryStep.__new__(MemoryStep)
            case "ActionStep":
                step = ActionStep.__new__(ActionStep)
                step.step_number = state["step_number"] if "step_number" in state else 0                
                step.timing  = Timing(start_time=state["timing"]["start_time"], end_time=state["timing"]["end_time"]) if "timing" in state and state["timing"] != None else None            
                step.model_input_messages = [ChatMessage.from_dict(msg) for msg in state["model_input_messages"]] if "model_input_messages" in state and state["model_input_messages"] != None else None                
                step.tool_calls = [ToolCall(name=tool_call["function"]["name"], arguments=tool_call["function"]["arguments"], id= tool_call["id"]) for tool_call in state["tool_calls"]] if "tool_calls" in state and state["tool_calls"] != None else None
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
                step.model_input_messages = [ChatMessage.from_dict(msg) for msg in state["model_input_messages"]] if "model_input_messages" in state and state["model_input_messages"] != None else None  
                step.model_output_message = ChatMessage.from_dict(state["model_output_message"]) if "model_output_message" in state and state["model_output_message"] != None else None
                step.plan = state["plan"] if "plan" in state else None
                step.timing  = Timing(start_time=state["timing"]["start_time"], end_time=state["timing"]["end_time"]) if "timing" in state and state["timing"] != None else None  
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
                #Ignores but prints class error
                print(f"""Error in step. Unknown Class: {item["class"]}""")

        #Appends current step to list of steps
        steps.append(step)
    
    #Returns
    return steps

@app.route("/request_reply", methods=['POST'])
def request_reply():
    """
    This function handles the HTTP requests for requesting a reply from a model.
    It requires a message, details about the current model, the fridge and the history of the conversation.
    The function replies to the incoming message using the loaded model and sends the response to the user.
    In the end it returns a json string containing a dictionary with the response, the updated fridge, the points given during this response, 
    a boolean of whether the conversation was ended during this response, and the updated steps of the model.

    Returns:
        flask response containing a json string: Response
    """
    #Initialize package as empty dictionary
    package = {}

    #Try Catch to avoid server shutting down
    try :
        #Load all necessary variables
        agent_app.global_ended = False
        agent_app.global_points = 0
        message = request.json["message"]
        steps = request.json["steps"]
        char_idx = request.json["char_idx"]
        model_idx = request.json["model_idx"]
        fridge = request.json["fridge"]
        injected_prompt = f"""[System Information: The fridge currently contains: {fridge}]
        Player says: "{message}"
        """
        #if the model or character doesn't match the requested model and character, we reload the character
        if char_idx != agent_app.character_index or model_idx != agent_app.model_index:
            agent_app.change_character(char_idx, model_idx)
        
        #Ensure fridge is set to requested fridge
        if fridge != agent_app.global_fridge:
            agent_app.global_fridge = fridge

        #Get response and update steps
        agent_app.agent.memory.steps = steps_from_dict(steps) #Load steps from request
        response = agent_app.agent.run(injected_prompt, reset=False) #Get response
        steps = steps_to_dict(agent_app.agent.memory.steps) #Store updated steps

        #If model has ended conversation, End conversation and write log
        if agent_app.global_ended :
             request.json["log"].append(['"' + message.replace('"', "'") + '"', '"' + response.replace('"', "'") + '"'])
             _ = end_convo()

        #Set returning variables
        package["response"] = response
        package["fridge"] = agent_app.global_fridge
        package["points"] = agent_app.global_points
        package["ended"] = agent_app.global_ended
        package["steps"] = steps

    except Exception as e:
        #Send error to client
        return jsonify({"error": f"Python Exception: {str(e)}"})
    
    return jsonify(package)

@app.route("/start_convo", methods=['GET'])
def start_convo():
    """
    This function handles the HTTP request for starting a conversation.
    It requires a character index to tell the server what model to load.
    The function gets a startup message from the loaded agent and sends it to the user.
    In the end it returns a json string containing a dictionary with the response, the fridge, the points given during this response, 
    a boolean of whether the conversation was ended during this response, and the steps of the model. 
    along with the model and character indices for the model

    Returns:
        flask response containing a json string: Response

    """
    #Initialize package
    package = {}

    #Try Catch to avoid server shutting down
    try :
        #Load all necessary variables
        agent_app.global_ended = False
        agent_app.global_points = 0
        char_idx = request.json["char_idx"]

        #If the character id is set, load the selected character with a random model
        if char_idx != None:
            agent_app.change_character(char_idx)

        #Generate fridge using the current characters difficulty
        character_difficulty = characters[agent_app.character_index]["difficulty"]
        generate_fridge(character_difficulty)

        #Set Starting prompt
        message = f"""[System Information: The fridge currently contains: {agent_app.global_fridge}]
        [System Event: The conversation has just started, and you are speaking first. 
        Generate your opening message to the player strictly based on your character's persona, current mood, and constraints. Do not break character.]"""
                
        #Get response and update steps
        response = agent_app.agent.run(message, reset=False) #Get response
        steps = steps_to_dict(agent_app.agent.memory.steps) #Store updated steps
        
    except Exception as e:
        #Send error to client
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
    """
    This function handles the HTTP request for ending a conversation.
    It requires a character index and model index used to describe the resulting log file.
    The function connects to the project Github and uploads the log file
    In the end it returns an empty json string

    Returns:
        flask response containing a json string: Response

    """
    #Try Catch to avoid server shutting down
    try:
        #Loads necessary variables
        model_idx = request.json["model_idx"]
        char_idx = request.json["char_idx"]
        log = request.json["log"]

        #Initializing github and getting repo
        repo_id = 1149716740
        g = Github(auth=Auth.Token(os.environ["GITHUB_TOKEN"]))
        repo = g.get_repo(repo_id)

        #Creates and uploads log file
        s = io.BytesIO() #Create empty stream
        f = f"models/log/{agent_app.global_models[model_idx]['key']}_{characters[char_idx]['name']}_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M')}.csv" #Set file path
        np.savetxt(s, [["Request", "Response"]] + log, fmt="%s", delimiter=",") #Write file to stream using numpy
        repo.create_file(f, f"Added log for {characters[char_idx]['name']} produced by model {agent_app.global_models[model_idx]['key']}",  s.getvalue()) #Upload file to github

    except Exception as e:
        #Send error to client
        return jsonify({"error": f"Python Exception: {str(e)}"})

    return jsonify()

@app.route("/ping")
def ping():
    """ 
    This function is used to check the health of the server in Azure
    
    Returns:
        flask response containing a json string with the string "pong": Response
    """
    return jsonify(["pong"])

@app.route("/")
def home():
    """
    Test Function
    """
    return jsonify(["Hello from Azure"])

#Running webserver when directly running file
if __name__ == '__main__' :
    app.run(debug=True)
