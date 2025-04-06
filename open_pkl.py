import pickle
import json

def load_pickle_file(file_path):
    try:
        with open(file_path, 'rb') as file:
            data = pickle.load(file)
            print("Pickle file contents:")
            print(data)
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
    except Exception as e:
        print(f"Error loading pickle file: {str(e)}")

# Example usage
if __name__ == "__main__":
    file_path = "parties.pkl"
    with open(file_path, 'rb') as file:
        data = pickle.load(file)
        formatted_data = json.dumps(data, indent=4)
        print(formatted_data)