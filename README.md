<p align="center">
  <img src="https://cdn.trustpilot.net/brand-assets/4.3.0/logo-black.svg" alt="Trustpilot logo" width="220" />
</p>

<p align="center">
  <a href="https://apify.com"><img src="https://img.shields.io/badge/Platform-Apify-2463EB?logo=apify&logoColor=white" alt="Apify platform" /></a>
  <a href="https://www.python.org"><img src="https://img.shields.io/badge/Python-3.12+-3776AB?logo=python&logoColor=white" alt="Python" /></a>
  <a href="https://www.trustpilot.com"><img src="https://img.shields.io/badge/Source-Trustpilot-00B67A?logo=trustpilot&logoColor=white" alt="Trustpilot" /></a>
  <img src="https://img.shields.io/badge/Output-XLSX%20%7C%20CSV%20%7C%20JSON-059669" alt="Output formats" />
  <img src="https://img.shields.io/badge/Delivery-Email%20%26%20Discord-5865F2?logo=discord&logoColor=white" alt="Email and Discord delivery" />
  <img src="https://img.shields.io/badge/API-apify--client-F59E0B" alt="Apify API" />
</p>

<p align="center">
  <strong>Scrape Trustpilot reviews — get results in Apify, your inbox, or Discord.</strong><br/>
  No coding required. Enter a <strong>business name</strong>, optionally enable <strong>file delivery</strong>, and receive a report as <strong>XLSX, CSV, or JSON</strong>.
</p>

---

## What does Trustpilot Review Scraper do?

