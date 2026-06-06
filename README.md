# Business Review Analyser & Sentiment Extractor

An [Apify Actor](https://apify.com/actors) that scrapes business reviews from **Trustpilot** and **Yelp**, runs **HuggingFace sentiment analysis**, detects fake reviews, and exports structured intelligence reports.

---

## Features

| Capability | Detail |
|---|---|
| **Multi-platform scraping** | Trustpilot · Yelp |
| **Sentiment analysis** | `cardiffnlp/twitter-roberta-base-sentiment` — loaded once, batched, INT8-quantised |
| **Fake review detection** | Short text · burst posting · generic filler rules |
| **Topic extraction** | Top keywords · complaints · praises |
| **Export** | CSV · JSON · XLSX — stored in Apify Key-Value store |
| **Discord notification** | Summary embed + file attachment via webhook |
| **Fault isolation** | One platform failing never stops the other |

---

## Project Structure

```
/
├── src/
│   ├── main.py                   # Actor entrypoint
│   ├── scrapers/
│   │   ├── trustpilot.py         # Trustpilot reviews
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
│   └── utils.py
├── .actor/
│   ├── actor.json
│   ├── input_schema.json
│   └── output_schema.json
├── requirements.txt
├── Dockerfile
└── .env.example
```

---

## Setup

### Prerequisites

- Python 3.12+
- [Apify CLI](https://docs.apify.com/cli) (for local runs) or an Apify account (for cloud runs)

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
# Edit .env — set APIFY_TOKEN for local runs
```

### 3. Create local input

Create `storage/key_value_stores/default/INPUT.json`:

```json
{
  "business_name": "Joe's Pizza",
  "location": "Berlin, Germany",
  "zip_code": "12167",
  "country": "DE",
  "platforms": ["trustpilot", "yelp"],
  "limit_per_platform": 50,
  "export_as_file": true,
  "export_format": "xlsx"
}
```

### 4. Run locally

```bash
python -m src.main
```

---

## Running on Apify Cloud

```bash
apify login
apify push
```

---

## Input Schema Reference

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `business_name` | string | **Yes** | — | Name of the business |
| `location` | string | No | — | City and country, e.g. `"Berlin, Germany"` |
| `zip_code` | string | No | — | Postal code |
| `country` | string | No | — | ISO alpha-2 country code |
| `platforms` | array | No | both | `["trustpilot", "yelp"]` |
| `limit_per_platform` | integer | No | `100` | Max reviews per platform (1–500) |
| `export_as_file` | boolean | No | `false` | Generate a downloadable file in Key-Value store |
| `export_format` | string | No | `"xlsx"` | `"xlsx"` \| `"csv"` \| `"json"` |
| `discord_webhook` | string | No | — | Discord webhook URL |

> **Note:** Results are always available as a dataset (table in Apify console, JSON via API) regardless of `export_as_file`. The file export is additive.

---

## Output Schema

```json
{
  "business_name": "Joe's Pizza",
  "location": "Berlin, Germany, 12167, DE",
  "platforms_scraped": ["trustpilot", "yelp"],
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
  "export_file_url": "https://api.apify.com/...",
  "reviews": [
    {
      "platform": "trustpilot",
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
  "scraped_at": "2026-06-06T14:22:01Z"
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

## Discord Notification

When `discord_webhook` is set the actor sends:

- An embed with: business name, overall sentiment, avg rating, rating trend, sentiment breakdown, fake risk, top 3 complaints, top 3 praises, and a download link (when `export_as_file=true`)
- The export file attached to the message (when `export_as_file=true`)

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `APIFY_TOKEN` | Cloud auto-set | Required for local `apify run` |

---

## Architecture Notes

- **One shared Chromium browser** is launched in `main.py` and passed to each scraper. Platforms run sequentially — each gets an isolated context (separate cookies, user agent, viewport), then closes it. This keeps peak memory to ~model + one browser.
- **Sentiment model** is quantised to INT8 on CPU (~125 MB vs ~500 MB FP32), loaded once, and reused via `analyse_batch()`.
- **HuggingFace offline mode** (`TRANSFORMERS_OFFLINE=1`) is set in the Dockerfile after the model is pre-baked, so no network calls to HF Hub at runtime.
