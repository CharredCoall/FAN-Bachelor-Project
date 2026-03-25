from smolagents import CodeAgent, InferenceClientModel, load_tool, tool
import yaml
import os
import sys
import random

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(SCRIPT_DIR)

from tools.final_answer import FinalAnswerTool

characters = [
    {
        "name": "Jim",
        "prompt_file": "Jim.yaml",
        "difficulty": 1
    }
]

global_model = "Qwen2.5-Coder-32B-Instruct"

global_fridge = {}

global_points = 0

global_ended = True

POSSIBLE_INGREDIENTS = [
    "apple", "banana", "cucumber", "carrot", "chicken breast", 
    "onion", "steak", "potato", "salmon fillet", "egg", 
    "tomato", "bell pepper", "lemon", "mushroom", "pork chop", 
    "shrimp", "avocado", "zucchini", "sausage", "sweet potato", 
    "corn", "garlic clove", "loaf of bread", "block of tofu", 
    "slice of bacon", "can of diced tomatoes", "can of black beans", "can of tuna", 
    "tortilla", "pita bread", "hot dog", "lime", 
    "orange", "peach", "plum", "kiwi", "mango", "jalapeno", 
    "leek", "eggplant", "lettuce", "cabbage", "broccoli", "cauliflower", 
    "stalk of celery", "radish", "turnip", "beet", "artichoke", "squash", 
    "pumpkin", "shallot", "pickle", "stick of butter", "block of cheese", 
    "pear", "grapefruit", "pineapple", "coconut", "fig", "papaya", "pomegranate",
]

def generate_fridge(difficulty:int) -> dict[str,int]:
    global global_fridge

    # Difficulty setting for the fridge:
    # 1 easy - 5 hard
    if difficulty == 1:
        unique_items_range = (4, 7)
        item_amount_range = (1, 3)
    elif difficulty == 2:
        unique_items_range = (8, 12)
        item_amount_range = (2, 5)
    elif difficulty == 3:
        unique_items_range = (13, 18)
        item_amount_range = (3, 8)
    elif difficulty == 4:
        unique_items_range = (19, 24)
        item_amount_range = (4, 10)
    elif difficulty >= 5:
        unique_items_range = (25, 30)
        item_amount_range = (5, 12)
    else:
        unique_items_range = (4, 7)
        item_amount_range = (1, 3)
    
    # unique items
    num_unique_items = random.randint(*unique_items_range)

    # Safety check:
    num_unique_items = min(num_unique_items, len(POSSIBLE_INGREDIENTS))

    selected_items = random.sample(POSSIBLE_INGREDIENTS, num_unique_items)

    new_fridge = {}
    for item in selected_items:
        new_fridge[item] = random.randint(*item_amount_range)
    
    global_fridge.clear()
    global_fridge.update(new_fridge)

    return global_fridge
    
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
def end_conversation() -> str:
    """This tool allows the model to end the conversation early, if the player makes the character too annoyed or mad. 
    Another usecase is if the character believes the conversation is over because they have received an appropriete dish. 
    The function returns a string to be used in the `final_answer` tool.
    """
    # Function to end the conversation
    global global_ended
    global_ended = True
    return "I am ending the conversation here!"

final_answer = FinalAnswerTool()
tool_list = [final_answer, count_fridge, take_from_fridge, calculate_points, end_conversation]

# If the agent does not answer, the model is overloaded, please use another model or the following Hugging Face Endpoint that also contains qwen2.5 coder:
# model_id='https://pflgm2locj2t89co.us-east-1.aws.endpoints.huggingface.cloud' 

model = InferenceClientModel(
max_tokens=2096,
temperature=0.5,
model_id=f'Qwen/{global_model}',
custom_role_conversions=None,
api_key=os.environ["HF_API_TOKEN"]
)

with open(SCRIPT_DIR + "\\" + "character2.yaml", 'r') as stream:
    prompt_templates = yaml.safe_load(stream)
    
agent = CodeAgent(
    model=model,
    tools=tool_list, 
    max_steps=4,
    verbosity_level=1,
    planning_interval=None,
    name=None,
    description=None,
    prompt_templates=prompt_templates
)


def chat_with_npc():

    print("Chat ready\n type to start conversation:")
    
    while True:
        request = input()

        if request == "q":
            break
        
        agent.run(request)

    print("Conversation ended")
    

if __name__ == "__main__":
    chat_with_npc()