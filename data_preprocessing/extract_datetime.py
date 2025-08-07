import re

def extract_datetime(text):
    if not isinstance(text, str):
        return ""

    patterns = [
        r"\b\d{1,2}[:.]\d{2}\s?(?:a\.?m\.?|p\.?m\.?)\s+\d{1,2}\s+[a-z]+\s+\d{4}\b", 
        r"\b\d{1,2}\s+[a-z]+\s+\d{4}\b",
        r"\b[a-z]+\s+\d{1,2},\s+\d{4}\b",
        r"\b[a-z]+\s+\d{1,2}\s+\d{4}\b",
        r"\b\d{1,2}/\d{1,2}/\d{4}\b",
        r"\b\d{1,2}[a-z]{3}\d{2,4}\b",
        r"\b[a-z]{3}\d{1,2}\d{2,4}\b",
        r"\b\d{4}[a-z]{3}\d{1,2}\b",
        r"\b[a-z]{3,6}\d{1,2}[a-z]{3}\d{2,4}?\b",
        r"\b[a-z]+day\s+\d{1,2}\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\b",
        r"\b\d{1,2}\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\b",
        r"\b\d{1,2}[:.]\d{2}\s?(?:a\.?m\.?|p\.?m\.?)\b",
        r"\b-\s*\d{1,2}[:.]\d{2}\s?(?:a\.?m\.?|p\.?m\.?)\b",
    ]

    matches = []
    for pattern in patterns:
        found = re.findall(pattern, text, flags=re.IGNORECASE)
        matches.extend(found)

    matches = [m for m in matches if not re.search(r"\b(kph|km|hpa|usd)\b", m)]
    return "; ".join(matches) if matches else ""
