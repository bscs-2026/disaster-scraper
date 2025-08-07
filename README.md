# Disaster Resilience Data Scraper & Cleaning Pipeline

> **Disaster-Resilience Chatbot** backend data-collection and preprocessing  
> Collects real-time social-media posts about floods, landslides, earthquakes, typhoons, fires, etc., then normalizes and cleans them for downstream RAG + LLM use.


## Features

- 🔍 **Multiplatform scraping**: Facebook, X, TikTok(discontinued)  
- 🗄️ **CSV output**: raw & merged data in `data/raw-data/`  
- 🧹 **Cleaning & formatting**: text normalization, date extraction, column standardization  
- ⚙️ **Configurable sources** via `social_media_config.py`  

---

## Prerequisites

- Python 3.8+  
- Chrome Driver (for Selenium)  
- A Git client

---

## Installation

```bash
# 1. Clone this repo
git clone https://github.com/your-org/disaster-scraper.git
cd disaster-scraper

# 2. Create & activate virtual environment
python3 -m venv .venv
source .venv/bin/activate    # macOS/Linux
.\.venv\Scripts\activate     # Windows

# 3. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

