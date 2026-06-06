"""
Apify Actor entrypoint — Business Review Analyser & Sentiment Extractor.
"""
import asyncio
import logging
from collections import Counter

from apify import Actor
from playwright.async_api import async_playwright

from src.analyser import FakeReviewDetector, SentimentAnalyzer, extract_topics, review_topics
from src.exporters import export_csv, export_json, export_xlsx, send_discord_summary
from src.scrapers import SCRAPER_MAP
from src.utils import compute_overall_sentiment, now_iso, rating_trend

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger(__name__)

_SUPPORTED_PLATFORMS = list(SCRAPER_MAP.keys())


async def main() -> None:
    async with Actor:
        actor_input: dict = await Actor.get_input() or {}
        logger.info("Actor input received: %s", list(actor_input.keys()))

        # ── Parse & validate input ────────────────────────────────────
        business_name: str = actor_input.get("business_name", "")
        location: str = actor_input.get("location", "")
        zip_code: str = actor_input.get("zip_code", "")
        country: str = actor_input.get("country", "")
        platforms: list[str] = [
            p.lower() for p in actor_input.get("platforms", _SUPPORTED_PLATFORMS)
            if p.lower() in SCRAPER_MAP
        ]
        limit_per_platform: int = int(actor_input.get("limit_per_platform", 100))
        export_as_file: bool = bool(actor_input.get("export_as_file", False))
        export_format: str = actor_input.get("export_format", "xlsx").lower()
        discord_webhook: str = actor_input.get("discord_webhook", "")

        if not business_name:
            await Actor.fail(status_message="business_name is required")
            return
        if not platforms:
            await Actor.fail(status_message="No valid platforms provided")
            return

        full_location = f"{location}, {zip_code}, {country}".strip(", ")

        # ── Load sentiment model once ─────────────────────────────────
        logger.info("Loading sentiment model…")
        sentiment_analyser = SentimentAnalyzer()
        fake_detector = FakeReviewDetector()

        # ── Scrape all platforms — one shared browser, sequential ─────
        # One Chromium process is reused across platforms; each scraper
        # gets its own context (isolated cookies/UA) then closes it.
        all_raw_reviews: list[dict] = []
        platforms_scraped: list[str] = []

        async with async_playwright() as pw:
            browser = await pw.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-dev-shm-usage"],
            )
            logger.info("Browser launched — scraping %s", platforms)
            try:
                for platform in platforms:
                    try:
                        result = await SCRAPER_MAP[platform]().scrape(
                            business_name, full_location, limit_per_platform,
                            browser=browser,
                        )
                        logger.info("[%s] Got %d reviews", platform, len(result))
                        all_raw_reviews.extend(result)
                        if result:
                            platforms_scraped.append(platform)
                    except Exception as exc:
                        logger.error("[%s] Scrape failed: %s", platform, exc)
                        await Actor.push_data({
                            "event": "scrape_error", "platform": platform, "error": str(exc)
                        })
            finally:
                await browser.close()

        if not all_raw_reviews:
            logger.warning("No reviews scraped from any platform")
            await Actor.push_data({
                "business_name": business_name,
                "location": full_location,
                "platforms_scraped": [],
                "total_reviews_analysed": 0,
                "error": "No reviews found",
                "scraped_at": now_iso(),
            })
            return

        # ── Sentiment analysis (batch) ────────────────────────────────
        texts = [r.get("text", "") for r in all_raw_reviews]
        logger.info("Running sentiment analysis on %d reviews…", len(texts))
        fake_detector.register_batch(all_raw_reviews)
        sentiment_results = sentiment_analyser.analyse_batch(texts)

        # ── Annotate reviews ──────────────────────────────────────────
        annotated: list[dict] = []
        for raw, sent in zip(all_raw_reviews, sentiment_results):
            # When VADER returns neutral but a star rating strongly disagrees,
            # trust the rating — it's the reviewer's explicit ground truth.
            label, score = sent.label, sent.score
            rating = raw.get("rating")
            if label == "neutral" and rating is not None:
                if rating <= 2:
                    label, score = "negative", round(1.0 - score, 4)
                elif rating >= 4:
                    label, score = "positive", round(1.0 - score, 4)

            annotated.append({
                **raw,
                "sentiment": label,
                "sentiment_score": score,
                "topics": review_topics(raw.get("text", "")),
                "is_fake_flag": fake_detector.is_fake(raw),
            })

        # ── Aggregate stats ───────────────────────────────────────────
        total = len(annotated)
        sentiment_counter: Counter = Counter(r["sentiment"] for r in annotated)
        breakdown = {
            "positive": round(sentiment_counter["positive"] / total * 100),
            "neutral":  round(sentiment_counter["neutral"]  / total * 100),
            "negative": round(sentiment_counter["negative"] / total * 100),
        }

        ratings = [r.get("rating") for r in annotated if r.get("rating") is not None]
        avg_rating = round(sum(ratings) / len(ratings), 2) if ratings else None

        fake_count = sum(1 for r in annotated if r["is_fake_flag"])
        fake_risk = (
            "high"   if fake_count / total > 0.3 else
            "medium" if fake_count / total > 0.1 else
            "low"
        )

        topic_result = extract_topics(annotated)
        output = {
            "business_name":          business_name,
            "location":               full_location,
            "platforms_scraped":      platforms_scraped,
            "total_reviews_analysed": total,
            "overall_sentiment":      compute_overall_sentiment(breakdown),
            "sentiment_breakdown":    breakdown,
            "rating_trend":           rating_trend(annotated),
            "average_rating":         avg_rating,
            "top_complaints":         topic_result.top_complaints,
            "top_praises":            topic_result.top_praises,
            "top_keywords":           topic_result.top_keywords,
            "fake_review_risk":       fake_risk,
            "fake_review_count":      fake_count,
            "reviews":                annotated,
            "scraped_at":             now_iso(),
            "export_file_url":        None,
        }

        # ── Optional file export (CSV / XLSX / JSON) ──────────────────
        export_bytes: bytes | None = None
        export_filename: str | None = None

        if export_as_file:
            store = await Actor.open_key_value_store()
            slug = business_name.lower().replace(" ", "_")
            if export_format == "json":
                export_bytes = export_json(output)
                export_filename = f"{slug}_reviews.json"
                content_type = "application/json"
            elif export_format == "csv":
                export_bytes = export_csv(annotated)
                export_filename = f"{slug}_reviews.csv"
                content_type = "text/csv"
            else:  # default xlsx
                export_bytes = export_xlsx(annotated, output)
                export_filename = f"{slug}_reviews.xlsx"
                content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

            await store.set_value(export_filename, export_bytes, content_type=content_type)
            output["export_file_url"] = store.get_public_url(export_filename)
            logger.info("File export saved: %s  (%d bytes)", export_filename, len(export_bytes))

        # ── Push to Apify dataset (always) ────────────────────────────
        await Actor.push_data(output)
        logger.info("Pushed results to Apify dataset")

        # ── Discord notification ──────────────────────────────────────
        if discord_webhook:
            try:
                await send_discord_summary(
                    discord_webhook,
                    summary={k: v for k, v in output.items() if k != "reviews"},
                    export_url=output["export_file_url"],
                    file_bytes=export_bytes,
                    file_name=export_filename,
                )
            except Exception as exc:
                logger.error("Discord notification failed: %s", exc)

        logger.info(
            "Actor finished — %d reviews analysed across %d platforms",
            total, len(platforms_scraped),
        )


if __name__ == "__main__":
    asyncio.run(main())
