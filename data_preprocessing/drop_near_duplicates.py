from rapidfuzz import fuzz

def drop_near_duplicates(df, threshold=90):
    seen = []
    drop_indices = set()

    for i in range(len(df)):
        if i in drop_indices:
            continue
        text_i = df.iloc[i]["text_content"]
        for j in range(i + 1, len(df)):
            if j in drop_indices:
                continue
            text_j = df.iloc[j]["text_content"]
            similarity = fuzz.token_set_ratio(text_i, text_j)
            if similarity >= threshold:
                drop_indices.add(j)
    return df.drop(df.index[list(drop_indices)])
