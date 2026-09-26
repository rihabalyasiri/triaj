from pandas import DataFrame
import pandas as pd


def read_file(filename) -> DataFrame:
    if(filename is None):
        raise ValueError("Filename is None. Please provide a valid filename.")
    
    try:
        return pd.read_csv(filename)
    except FileNotFoundError:
        print(f"File Error '{filename}' not found. Please provide file in project level directory.") 


TOOL_SCHEMA = [
    {
    "type": "function",
    "function": {
        "name": "read_file",
        "description": "A function to read a CSV file and return its content as a DataFrame.",
        "parameters": {
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "The name of the CSV file to read. The file should be located in the project level directory."
                    }
                },
                "required": ["filename"]
            }
    }
}
]