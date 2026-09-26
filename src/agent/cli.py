# cli.py

import argparse
import json
from itertools import islice

from agent.enricher import preprocessing  
from agent.suggester import triage
from agent.adapter import read_file
from agent.writer import write_results


def cli_app():
    # adapter -> enricher -> classifier -> scoring -> action -> final result on cli & write on csv
    df = read_file("tickets.csv") 
    p = argparse.ArgumentParser(prog="triage", description="Triage tickets from the preprocessor")
    p.add_argument("-n", "--num", type=int, default=None,
                   help="number of records to process (default: all)")
    args = p.parse_args()

    if args.num is not None and args.num < 1:
        p.error("-n must be >= 1")

    records = islice(preprocessing(df), args.num)  

    for i, rec in enumerate(records, start=1):
    
        try:
            result = triage(rec)
            print(json.dumps({"id": i, "message": rec, **result.model_dump(mode="json")},
                             ensure_ascii=False))
            write_results([rec]) 
        except Exception as e:
            print(json.dumps({"id": i, "message": rec, "error": str(e)}, ensure_ascii=False))