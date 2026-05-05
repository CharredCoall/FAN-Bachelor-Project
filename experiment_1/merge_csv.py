import os
import glob
import csv
from collections import defaultdict

def merge_logs():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_dir = os.path.join(script_dir, "..", "models", "log")
    input_dir = os.path.abspath(input_dir)

    search_pattern = os.path.join(input_dir, "*.csv")
    csv_files = glob.glob(search_pattern)

    if not csv_files:
        print(f"No CSV files found in directory: {input_dir}")
        return
    
    print(f"Found {len(csv_files)} files. Organizing for even distribution...")

    grouped_files = defaultdict(lambda: defaultdict(list))

    for file_path in csv_files:
        filename = os.path.basename(file_path)
        name_without_ext = os.path.splitext(filename)[0]
        parts = name_without_ext.split('_')
        
        if len(parts) >= 2:
            model_key = parts[0]
            character = parts[1]
            grouped_files[character][model_key].append((file_path, model_key, character))
        else:
            print(f"Skipping {filename}: Filename doesn't match expected format.")
        
    if not grouped_files:
        print("No valid files to process after checking names.")
        return
    
    char_queues = {}
    for char, models_dict in grouped_files.items():
        queue = []
        model_keys = list(models_dict.keys())

        max_model_files = max(len(lst) for lst in models_dict.values()) if models_dict else 0

        for i in range(max_model_files):
            for m_key in model_keys:
                if i < len(models_dict[m_key]):
                    queue.append(models_dict[m_key][i])

        char_queues[char] = queue
    
    ordered_files = []
    char_keys = list(char_queues.keys())
    max_char_files = max(len(q) for q in char_queues.values()) if char_queues else 0

    for i in range(max_char_files):
        for c_key in char_keys:
            if i < len(char_queues[c_key]):
                ordered_files.append(char_queues[c_key][i])

    chunk_size = 25
    chunks = [ordered_files[i:i + chunk_size] for i in range(0, len(ordered_files), chunk_size)]

    print(f"Divided into {len(chunks)} chunks.")

    for chunk_idx, chunk_files in enumerate(chunks, start=1):
        output_file = os.path.join(script_dir, f"merged_dataset_part{chunk_idx}.csv")
        
        models_in_chunk = defaultdict(int)
        chars_in_chunk = defaultdict(int)
        for _, m_key, char in chunk_files:
            models_in_chunk[m_key] += 1
            chars_in_chunk[char] += 1
        
        print(f"Processing part {chunk_idx} ({len(chunk_files)} files) -> {os.path.basename(output_file)}")
        print(f"  Distribution - Models: {dict(models_in_chunk)} | Characters: {dict(chars_in_chunk)}")

        with open(output_file, mode='w', newline='', encoding='utf-8') as outfile:
            writer = csv.writer(outfile)
            writer.writerow(["Request", "History", "Response", "Model_Key", "Character", "Score"])

            for file_path, model_key, character in chunk_files:
                with open(file_path, mode='r', encoding='cp1252') as infile:
                    reader = csv.reader(infile)
                    next(reader, None)

                    conversation_history = []
                    
                    for row in reader:
                        if len(row) >= 2:
                            request = row[0]
                            response = row[1]
                            current_history_str = "\n\n".join(conversation_history)
                            writer.writerow([request, current_history_str, response, model_key, character, None])

                            turn_string = f"Player: {request}\n{character}: {response}"
                            conversation_history.append(turn_string)
    
    print("All merging completed successfully!")

if __name__ == "__main__":
    merge_logs()