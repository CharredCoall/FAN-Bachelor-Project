from smolagents import CodeAgent, HfApiModel, load_tool, tool
import datetime
import requests
import pytz
import yaml
from tools.final_answer import FinalAnswerTool
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn

global_fridge = {
    "apple": 3,
    "banana": 8,
    "cucumber": 2,
    "bread": 3,
    "chicken breast": 4,
    "soy sauce": 3,
    "milk": 2,
    "onion": 7,
    "dragon fruit": 4
}

global_points = 0

@tool
def fetch_fridge() -> dict[str,int]:
    """A tool that retrieves a global variable global_fridge and returns it."""
    # fetching fridge
    global global_fridge
    try:
        return global_fridge
    
    except Exception as e:
        # This catches the crash and lets the agent see the error message instead
        return f"Error fetching fridge: {str(e)}"
    
@tool
def count_fridge(fridge: dict[str,int]) -> int:
    """A tool that retrieves the amount of items in a given fridge by counting the items.
    
    Args:
        fridge: dictionary of items in the format item and the amount: str: int
    """
    try:
        # Sum of of the elements in the fridge and their amounts
        return sum(fridge.values())
        
    except Exception as e:
        # This catches the crash and lets the agent see the error message instead
        return f"Error performing fridge count: {str(e)}"

@tool
def take_from_fridge(fridge: dict[str,int], remove: dict[str, int]) -> dict[str,int]:
    """A tool that can take a given amount of items in a fridge out of the fridge and then return what is left inside the fridge.

    Args:
        fridge: dictionary of items in the format item and the amount: str: int
        remove: dictionary of items that are being taken out of fridge in the format item and the amount: str: int
    """
    global global_fridge
    try:
        # Loop through all items to be removed
        for item, amount in remove.items():
            # if that item is in the fridge remove the amount specified
            if item in fridge:
                fridge[item] -= amount

                # Remove the item entirely if there is none left
                if fridge[item] <= 0:
                    del fridge[item]

        # return the new fridge and set global fridge to the updated fridge
        global_fridge = fridge
        return fridge

    except Exception as e:
        # This catches the crash and lets the agent see the error message instead
        return f"Error removing from fridge: {str(e)}"

@tool
def calculate_points(previous_fridge_amount:int, current_fridge_amount:int) -> int:
    """A tool that takes an amount that has previously been in the fridge and subtracts the current amount in the fridge, returning the difference as points.

    Args:
        previous_fridge_amount: an integer repressenting how many items was in the fridge: int
        current_fridge_amount: an integer repressenting how many items are currently in the fridge: int
    """
    global global_points
    try:
        # Calculate points
        points = previous_fridge_amount-current_fridge_amount
        # Set Global points to points
        global_points = points
        return points
        
    except Exception as e:
        # This catches the crash and lets the agent see the error message instead
        return f"Error removing from fridge: {str(e)}"

@tool
def print_fridge_points() -> tuple[dict[str,int], int]:
    """A tool that prints out global variables as a varification that all other tools are working, and returns these values"""
    global global_fridge
    global global_points
    try:
        print(f"The fridge: {global_fridge}")
        print(f"Points: {global_points}")
        return global_fridge, global_points
    except Exception as e:
        # This catches the crash and lets the agent see the error message instead
        return f"Error printing: {str(e)}"


final_answer = FinalAnswerTool()
tool_list = [final_answer, count_fridge, take_from_fridge, fetch_fridge, calculate_points, print_fridge_points]

# If the agent does not answer, the model is overloaded, please use another model or the following Hugging Face Endpoint that also contains qwen2.5 coder:
# model_id='https://pflgm2locj2t89co.us-east-1.aws.endpoints.huggingface.cloud' 

model = HfApiModel(
max_tokens=2096,
temperature=0.5,
model_id='Qwen/Qwen2.5-Coder-32B-Instruct',# it is possible that this model may be overloaded
custom_role_conversions=None,
)


# Import tool from Hub
image_generation_tool = load_tool("agents-course/text-to-image", trust_remote_code=True)

with open("prompts.yaml", 'r') as stream:
    prompt_templates = yaml.safe_load(stream)
    
agent = CodeAgent(
    model=model,
    tools=tool_list, 
    max_steps=6,
    verbosity_level=1,
    grammar=None,
    planning_interval=None,
    name=None,
    description=None,
    prompt_templates=prompt_templates
)

app = FastAPI()

class ChatRequest(BaseModel):
    prompt: str

# This creates the endpoint (http://127.0.0.1:8000/chat)
@app.post("/chat")
def chat_with_npc(request: ChatRequest):
    print(f"Received prompt from game: {request.prompt}")

    agent_response = agent.run(request.prompt)
    
    return {"response": str(agent_response)}

if __name__ == "__main__":
    print("Starting NPC Agent Server...")
    uvicorn.run(app, host="127.0.0.1", port=8000)