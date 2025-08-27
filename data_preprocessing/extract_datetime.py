import re
import pandas as pd
from dateutil import parser
from datetime import datetime
from dateutil.tz import gettz

TAGALOG_TO_ENGLISH_MONTHS = {
    "enero": "january", "pebrero": "february", "marso": "march", "abril": "april",
    "mayo": "may", "hunyo": "june", "hulyo": "july", "agosto": "august",
    "setyembre": "september", "oktubre": "october", "nobyembre": "november", "disyembre": "december"
}

PH_TZ = gettz("Asia/Manila")
CURRENT_YEAR = datetime.now().year

def translate_tagalog_months(text):
    for tgl, eng in TAGALOG_TO_ENGLISH_MONTHS.items():
        text = re.sub(rf"\b{tgl}\b", eng, text, flags=re.IGNORECASE)
    return text

def extract_datetime_string(text):
    if not isinstance(text, str):
        return ""

    text = translate_tagalog_months(text.lower())

    patterns = [
        # e.g. 5:00 pm 22 july 2025
        r"\b\d{1,2}[:.]\d{2}\s?(?:a\.?m\.?|p\.?m\.?)?\s+\d{1,2}\s+[a-z]+\s+\d{4}\b",

        # e.g. 22 july 2025, july 22 2025
        r"\b\d{1,2}\s+[a-z]+\s+\d{4}\b",
        r"\b[a-z]+\s+\d{1,2},?\s+\d{4}\b",

        # Numeric: 08/04/2025
        r"\b\d{1,2}/\d{1,2}/\d{4}\b",

        # Compact dates like 28jul25
        r"\b\d{1,2}[a-z]{3}\d{2,4}\b",

        # Month-day only (e.g. july 24)
        r"\b[a-z]{3,9}\s+\d{1,2}\b",

        # Day-name month day (e.g. thursday july 24)
        r"\b[a-z]+day\s+[a-z]{3,9}\s+\d{1,2}\b",

        # Compact timestamp + date (e.g. 825pm28jul25)
        r"\b\d{3,4}(?:a\.?m\.?|p\.?m\.?)?\d{1,2}[a-z]{3}\d{2,4}\b"
    ]

    matches = []
    for pattern in patterns:
        found = re.findall(pattern, text, flags=re.IGNORECASE)
        matches.extend(found)

    matches = [m for m in matches if not re.search(r"\b(kph|km|hpa|usd)\b", m)]
    return "; ".join(matches) if matches else ""

def parse_datetime(row):
    ts = str(row.get("post_timestamp", "")).strip()
    if ts and ts.lower() != "nan":
        try:
            parsed = parser.parse(ts, fuzzy=True)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=PH_TZ)
            if 2000 <= parsed.year <= CURRENT_YEAR:
                return parsed.strftime('%Y-%m-%d %H:%M')
        except:
            pass

    extracted = row.get("extracted_date_time", "")
    if extracted:
        for piece in extracted.split(";"):
            try:
                parsed = parser.parse(piece.strip(), fuzzy=True)
                if parsed.tzinfo is None:
                    parsed = parsed.replace(tzinfo=PH_TZ)
                if 2000 <= parsed.year <= CURRENT_YEAR:
                    return parsed.strftime('%Y-%m-%d %H:%M')
            except:
                continue
            
    scraped = row.get("scraped_timestamp", "")
    if scraped:
        try:
            parsed = parser.parse(scraped, fuzzy=True)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=PH_TZ)
            return parsed.strftime('%Y-%m-%d %H:%M')
        except:
            pass

    # Fallback: return NOW_PH in same format
    return datetime.now(tz=PH_TZ).strftime('%Y-%m-%d %H:%M')