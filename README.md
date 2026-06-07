<p align="center">
  <img src="https://cdn.trustpilot.net/brand-assets/4.3.0/logo-black.svg" alt="Trustpilot review scraper logo" width="220" />
</p>

<p align="center">
  <a href="https://apify.com"><img src="https://img.shields.io/badge/Platform-Apify-2463EB?logo=apify&logoColor=white" alt="Runs on Apify cloud" /></a>
  <a href="https://www.trustpilot.com"><img src="https://img.shields.io/badge/Scrape-Trustpilot-00B67A" alt="Scrape Trustpilot reviews" /></a>
  <img src="https://img.shields.io/badge/Delivery-Email%20%7C%20Discord-5865F2?logo=discord&logoColor=white" alt="Email and Discord file delivery" />
  <img src="https://img.shields.io/badge/Export-XLSX%20%7C%20CSV%20%7C%20JSON-059669" alt="Export formats" />
  <img src="https://img.shields.io/badge/Apify%20API-Supported-F59E0B" alt="Apify API supported" />
</p>

<p align="center">
  <strong>No coding required.</strong> Enter a business name on Trustpilot — get structured review data in Apify, or have the report sent to your <strong>email</strong> or <strong>Discord</strong> as Excel, CSV, or JSON.
</p>

---

## What does Trustpilot Review Scraper do?

