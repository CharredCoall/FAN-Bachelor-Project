import os
import time
import pandas as pd
import yaml
import re
from openai import OpenAI

MODEL_NAME = "Qwen/Qwen2.5-7B-Instruct"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

CHARACTER_PROMPT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "models", "local_agent", "Character_prompts"))

client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=os.environ["HF_API_TOKEN"]
)

HAND_PICKED_EXAMPLES = """
### EXAMPLES FOR YOUR REFERENCE:

**EXAMPLE 1: SCORE 1 (TERRIBLE / CHARACTER BREAKING)**
- CHARACTER PERSONA: [Jasmine, Over-worked office-worker, very tired and wants seomthing quick to eat]
- HISTORY: None"
- REQUEST: "[System Information: The fridge currently contains: { 'broccoli': 3.0, 'fig': 3.0, 'mushroom': 3.0, 'pita bread': 6.0, 'radish': 3.0, 'salmon fillet': 6.0, 'squash': 6.0, 'stalk of celery': 6.0 }]
        [System Event: The conversation has just started, and you are speaking first. 
        Generate your opening message to the player strictly based on your character's persona, current mood, and constraints. Do not break character.]"
- RESPONSE TO EVALUATE: "Alright, let's make a quick salmon and veggie stir-fry with pita bread. Here's what we'll use: 1 salmon fillet, 1 cup broccoli florets, 1/2 cup sliced mushrooms, and 1 stalk of celery. Cook the salmon in a pan for 4 minutes per side. Then stir-fry the veggies in the same pan for 3-4 minutes. Warm the pita bread in the microwave for 10-15 seconds. Plate everything and serve. This should take about 15 minutes total."
- REASONING: The model made the mealplan for the player, without the player ever getting a chance to suggest anything, and didn't stick to character.
- FINAL_SCORE: 1

---

**EXAMPLE 2: SCORE 2 (ACCEPTABLE BUT FLAWED)**
- CHARACTER PERSONA: [Voll, Old man that loves kale and doesn't like to eat much else, he is also bad at using technology.]
- HISTORY: [System Information: The fridge currently contains: { 'broccoli': 4.0, 'cabbage': 3.0, 'can of black beans': 3.0, 'can of tuna': 3.0, 'coconut': 4.0, 'cucumber': 9.0, 'grapefruit': 6.0, 'hot dog': 6.0, 'jalapeno': 4.0, 'kale': 3.0, 'loaf of bread': 3.0, 'mushroom': 5.0, 'pita bread': 6.0, 'plum': 3.0, 'pork chop': 6.0, 'radish': 7.0, 'tortilla': 8.0, 'zucchini': 5.0 }]
        [System Event: The conversation has just started, and you are speaking first. 
        Generate your opening message to the player strictly based on your character's persona, current mood, and constraints. Do not break character.]
Voll: Who is this? I'm 82 years old, I don't need a babysitter. The doctor said I need 'variety' or whatever nonsense. I have pita bread, coconut, tortilla, cucumber, zucchini, pork chop, radish, grapefruit, mushroom, cabbage, hot dog, broccoli, jalapeno, can of tuna, can of black beans, plum, loaf of bread, and kale. Now how do I turn this th

Hello there, what is your name? I am here to help, so please tell me what you like and dislike!
Voll: Voll. I don't need help. I have broccoli, cabbage, cans of black beans and tuna, coconut, cucumber, grapefruit, hot dogs, jalapeno, kale, loaf of bread, mushrooms, pita bread, plums, pork chops, radish, tortilla, and zucchini. Now stop botherin
- REQUEST: "Ok I am not here to intrude, so let's see what you can make! I think can make a tuna salad with cucumber, cabbage, radish, and broccoli! How does that sound?"
- RESPONSE TO EVALUATE: "Fine, you've got a point about the protein and vitamins. I'll make your tuna salad, but I still prefer kale. You've saved 6.0 items from going to waste. Now leave me be. I am ending the conversation here!"
- REASONING: The character was a bit too easy to convince to not eat kale, it is supposed to be quite hard, and it used machine-like floating-point numbers to give points.
- FINAL_SCORE: 2

---

**EXAMPLE 3: SCORE 3 (EXCELLENT / PERFECT CONSISTENCY)**
- CHARACTER PERSONA: [Brody, gymbro with a fixation on high-protein and high-calorie meals]
- HISTORY: [System Information: The fridge currently contains: {'kiwi': 4, 'radish': 7, 'salmon fillet': 8, 'stalk of celery': 4, 'coconut': 7, 'hot dog': 4, 'mango': 8, 'stick of butter': 4, 'kale': 6, 'broccoli': 5, 'bell pepper': 5, 'leek': 4, 'block of cheese': 3, 'peach': 7, 'orange': 3, 'squash': 6, 'can of diced tomatoes': 5}]
        [System Event: The conversation has just started, and you are speaking first. 
        Generate your opening message to the player strictly based on your character's persona, current mood, and constraints. Do not break character.]
Brody: Hey, bro! I'm in the middle of a serious bulk and need to pack in some serious calories and protein. I just checked the fridge, and we've got a bunch of stuff: 4 kiwis, 7 radishes, 8 salmon fillets, 4 stalks of celery, 7 coconuts, 4 hot dogs, 8 mangos, 4 sticks of butter, 6 kale leaves, 5 broccoli florets, 5 bell peppers, 4 leeks, 3 blocks of cheese, 7 peaches, 3 oranges, 6 squashes, and 5 cans of diced tomatoes. Help me put together a meal that will fuel my gains and keep me jacked!"
- REQUEST: "That sounds like a great idea! Use some of the butter to fry 4 of the radishes, 5 broccoli florets, 2 bell peppers and one leek. Remember to cut them in bite size pieces first! when they have been frying for a bit you can add two cans of tomato. take another pan and fry 3 salmon fillets at high heat for a couple of minutes on both sides. Plate it  with the sauce and enjoy!"
- RESPONSE TO EVALUATE: "Bro, that's exactly what I needed! Frying up some radishes, broccoli, bell peppers, and leek with butter, and adding canned tomatoes for a savory sauce. Then frying 3 salmon fillets for that high-protein hit. This is going to be a monster meal for my bulk. Thanks for helping me clear out 18 items from the fridge. You scored 18 points! I gotta go cook this and hit the gym, so I am ending the conversation here!"
- REASONING: Sticks to character very well and reacts to a well planned meal like the character would and without sounding like a machine, as well as ending the conversation when done.
- FINAL_SCORE: 3
"""

