
import os
import sys
import pandas as pd

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from data_preprocessing.clean_text import clean_text
from data_preprocessing.extract_datetime import extract_datetime_string, parse_datetime
from data_preprocessing.extract_pagesource import extract_pagesource
from data_preprocessing.format_columns import format_columns
from data_preprocessing.drop_near_duplicates import drop_near_duplicates
from data_preprocessing.location_filter import mentions_ph_location
from dateutil import parser

INPUT_PATH = "data/raw-data/merged_raw_disaster_posts.csv"
OUTPUT_PATH = "data/cleaned-data/cleaned_disaster_posts.csv"
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
df["text_content"] = df["text"].fillna("").apply(clean_text)

# Drop rows where cleaned text is empty after stripping
df = df[df["text_content"].str.strip().astype(bool)]

print("🧽 Removing exact duplicate posts...")
df = df.drop_duplicates(subset=["text_content"], keep="first")

print("🤏 Removing near-duplicate posts...")
df = drop_near_duplicates(df, threshold=90)

print("🌏 Filtering non-Philippine context posts...")
df = df[df["text_content"].apply(mentions_ph_location)]

print("⏱️ Extracting date-time from text...")
df["extracted_date_time"] = df["text_content"].apply(extract_datetime_string)
df["date-time"] = df.apply(parse_datetime, axis=1)

print("🔍 Extracting page source...")
df["page_source"] = df["post_url"].apply(extract_pagesource)

print("📊 Formatting columns...")
df = format_columns(df)

print("📌 Sorting by date-time (newest first)...")
df = df.sort_values(by="date-time", ascending=False)

df.to_csv(OUTPUT_PATH, index=False)
print("✅ Done! Cleaned data saved to:", OUTPUT_PATH)

