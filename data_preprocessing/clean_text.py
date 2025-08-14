import pandas as pd
import re
import os
import unicodedata as ud

OUTPUT_DIR = 'data/cleaned-data'
os.makedirs(OUTPUT_DIR, exist_ok=True)

df = pd.read_csv('data/raw-data/merged_raw_disaster_posts.csv')

def normalize_fonted_unicode(text):
    return ''.join(
        c for c in ud.normalize('NFKD', text)
        if not ud.combining(c)
    )
    
def clean_text(text):
    text = str(text)
    if text.lower().strip() in {"", "nan", "none"}:
        return ""

    text = normalize_fonted_unicode(text)                      # Normalize stylized Unicode (𝑨 → A)
    text = text.lower()                                        # Lowercase
    text = re.sub(r"https?://\S+|www\.\S+", "", text)          # Remove URLs
    text = re.sub(r"<.*?>", "", text)                          # Remove HTML tags
    text = re.sub(r"[@#]\w+", "", text)                        # Remove mentions and hashtags
    text = text.encode("ascii", "ignore").decode("ascii")      # Remove emojis and non-ASCII
    text = re.sub(r"&\w+;", "", text)                          # Remove HTML entities like &amp;
    text = re.sub(r"[-]", " ", text)                           # Replace hyphens with spaces
    text = re.sub(r"[^\w\s]", " ", text)                       # Keeps only alphanumeric + whitespace
    text = re.sub(r"\s+", " ", text).strip()                   # Remove excess whitespace

    # Skip if only punctuation or too short
    if len(text) < 100 or re.fullmatch(r"[. ]+", text):
        return ""

    # Skip if text is mostly numeric or looks like a garbage timestamp
    if re.fullmatch(r"[0-9\s:/.-]{6,}", text):
        return ""

    return text