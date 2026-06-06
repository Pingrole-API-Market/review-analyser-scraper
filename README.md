# Trustpilot Review Scraper

An [Apify Actor](https://apify.com/actors) that scrapes business reviews and company details from **Trustpilot** and exports structured JSON results.

---

## Features

| Capability | Detail |
|---|---|
| **Review scraping** | Author, rating, review text, date, verified flag |
| **Company overview** | Overall rating, total reviews, star-count breakdown |
| **Company details** | Categories, description, address, phone, email, website |
| **File export** | CSV · JSON · XLSX — optional, stored in Apify Key-Value store |
| **Pagination** | Scrapes all pages up to the configured limit |

---

## Project Structure

```
/
├── src/
│   ├── main.py                   # Actor entrypoint
│   ├── scrapers/
│   │   └── trustpilot.py         # Trustpilot scraper
│   ├── exporters/
│   │   ├── csv_exporter.py
│   │   ├── json_exporter.py
│   │   └── xlsx_exporter.py
│   └── utils.py
├── .actor/
│   ├── actor.json
│   ├── input_schema.json
│   └── output_schema.json
├── requirements.txt
└── Dockerfile
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

### 2. Create local input

Create `storage/key_value_stores/default/INPUT.json`:

```json
{
  "business_name": "Joe's Pizza",
  "location": "New York, USA",
  "zip_code": "10013",
  "country": "US",
  "limit_per_platform": 50,
  "export_as_file": false,
  "export_format": "xlsx"
}
```

### 3. Run locally

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

## Input Schema

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `business_name` | string | **Yes** | — | Name of the business to scrape |
| `location` | string | No | — | City and country, e.g. `"New York, USA"` |
| `zip_code` | string | No | — | Postal code to narrow search results |
| `country` | string | No | — | ISO alpha-2 country code, e.g. `"US"` |
| `limit_per_platform` | integer | No | `100` | Max reviews to scrape (1–500) |
| `export_as_file` | boolean | No | `false` | Save a downloadable file in the Key-Value store |
| `export_format` | string | No | `"xlsx"` | `"xlsx"` \| `"csv"` \| `"json"` |

> Results are always available as a dataset (JSON in the Apify console and API) regardless of `export_as_file`.

---

## Output Schema

One dataset item per run, structured as:

```json
{
  "business_name": "Casa D'Angelo New York",
  "platform": "trustpilot",
  "overall_rating": 4.8,
  "total_reviews": 15,
  "rating_breakdown": {
    "5_star": 12,
    "4_star": 2,
    "3_star": 1,
    "2_star": 0,
    "1_star": 0
  },
  "company_info": {
    "categories": ["Italian Restaurant", "Fine Dining Restaurant", "Pizza Restaurant"],
    "description": "Casa D'Angelo – Best Italian Restaurant in Little Italy, NYC...",
    "address": "146 Mulberry Street, 10013-4708, New York City, United States",
    "phone": "2128048656",
    "email": "cangelony@gmail.com",
    "website": "https://cangelomulberry.com"
  },
  "reviews": [
    {
      "author": "Stephanie Doe",
      "author_country": "US",
      "author_total_reviews": 1,
      "rating": 5,
      "feedback_text": "One of the best pizzas I have eaten in a long time...",
      "date": "2026-04-27",
      "verified": false,
      "unprompted": true
    }
  ],
  "scraped_at": "2026-06-06T16:32:46Z"
}
```

---

## Architecture Notes

- **One shared Chromium browser** is launched in `main.py` and passed to the scraper, which uses an isolated context (separate cookies, user agent, viewport).
- **Company info** is scraped from the `/info` sub-page of each Trustpilot company profile.
- **Rating breakdown** is extracted from the page histogram as percentages and converted to counts (`round(pct% × total_reviews)`). If page extraction fails, counts are computed directly from the scraped reviews.
- **Output** is always written to the Apify dataset and the key-value store `OUTPUT` key as pretty JSON. File export (xlsx/csv/json) is optional.
