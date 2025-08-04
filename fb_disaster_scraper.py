#!/Library/Frameworks/Python.framework/Versions/3.13/bin/python3
import os
import time
import logging
from datetime import datetime, timedelta, timezone

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

import pandas as pd
from social_media_config import KEYWORDS, FACEBOOK

# Constants
PH_TIME     = timezone(timedelta(hours=8))
FB_OUT      = 'raw-data/fb_raw_disaster_posts.csv'
MERGED_OUT  = 'raw-data/merged_raw_disaster_posts.csv'

def init_driver() -> webdriver.Chrome:
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-notifications")
    options.add_argument("--window-size=1920,1080")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    )
    return webdriver.Chrome(options=options)

def scroll_page(driver, scroll_times=60, pause=1):
    last = driver.execute_script("return document.body.scrollHeight")
    for _ in range(scroll_times):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(pause)
        nxt = driver.execute_script("return document.body.scrollHeight")
        if nxt == last:
            break
        last = nxt

def expand_see_more(driver, post):
    try:
        btn = post.find_element(
            By.XPATH,
            ".//div[contains(@role,'button') and contains(text(),'See more')]"
        )
        driver.execute_script("arguments[0].click();", btn)
        time.sleep(1)
    except:
        pass

def extract_utime(post):
    try:
        raw = post.find_element(By.XPATH, ".//abbr").get_attribute("data-utime")
        return int(raw) if raw else None
    except:
        return None

def format_readable(ts):
    return ts.strftime('%A, %B %d, %Y at %I:%M %p')

def extract_caption(driver, post):
    try:
        expand_see_more(driver, post)
        blocks = post.find_elements(By.XPATH, ".//div[@dir='auto']")
        return " ".join(b.text.strip() for b in blocks if b.text.strip())
    except:
        return None

def extract_username(post):
    try:
        return post.find_element(By.XPATH, ".//h4//a").text
    except:
        return "Unknown"

def extract_post_url(driver, post):
    try:
        return post.find_element(
            By.XPATH, ".//a[contains(@href,'/posts/')]"
        ).get_attribute("href")
    except:
        return driver.current_url

def process_fb_articles(driver, results, identifier, is_search_query,
                        since_page, since_hashtag, scraped_timestamp):
    articles = driver.find_elements(By.XPATH, "//div[@role='article']")
    count = 0
    for art in articles:
        text = extract_caption(driver, art)
        if not text or not any(k in text.lower() for k in KEYWORDS):
            continue

        ut = extract_utime(art)
        if ut:
            post_time = datetime.fromtimestamp(ut, tz=PH_TIME)
            cutoff    = since_hashtag if is_search_query else since_page
            if post_time < cutoff:
                continue
            post_timestamp = format_readable(post_time)
        else:
            post_timestamp = "Unknown"

        results.append({
            'source':            'Facebook',
            'query_page':        identifier,
            'text':              text[:5000],
            'post_timestamp':    post_timestamp,
            'scraped_timestamp': scraped_timestamp,
            'user':              extract_username(art),
            'post_url':          extract_post_url(driver, art)
        })
        count += 1

    logging.info(
        f"[Facebook: {identifier}] appended {count} posts "
        f"(found {len(articles)} total articles)"
    )

def save_results(df: pd.DataFrame):
    os.makedirs(os.path.dirname(FB_OUT), exist_ok=True)

    # FB-only file
    if os.path.exists(FB_OUT):
        old_fb = pd.read_csv(FB_OUT)
        df_fb  = pd.concat([old_fb, df], ignore_index=True) \
                     .drop_duplicates(subset=['text'], keep='last')
    else:
        df_fb = df.copy()
        
    df_fb.to_csv(FB_OUT, index=False)
    logging.info(f"✅ New fb rows saved: {len(df)}")
    logging.info(f"✅ FB Total: {len(df_fb)}")

    # Merged file
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
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

    # compute time thresholds
    now_ph             = datetime.now(PH_TIME)
    since_time_page    = now_ph - timedelta(hours=24)
    since_time_hashtag = now_ph - timedelta(hours=720)
    scraped_timestamp  = now_ph.strftime('%Y-%m-%d %H:%M')

    FB_PAGES   = FACEBOOK["users"]
    FB_QUERIES = FACEBOOK["search_queries"]

    driver  = init_driver()
    results = []

    # 1) Page feeds
    for page in FB_PAGES:
        url = f"https://www.facebook.com/{page.rstrip('/')}/posts"
        logging.info(f"[fb_page] Visiting {url}")
        driver.get(url)
        time.sleep(5)
        scroll_page(driver)
        process_fb_articles(driver, results, page, False,
                            since_time_page, since_time_hashtag, scraped_timestamp)

    # 2) Hashtag feeds
    for tag in FB_QUERIES:
        url = f"https://www.facebook.com/hashtag/{tag}"
        logging.info(f"[fb_hashtag] Visiting #{tag}")
        driver.get(url)
        time.sleep(5)
        scroll_page(driver)
        process_fb_articles(driver, results, f"#{tag}", True,
                            since_time_page, since_time_hashtag, scraped_timestamp)

    # 3) Search feeds
    for query in FB_QUERIES:
        url = f"https://www.facebook.com/search/posts/?q={query}"
        logging.info(f"[fb_search] Visiting search '{query}'")
        driver.get(url)
        time.sleep(5)
        scroll_page(driver)
        process_fb_articles(driver, results, query, True,
                            since_time_page, since_time_hashtag, scraped_timestamp)

    driver.quit()

    # save everything
    df = pd.DataFrame(results)
    save_results(df)

if __name__ == "__main__":
    main()