**Trustpilot Review Scraper** is an [Apify Actor](https://apify.com) that extracts public **business reviews, ratings, and company details** from [Trustpilot](https://www.trustpilot.com). There is no official free Trustpilot API for bulk review access — this Actor is a reliable, cloud-based alternative.

Enter a **business name** and optional **location**. The Actor finds the right Trustpilot profile, scrapes reviews, and saves structured JSON to your Apify dataset. Optionally, it **emails or Discord-DMs the full report file** to you — in **Excel, CSV, or JSON** format.

> **Headline feature:** turn on **Send Results as File** and choose **Email** or **Discord** as your destination. No manual download step.

---

## How it works

<p align="center">
  <img
    src="https://raw.githubusercontent.com/Pingrole-API-Market/review-analyser-scraper/main/docs/how-it-works.svg"
    alt="Flow: User request → Trustpilot scrape → Apify dataset → Email or Discord delivery"
    width="100%"
  />
</p>

<table align="center">
  <tr>
    <td align="center"><strong>1. User Request</strong><br/>Business name, limit, file format, email or Discord</td>
    <td align="center">→</td>
    <td align="center"><strong>2. Trustpilot</strong><br/>Find profile, scrape reviews, company details</td>
    <td align="center">→</td>
    <td align="center"><strong>3. Apify</strong><br/>Save JSON dataset, build XLSX / CSV / JSON file</td>
    <td align="center">→</td>
    <td align="center"><strong>4. Delivery</strong><br/>Email attachment or Discord DM</td>
  </tr>
</table>

| Step | What happens |
|---|---|
| 1 | You submit a business name, location, and optional delivery settings |
| 2 | The Actor searches [Trustpilot](https://www.trustpilot.com) and scrapes reviews + company info |
| 3 | Results are saved to your **Apify dataset** (always available via Console or API) |
| 4 | If enabled, a report file is built and **sent to your email or Discord** |

---

## Send reports by Email or Discord

This Actor can **deliver the scraped report directly to you** — no need to pull files from storage.

| | 📧 Email | 💬 Discord |
|---|---|---|
| **How it works** | Report attached to an email | Bot sends a DM with the file attached |
| **Formats** | XLSX · CSV · JSON | XLSX · CSV · JSON |
| **You provide** | Your email address | Your Discord username |
| **Setup** | Actor secrets for Office365 SMTP | Join the [Pingrole server](https://discord.gg/p5aCRvkHWE) first |

**Enable delivery in three clicks:**

1. ✅ **Send Results as File** (`get_as_file`)
2. 📁 Pick **File Format** — `xlsx`, `csv`, or `json`
3. 📬 Set **Destination** — `email` or `discord` + your address/username

Results always appear in the Apify **dataset** and **Output** tab. The file is **sent to you** — not stored for download in Key-Value storage. If delivery fails, the scrape still succeeds; check `delivery_status` in Output for details.

---

## What can Trustpilot Review Scraper do?

- ⭐ Extract overall rating and star-count breakdown (1–5 stars)
- 📝 Scrape full review text, reviewer name, country, and date
- 🏢 Collect company categories, description, address, phone, email, and website
- 📁 **Send reports by email or Discord** in XLSX, CSV, or JSON
- 📅 Schedule runs daily, weekly, or on any custom interval
- 🔌 Connect to **Zapier, Make, Google Sheets**, and 800+ tools via Apify
- 🐍 Access data programmatically with the **Apify API** and Python client
- 🔄 Built-in **proxy rotation** for reliable cloud scraping

### What data can you extract from Trustpilot?

| Field | Description |
|---|---|
| `overall_rating` | Average star rating (e.g. `4.8`) |
| `total_reviews` | Total review count on Trustpilot |
| `rating_breakdown` | Count of 1–5 star reviews |
| `company_info.categories` | Business category tags |
| `company_info.address` | Physical address |
| `company_info.phone` | Phone number |
| `company_info.email` | Contact email |
| `company_info.website` | Business website URL |
| `reviews[].author` | Reviewer display name |
| `reviews[].author_country` | Reviewer's country |
| `reviews[].rating` | Star rating (1–5) |
| `reviews[].feedback_text` | Full review text |
| `reviews[].date` | Review date (YYYY-MM-DD) |
| `reviews[].verified` | Verified review flag |

---

## Why use Trustpilot Review Scraper?

Trustpilot does not offer a free public API for bulk review extraction. This Actor gives you:

| Advantage | Benefit |
|---|---|
| ☁️ **Apify cloud** | No servers, no browser setup, runs on Apify infrastructure |
| 📧 **Email delivery** | Get an XLSX/CSV/JSON attachment in your inbox |
| 💬 **Discord delivery** | Receive the report as a DM — great for teams |
| ⏰ **Scheduling** | Monitor reputation automatically on a cron schedule |
| 🔗 **Integrations** | Pipe data into your stack via webhooks, API, or exports |
| 💰 **Free tier** | Dozens of runs per month within Apify's $5 free credit |

Use cases: **competitor research**, **reputation monitoring**, **sentiment analysis**, **market research**, and **lead qualification**.

---

## How to scrape Trustpilot reviews

1. Open this Actor on [Apify Store](https://apify.com/store) and click **Try for free**
2. Enter a **business name** (e.g. `Casa D' Angelo New York`) and optional **location**
3. Set **Reviews Limit** (default 100, max 500)
4. *(Optional)* Enable **Send Results as File** → pick format → choose **Email** or **Discord**
5. Click **Run** — results appear in seconds to a few minutes
6. View JSON in the Output tab, use the **API**, or check your **email / Discord** for the file

> Configure input fields in the **[Input tab](https://console.apify.com)** — hover tooltips explain each option.

---

## How much does it cost to scrape Trustpilot?

Trustpilot Review Scraper uses **Apify consumption-based pricing** (Compute Units). A typical run scraping **50–100 reviews** costs roughly **$0.005–$0.01** — well within the **free $5 monthly credit** every Apify account receives.

| Plan | What you get |
|---|---|
| **Free** | ~$5/month in credits — enough for dozens of runs |
| **Paid** | From $49/month with higher CU limits for scheduled / high-volume use |

> Check **Costs & limits** before your first run, or review CU usage in the **Log** tab afterwards.

---

## Input

| Field | Required | Default | Description |
|---|---|---|---|
| `business_name` | **Yes** | — | Business to look up on Trustpilot |
| `location` | No | — | City and country (e.g. `New York, USA`) |
| `zip_code` | No | — | Postal code for precise matching |
| `country` | No | `US` | ISO alpha-2 country code |
| `limit_per_platform` | No | `100` | Max reviews to scrape (1–500) |
| `get_as_file` | No | `false` | Send report file by email or Discord |
| `export_format` | No | `xlsx` | `xlsx`, `csv`, or `json` |
| `destination_platform` | No | `email` | `email` or `discord` |
| `destination_address` | When sending | — | Email address or Discord username |

### Example — Excel report by email

```json
{
  "business_name": "Casa D' Angelo New York",
  "location": "New York, USA",
  "limit_per_platform": 50,
  "get_as_file": true,
  "export_format": "xlsx",
  "destination_platform": "email",
  "destination_address": "you@example.com"
}
```

### Example — CSV report via Discord DM

```json
{
  "business_name": "Casa D' Angelo New York",
  "location": "New York, USA",
  "limit_per_platform": 50,
  "get_as_file": true,
  "export_format": "csv",
  "destination_platform": "discord",
  "destination_address": "your_discord_username"
}
```

For Discord, join the [Pingrole server](https://discord.gg/p5aCRvkHWE) first so the bot can find your username.

### Delivery secrets (Actor owner)

Configure in Apify Console → **Settings → Secrets**:

| Secret | Purpose |
|---|---|
| `PINGROLE_EMAIL` | Office365 sender address |
| `PINGROLE_PASSWORD` | Office365 SMTP password |
| `DISCORD_TOKEN` | Discord bot token for DMs |
| `DISCORD_INFRA_CHANNEL_ID` | Channel ID to resolve guild for member lookup |
| `DISCORD_WEBHOOK_URL` | Optional — alerts on delivery failure |

---

## Extract Trustpilot data in Python

Use the **[Apify API](https://docs.apify.com/api/v2)** and `apify-client` to run the Actor programmatically. Full example: [`run_client.py`](run_client.py).

```python
import os
from apify_client import ApifyClient

client = ApifyClient(os.environ["APIFY_API_TOKEN"])

run_input = {
    "business_name": "Casa D' Angelo New York",
    "location": "New York, USA",
    "limit_per_platform": 50,
    "get_as_file": True,
    "export_format": "xlsx",
    "destination_platform": "email",
    "destination_address": "you@example.com",
}

run = client.actor("oyxxsUyPX6Oa4P2h0").call(run_input=run_input)

for item in client.dataset(run.default_dataset_id).iterate_items():
    print(item)

output = client.key_value_store(run.default_key_value_store_id).get_record("OUTPUT")
print(output["value"].get("delivery_status"))
```

The file is **sent inside the Actor** (email or Discord). Your Python client reads dataset results and checks `delivery_status` to confirm delivery.

---

## Output example

Download dataset items as **JSON, CSV, or Excel** from the Storage tab, or access them via the **API**. When file delivery is enabled, `delivery_status` confirms the email or Discord send:

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
    "categories": ["Italian Restaurant", "Fine Dining Restaurant"],
    "address": "146 Mulberry Street, New York City, United States",
    "phone": "2128048656",
    "website": "https://cangelomulberry.com"
  },
  "reviews": [
    {
      "author": "Stephanie Doe",
      "rating": 5,
      "feedback_text": "One of the best pizzas I have eaten in a long time.",
      "date": "2026-04-27"
    }
  ],
  "scraped_at": "2026-06-06T16:32:46Z",
  "delivery_status": {
    "success": true,
    "platform": "email",
    "destination": "you@example.com",
    "filename": "casa_d_angelo_new_york_reviews.xlsx",
    "error": null
  }
}
```

---

## Is it legal to scrape Trustpilot?

This Actor only collects **publicly available** information visible on Trustpilot without logging in — review text, star ratings, and business profile details. No private credentials or hidden data are accessed.

> Our scrapers are ethical and do not extract private user data such as passwords. They only extract what users have chosen to share publicly. However, results may contain personal names. If you operate under **GDPR** or similar regulations, ensure you have a legitimate basis for processing. Read [Apify's blog on the legality of web scraping](https://blog.apify.com/is-web-scraping-legal/).

---

## FAQ

### How do I receive the report file?

Enable `get_as_file`, choose `export_format` (`xlsx`, `csv`, or `json`), set `destination_platform` to `email` or `discord`, and enter `destination_address`. For Discord, join [Pingrole](https://discord.gg/p5aCRvkHWE) first.

### Which file format should I choose?

| Format | Best for |
|---|---|
| **XLSX** | Excel, business reports, non-technical users |
| **CSV** | Spreadsheets, data imports, lightweight pipelines |
| **JSON** | Developers, APIs, custom integrations |

### The file did not arrive — what now?

Check `delivery_status.error` in the **Output** tab. Common causes: wrong email, Discord user not in the server, or missing Actor secrets.

### The Actor found the wrong business — what do I do?

Add a more specific `location`, `zip_code`, and/or `country`. The scraper picks the first Trustpilot search result.

### Can I scrape more than 500 reviews?

The limit is **500 per run**. Run the Actor multiple times or contact us for a custom solution.

### How do I schedule automatic runs?

Apify Console → **Schedules** → set a cron interval with your preferred delivery settings.

### Can I integrate with other tools?

Yes. Use the **Apify API**, webhooks, or native integrations with **Zapier**, **Make**, **Google Sheets**, and hundreds of other platforms.

---

## Support

Found a bug or have a feature request? Open an issue in the **Issues** tab on this Actor's page — feedback is always welcome. We're also open to building **custom scraping solutions** based on this Actor.

---

## Developer

Built by **Hermann Samimi**

<p align="center">
  <a href="https://github.com/HermannSamimi"><img src="https://img.shields.io/badge/GitHub-HermannSamimi-181717?logo=github&logoColor=white" alt="GitHub" /></a>
  <a href="https://www.linkedin.com/in/hermann-samimi/"><img src="https://img.shields.io/badge/LinkedIn-hermann--samimi-0A66C2?logo=linkedin&logoColor=white" alt="LinkedIn" /></a>
</p>
