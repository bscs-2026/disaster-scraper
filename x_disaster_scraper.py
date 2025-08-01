#!/usr/bin/env python3
import os, time, logging
from datetime import datetime, timedelta, timezone
from urllib.parse import quote_plus

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

import pandas as pd
from social_media_config import KEYWORDS, X

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

PH_TIME            = timezone(timedelta(hours=8))
now_ph             = datetime.now(PH_TIME)
since_user   = now_ph - timedelta(hours=24)
since_search = now_ph - timedelta(hours=48)
scraped_at   = now_ph.strftime('%Y-%m-%d %H:%M')

X_USERS        = X["users"]
X_SEARCH_QUERIES = X["search_queries"]

# Chrome Driver Setup 
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

def scroll_page(times=40):
    last = driver.execute_script("return document.body.scrollHeight")
    for _ in range(times):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        nxt = driver.execute_script("return document.body.scrollHeight")
        if nxt == last:
            break
        last = nxt

def format_ts(dt):
    return dt.strftime('%Y-%m-%d %H:%M')

results = []

def process_twitter_cards(source: str,
                          identifier: str,
                          cards,
                          cutoff_dt: datetime) -> None:
    added = 0
    for c in cards:
        # Text
        try:
            txt = c.find_element(By.XPATH, ".//div[@data-testid='tweetText']").text
        except Exception:
            continue
        if not any(kw in txt.lower() for kw in KEYWORDS):
            continue

        # Timestamp
        try:
            iso = c.find_element(By.TAG_NAME, "time").get_attribute("datetime")
            dt0 = datetime.fromisoformat(iso.replace("Z", "+00:00"))  # ISO → UTC
            post_dt = dt0.astimezone(PH_TIME)
        except Exception:
            continue
        if post_dt < cutoff_dt:
            continue

        # URL & username
        try:
            link = c.find_element(By.XPATH,
                                  ".//a[contains(@href,'/status/')]").get_attribute("href")
            handle = link.split("/")[3]
        except Exception:
            link, handle = None, "unknown"

        # Save
        results.append({
            "Source":            source,
            "Query/Page":        identifier,
            "Text":              txt[:5000],
            "Post Timestamp":    format_ts(post_dt),
            "Scraped Timestamp": scraped_at,
            "User":              handle,
            "Post URL":          link
        })
        added += 1
    logging.info(f"[{source}] {identifier}: appended {added} posts "
                 f"(total collected: {len(results)})")

for user in X_USERS:
    url = f"https://x.com/{user}"
    logging.info(f"[x_user] Visiting {url}")
    driver.get(url)
    time.sleep(3)
    scroll_page()
    cards = driver.find_elements(By.XPATH, "//article[@role='article']")
    process_twitter_cards("x_user", user, cards, since_user)

for query in X_SEARCH_QUERIES:
    url = f"https://x.com/search?q={quote_plus(query)}&src=typed_query&f=live"
    logging.info(f"[x_search] Visiting {url}")
    driver.get(url)
    time.sleep(3)
    scroll_page()
    cards = driver.find_elements(By.XPATH, "//article[@role='article']")
    process_twitter_cards("x_search", query, cards, since_search)

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