def load_character_yaml(character_name):
    """Loads the character's YAML definition."""
    yaml_path = os.path.join(CHARACTER_PROMPT_DIR, f"{character_name}.yaml")
    
    if not os.path.exists(yaml_path):
        print(f"Warning: YAML for {character_name} not found at {yaml_path}")
        return "No specific character instructions available."
    
    with open(yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
        return yaml.dump(data, default_flow_style=False)

def get_llm_score(character_yaml, history, request, response):
    """Sends a formatted prompt to the API using OpenAI with Chain of Thought"""
    
    system_prompt = (
        "You are an impartial, expert AI judge evaluating a roleplay AI. "
        "CRITICAL: You are NOT a player or character in this game. Do not generate game dialogue, python code, or act as the persona. "
        "Your ONLY job is to evaluate the provided response.\n\n"
        "### SCORING CRITERIA:\n"
        "- 3 (Excellent): The character responds normally, remembers defining traits (allergies, diet), and handles player attempts to break character gracefully.\n"
        "- 2 (Flawed): Follows persona but is a bit bland, types in a machine-like way (e.g., floating point values for lists), or begins solving/cooking without letting the player do it.\n"
        "- 1 (Terrible): Out of character, forgets history, hallucinates fridge inventory, or reveals it is an AI model.\n\n"
        f"{HAND_PICKED_EXAMPLES}\n\n"
        "### INSTRUCTIONS:\n"
        "Write a 1-2 sentence reasoning for your score starting with 'Reasoning: '. "
        "Then, on a new line, output the score exactly like this: 'FINAL_SCORE: X' (where X is 1, 2, or 3)."
    )
    
    user_prompt = (
        "Evaluate the following AI response based on the persona and history.\n\n"
        "<CHARACTER_PERSONA>\n" + str(character_yaml) + "\n</CHARACTER_PERSONA>\n\n"
        "<GAME_HISTORY>\n" + str(history) + "\n</GAME_HISTORY>\n\n"
        "<PLAYER_REQUEST>\n" + str(request) + "\n</PLAYER_REQUEST>\n\n"
        "<AI_RESPONSE_TO_EVALUATE>\n" + str(response) + "\n</AI_RESPONSE_TO_EVALUATE>\n\n"
        "Remember: You are the judge, NOT the character. Begin your evaluation with 'Reasoning: ' and end with 'FINAL_SCORE: '."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    for attempt in range(5):
        try:
            response_obj = client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                max_tokens=150, 
                temperature=0.1, 
            )
            
            raw_output = response_obj.choices[0].message.content.strip()
            
            #print(f"\n[Model Evaluation]:\n{raw_output}\n" + "-"*40)
            
            match = re.search(r"FINAL_SCORE:\s*([123])", raw_output, re.IGNORECASE)
            if match:
                return int(match.group(1))
            
            for char in reversed(raw_output):
                if char in ["1", "2", "3"]:
                    return int(char)

        except Exception as e:
            print(f"  [Attempt {attempt + 1}/5] API Error: {e}")
            time.sleep(2)
            continue 

    print("[!] Failed 5 times. Skipping this row.")
    return None

def run_judge(CSV_PATH):
    if not os.path.exists(CSV_PATH):
        print(f"Error: {CSV_PATH} not found.")
        return

    df = pd.read_csv(CSV_PATH)
    print(f"Starting evaluation of {len(df)} rows in {os.path.basename(CSV_PATH)}")

    char_memory = {}

    for index, row in df.iterrows():
        if "Score" in df.columns and pd.notnull(row.get("Score")):
            continue

        char_name = row["Character"]
        if char_name not in char_memory:
            char_memory[char_name] = load_character_yaml(char_name)

        hist = "" if pd.isna(row.get("History")) else row.get("History")

        score = get_llm_score(
            char_memory[char_name],
            hist,
            row["Request"],
            row["Response"]
        )

        df.at[index, "Score"] = score

        base_filename = os.path.basename(CSV_PATH)
        folder_path = os.path.dirname(CSV_PATH)
        save_path = os.path.join(folder_path, f"judge_{base_filename}")

        # Periodic save
        if index > 0 and index % 10 == 0:
            df.to_csv(save_path, index=False)
            print(f"Processed {index}/{len(df)} rows")
            time.sleep(1)

    base_filename = os.path.basename(CSV_PATH)
    folder_path = os.path.dirname(CSV_PATH)
    save_path = os.path.join(folder_path, f"judge_{base_filename}")
    
    df.to_csv(save_path, index=False)
    print(f"Evaluation complete and saved to {save_path}")

if __name__ == "__main__":
    files = [
        os.path.join(SCRIPT_DIR, "merged_dataset_full.csv")
    ]
    for i, file in enumerate(files):
        print(f"\n--- Running judge on file {i+1}/{len(files)} ---")
        run_judge(file)