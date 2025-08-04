
import os
import sys
import pandas as pd

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from data_preprocessing.clean_text import clean_text
from data_preprocessing.extract_datetime import extract_datetime
from data_preprocessing.format_columns import format_columns

INPUT_PATH = "disaster-scraper/data/raw-data/merged_raw_disaster_posts.csv"
OUTPUT_PATH = "disaster-scraper/data/cleaned-data/cleaned_disaster_posts.csv"

os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

from dateutil import parser

def parse_datetime_safe(x):
    try:
        return parser.parse(x, fuzzy=True)
    except:
        return pd.NaT

print("📥 Loading raw data...")

df = pd.read_csv(INPUT_PATH)

print("🧹 Cleaning text...")
df["text_content"] = df["text"].apply(clean_text)
df = df[df["text_content"].str.strip() != ""]

# *** will find way to extract it better later kasi medyo crazy siya ***
# print("⏱️ Extracting date-time from text...")
# df["extracted_date_time"] = df["text_content"].apply(extract_datetime)


# Extract poster name from URL like "https://www.facebook.com/SunstarDavao/"
df["page_source"] = df["post_url"].str.extract(r"(?:facebook\.com|x\.com)/([^/?\s]+)", expand=False)

print("📊 Formatting columns...")
df = format_columns(df)

df.to_csv(OUTPUT_PATH, index=False)
print("✅ Done! Cleaned data saved to:", OUTPUT_PATH)

