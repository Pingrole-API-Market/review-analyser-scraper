# Trustpilot Review Scraper

Extract **business reviews, ratings, and company details** from [Trustpilot](https://www.trustpilot.com) — no coding required. Simply enter a business name and location, and the scraper delivers structured JSON results directly in the Apify dataset, ready to download or connect to your workflows.

---

## What does Trustpilot Review Scraper do?

**Trustpilot Review Scraper** is an Apify Actor that automatically scrapes public business reviews from Trustpilot. It collects the full review text, star ratings, reviewer details, and company profile information — and packages it all as clean, structured JSON.

🔍 Provide a **business name** and an optional **location** — the Actor finds the right Trustpilot profile and extracts everything automatically.

---

## What can Trustpilot Review Scraper extract?

- ⭐ Overall rating and star-count breakdown (1–5 stars)
- 📝 Full review text, title-free and clean
- 👤 Reviewer name, country, and total reviews on their profile
- 📅 Review date
- ✅ Verified purchase flag and unprompted review flag
- 🏢 Company categories, description written by the business
- 📍 Business address, phone number, email, and website
- 📊 Total review count directly from Trustpilot

### Data you can extract from Trustpilot

| Field | Description |
|---|---|
| `overall_rating` | Average star rating on the platform (e.g. `4.8`) |
| `total_reviews` | Total number of reviews on Trustpilot |
| `rating_breakdown` | Count of 1 ⭐ through 5 ⭐ reviews |
| `company_info.categories` | Business category tags (e.g. `Italian Restaurant`) |
| `company_info.address` | Physical address of the business |
| `company_info.phone` | Phone number |
| `company_info.email` | Contact email |
| `company_info.website` | Business website URL |
| `reviews[].author` | Reviewer display name |
| `reviews[].author_country` | Reviewer's country |
| `reviews[].rating` | Star rating (1–5) |
| `reviews[].feedback_text` | Full review text |
| `reviews[].date` | Review date (YYYY-MM-DD) |
| `reviews[].verified` | Whether the review is marked as verified |

---

## Why use Trustpilot Review Scraper?

Trustpilot does not provide a free public API for bulk review access. This Actor is a reliable alternative that:

- 🚀 Runs in the cloud — no setup, no servers, no browser needed on your end
- 🔄 Integrates with **Zapier, Make, Google Sheets**, and hundreds of other tools via the Apify platform
- 📅 Can be **scheduled** to run automatically (daily, weekly, or any custom interval)
- 📡 Results are instantly accessible via the **Apify API** for programmatic use
- 💾 Supports export to **JSON, CSV, and XLSX** with a single checkbox
- 🔍 Built-in **proxy rotation** ensures reliable scraping at scale

---

## How to scrape Trustpilot reviews

1. **Open** the Actor on [Apify Store](https://apify.com/store) and click **Try for free**
2. **Enter** the business name (e.g. `Joe's Pizza`) and an optional location (e.g. `New York, USA`)
3. **Set** the review limit — how many reviews to collect (default: 100, max: 500)
4. **Enable** file export (optional) if you want a downloadable XLSX or CSV file
5. **Click Run** — results appear in the Output tab within seconds to a few minutes
6. **Download** the dataset as JSON, CSV, or Excel — or connect it to your tools via the API

---

## How much does it cost to scrape Trustpilot?

Trustpilot Review Scraper runs on **Apify's consumption-based pricing** (Compute Units). A typical run scraping **50–100 reviews** costs approximately **$0.005–$0.01** — well within the **free $5 monthly credit** every Apify account receives.

You can run this Actor **for free** dozens of times per month on the free plan. For high-volume or scheduled use, Apify's paid plans start at $49/month with generous CU allowances.

> 💡 To estimate your cost: go to the Actor's **Costs & limits** section before running, or check the CU usage after your first run in the **Log** tab.

---

## Input

The Actor has a simple, no-code input form. Key fields:

| Field | Required | Default | Description |
|---|---|---|---|
| `business_name` | **Yes** | — | Name of the business to look up on Trustpilot |
| `location` | No | — | City and country to narrow the search (e.g. `New York, USA`) |
| `zip_code` | No | — | Postal code for more precise matching |
| `country` | No | — | ISO alpha-2 country code (e.g. `US`, `DE`, `GB`) |
| `limit_per_platform` | No | `100` | Maximum number of reviews to scrape (1–500) |
| `export_as_file` | No | `false` | Also save a downloadable file to Key-Value store |
| `export_format` | No | `xlsx` | File format: `xlsx`, `csv`, or `json` |

---

## Output example

Results are always available in the **Output** tab as pretty JSON. Here is a sample:

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
      "feedback_text": "One of the best pizzas I have eaten in a long time. Totally worth it.",
      "date": "2026-04-27",
      "verified": false,
      "unprompted": true
    },
    {
      "author": "Doroth P.",
      "author_country": "US",
      "author_total_reviews": 1,
      "rating": 3,
      "feedback_text": "Food was super yummy, but the service wasn't the best.",
      "date": "2025-12-09",
      "verified": false,
      "unprompted": true
    }
  ],
  "scraped_at": "2026-06-06T16:32:46Z"
}
```

You can download the full dataset in **JSON, CSV, or Excel** format from the Storage tab, or access it programmatically via the Apify API.

---

## Is it legal to scrape Trustpilot?

This scraper only collects **publicly available** information that any visitor can see on Trustpilot without logging in — review text, star ratings, and business profile details. No private user data, passwords, or email addresses are accessed.

We believe using this Actor for legitimate business purposes (competitor research, reputation monitoring, sentiment analysis) is safe. That said, you should be aware that scraped review data may contain personal names. If you operate under GDPR or similar regulations, ensure your use case has a valid legal basis for processing that data.

> For more context, see [Apify's blog post on the legality of web scraping](https://blog.apify.com/is-web-scraping-legal/).

---

## FAQ

**The Actor found the wrong business — what do I do?**
Add a more specific `location` (city, country) and/or `country` code to narrow the Trustpilot search. The scraper picks the first result, so a precise name + location usually resolves ambiguity.

**Why is `overall_rating` or `rating_breakdown` null?**
These are scraped from the Trustpilot overview page. If the page structure differs or loads slowly, they may fall back to values computed from the scraped reviews themselves (which is still accurate for the reviews collected).

**Can I scrape more than 500 reviews?**
The limit is currently capped at 500 per run. For larger datasets, you can run the Actor multiple times or contact us to discuss a custom solution.

**Where do I find the export file?**
When `export_as_file` is enabled, the file is saved to the **Storage → Key-Value Store** tab of your run. You'll find a public download link there.

**How do I schedule automatic runs?**
In the Apify Console, open the Actor, go to **Schedules**, and set any cron-based interval (daily, weekly, etc.).

---

## Support

Found a bug or have a feature request? Open an issue in the **Issues** tab on this Actor's page — feedback is always welcome. We're also open to building custom scraping solutions based on this Actor.
