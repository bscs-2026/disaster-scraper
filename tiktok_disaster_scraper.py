#!/usr/bin/env python3
import os
import time
import logging
from datetime import datetime, timedelta, timezone
from urllib.parse import quote_plus

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

import pandas as pd

# Logging 
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

# Timezone & thresholds 
PH_TIME          = timezone(timedelta(hours=8))
now_ph           = datetime.now(PH_TIME)
since_time_search= now_ph - timedelta(hours=48)  # last 48h for search
scraped_at       = now_ph.strftime("%Y-%m-%d %H:%M")

# Search queries 
SEARCH_QUERIES = [
    "flood philippines",
    "landslide philippines",
    "earthquake philippines",
    "typhoon philippines",
    "fire philippines",
    "volcano philippines"
]

# Disaster keywords 
KEYWORDS = [
    # English
    'earthquake', 'aftershock', 'ground shaking', 'seismic',
    'flood', 'flooding', 'evacuation',
    'typhoon', 'storm', 'storm surge', 'tropical storm', 'tropical depression',
    'landslide', 'soil erosion',
    'fire', 'blaze', 'burning', 'wildfire',
    'volcano', 'volcanic', 'eruption', 'ashfall', 'lava',
    'disaster', 'emergency', 'rescue', 'relief',
    'weather', 'rain', 'heavy rain', 'LPA', 'low pressure area',
    'warning', 'alert', 'advisory', 'monsoon',

    # Tagalog
    'lindol', 'pagyanig', 'pag-uga', 'pagguho ng lupa',
    'baha', 'bahain', 'pagbaha', 'paglikas',
    'bagyo', 'unos', 'malakas na ulan', 'tropical depression',
    'sunog', 'nasunog', 'apoy',
    'bulkan', 'pagputok ng bulkan', 'abo', 'lava', 'mainit na bato',
    'kalamidad', 'sakuna', 'rescue', 'relief operation',
    'babala', 'abiso', 'delubyo', 'emergency response',

    # Bisaya / Cebuano
    'linog', 'nangurog', 'nahulog ang yuta',
    'baha', 'lunop', 'nabahaan',
    'bagyo', 'kusog nga ulan', 'ting-ulan',
    'sunog', 'kalayo', 'nasunog',
    'bulkan', 'bukid nga nagbuto', 'abo', 'lava',
    'kalamidad', 'kasamok', 'tabang', 'rescue', 'relief',
    'pahimangno', 'pasidaan', 'emergency'
]

# Selenium setup 
opts = Options()
opts.add_argument("--headless=new")
opts.add_argument("--disable-gpu")
opts.add_argument("--disable-notifications")
opts.add_argument("--window-size=1920,1080")
opts.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)
driver = webdriver.Chrome(options=opts)

def scroll_page(times=10, pause=2):
    last = driver.execute_script("return document.body.scrollHeight")
    for _ in range(times):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(pause)
        nxt = driver.execute_script("return document.body.scrollHeight")
        if nxt == last:
            break
        last = nxt

def parse_video_page(url):
    """Open a video URL, return (caption, post_dt) or (None,None)."""
    driver.get(url)
    time.sleep(2)
    try:
        iso = driver.find_element(By.TAG_NAME, "time")\
                   .get_attribute("datetime")
        dt = datetime.fromisoformat(iso.replace("Z","+00:00"))\
                     .astimezone(PH_TIME)
        caption = driver.find_element(By.TAG_NAME, "h1").text
        return caption, dt
    except:
        return None, None

results = []

for query in SEARCH_QUERIES:
    q = quote_plus(query)
    url = f"https://www.tiktok.com/search?q={q}"
    logging.info(f"[tt_search] Visiting search: {query}")
    driver.get(url)
    time.sleep(3)
    scroll_page()

    # collect all video links
    elems = driver.find_elements(By.XPATH, "//a[contains(@href,'/video/')]")
    links = {a.get_attribute("href") for a in elems if a.get_attribute("href")}
    logging.info(f"[tt_search] '{query}' → found {len(links)} videos")

    for link in links:
        caption, post_dt = parse_video_page(link)
        if not caption or post_dt < since_time_search:
            continue

        text = caption.lower()
        if not any(kw in text for kw in KEYWORDS):
            continue

        results.append({
            "Source":            "tt_search",
            "Query/Page":        query,
            "Text":              caption,
            "Post Timestamp":    post_dt.strftime("%Y-%m-%d %H:%M"),
            "Scraped Timestamp": scraped_at,
            "User":              link.split("/")[3],  # handle from URL
            "Post URL":          link
        })

    logging.info(f"[tt_search] '{query}' → collected {len(results)} items so far")

driver.quit()

# — save to CSV (dedupe by Text) —
df = pd.DataFrame(results)
out = "raw-data/tiktok_search_disaster_posts.csv"
os.makedirs(os.path.dirname(out), exist_ok=True)

if os.path.exists(out):
    old = pd.read_csv(out)
    df  = pd.concat([old, df], ignore_index=True)\
            .drop_duplicates(subset=["Text"], keep="last")

df.to_csv(out, index=False)
logging.info(f"✅ Done! total rows: {len(df)}")
