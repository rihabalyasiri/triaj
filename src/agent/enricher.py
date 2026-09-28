# enricher.py
from pandas import DataFrame


def preprocessing(data: DataFrame) -> list[dict]:
    # use german data
    df = data[data['language'] == 'de']

    # replace null values to empty string
    df['subject'] = df['subject'].fillna("")
    df['body'] = df['body'].fillna("")

    # remove duplicate duplicate body
    deduplicate = df.drop_duplicates(subset='body')

    # remove new lines and all symbols from body 
    pattern = r"[^\w\s.,!?:;()\-€%]"
    for col in ('subject', 'body'):
        df[col] = (
            df[col]
            .str.replace(r"\\[nrt]", " ", regex=True)
            .str.replace(pattern, " ", regex=True)
            .str.replace(r"\s+", " ", regex=True)
            .str.strip()
        )

    return [
    {
        "ticket_id": i,
        "message": f"{row['subject']} {row['body']}".strip(),
        "queue": row["queue"], # will be used as ground truth for evaluation only, never seen by the models
        "priority": row["priority"], # will be used as ground truth for evaluation only, never seen by the models
    }
    for i, row in deduplicate.iterrows()
]


