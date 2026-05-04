import pandas as pd
import torch
from datasets import Dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainingArguments
)
from peft import LoraConfig, get_peft_model
from trl import SFTTrainer

MODEL_NAME = "meta-llama/Meta-Llama-3-8B-Instruct" 
DATASET_PATH = "merged_dataset.csv"
OUTPUT_DIR = "./judge_model_checkpoints"

def format_instruction(row):
    """
    Format csv row into a prompt for the model to learn from
    """
    system_prompt = (
        "You are an impartial and expert judge. Evaluate the 'Response' to the 'Request' "
        f"based on how well it portrays the character '{row['Character']}'. "
        "Provide only a single integer score at the end."
    )
    
    user_prompt = f"Request: {row['Request']}\nResponse: {row['Response']}\n\nScore:"
    
    # The expected score
    expected_output = str(row['Score'])
    
    # Combine into a single string for the model to learn from
    return f"<|system|>\n{system_prompt}</s>\n<|user|>\n{user_prompt}</s>\n<|assistant|>\n{expected_output}</s>"

def main():
    print("Loading and preparing data")
    # Load annotated csv
    df = pd.read_csv(DATASET_PATH)
    
    # Filter out any rows not annotated
    df = df.dropna(subset=['Score'])
    
    # Create the training text
    df['text'] = df.apply(format_instruction, axis=1)
    
    # Convert pandas dataframe to Hugging Face Dataset
    dataset = Dataset.from_pandas(df[['text']])
    
    # Split into training and validation
    dataset = dataset.train_test_split(test_size=0.1)
    train_data = dataset["train"]
    val_data = dataset["test"]

    print(f"Training on {len(train_data)} examples, validating on {len(val_data)} examples.")

    # Allows running large models on consumer GPUs
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16
    )

    print("Loading Model and Tokenizer")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    tokenizer.pad_token = tokenizer.eos_token # Essential for training

    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        quantization_config=bnb_config,
        device_map="auto"
    )

    # Setup LoRA to only train a small percentage of the model weights which saves memory
    peft_config = LoraConfig(
        r=16, 
        lora_alpha=32, 
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM"
    )

    # Training Arguments
    training_args = TrainingArguments(
        output_dir=OUTPUT_DIR,
        per_device_train_batch_size=4, # Reduce if we run out of memory
        gradient_accumulation_steps=4, # Increase if we reduce batch size
        learning_rate=2e-4,
        logging_steps=10,
        num_train_epochs=3.0,
        evaluation_strategy="steps",
        eval_steps=50,
        save_strategy="steps",
        save_steps=50,
        fp16=False,
        bf16=True, # Only use bf16 if your GPU supports it, I haven't tested yet
        optim="paged_adamw_8bit"
    )

    # Initialize Trainer
    trainer = SFTTrainer(
        model=model,
        train_dataset=train_data,
        eval_dataset=val_data,
        peft_config=peft_config,
        dataset_text_field="text",
        max_seq_length=1024, # Reduce if our inputs are short to save memory, haven't tested yet
        tokenizer=tokenizer,
        args=training_args,
    )

    print("Starting Training")
    trainer.train()

    print(f"Saving final model to {OUTPUT_DIR}/final_model")
    trainer.model.save_pretrained(f"{OUTPUT_DIR}/final_model")
    tokenizer.save_pretrained(f"{OUTPUT_DIR}/final_model")

if __name__ == "__main__":
    main()