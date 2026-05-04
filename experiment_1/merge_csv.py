import os
import glob
import csv

def merge_logs():
    # relative path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_dir = os.path.join(script_dir, "..", "models", "log")
    input_dir = os.path.abspath(input_dir)
    output_file = os.path.join(script_dir, "merged_dataset.csv")

    # Search for all CSV files in the logs directory
    search_pattern = os.path.join(input_dir, "*.csv")
    csv_files = glob.glob(search_pattern)

    if not csv_files:
        print(f"No CSV files found in directory: {input_dir}")
        return

    print(f"Found {len(csv_files)} files.")

    # Open output file and setup csv writer
    with open(output_file, mode='w', newline='', encoding='utf-8') as outfile:
        writer = csv.writer(outfile)
        
        # header
        writer.writerow(["Request", "History", "Response", "Model_Key", "Character", "Score"])

        # Iterate through every file
        for file_path in csv_files:
            filename = os.path.basename(file_path)
            
            # remove .csv
            name_without_ext = os.path.splitext(filename)[0]
            
            # Split the filename into parts
            parts = name_without_ext.split('_')
            
            # extract key and character
            if len(parts) >= 2:
                model_key = parts[0]
                character = parts[1]
                
                # Open the log
                with open(file_path, mode='r', encoding='cp1252') as infile:
                    reader = csv.reader(infile)
                    
                    # Skip the header row
                    next(reader, None) 

                    conversation_history = []
                    
                    # Read the rows, append the new data, and write to output file
                    for row in reader:
                        if len(row) >= 2: # Ensure the row isn't blank
                            request = row[0]
                            response = row[1]

                            current_history_str = "\n\n".join(conversation_history)

                            writer.writerow([request, current_history_str, response, model_key, character, None])

                            turn_string = f"Player: {request}\n{character}: {response}"
                            conversation_history.append(turn_string)
            else:
                print(f"Skipping {filename}: Filename doesn't match expected format.")

    print(f"Merged data saved to: {os.path.abspath(output_file)}")

if __name__ == "__main__":
    merge_logs()