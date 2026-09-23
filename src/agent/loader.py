# loader.py
import pandas as pd

def read_file(filename):
    df = pd.read_csv(filename)
    print(df.values)
    
