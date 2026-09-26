# loader.py
import pandas as pd
from pandas import DataFrame

def read_file(filename) -> DataFrame:
    if(filename is None):
        raise ValueError("Filename is None. Please provide a valid filename.")
    
    try:
        return pd.read_csv(filename)
    except FileNotFoundError:
        print(f"File Error '{filename}' not found. Please provide file in project level directory.") 
     
    
