#!/usr/bin/env python3
import time
import logging
from datetime import datetime, timedelta, timezone
from urllib.parse import quote_plus
from pathlib import Path

import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

from scraping.social_media_config import KEYWORDS, X

# --- Setup base dirs (safe absolute paths) ---
BASE_DIR = Path(__file__).resolve().parents[2]
LOOKUP_DIR = BASE_DIR / "data" / "lookup"
RAW_DIR = BASE_DIR / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

# --- Constants ---
PH_TIME = timezone(timedelta(hours=8))
LOG_FORMAT = '%(asctime)s [%(levelname)s] %(message)s'

# --- Load PH location reference data ---
ref_cities = pd.read_csv(LOOKUP_DIR / 'refcitymun.csv')
ref_provs = pd.read_csv(LOOKUP_DIR / 'refprovince.csv')
ref_regs = pd.read_csv(LOOKUP_DIR / 'refregion.csv')

PH_LOCATIONS = set(
    pd.concat([
        ref_cities['citymunDesc'],
        ref_provs['provDesc'],
        ref_regs['regDesc']
    ], ignore_index=True).str.lower().str.strip().unique()
)
PH_LOCATIONS.update(['philippines', 'pilipinas', 'ph'])

# --- Selenium Setup ---
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

def mentions_ph_location(text):
    text = text.lower()
    return any(loc in text for loc in PH_LOCATIONS)

def process_x_cards(results: list, identifier: str, cards, cutoff_dt: datetime, scraped_at: str):
    added = 0
    for c in cards:
        try:
            txt = c.find_element(By.XPATH, ".//div[@data-testid='tweetText']").text
        except:
            continue

        if not any(kw in txt.lower() for kw in KEYWORDS):
            continue
        if not mentions_ph_location(txt):
            continue

        try:
            iso = c.find_element(By.TAG_NAME, "time").get_attribute("datetime")
            dt0 = datetime.fromisoformat(iso.replace("Z", "+00:00"))
            post_dt = dt0.astimezone(PH_TIME)
        except:
            continue

        if post_dt < cutoff_dt:
            continue

        try:
            link = c.find_element(By.XPATH, ".//a[contains(@href,'/status/')]").get_attribute("href")
            username = link.split("/")[3] if link else "unknown"
        except:
            link, username = None, "unknown"

        results.append({
            "source": "X",
            "query_page": identifier,
            "text": txt[:5000],
            "post_timestamp": format_ts(post_dt),
            "scraped_timestamp": scraped_at,
            "user": username,
            "post_url": link
        })
        added += 1

    logging.info(f"[X] {identifier}: appended {added} posts (cards processed: {len(cards)})")

# --- Main callable function ---
def scrape_x(hours_user=96, hours_search=720):
    """Scrape disaster-related posts from X (Twitter)."""
    logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)

    now_ph = datetime.now(PH_TIME)
    since_user = now_ph - timedelta(hours=hours_user)
    since_search = now_ph - timedelta(hours=hours_search)
    scraped_at = now_ph.strftime('%Y-%m-%d %H:%M')

    users = X["users"]
    queries = X["search_queries"]

    driver = init_driver()
    results = []

    # User timelines
    for user in users:
        url = f"https://x.com/{user}"
        logging.info(f"[x_user] Visiting {url}")
        driver.get(url)
        time.sleep(3)
        scroll_page(driver)
        cards = driver.find_elements(By.XPATH, "//article[@role='article']")
        process_x_cards(results, user, cards, since_user, scraped_at)

    # Search queries
    for query in queries:
        url = f"https://x.com/search?q={quote_plus(query)}&src=typed_query&f=live"
        logging.info(f"[x_search] Visiting {url}")
        driver.get(url)
        time.sleep(3)
        scroll_page(driver)
        cards = driver.find_elements(By.XPATH, "//article[@role='article']")
        process_x_cards(results, query, cards, since_search, scraped_at)

    driver.quit()

    df = pd.DataFrame(results)
    logging.info(f"✅ Scraped {len(df)} total posts from X")
    return df

# --- CLI mode (optional) ---
if __name__ == "__main__":
    df = scrape_x()
    out_path = RAW_DIR / "x_raw_disaster_posts.csv"
    df.to_csv(out_path, index=False)
    logging.info(f"✅ Saved to {out_path}")

