# Business Review Analyser & Sentiment Extractor

An [Apify Actor](https://apify.com/actors) that scrapes business reviews from **Google Maps**, **Trustpilot**, **Glassdoor**, and **Yelp**, runs **HuggingFace sentiment analysis**, detects fake reviews, and exports structured intelligence reports.

---

## Features

| Capability | Detail |
|---|---|
| **Multi-platform scraping** | Google Maps · Trustpilot · Glassdoor · Yelp |
| **Sentiment analysis** | `cardiffnlp/twitter-roberta-base-sentiment` (loaded once, batched) |
| **Fake review detection** | Short text · burst posting · generic filler rules |
| **Topic extraction** | Top keywords · complaints · praises |
| **Export** | CSV · JSON · XLSX — stored in Apify Key-Value store |
| **Discord notification** | Summary embed + file attachment via webhook |
| **MongoDB persistence** | Upsert by composite key, no duplicates |
| **Fault isolation** | One platform failure never stops others |

---

## Project Structure

```
/
├── src/
│   ├── main.py                   # Actor entrypoint
│   ├── scrapers/
│   │   ├── google.py             # Google Maps reviews
│   │   ├── trustpilot.py         # Trustpilot reviews
│   │   ├── glassdoor.py          # Glassdoor company reviews
│   │   └── yelp.py               # Yelp reviews
│   ├── analyser/
│   │   ├── sentiment.py          # HuggingFace sentiment pipeline
│   │   ├── topics.py             # Keyword & topic extraction
│   │   └── fake_detector.py      # Fake review detection
│   ├── exporters/
│   │   ├── csv_exporter.py
│   │   ├── json_exporter.py
│   │   ├── xlsx_exporter.py
│   │   └── discord.py            # Discord webhook delivery
│   ├── storage.py                # MongoDB handler
│   └── utils.py                  # User agents, retry, helpers
├── actor.json                    # Apify Actor manifest
├── input_schema.json             # Actor input schema
├── requirements.txt
├── Dockerfile
└── .env.example
```

---

## Setup

### Prerequisites

- Python 3.12+
- MongoDB instance (optional — actor runs without it, storage is skipped)
- Apify account (for cloud runs) or [Apify CLI](https://docs.apify.com/cli) (for local runs)

### 1. Clone & install

```bash
git clone <repo-url>
cd review-analyser-scraper

python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env — set MONGODB_URI and APIFY_TOKEN
```

### 3. Create local input

Create `INPUT.json` in the project root (Apify CLI picks this up automatically):

```json
{
  "business_name": "Joe's Pizza",
  "location": "Berlin, Germany",
  "zip_code": "12167",
  "country": "DE",
  "platforms": ["google", "trustpilot"],
  "limit_per_platform": 50,
  "export": true,
  "export_format": "csv",
  "discord_webhook": ""
}
```

### 4. Run locally

```bash
apify run
```

Or directly with Python (without Apify CLI):

```bash
python -m src.main
```

---

## Running on Apify Cloud

### Push & deploy

```bash
apify login
apify push
```

### Configure via Apify Console

Set the `MONGODB_URI` environment variable under **Actor → Settings → Environment variables**.

---

## Input Schema Reference

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `business_name` | string | **Yes** | — | Name of the business |
| `location` | string | No | — | City and country |
| `zip_code` | string | No | — | Postal code |
| `country` | string | No | — | ISO alpha-2 country code |
| `platforms` | array | No | all | `["google","trustpilot","glassdoor","yelp"]` |
| `limit_per_platform` | integer | No | `100` | Max reviews per platform (1–500) |
| `export` | boolean | No | `true` | Generate downloadable export file |
| `export_format` | string | No | `"csv"` | `"csv"` \| `"json"` \| `"xlsx"` |
| `discord_webhook` | string | No | — | Discord webhook URL for notification |

---

## Output Schema

```json
{
  "business_name": "Joe's Pizza",
  "location": "Berlin, Germany, 12167, DE",
  "platforms_scraped": ["google", "trustpilot"],
  "total_reviews_analysed": 142,
  "overall_sentiment": "neutral",
  "sentiment_breakdown": {
    "positive": 58,
    "neutral": 23,
    "negative": 19
  },
  "rating_trend": "declining",
  "average_rating": 3.6,
  "top_complaints": ["slow", "cold", "rude"],
  "top_praises": ["great", "friendly", "fresh"],
  "top_keywords": ["pizza", "service", "wait", "price", "staff"],
  "fake_review_risk": "low",
  "fake_review_count": 4,
  "reviews": [
    {
      "platform": "google",
      "author": "John D.",
      "rating": 2,
      "text": "Waited 45 minutes for cold pizza.",
      "date": "2026-04-10",
      "sentiment": "negative",
      "sentiment_score": 0.9312,
      "topics": ["wait time", "food quality"],
      "is_fake_flag": false
    }
  ],
  "scraped_at": "2026-06-05T14:22:01Z"
}
```

---

## Fake Review Detection Rules

A review is flagged when **any** of the following are true:

1. **Short text** — fewer than 10 words
2. **Rating-only** — 5-star or 1-star with no text
3. **Generic filler** — text matches a known filler phrase with ≤3 additional words
4. **Author burst** — same author posted ≥3 reviews within a 7-day window in the scraped batch

---

## MongoDB Collections

| Collection | Purpose |
|---|---|
| `review_analyser.reviews` | Raw + annotated individual reviews (upsert, no duplicates) |
| `review_analyser.analysed_results` | Aggregated per-run output (without the `reviews` array) |

Composite unique index on `reviews`: `(platform, author, date, text_hash)`.

---

## Discord Notification

When `discord_webhook` is provided the actor sends:

- An embed with: business name, overall sentiment, avg rating, rating trend, sentiment breakdown, fake risk, top 3 complaints, top 3 praises, and a download link (if `export=true`)
- The export file attached directly to the message

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `MONGODB_URI` | No | Full MongoDB connection string. Actor runs without it (storage skipped). |
| `APIFY_TOKEN` | Cloud auto-set | Required for local `apify run` |

---

## Architecture Notes

- **Sentiment model** is instantiated once in `main.py` and shared across all reviews via `analyse_batch()` — no repeated model loading.
- **Platform scrapers** run concurrently with `asyncio.gather(..., return_exceptions=True)` — a crash in one platform is caught and logged without aborting others.
- **Retry logic** (3 attempts, exponential back-off) wraps the outer scrape call per platform.
- **Rotating user agents** and randomised delays are applied per request inside each scraper.
- **Playwright** runs in headless Chromium; the Docker image pre-installs the browser and pre-downloads the model to avoid cold-start latency.
