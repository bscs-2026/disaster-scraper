"""
📅 Datetime Extraction using XLM-RoBERTa NER
--------------------------------------------
Extracts DATE and TIME entities from text using 'programmersilvanus/ner-xlmr',
normalizes them into ISO 8601, and prioritizes:
    1️⃣ Model-detected DAT/TIM in text_content
    2️⃣ post_timestamp
    3️⃣ scraped_timestamp
    4️⃣ Fallback: current time

Usage:
    df = extract_datetime(df)
"""

import re
import pandas as pd
from tqdm import tqdm
from datetime import datetime
from transformers import pipeline
from dateutil import parser

# ======================================================
# 🔧 Helpers
# ======================================================
def _preprocess_for_ner(text: str) -> str:
    """Light cleanup before feeding to NER."""
    text = str(text or "").strip()
    text = re.sub(r"\s+", " ", text)
    return text


def _normalize_date(text: str):
    """Try to parse extracted date string into ISO format."""
    try:
        dt = parser.parse(text, fuzzy=True)
        return dt.isoformat()
    except Exception:
        return None


def _is_valid_str(val):
    """Check if a string is non-empty and not a placeholder like 'Unknown'."""
    if not val or pd.isna(val):
        return False
    val = str(val).strip().lower()
    return val not in {"none", "nan", "unknown", "null", ""}


# ======================================================
# 🧩 Core Extraction Logic
# ======================================================
def extract_datetime(df_data: pd.DataFrame) -> pd.DataFrame:
    """
    Extract 'DAT' and 'TIM' entities using XLM-RoBERTa NER,
    then normalize them to ISO 8601 with priority:
    text_content > post_timestamp > scraped_timestamp
    """
    global _NER_PIPELINE
    try:
        _NER_PIPELINE
    except NameError:
        _NER_PIPELINE = None

    # Load NER model once
    if _NER_PIPELINE is None:
        print("🔹 Loading XLM-RoBERTa NER model for DATE/TIME extraction...")
        _NER_PIPELINE = pipeline(
            "token-classification",
            model="programmersilvanus/ner-xlmr",
            aggregation_strategy="simple"
        )
        print("🧠 Model loaded:", _NER_PIPELINE.model.name_or_path)
    else:
        print("🧠 Using cached XLM-RoBERTa DATE/TIME model.")

    TEXT_COL = "text_content" if "text_content" in df_data.columns else "text"

    raw_mentions, normalized_dates, primary_iso, priority_used = [], [], [], []
    fallback_count = 0

    # ------------------------------------------------------
    # Main extraction loop
    # ------------------------------------------------------
    detected_count = 0
    fallback_count = 0 
    total_rows = len(df_data)

    raw_mentions, normalized_dates, primary_iso, priority_used = [], [], [], []

    for _, row in tqdm(df_data.iterrows(), total=total_rows, desc="📅 Phase 2: datetime (model)"):
        text = _preprocess_for_ner(row.get(TEXT_COL, ""))

        # Run NER model
        ents = _NER_PIPELINE(text)

        # Filter only DAT (date) and TIM (time) entities
        temporal_ents = [ent.get("word", "").strip() for ent in ents if ent.get("entity_group") in {"DAT", "TIM"}]

        # Combine date + time expressions into one string
        combined = " ".join(temporal_ents)
        parsed_dates = []
        if combined:
            parsed = _normalize_date(combined)
            if parsed:
                parsed_dates.append(parsed)

        if temporal_ents:
            detected_count += 1

        # 🎯 Priority selection
        primary, used = None, None

        # 1️⃣ From text (model)
        if parsed_dates:
            parsed_dates.sort()
            primary = parsed_dates[0]
            used = "text_content"

        # 2️⃣ From post_timestamp
        elif _is_valid_str(row.get("post_timestamp")):
            try:
                primary = parser.parse(str(row["post_timestamp"]), fuzzy=True).isoformat()
                used = "post_timestamp"
            except Exception:
                pass

        # 3️⃣ From scraped_timestamp
        elif _is_valid_str(row.get("scraped_timestamp")):
            try:
                primary = parser.parse(str(row["scraped_timestamp"]), fuzzy=True).isoformat()
                used = "scraped_timestamp"
            except Exception:
                pass

        # 4️⃣ Fallback: current system time
        else:
            primary = datetime.now().isoformat()
            used = "fallback_now"
            fallback_count += 1

        # Store results
        raw_mentions.append(temporal_ents)
        normalized_dates.append(parsed_dates)
        primary_iso.append(primary)
        priority_used.append(used)

    # Attach to DataFrame
    df_data["time_mentions_raw"] = raw_mentions
    df_data["time_parsed"] = normalized_dates
    df_data["event_time_primary_iso"] = primary_iso
    df_data["event_time_source"] = priority_used

    # Human-readable datetime
    def _format_event_time(iso_str):
        if not iso_str:
            return None
        try:
            dt = datetime.fromisoformat(iso_str)
            return dt.strftime("%B %d, %Y %H:%M:%S")
        except Exception:
            return iso_str

    df_data["event_time_primary"] = df_data["event_time_primary_iso"].apply(_format_event_time)

    # Summary
    success = total_rows - fallback_count
    print(f"📅 Datetime extraction complete: {success}/{total_rows} posts parsed "
        f"({fallback_count} fallback defaults, {detected_count} with DAT/TIM entities).")

    return df_data
