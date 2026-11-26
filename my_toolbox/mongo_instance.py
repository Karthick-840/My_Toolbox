import json

def convert_to_mongodb_json(input_file, output_file):
    """
    Converts a JSON file to MongoDB-compatible JSON (array of objects).

    Args:
        input_file (str): Path to the input JSON file.
        output_file (str): Path to the output JSON file.
    """
    try:
        with open(input_file, 'r') as infile:
            data = json.load(infile)

        if isinstance(data, list):
            # Already in the correct format.
            with open(output_file, 'w') as outfile:
                json.dump(data, outfile, indent=2) #indent for readability.
        else:
            # Convert to array of objects.
            with open(output_file, 'w') as outfile:
                json.dump([data], outfile, indent=2) #make a list of the data.

        print(f"Successfully converted {input_file} to {output_file}")

    except FileNotFoundError:
        print(f"Error: File not found.")
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON.")
    except Exception as e:
        print(f"An error occured: {e}")

# Example Usage
input_json = "reorganization_report.json" #replace with your input json file.
output_json = "mongodb_reorganization_report.json" #replace with your desired output file name.

#create dummy input json.
with open(input_json, 'w') as file:
    json.dump({"test" : "data"}, file)

convert_to_mongodb_json(input_json, output_json)