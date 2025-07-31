#!/usr/bin/env python3
import os, time, logging
from datetime import datetime, timedelta, timezone
from urllib.parse import quote_plus

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

import pandas as pd

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

PH_TIME            = timezone(timedelta(hours=8))
now_ph             = datetime.now(PH_TIME)
since_user_hours   = 24
since_search_hours = 48
since_user   = now_ph - timedelta(hours=since_user_hours)
since_search = now_ph - timedelta(hours=since_search_hours)
scraped_at   = now_ph.strftime('%Y-%m-%d %H:%M')

X_USERS        = ['ABSCBNNews','rapplerdotcom','gmanews','dost_pagasa', 'inquirerdotnet' , 
                  'phivolcs_dost', 'NDRRMC_OpCen']
X_SEARCH_QUERIES = [
    "flood philippines", "Flood in Davao",
    "landslide philippines", "Landslide in Davao",
    "earthquake philippines", "Earthquake in Davao",
    "typhoon philippines", "Typhoon in Davao",
    "fire philippines", "Fire in Davao",
    "volcano eruption philippines", "Volcano eruption Davao",
    "disaster news philippines", "Disaster news Davao",
    
]

# Keywords for Filtering 
KEYWORDS = [
    # Typhoon / Storm
    "typhoon", "storm", "storm surge",
    "tropical storm", "tropical depression",
    "bagyo", "unos",           
    "#typhoon", "#storm",

    # Rain / Weather
    "weather", "rain", "raining", "rainfall", "downpour", "showers",
    "drizzle", "heavy rain", "monsoon",
    "LPA", "low pressure area",
    "malakas na ulan",
    
    # Flood (and related)
    "flood", "flooding", "flash flood", "river overflow",
    "baha", "lunop", "Street Flood",      
    "#flood", "#FloodAlert", "#BahaPH", "#StreetFloodAlert",

    # Landslide / Mudslide
    "landslide", "mudslide", "soil erosion", "slope failure",
    "pagguho ng lupa", "nangurog",  
    "#landslide", "#LandslideAlert", "#LandslidePH",

    # Earthquake
    "earthquake", "aftershock", "ground shaking", "seismic",
    "linog", "pagyanig",       
    "#EarthquakeAlert", "#EarthquakePH",

    # Tsunami
    "tsunami", "tidal wave", "sea surge", "coastal surge",
    "daluyong",                     
    "#tsunami",

    # Fire / Wildfire
    "fire", "blaze", "burning", "wildfire",
    "sunog", "nasunog","apoy",            
    "#FireAlert",

    # Volcano
    "volcano", "volcanic", "eruption", "ashfall", "lava",
    "bulkan", "pagputok ng bulkan",  
    "#volcano",

    # General disaster / emergency
    "disaster", "emergency", "rescue", "relief",
    "evacuation", "#evacuation",

    # Warnings & Alerts
    "warning", "alert", "advisory", "bulletin",
    "babala", "abiso",              
    "#warning", "#alert",

    # Tagalog / Cebuano extras
    "pag-uga", "pagbaha", "paglikas", "malakas na ulan",
    "mainit na bato", "kalamidad", "sakuna",
    "pahimangno", "pasidaan",

    # Bisaya / Cebuano extras
    "nahulog ang yuta", "nabahaan",
    "kusog nga ulan", "ting-ulan",
    "kasamok", "tabang"
]

# SELENIUM SETUP
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

def scroll_page(times=40, pause=2):
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

# SCRAPE USER TIMELINES
for user in X_USERS:
    url = f"https://x.com/{user}"
    logging.info(f"[x_user] Visiting {url}")
    driver.get(url)
    time.sleep(3)
    scroll_page()

    cards = driver.find_elements(By.XPATH, "//article[@role='article']")
    logging.info(f"[x_user] {user}: {len(cards)} cards found")

    for c in cards:
        try:
            txt = c.find_element(By.XPATH, ".//div[@data-testid='tweetText']").text
        except:
            continue
        if not any(kw in txt.lower() for kw in KEYWORDS):
            continue

        try:
            iso = c.find_element(By.TAG_NAME, "time").get_attribute("datetime")
            dt0 = datetime.fromisoformat(iso.replace("Z","+00:00"))
            post_dt = dt0.astimezone(PH_TIME)
        except:
            continue
        if post_dt < since_user:
            continue

        try:
            link = c.find_element(By.XPATH, ".//a[contains(@href,'/status/')]") \
                   .get_attribute("href")
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

# SCRAPE FREE-FORM SEARCHES
for query in X_SEARCH_QUERIES:
    q = quote_plus(query)
    url = f"https://x.com/search?q={q}&src=typed_query&f=live"
    logging.info(f"[x_search] Visiting {url}")
    driver.get(url)
    time.sleep(3)
    scroll_page()

    cards = driver.find_elements(By.XPATH, "//article[@role='article']")
    logging.info(f"[x_search] “{query}”: {len(cards)} cards found")

    for c in cards:
        try:
            txt = c.find_element(By.XPATH, ".//div[@data-testid='tweetText']").text
        except:
            continue
        if not any(kw in txt.lower() for kw in KEYWORDS):
            continue

        try:
            iso = c.find_element(By.TAG_NAME, "time").get_attribute("datetime")
            dt0 = datetime.fromisoformat(iso.replace("Z","+00:00"))
            post_dt = dt0.astimezone(PH_TIME)
        except:
            continue
        if post_dt < since_search:
            continue

        try:
            link = c.find_element(By.XPATH, ".//a[contains(@href,'/status/')]") \
                   .get_attribute("href")
            handle = link.split("/")[3]
        except:
            link, handle = None, "unknown"

        results.append({
            "Source":           "x_search",
            "Query/Page":       query,
            "Text":             txt[:5000],
            "Post Timestamp":   format_ts(post_dt),
            "Scraped Timestamp":scraped_at,
            "User":             handle,
            "Post URL":         link
        })
    logging.info(f"[x_search] “{query}”: collected so far {len(results)} items")

driver.quit()

# Save results to CSV

df = pd.DataFrame(results)
out = "raw-data/x_raw_disaster_posts.csv"
os.makedirs(os.path.dirname(out), exist_ok=True)

if os.path.exists(out):
    old = pd.read_csv(out)
    df  = pd.concat([old, df], ignore_index=True) \
           .drop_duplicates(subset=["Text"], keep="last")

df.to_csv(out, index=False)
logging.info(f"✅ Done! total rows: {len(df)}")
