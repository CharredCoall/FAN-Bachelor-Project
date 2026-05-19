import os
import glob
import csv

def merge_logs():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_dir = os.path.join(script_dir, "..", "models", "log")
    input_dir = os.path.abspath(input_dir)

    search_pattern = os.path.join(input_dir, "*.csv")
    csv_files = glob.glob(search_pattern)

    if not csv_files:
        print(f"No CSV files found in directory: {input_dir}")
        return
    
    print(f"Found {len(csv_files)} files. Merging into a single dataset...")

    # Output to a single file
    output_file = os.path.join(script_dir, "merged_dataset_full.csv")

    with open(output_file, mode='w', newline='', encoding='utf-8') as outfile:
        writer = csv.writer(outfile)
        # Added Game_ID to the CSV headers
        writer.writerow(["Game_ID", "Request", "History", "Response", "Model_Key", "Character", "Score"])

        for file_path in csv_files:
            filename = os.path.basename(file_path)
            name_without_ext = os.path.splitext(filename)[0]
            parts = name_without_ext.split('_')
            
            # Ensure the filename extract Key, Character, and Game ID
            if len(parts) >= 3:
                model_key = parts[0]
                character = parts[1]
                game_id = parts[2]
            else:
                print(f"Skipping {filename}: Filename doesn't match expected format.")
                continue

            with open(file_path, mode='r', encoding='Latin-1') as infile:
                reader = csv.reader(infile)
                next(reader, None)  # Skip the header row

                conversation_history = []
                
                for row in reader:
                    if len(row) >= 2:
                        request = row[0]
                        response = row[1]
                        current_history_str = "\n\n".join(conversation_history)
                        
                        writer.writerow([game_id, request, current_history_str, response, model_key, character, None])

                        # Append to history for the next turn
                        turn_string = f"{request}\n{character}: {response}"
                        conversation_history.append(turn_string)
    
    print(f"All merging completed successfully! Saved to: {os.path.basename(output_file)}")

if __name__ == "__main__":
    merge_logs()