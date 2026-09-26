# preprocessor.py
from pandas import DataFrame

# TODO: there are some wrong language type
# TODO: subjects are in english
def preprocessing(data: DataFrame) -> list[str]:
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

    # concat subject and body, return as list
    return (df['subject'] + ' ' + df['body']).str.strip().tolist()


