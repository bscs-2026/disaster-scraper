# 🌊 Disaster-Scraper

**Automated Social Media Data Pipeline for Disaster Monitoring and Analysis**

This repository powers the **DisasterReady AI Chatbot** dataset pipeline — an end-to-end system that scrapes, cleans, and processes social-media posts (Facebook, X/Twitter) for disaster-related content in the Philippines. It integrates **XLM-RoBERTa-based NER** for extracting locations and datetimes, plus **zero-shot classification** for disaster type labeling.

---

## 🧩 Pipeline Overview

```
1️⃣ Scrape → 2️⃣ NER (Location, Datetime) → 3️⃣ Cleaning → 4️⃣ Classification → 5️⃣ Output
```

## Each phase can be executed independently or end-to-end using `run_full_pipeline.py`.

## 📁 Repository Structure

```
disaster-scraper/
├── data/
│   ├── raw/          # raw scraped CSVs (Facebook/X)
│   ├── interim/      # intermediate outputs (NER, cleaned, partial)
│   ├── processed/    # final processed datasets (for QDRANT DB)
│   └── lookup/       # PSGC or other lookup tables
│
├── src/
│   ├── scraping/     # scrapers and API configs
│   │   ├── fb_disaster_scraper.py
│   │   ├── x_disaster_scraper.py
│   │   └── social_media_config.py
│   │
│   ├── ner/          # Named Entity Recognition modules
│   │   ├── extract_location.py
│   │   ├── extract_datetime.py
│   │   └── classify_disaster.py
│   │
│   ├── preprocessing/
│   │   ├── clean_text.py
│   │   ├── extract_pagesource.py
│   │   ├── location_filter.py
│   │   ├── format_columns.py
│   │   ├── drop_tail_near_duplicates.py
│   │   └── data_cleaning_pipeline.py
│   │
│   ├── utils/
│   │   ├── run_full_pipeline.py
│   │   └── test_extract_datetime.py
│
├── requirements.txt
├── .gitignore
└── README.md
```

---

## ⚙️ Setup & Installation

### Clone the repository and install dependencies

```bash
git clone https://github.com/<yourusername>/disaster-scraper.git
cd disaster-scraper
```

---

## 🚀 Running the Pipeline

### 🔹 Run the entire end-to-end pipeline

```bash
python3 src/utils/run_full_pipeline.py
```

### 🔹 Skip specific phases

```bash
example: datetime extraction only
python3 src/utils/run_full_pipeline.py --skip-scrape --skip-ner-loc --skip-clean --skip-classify
```

| Flag                  | Effect                                 |
| --------------------- | -------------------------------------- |
| `--skip-scrape`       | Uses existing CSVs instead of scraping |
| `--skip-ner-loc`      | Skips location extraction              |
| `--skip-ner-datetime` | Skips datetime extraction              |
| `--skip-clean`        | Skips text cleaning and filtering      |
| `--skip-classify`     | Skips disaster-type classification     |

---

## 🤖 Models Used

| Function                | Model                             | Source      |
| ----------------------- | --------------------------------- | ----------- |
| Location Extraction     | `Davlan/xlm-roberta-base-ner-hrl` | HuggingFace |
| Datetime Extraction     | `programmersilvanus/ner-xlmr`     | HuggingFace |
| Disaster Classification | `joeddav/xlm-roberta-large-xnli`  | HuggingFace |

---

## 📊 Output Columns

| Column               | Description                   |
| -------------------- | ----------------------------- |
| `source`             | Platform (Facebook/X)         |
| `text_content`       | Cleaned post text             |
| `event_time_primary` | Normalized datetime           |
| `location`           | Extracted Philippine location |
| `disaster_type`      | Predicted disaster category   |
| `url`                | Post source link              |
