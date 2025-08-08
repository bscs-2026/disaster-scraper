import re
import numpy as np

# Define mapping from raw usernames → formatted organization names
SOURCE_NAME_MAP = {
    "abscbnnews": "ABS-CBN",
    "abscbn": "ABS-CBN",
    "gmanews": "GMA News",
    "phivolcs": "PHIVOLCS",
    "pagasa.dost.gov.ph": "PAGASA",
    "dost.pagasa": "PAGASA",
    "ndrrmc": "NDRRMC",
    "manilabulletin": "Manila Bulletin",
    "sunstarphilippines": "SunStar Philippines",
    "sunstardavaonews": "SunStar Davao",
    "rapplerdotcom": "Rappler",
    "philstarnews": "Philstar News",
    "inquirerdotnet": "Inquirer.net",
    "davaodrrmo": "Davao City DRRMO",
   
    # Add more as needed...
}

def extract_pagesource(url):
    if not isinstance(url, str):
        return np.nan

    # 1. If URL points to a hashtag
    hashtag_match = re.search(r"(?:facebook\.com|x\.com)/hashtag/([^/?#\s]+)", url)
    if hashtag_match:
        return f"#{hashtag_match.group(1).lower()}"

    # 2. Otherwise extract the page name/username
    match = re.search(r"(?:facebook\.com|x\.com)/(?!hashtag|watch|reel)([^/?#\s]+)", url)
    if match:
        raw_page = match.group(1).lower().strip().strip(".@/")
        return SOURCE_NAME_MAP.get(raw_page, raw_page)

    return np.nan