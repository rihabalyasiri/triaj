# __init__.py
from agent.loader import read_file

def main() -> None:
    # loader -> preprocessor -> triage -> scoring -> router -> suggester -> cli
    read_file("aa_dataset-tickets-multi-lang-5-2-50-version-selected-columns.csv")
    pass
