"""Discord webhook delivery."""
import json
import logging

import httpx

logger = logging.getLogger(__name__)

_RATING_COLOUR = {5: 0x2ECC71, 4: 0x27AE60, 3: 0xF39C12, 2: 0xE67E22, 1: 0xE74C3C}


async def send_discord_summary(
    webhook_url: str,
    results: list[dict],
    export_url: str | None = None,
    file_bytes: bytes | None = None,
    file_name: str | None = None,
) -> None:
    embeds = []
    for result in results:
        business    = result.get("business_name", "Unknown")
        platform    = (result.get("platform") or "").capitalize()
        rating      = result.get("overall_rating")
        total       = result.get("total_reviews")
        last_12     = result.get("reviews_last_12_months")
        scraped_at  = result.get("scraped_at", "")
        bd          = result.get("rating_breakdown") or {}
        review_count = len(result.get("reviews", []))

        colour = _RATING_COLOUR.get(round(rating) if rating else 0, 0x95A5A6)

        fields = [
            {"name": "⭐ Overall Rating", "value": str(rating) if rating else "N/A", "inline": True},
            {"name": "📝 Total Reviews",  "value": f"{total:,}" if total else "N/A", "inline": True},
            {"name": "📅 Last 12 Months", "value": str(last_12) if last_12 is not None else "N/A", "inline": True},
            {"name": "📦 Scraped",        "value": f"{review_count} reviews",        "inline": True},
        ]

        if any(bd.values()):
            stars = "\n".join(
                f"{'★' * i}{'☆' * (5-i)} — {bd.get(f'{i}_star', 0)}"
                for i in range(5, 0, -1)
            )
            fields.append({"name": "📊 Rating Breakdown", "value": stars, "inline": False})

        if export_url:
            fields.append({"name": "📥 Download Report", "value": f"[{file_name or 'Export'}]({export_url})", "inline": False})

        embeds.append({
            "title":       f"📋 {business} — {platform}",
            "color":       colour,
            "fields":      fields,
            "footer":      {"text": f"Scraped at {scraped_at}"},
        })

    payload: dict = {"embeds": embeds[:10]}  # Discord max 10 embeds per message

    async with httpx.AsyncClient(timeout=30) as client:
        if file_bytes and file_name:
            response = await client.post(
                webhook_url,
                data={"payload_json": json.dumps(payload)},
                files={"file": (file_name, file_bytes, _mime(file_name))},
            )
        else:
            response = await client.post(webhook_url, json=payload)

    if response.status_code not in (200, 204):
        logger.error("[discord] Webhook failed: %d %s", response.status_code, response.text)
    else:
        logger.info("[discord] Notification sent")


def _mime(filename: str) -> str:
    if filename.endswith(".csv"):
        return "text/csv"
    if filename.endswith(".xlsx"):
        return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    return "application/json"
