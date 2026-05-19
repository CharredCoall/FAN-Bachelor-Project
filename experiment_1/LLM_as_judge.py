import os
import pandas as pd
import yaml
import torch
from transformers import pipeline

# --- Configuration ---
MODEL_NAME = "meta-llama/Meta-Llama-3-8B-Instruct"
CSV_PATH = "merged_dataset_full.csv"
CHARACTER_PROMPT_DIR = os.path.join("..", "models", "local_agent", "Character_prompts")

# Llama-3 pipeline
pipe = pipeline(
    "text-generation",
    model=MODEL_NAME,
    model_kwargs={"torch_dtype": torch.bfloat16},
    device_map="auto",
)

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
    """Sends a formatted prompt to Llama-3 to get a 1-3 rating."""
    
    system_prompt = (
        "You are an expert judge evaluating a roleplay AI. "
        "Rate the response 1 (bad), 2 (acceptable), or 3 (good) based on persona consistency and quality. "
        "Output ONLY the number."
    )
    
    user_prompt = (
        "### CHARACTER PERSONA:\n" + str(character_yaml) + "\n\n"
        "### HISTORY:\n" + str(history) + "\n\n"
        "### REQUEST:\n" + str(request) + "\n\n"
        "### RESPONSE TO EVALUATE:\n" + str(response) + "\n\n"
        "### CRITERIA:\n"
        "1: Bad (Out of character, repetitive, or nonsensical)\n"
        "2: Acceptable (Follows persona but is a bit bland)\n"
        "3: Good (Perfectly captures the character's voice)\n\n"
        "Output ONLY a single number (1, 2, or 3)."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    # Generate response
    outputs = pipe(
        messages,
        max_new_tokens=5,
        do_sample=False,
    )
    
    raw_output = outputs[0]["generated_text"][-1]["content"].strip()
    
    # Extract just the digit
    for char in raw_output:
        if char in ["1", "2", "3"]:
            return int(char)
    
    return None

def run_judge():
    if not os.path.exists(CSV_PATH):
        print(f"Error: {CSV_PATH} not found.")
        return

    df = pd.read_csv(CSV_PATH)
    print(f"Starting evaluation of {len(df)} rows")

    char_memory = {}

    for index, row in df.iterrows():
        # Skip if already scored
        if "Score" in df.columns and pd.notnull(row.get("Score")):
            continue

        char_name = row["Character"]
        if char_name not in char_memory:
            char_memory[char_name] = load_character_yaml(char_name)

        # Handle empty history (pandas reads empty CSV cells as float NaN)
        hist = "" if pd.isna(row["History"]) else row["History"]

        score = get_llm_score(
            char_memory[char_name],
            hist,
            row["Request"],
            row["Response"]
        )

        df.at[index, "Score"] = score
        
        # Periodic saving
        if index > 0 and index % 10 == 0:
            df.to_csv(CSV_PATH, index=False)
            print(f"Processed {index}/{len(df)} rows")

    # Final save
    df.to_csv(CSV_PATH, index=False)
    print("Evaluation complete and saved.")

if __name__ == "__main__":
    run_judge()