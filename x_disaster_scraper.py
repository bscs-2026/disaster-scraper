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
from social_media_config import KEYWORDS, X

# Constants
PH_TIME        = timezone(timedelta(hours=8))
X_OUT          = 'data/raw-data/x_raw_disaster_posts.csv'
MERGED_OUT     = 'data/raw-data/merged_raw_disaster_posts.csv'
LOG_FORMAT     = '%(asctime)s [%(levelname)s] %(message)s'

def init_driver() -> webdriver.Chrome:
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--disable-notifications")
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    )
    return webdriver.Chrome(options=opts)

def scroll_page(driver, scroll_times=60, pause=1):
    last = driver.execute_script("return document.body.scrollHeight")
    for _ in range(scroll_times):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(pause)
        nxt = driver.execute_script("return document.body.scrollHeight")
        if nxt == last:
            break
        last = nxt

def format_ts(dt: datetime) -> str:
    return dt.strftime('%Y-%m-%d %H:%M')

def process_x_cards(results: list,
                    identifier: str,
                    cards,
                    cutoff_dt: datetime) -> None:
    added = 0
    for c in cards:
        # extract text
        try:
            txt = c.find_element(By.XPATH, ".//div[@data-testid='tweetText']").text
        except:
            continue
        if not any(kw in txt.lower() for kw in KEYWORDS):
            continue

        # extract and convert timestamp
        try:
            iso = c.find_element(By.TAG_NAME, "time") \
                   .get_attribute("datetime")
            dt0 = datetime.fromisoformat(iso.replace("Z", "+00:00"))
            post_dt = dt0.astimezone(PH_TIME)
        except:
            continue
        if post_dt < cutoff_dt:
            continue

        # extract URL and username
        try:
            link = c.find_element(
                By.XPATH, ".//a[contains(@href,'/status/')]"
            ).get_attribute("href")
            username = link.split("/")[3]
        except:
            link, username = None, "unknown"

        results.append({
            "source":           'X',
            "query_page":        identifier,
            "text":              txt[:5000],
            "post_timestamp":    format_ts(post_dt),
            "scraped_timestamp": scraped_at,
            "user":              username,
            "post_url":          link
        })
        added += 1

    logging.info(f"[X] {identifier}: appended {added} posts "
                 f"(total cards processed: {len(cards)})")

def save_results(df: pd.DataFrame):
    os.makedirs(os.path.dirname(X_OUT), exist_ok=True)

    # 1) X-only file
    if os.path.exists(X_OUT):
        old_x = pd.read_csv(X_OUT)
        df_x  = pd.concat([old_x, df], ignore_index=True) \
                     .drop_duplicates(subset=['text'], keep='last')
    else:
        df_x = df.copy()

    df_x.to_csv(X_OUT, index=False)
    logging.info(f"✅ New x rows saved: {len(df)}")
    logging.info(f"✅ X Total: {len(df_x)}")

    # 2) merged file 
    if os.path.exists(MERGED_OUT):
        old_merge = pd.read_csv(MERGED_OUT)
        df_merge  = pd.concat([old_merge, df], ignore_index=True) \
                       .drop_duplicates(subset=['text'], keep='last')
    else:
        df_merge = df.copy()

    df_merge.to_csv(MERGED_OUT, index=False)
    logging.info(f"✅ All Total: {len(df_merge)}")

def main():
    # configure logging
    logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)

    # timestamps
    now_ph       = datetime.now(PH_TIME)
    since_user   = now_ph - timedelta(hours=24)
    since_search = now_ph - timedelta(hours=720)
    global scraped_at
    scraped_at   = now_ph.strftime('%Y-%m-%d %H:%M')

    # load config
    users   = X["users"]
    queries = X["search_queries"]

    driver  = init_driver()
    results = []

    # scrape each user timeline
    for user in users:
        url = f"https://x.com/{user}"
        logging.info(f"[x_user] Visiting {url}")
        driver.get(url)
        time.sleep(3)
        scroll_page(driver)
        cards = driver.find_elements(By.XPATH, "//article[@role='article']")
        process_x_cards(results, user, cards, since_user)

    # scrape each search query
    for query in queries:
        url = f"https://x.com/search?q={quote_plus(query)}&src=typed_query&f=live"
        logging.info(f"[x_search] Visiting {url}")
        driver.get(url)
        time.sleep(3)
        scroll_page(driver)
        cards = driver.find_elements(By.XPATH, "//article[@role='article']")
        process_x_cards(results, query, cards, since_search)

    driver.quit()

    # save to CSV
    df = pd.DataFrame(results)
    save_results(df)

if __name__ == "__main__":
    main()