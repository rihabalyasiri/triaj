# __init__.py
from agent.loader import read_file
from agent.preprocessor import preprocessing

def main() -> None:
    # loader -> preprocessor -> triage -> scoring -> router -> suggester -> cli
    df = read_file("aa_dataset-tickets-multi-lang-5-2-50-version-selected-columns.csv") 
    data = preprocessing(df)
    print(data[2])
    pass
