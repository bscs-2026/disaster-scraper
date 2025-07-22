
import os
import time
import logging
from datetime import datetime, timedelta, timezone
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import pandas as pd

# Logging 
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

# Timezone & Thresholds 
PH_TIME            = timezone(timedelta(hours=8))
now_ph             = datetime.now(PH_TIME)
since_time_page    = now_ph - timedelta(hours=24)  # last 24h for pages
since_time_hashtag = now_ph - timedelta(hours=48)  # last 48h for hashtags
scraped_at         = now_ph.strftime('%Y-%m-%d %H:%M')

# Facebook Pages & Hashtags 
PAGES = [
    'abscbnNEWS', 'rapplerdotcom', 'gmanews',
    'manilabulletin', 'sunstarphilippines', 'PhilstarNews',
    'inquirerdotnet', 'pagasa.dost.gov.ph', 'davaocitydrmmc',
    'NDRRMC', 'UNTVNewsRescue', 'PIAgovernment', 'DavaoDRRMO',
    'sunstardavaonews', 'profile.php?id=61568208630146', 'PHIVOLCS'
]

HASHTAGS = [
    'FloodAlert', 'BahaPH', 'StreetFloodAlert',
    'LandslideAlert', 'FireAlert', 'EarthquakeAlert', 'EarthquakePH'
]

# Keywords for Filtering 
KEYWORDS = [
    '#FloodAlert', '#BahaPH', '#StreetFloodAlert',
    '#LandslideAlert', '#FireAlert', '#EarthquakeAlert', '#EarthquakePH',

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

# === Chrome Driver Setup ===
options = Options()
options.add_argument("--headless=new")
options.add_argument("--disable-gpu")
options.add_argument("--disable-notifications")
options.add_argument("--window-size=1920,1080")
options.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)
driver = webdriver.Chrome(options=options)


# === Helper Functions ===
def scroll_page(scroll_times=15):
    last = driver.execute_script("return document.body.scrollHeight")
    for _ in range(scroll_times):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)
        nxt = driver.execute_script("return document.body.scrollHeight")
        if nxt == last:
            break
        last = nxt

def expand_see_more(post):
    try:
        btn = post.find_element(By.XPATH,
             ".//div[contains(@role,'button') and contains(text(),'See more')]")
        driver.execute_script("arguments[0].click();", btn)
        time.sleep(1)
    except:
        pass

def extract_utime(elem):
    try:
        raw = elem.find_element(By.XPATH, ".//abbr").get_attribute("data-utime")
        return int(raw) if raw else None
    except:
        return None

def format_readable(ts):
    return ts.strftime('%A, %B %d, %Y at %I:%M %p')

def extract_caption(post):
    try:
        expand_see_more(post)
        blocks = post.find_elements(By.XPATH, ".//div[@dir='auto']")
        return " ".join(b.text.strip() for b in blocks if b.text.strip())
    except:
        return None

def extract_username(post):
    try:
        return post.find_element(By.XPATH, ".//h4//a").text
    except:
        return "Unknown"

def extract_post_url(post):
    try:
        return post.find_element(
            By.XPATH, ".//a[contains(@href,'/posts/')]"
        ).get_attribute("href")
    except:
        return driver.current_url


# Core Processing 
results = []

def process_articles(source_type, identifier, is_hashtag=False):
    articles = driver.find_elements(By.XPATH, "//div[@role='article']")
    logging.info(f"[{source_type}] {identifier}: found {len(articles)} articles")
    count = 0

    for art in articles:
        text = extract_caption(art)
        if not text:
            continue

        low = text.lower()

        # region filter only for hashtags
        if is_hashtag and ('davao' not in low and 'philippines' not in low):
            continue

        if not any(k in low for k in KEYWORDS):
            continue

        ut = extract_utime(art)
        if ut:
            post_time = datetime.fromtimestamp(ut, tz=PH_TIME)
            # apply different thresholds
            cutoff = since_time_hashtag if is_hashtag else since_time_page
            if post_time < cutoff:
                continue
            time_str = format_readable(post_time)
        else:
            time_str = "Unknown"

        user = extract_username(art)
        url  = extract_post_url(art)

        results.append({
            'Source':       source_type,
            'Query/Page':   identifier,
            'Text':         text[:5000],
            'Post Timestamp':      time_str,
            'Scraped Timestamp':   scraped_at,
            'User':         user,
            'Post URL':     url
        })
        count += 1

    logging.info(f"[{source_type}] {identifier}: appended {count} posts")


# MAIN LOOP

# 1) Scrape each page's /posts feed
for pg in PAGES:
    feed_url = f"https://www.facebook.com/{pg.rstrip('/')}/posts" 
    logging.info(f"*** Scraping PAGE feed: {feed_url}")
    driver.get(feed_url)
    time.sleep(5)
    scroll_page()
    process_articles("Page", pg, is_hashtag=False)

# 2) Scrape each hashtag page
for tag in HASHTAGS:
    tag_url = f"https://www.facebook.com/hashtag/{tag}"
    logging.info(f" - Searching hashtag: #{tag}")
    driver.get(tag_url)
    time.sleep(5)
    scroll_page()
    process_articles("Hashtag", f"#{tag}", is_hashtag=True)

driver.quit()

# === Save to CSV ===
df = pd.DataFrame(results)
out = 'raw-data/fb_raw_disaster_posts.csv'

if os.path.exists(out):
    old = pd.read_csv(out)
    # combine old + new, then drop rows with duplicate Text (keep latest)
    df = pd.concat([old, df], ignore_index=True) \
           .drop_duplicates(subset=['Text'], keep='last')

df.to_csv(out, index=False)
logging.info(f"✅ Done! rows saved: {len(df)}")
