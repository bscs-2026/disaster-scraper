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
    format='%(asctime)s [%(levelname)s] %(message)s'
)

# Timezone & thresholds 
PH_TIME            = timezone(timedelta(hours=8))
now_ph             = datetime.now(PH_TIME)
since_time_user    = now_ph - timedelta(hours=24)  # last 24 h for users
since_time_hashtag = now_ph - timedelta(hours=48)  # last 48 h for hashtags
scraped_at         = now_ph.strftime('%Y-%m-%d %H:%M')

# X configs
X_USERS    = ['abscbnNEWS','rapplerdotcom','gmanews', 'dost_pagasa']
X_HASHTAGS = ['RescuePH','FloodAlert','BahaPH','StreetFloodAlert',
              'LandslideAlert','LandslidePH','FireAlert',
              'EarthquakeAlert','EarthquakePH']

# Disaster keywords
KEYWORDS = [
    '#FloodAlert', '#BahaPH', '#StreetFloodAlert',
    '#LandslideAlert', '#LandslidePH' '#FireAlert', '#EarthquakeAlert', '#EarthquakePH',

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

def format_ts(dt):
    return dt.strftime('%Y-%m-%d %H:%M')

results = []

# — scrape by user timeline —
for user in X_USERS:
    url = f"https://twitter.com/{user}"
    logging.info(f"[x_user] Visiting {url}")
    driver.get(url)
    time.sleep(4)
    scroll_page()

    cards = driver.find_elements(By.XPATH, "//article[@role='article']")
    logging.info(f"[x_user] {user}: {len(cards)} cards found")

    for c in cards:
        # text
        try:
            txt = c.find_element(By.XPATH, ".//div[@data-testid='tweetText']").text
        except:
            continue
        if not any(kw.lower() in txt.lower() for kw in KEYWORDS):
            continue

        # timestamp
        try:
            iso = c.find_element(By.TAG_NAME, "time").get_attribute("datetime")
            dt0 = datetime.fromisoformat(iso.replace("Z","+00:00"))
            post_dt = dt0.astimezone(PH_TIME)
        except:
            continue
        if post_dt < since_time_user:
            continue

        # url & user handle
        try:
            link = c.find_element(
                By.XPATH, ".//a[contains(@href,'/status/')]"
            ).get_attribute("href")
            handle = link.split("/")[3]
        except:
            link, handle = None, user

        results.append({
            "Source":           "x_user",
            "Query/Page":       user,
            "Text":             txt[:5000],
            "Post Timestamp":   format_ts(post_dt),
            "Scraped Timestamp":scraped_at,
            "User":             handle,
            "Post URL":         link
        })
    logging.info(f"[x_user] {user}: collected so far {len(results)} items")

# — scrape by hashtag search —
for tag in X_HASHTAGS:
    q = quote_plus(f"#{tag}")
    url = f"https://twitter.com/search?q={q}&f=live"
    logging.info(f"[x_tag] Visiting {url}")
    driver.get(url)
    time.sleep(4)
    scroll_page()

    cards = driver.find_elements(By.XPATH, "//article[@role='article']")
    logging.info(f"[x_tag] #{tag}: {len(cards)} cards found")

    for c in cards:
        try:
            txt = c.find_element(By.XPATH, ".//div[@data-testid='tweetText']").text
        except:
            continue
        if not any(kw.lower() in txt.lower() for kw in KEYWORDS):
            continue

        try:
            iso = c.find_element(By.TAG_NAME, "time").get_attribute("datetime")
            dt0 = datetime.fromisoformat(iso.replace("Z","+00:00"))
            post_dt = dt0.astimezone(PH_TIME)
        except:
            continue
        if post_dt < since_time_hashtag:
            continue

        try:
            link = c.find_element(
                By.XPATH, ".//a[contains(@href,'/status/')]"
            ).get_attribute("href")
            handle = link.split("/")[3]
        except:
            link, handle = None, "unknown"

        results.append({
            "Source":           "x_tag",
            "Query/Page":       f"#{tag}",
            "Text":             txt[:5000],
            "Post Timestamp":   format_ts(post_dt),
            "Scraped Timestamp":scraped_at,
            "User":             handle,
            "Post URL":         link
        })
    logging.info(f"[x_tag] #{tag}: collected so far {len(results)} items")

driver.quit()

# — Save to CSV (dedupe on Text) —
df = pd.DataFrame(results)
out = "raw-data/x_raw_disaster_posts.csv"
os.makedirs(os.path.dirname(out), exist_ok=True)

if os.path.exists(out):
    old = pd.read_csv(out)
    df  = pd.concat([old, df], ignore_index=True)\
           .drop_duplicates(subset=["Text"], keep="last")

df.to_csv(out, index=False)
logging.info(f"✅ Done! total rows: {len(df)}")
