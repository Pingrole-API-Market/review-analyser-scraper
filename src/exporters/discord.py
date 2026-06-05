"""Discord webhook delivery for analysis results."""
import logging

import httpx

logger = logging.getLogger(__name__)

_SENTIMENT_COLOUR = {
    "positive": 0x2ECC71,   # green
    "neutral":  0xF39C12,   # amber
    "negative": 0xE74C3C,   # red
}
_TREND_EMOJI = {"improving": "📈", "declining": "📉", "stable": "➡️"}


async def send_discord_summary(
    webhook_url: str,
    summary: dict,
    export_url: str | None = None,
    file_bytes: bytes | None = None,
    file_name: str | None = None,
) -> None:
    business = summary.get("business_name", "Unknown")
    location = summary.get("location", "")
    sentiment = summary.get("overall_sentiment", "neutral")
    trend = summary.get("rating_trend", "unknown")
    avg_rating = summary.get("average_rating", "N/A")
    total = summary.get("total_reviews_analysed", 0)
    breakdown = summary.get("sentiment_breakdown", {})
    complaints = summary.get("top_complaints", [])[:3]
    praises = summary.get("top_praises", [])[:3]
    fake_risk = summary.get("fake_review_risk", "unknown")
    fake_count = summary.get("fake_review_count", 0)
    scraped_at = summary.get("scraped_at", "")

    colour = _SENTIMENT_COLOUR.get(sentiment, 0x95A5A6)
    trend_emoji = _TREND_EMOJI.get(trend, "")

    fields = [
        {"name": "📊 Overall Sentiment", "value": sentiment.capitalize(), "inline": True},
        {"name": "⭐ Avg Rating", "value": str(avg_rating), "inline": True},
        {"name": f"{trend_emoji} Rating Trend", "value": trend.capitalize(), "inline": True},
        {"name": "📝 Reviews Analysed", "value": str(total), "inline": True},
        {
            "name": "😊 Sentiment Breakdown",
            "value": (
                f"Positive: {breakdown.get('positive', 0)}%\n"
                f"Neutral: {breakdown.get('neutral', 0)}%\n"
                f"Negative: {breakdown.get('negative', 0)}%"
            ),
            "inline": True,
        },
        {"name": "⚠️ Fake Review Risk", "value": f"{fake_risk.capitalize()} ({fake_count} flagged)", "inline": True},
    ]
    if complaints:
        fields.append({"name": "🔴 Top Complaints", "value": "\n".join(f"• {c}" for c in complaints), "inline": True})
    if praises:
        fields.append({"name": "🟢 Top Praises", "value": "\n".join(f"• {p}" for p in praises), "inline": True})
    if export_url:
        fields.append({"name": "📥 Export Download", "value": f"[Download Report]({export_url})", "inline": False})

    embed = {
        "title": f"📋 Review Analysis: {business}",
        "description": f"**{location}** — Analysis complete",
        "color": colour,
        "fields": fields,
        "footer": {"text": f"Scraped at {scraped_at}"},
    }

    payload: dict = {"embeds": [embed]}

    async with httpx.AsyncClient(timeout=30) as client:
        if file_bytes and file_name:
            # Send as multipart with the file attached
            response = await client.post(
                webhook_url,
                data={"payload_json": _json_str(payload)},
                files={"file": (file_name, file_bytes, _mime_type(file_name))},
            )
        else:
            response = await client.post(webhook_url, json=payload)

    if response.status_code not in (200, 204):
        logger.error("[discord] Webhook failed: %d %s", response.status_code, response.text)
    else:
        logger.info("[discord] Notification sent successfully")


def _json_str(payload: dict) -> str:
    import json
    return json.dumps(payload)


def _mime_type(filename: str) -> str:
    if filename.endswith(".csv"):
        return "text/csv"
    if filename.endswith(".xlsx"):
        return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    return "application/json"
