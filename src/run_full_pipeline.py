#!/usr/bin/env python3
"""
run_full_pipeline.py
--------------------
End-to-end Disaster Data Pipeline:
1️⃣ Scrape → 2️⃣ NER → 3️⃣ Clean → 4️⃣ Classify
Each step can be skipped using CLI flags.
"""

import argparse
from datetime import datetime
from pathlib import Path
import pandas as pd

# --- Import pipeline modules ---
from scraping.fb_disaster_scraper import scrape_facebook
from scraping.x_disaster_scraper import scrape_x
from preprocessing.data_cleaning_pipeline import run_cleaning_pipeline
from ner.extract_location import extract_location
from ner.extract_datetime import extract_datetime
from ner.classify_disaster import classify_disaster
from utils.file_ops import save_to_csv
from preprocessing.format_columns import format_columns

# True = if testing/debugging to save files per step; False = saves raw and final files only
SAVE_INTERMEDIATE = True

# ---------------------------------------------------------------------
# Helper: timestamped filenames
# ---------------------------------------------------------------------
def timestamped(name: str, ext: str = "csv", folder: str = "") -> str:
    """Return a timestamped filename, e.g. data/interim/cleaned_data_2025-10-12_1823.csv"""
    ts = datetime.now().strftime("%Y-%m-%d_%H%M")
    folder = folder.rstrip("/") + "/" if folder else ""
    Path(folder).mkdir(parents=True, exist_ok=True)
    return f"{folder}{name}_{ts}.{ext}"

# ---------------------------------------------------------------------
# Helper: auto-load latest file by prefix
# ---------------------------------------------------------------------
def load_latest(prefix: str, folder: str) -> str:
    folder_path = Path(folder)
    files = sorted(
        folder_path.glob(f"{prefix}_*.csv"),
        key=lambda f: f.stat().st_mtime,
        reverse=True
    )
    if not files:
        raise FileNotFoundError(f"No matching files found for prefix '{prefix}' in {folder}")
    latest_file = files[0]
    df_tmp = pd.read_csv(latest_file)
    print(f"📂 Using latest file: {latest_file} ({len(df_tmp)} rows)")
    return str(latest_file)


# ---------------------------------------------------------------------
# Main Pipeline Function
# ---------------------------------------------------------------------
def run_full_pipeline(skip_scrape=False, skip_ner_loc=False, skip_ner_datetime=False, skip_clean=False, skip_classify=False):
    print("\n🚀 Starting Disaster Data Pipeline...")

    # ----------------------------------
    # 1 Scrape or Load Existing
    # ----------------------------------
    if not skip_scrape:
        print("\n🌐  [1] Scraping social media posts...")
        fb_data = scrape_facebook()
        x_data = scrape_x()
        raw_data = pd.concat([fb_data, x_data], ignore_index=True)

        raw_path = timestamped("merged_raw_disaster_posts", folder="data/raw")
        print(f"✅ Scraped {len(fb_data)} FB + {len(x_data)} X posts → {len(raw_data)} total")
        save_to_csv(raw_data, raw_path)
        print(f"💾 Saved raw data → {raw_path}")
    else:
        print("⚠️  Skipping scraping, loading latest raw CSV...")
        raw_latest = load_latest("merged_raw_disaster_posts", folder="data/raw")
        raw_data = pd.read_csv(raw_latest)

    # ----------------------------------
    # 2 Named Entity Recognition
    # ----------------------------------
    # LOCATION
    if not skip_ner_loc:
        print("\n📍  [2] Extracting LOCATION entities from posts...")
        ner_df = extract_location(raw_data)

        if SAVE_INTERMEDIATE:
            ner_loc_path = timestamped("ner_with_locations", folder="data/interim")
            save_to_csv(ner_df, ner_loc_path)
            print(f"✅ Location extraction complete → {ner_loc_path}")
    else:
        print("⚠️  Skipping NER (Location), loading latest output...")
        ner_loc_latest = load_latest("ner_with_locations", folder="data/interim")
        ner_df = pd.read_csv(ner_loc_latest)

    # DATETIME
    if not skip_ner_datetime:
        print("\n📅  [3] Extracting DATETIME entities from posts...")
        ner_df = extract_datetime(ner_df) 
        
        if SAVE_INTERMEDIATE:
            ner_dt_path = timestamped("ner_with_datetime", folder="data/interim")
            save_to_csv(ner_df, ner_dt_path)
            print(f"✅ Datetime extraction complete → {ner_dt_path}")
    else:
        print("⚠️  Skipping NER (Datetime), loading latest combined output...")
        ner_dt_latest = load_latest("ner_with_datetime", folder="data/interim")
        ner_df = pd.read_csv(ner_dt_latest)

    # ----------------------------------
    # 3 Cleaning Pipeline
    # ----------------------------------
    if not skip_clean:
        print("\n🧹  [4] Running cleaning pipeline...")
        cleaned_df = run_cleaning_pipeline(ner_df)

        if SAVE_INTERMEDIATE:
            clean_path = timestamped("cleaned_ner_with_locations_datetime", folder="data/interim")
            save_to_csv(cleaned_df, clean_path)
            print(f"✅ Cleaning complete → {clean_path}")
    else:
        print("⚠️  Skipping cleaning, using NER output as-is.")
        cleaned_df = ner_df

    # ----------------------------------
    # 4 Disaster Type Classification
    # ----------------------------------
    if not skip_classify:
        print("\n🗂️  [5] Classifying disaster type...")
        classified_df = classify_disaster(cleaned_df)

        final_df = format_columns(classified_df)
        final_path = timestamped("final_output", folder="data/processed")
        save_to_csv(final_df, final_path)
        print(f"\n✅ Final dataset saved ({len(final_df)} rows) → {final_path}")

    else:
        print("⚠️  Disaster classification skipped")
        
    # ----------------------------------
    # 5 Pipeline Summary 
    # ----------------------------------
    steps = {
        "Scraping": not skip_scrape,
        "NER-Location": not skip_ner_loc,
        "NER-Datetime": not skip_ner_datetime,
        "Cleaning": not skip_clean,
        "Classification": not skip_classify,
    }

    done = [k for k, v in steps.items() if v]
    skipped = [k for k, v in steps.items() if not v]

    print(f"\n📋 Pipeline Summary → Completed: {', '.join(done) or 'None'} │ Skipped: {', '.join(skipped) or 'None'}")
    print("\n🎉 Pipeline execution finished successfully.\n")

# ---------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the Disaster Data Pipeline with optional steps.")
    parser.add_argument("--skip-scrape", action="store_true", help="Skip scraping and use latest raw data.")
    parser.add_argument("--skip-ner-loc", action="store_true", help="Skip NER (location extraction).")
    parser.add_argument("--skip-ner-datetime", action="store_true", help="Skip NER (datetime extraction).")
    parser.add_argument("--skip-clean", action="store_true", help="Skip cleaning and use NER output as-is.")
    parser.add_argument("--skip-classify",  action="store_true", help="Skip disaster type classification")

    args = parser.parse_args()

    run_full_pipeline(
        skip_scrape=args.skip_scrape,
        skip_ner_loc=args.skip_ner_loc,
        skip_ner_datetime=args.skip_ner_datetime,
        skip_clean=args.skip_clean,
        skip_classify=args.skip_classify,
    )