**Trustpilot Review Scraper** is an [Apify Actor](https://apify.com) that **scrapes public business reviews, star ratings, and company profile data** from [Trustpilot](https://www.trustpilot.com). Trustpilot has **no free public API** for bulk review access — this tool is a simple, cloud-based way to **extract Trustpilot data** without running your own browser or server.

Enter a **business name** and optional **location**, click **Run**, and results appear in your Apify dataset. Optionally enable **Send Results as File** to receive the full report by **email attachment** or **Discord DM** — in **XLSX, CSV, or JSON**.

### How it works

<table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:separate;border-spacing:0;background:#F8FAFC;border:1px solid #E2E8F0;border-radius:16px;padding:20px;margin:8px 0;">
  <tr>
    <td colspan="7" align="center" style="padding:0 0 16px 0;font-family:ui-sans-serif,system-ui,sans-serif;">
      <div style="font-size:17px;font-weight:700;color:#0F172A;">Your request → Trustpilot → Apify → Email or Discord</div>
    </td>
  </tr>
  <tr valign="top">
    <td width="22%" style="background:#FFFBEB;border:1.5px solid #F59E0B;border-radius:14px;padding:14px;font-family:ui-sans-serif,system-ui,sans-serif;">
      <div style="font-size:11px;font-weight:700;color:#B45309;">STEP 1</div>
      <div style="font-size:14px;font-weight:700;color:#78350F;margin:6px 0 8px;">👤 Your input</div>
      <div style="font-size:11px;color:#92400E;line-height:1.5;background:#FEF3C7;border-radius:8px;padding:7px;margin-bottom:5px;">Business + location</div>
      <div style="font-size:11px;color:#92400E;line-height:1.5;background:#FEF3C7;border-radius:8px;padding:7px;margin-bottom:5px;">Review limit</div>
      <div style="font-size:11px;color:#92400E;line-height:1.5;background:#FEF3C7;border-radius:8px;padding:7px;">Email or Discord (optional)</div>
    </td>
    <td width="3%" align="center" style="font-size:20px;color:#6366F1;font-weight:700;padding-top:50px;">→</td>
    <td width="22%" style="background:#ECFDF5;border:1.5px solid #059669;border-radius:14px;padding:14px;font-family:ui-sans-serif,system-ui,sans-serif;">
      <div style="font-size:11px;font-weight:700;color:#047857;">STEP 2</div>
      <div style="font-size:14px;font-weight:700;color:#064E3B;margin:6px 0 8px;">⭐ Trustpilot</div>
      <div style="font-size:11px;color:#065F46;line-height:1.5;background:#D1FAE5;border-radius:8px;padding:7px;margin-bottom:5px;">Find profile</div>
      <div style="font-size:11px;color:#065F46;line-height:1.5;background:#D1FAE5;border-radius:8px;padding:7px;margin-bottom:5px;">Scrape reviews</div>
      <div style="font-size:11px;color:#065F46;line-height:1.5;background:#D1FAE5;border-radius:8px;padding:7px;">Company details</div>
    </td>
    <td width="3%" align="center" style="font-size:20px;color:#6366F1;font-weight:700;padding-top:50px;">→</td>
    <td width="22%" style="background:#EFF6FF;border:1.5px solid #2563EB;border-radius:14px;padding:14px;font-family:ui-sans-serif,system-ui,sans-serif;">
      <div style="font-size:11px;font-weight:700;color:#1D4ED8;">STEP 3</div>
      <div style="font-size:14px;font-weight:700;color:#1E3A8A;margin:6px 0 8px;">☁️ Apify</div>
      <div style="font-size:11px;color:#1E40AF;line-height:1.5;background:#DBEAFE;border-radius:8px;padding:7px;margin-bottom:5px;">JSON dataset</div>
      <div style="font-size:11px;color:#1E40AF;line-height:1.5;background:#DBEAFE;border-radius:8px;padding:7px;">Build report file</div>
    </td>
    <td width="3%" align="center" style="font-size:20px;color:#6366F1;font-weight:700;padding-top:50px;">→</td>
    <td width="25%" style="font-family:ui-sans-serif,system-ui,sans-serif;">
      <div style="background:#F5F3FF;border:1.5px solid #7C3AED;border-radius:14px;padding:12px;">
        <div style="font-size:11px;font-weight:700;color:#6D28D9;">STEP 4 · OPTIONAL</div>
        <div style="font-size:14px;font-weight:700;color:#4C1D95;margin:6px 0 8px;">📤 Delivery</div>
        <table width="100%" cellpadding="0" cellspacing="0">
          <tr>
            <td width="48%" style="background:#FFF7ED;border:1px solid #FB923C;border-radius:10px;padding:9px;text-align:center;">
              <div style="font-size:16px;">📧</div>
              <div style="font-size:11px;font-weight:700;color:#9A3412;">Email</div>
            </td>
            <td width="4%"></td>
            <td width="48%" style="background:#EEF2FF;border:1px solid #5865F2;border-radius:10px;padding:9px;text-align:center;">
              <div style="font-size:16px;">💬</div>
              <div style="font-size:11px;font-weight:700;color:#312E81;">Discord</div>
            </td>
          </tr>
        </table>
      </div>
    </td>
  </tr>
</table>

---

## What can Trustpilot Review Scraper do?

- 📧 **Send reports by email** — XLSX, CSV, or JSON attached to your inbox
- 💬 **Send reports by Discord DM** — file delivered directly in Discord
- ⭐ Scrape **overall rating**, star breakdown, and every review text from Trustpilot
- 🏢 Extract **company info** — address, phone, website, categories, description
- ☁️ Run in the **Apify cloud** — no local browser, no server setup
- ⏰ **Schedule** runs (daily, weekly, or custom) for ongoing reputation monitoring
- 🔌 Connect to **Zapier, Make, Google Sheets**, and 800+ tools
- 📡 Access results via the **Apify API** or download from the Storage tab
- 🔄 Built-in **proxy rotation** for reliable scraping at scale

### Send results by Email or Discord

| | 📧 Email | 💬 Discord |
|---|---|---|
| **Format** | XLSX · CSV · JSON | XLSX · CSV · JSON |
| **You enter** | Your email address | Your Discord username |
| **Requirement** | Actor owner configures SMTP secrets | Join [Pingrole server](https://discord.gg/p5aCRvkHWE) first |

Enable **Send Results as File** → pick a format → choose **email** or **discord** → enter your address. The file is sent automatically — not stored for manual download.

---

## What data can you extract from Trustpilot?

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

## Why scrape Trustpilot?

Trustpilot is a leading review platform, but it does **not** provide a free public **Trustpilot API** for bulk data extraction. This Actor + the **Apify platform** gives you advantages a standalone script cannot match:

| Without Apify | With this Actor on Apify |
|---|---|
| Run your own browser and server | ☁️ Fully managed cloud runs |
| Manual file handling | 📧 Automatic email / Discord delivery |
| No scheduling | ⏰ Cron-based schedules |
| No monitoring | 📊 Run logs and status in Console |
| Build your own integrations | 🔌 API, webhooks, Zapier, Make |

**Use cases:** competitor research, reputation monitoring, sentiment analysis, market research, and lead qualification.

---

## How to scrape Trustpilot reviews

1. Open this Actor on [Apify Store](https://apify.com/store) and click **Try for free**
2. Go to the **Input** tab — enter a **business name** and optional **location**
3. Set **Reviews Limit** (default 100, max 500 per run)
4. *(Optional)* Enable **Send Results as File**, pick **XLSX / CSV / JSON**, and choose **Email** or **Discord**
5. Click **Run** — results appear in the **Output** tab within seconds to a few minutes
6. View data in Apify, download from **Storage**, use the **API** tab, or check your **email / Discord** for the file

Trustpilot Review Scraper has all input options in the **Input** tab on this page. Hover over any field for a short explanation.

---

## How much does it cost to scrape Trustpilot?

Trustpilot Review Scraper uses **Apify consumption-based pricing** (Compute Units). Scraping **50–100 reviews** typically costs **$0.005–$0.01** per run — well within the **free $5 monthly credit** every Apify account receives.

| Volume | Approximate cost | Free plan |
|---|---|---|
| 50 reviews | ~$0.005 | ✅ Covered by free credit |
| 100 reviews | ~$0.01 | ✅ Covered by free credit |
| Scheduled daily runs | ~$0.30/month | ✅ Usually covered |

On the free plan you can run this Actor **dozens of times per month**. Paid plans from $49/month offer higher Compute Unit limits for large-scale or scheduled scraping.

> Check **Costs & limits** on this Actor page before your first run, or review usage in the **Log** tab afterwards.

---

## Input

Trustpilot Review Scraper has the following input options. Click the **Input** tab above for the full form with tooltips.

| Field | Required | Default | Description |
|---|---|---|---|
| `business_name` | **Yes** | — | Business to look up on Trustpilot |
| `location` | No | — | City and country (e.g. `New York, USA`) |
| `zip_code` | No | — | Postal code for precise matching |
| `country` | No | `US` | ISO alpha-2 country code |
| `limit_per_platform` | No | `100` | Max reviews to scrape (1–500) |
| `get_as_file` | No | `false` | Send report by email or Discord |
| `export_format` | No | `xlsx` | `xlsx`, `csv`, or `json` |
| `destination_platform` | No | `email` | `email` or `discord` |
| `destination_address` | When sending | — | Email address or Discord username |

### Input example — email delivery (XLSX)

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

### Input example — Discord delivery (CSV)

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

---

## Output example

You can download the dataset extracted by Trustpilot Review Scraper in **JSON** from the Storage tab, or access it via the **Apify API**. When file delivery is enabled, the report is sent to your **email or Discord** — check `delivery_status` in Output to confirm:

```json
{
  "business_name": "Casa D'Angelo New York",
  "platform": "trustpilot",
  "overall_rating": 4.8,
  "total_reviews": 15,
  "rating_breakdown": { "5_star": 12, "4_star": 2, "3_star": 1 },
  "company_info": {
    "categories": ["Italian Restaurant"],
    "address": "146 Mulberry Street, New York City, United States",
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

## Tips and advanced options

### Limit compute usage

- Set a lower **Reviews Limit** if you only need recent reviews
- Use a specific **location** and **country** to avoid failed searches and retries

### Extract Trustpilot data in Python

Use the **Apify API** and [`apify-client`](https://docs.apify.com/api/client/python) to run the Actor programmatically. See [`run_client.py`](run_client.py) in the repository.

```python
import os
from apify_client import ApifyClient

client = ApifyClient(os.environ["APIFY_API_TOKEN"])
run = client.actor("oyxxsUyPX6Oa4P2h0").call(run_input={
    "business_name": "Casa D' Angelo New York",
    "get_as_file": True,
    "export_format": "xlsx",
    "destination_platform": "email",
    "destination_address": "you@example.com",
})
print(client.key_value_store(run.default_key_value_store_id)
      .get_record("OUTPUT")["value"]["delivery_status"])
```

### Delivery setup (Actor owner only)

Configure secrets in **Settings → Secrets**: `PINGROLE_EMAIL`, `PINGROLE_PASSWORD`, `DISCORD_TOKEN`, `DISCORD_INFRA_CHANNEL_ID`, `DISCORD_WEBHOOK_URL` (optional).

---

## Is it legal to scrape Trustpilot?

> Our scrapers are ethical and do not extract any private user data, such as passwords. They only extract what users have chosen to share publicly on [Trustpilot](https://www.trustpilot.com). We believe our scrapers, when used for ethical purposes, are safe. However, your results could contain personal names. Personal data is protected by **GDPR** and other regulations — ensure you have a legitimate reason to process it. Read [Apify's blog on the legality of web scraping](https://blog.apify.com/is-web-scraping-legal/).

---

## FAQ

### How do I receive the report by email or Discord?

Enable **Send Results as File**, choose a format (`xlsx`, `csv`, `json`), set destination to `email` or `discord`, and enter your address. For Discord, join the [Pingrole server](https://discord.gg/p5aCRvkHWE) first.

### Is there an official Trustpilot API?

No free public API exists for bulk review extraction. This Actor is a practical alternative, with the added benefit of **Apify scheduling, API access, integrations, and email/Discord delivery**.

### The file did not arrive — what should I do?

Open the **Output** tab and check `delivery_status.error`. Common causes: wrong email, Discord username not in the server, or missing delivery secrets.

### The Actor found the wrong business — what do I do?

Add a more specific **location**, **zip code**, and **country**. The scraper uses the first Trustpilot search result.

### Can I integrate with Zapier, Make, or Google Sheets?

Yes. Use the **API** tab on this Actor page, webhooks, or Apify's native integrations.

### How do I schedule automatic runs?

Go to **Schedules** in Apify Console and set a cron interval with your preferred delivery settings.

### Can I scrape more than 500 reviews?

The limit is **500 per run**. Run the Actor multiple times or contact us for a custom solution.

---

## Support

Found a bug or have a feature request? Open an issue in the **Issues** tab on this Actor's page — we welcome feedback. We're also happy to build **custom scraping solutions** based on this Actor.

<p align="center">
  <strong>Developer: Hermann Samimi</strong><br/><br/>
  <a href="https://github.com/HermannSamimi"><img src="https://img.shields.io/badge/GitHub-HermannSamimi-181717?logo=github&logoColor=white" alt="GitHub Hermann Samimi" /></a>
  &nbsp;
  <a href="https://www.linkedin.com/in/hermann-samimi/"><img src="https://img.shields.io/badge/LinkedIn-hermann--samimi-0A66C2?logo=linkedin&logoColor=white" alt="LinkedIn Hermann Samimi" /></a>
</p>
