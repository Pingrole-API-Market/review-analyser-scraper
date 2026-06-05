"""
Apify Actor entrypoint — Business Review Analyser & Sentiment Extractor.
"""
import asyncio
import logging
from collections import Counter

from apify import Actor

from src.analyser import FakeReviewDetector, SentimentAnalyzer, extract_topics, review_topics
from src.exporters import export_csv, export_json, export_xlsx, send_discord_summary
from src.scrapers import SCRAPER_MAP
from src.storage import MongoStorage
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
        do_export: bool = bool(actor_input.get("export", False))
        export_format: str = actor_input.get("export_format", "csv").lower()
        discord_webhook: str = actor_input.get("discord_webhook", "")

        if not business_name:
            await Actor.fail(status_message="business_name is required")
            return
        if not platforms:
            await Actor.fail(status_message="No valid platforms provided")
            return

        full_location = f"{location}, {zip_code}, {country}".strip(", ")

        # ── Initialise shared resources (loaded once) ─────────────────
        logger.info("Loading sentiment model…")
        sentiment_analyser = SentimentAnalyzer()
        fake_detector = FakeReviewDetector()
        storage = MongoStorage()

        # ── Scrape all platforms (isolated — failures don't propagate) ─
        all_raw_reviews: list[dict] = []
        platforms_scraped: list[str] = []

        scrape_tasks = {
            platform: SCRAPER_MAP[platform]().scrape(
                business_name, full_location, limit_per_platform
            )
            for platform in platforms
        }

        results = await asyncio.gather(*scrape_tasks.values(), return_exceptions=True)

        for platform, result in zip(scrape_tasks.keys(), results):
            if isinstance(result, BaseException):
                logger.error("[%s] Scrape failed: %s", platform, result)
                await Actor.push_data({"event": "scrape_error", "platform": platform, "error": str(result)})
            else:
                logger.info("[%s] Got %d reviews", platform, len(result))
                all_raw_reviews.extend(result)
                if result:
                    platforms_scraped.append(platform)

        if not all_raw_reviews:
            logger.warning("No reviews scraped from any platform — exiting")
            await Actor.push_data({
                "business_name": business_name,
                "location": full_location,
                "platforms_scraped": [],
                "total_reviews_analysed": 0,
                "error": "No reviews found",
                "scraped_at": now_iso(),
            })
            return

        # ── Pre-register all reviews for burst-detection context ──────
        fake_detector.register_batch(all_raw_reviews)

        # ── Sentiment analysis (batch for performance) ────────────────
        texts = [r.get("text", "") for r in all_raw_reviews]
        logger.info("Running sentiment analysis on %d reviews…", len(texts))
        sentiment_results = sentiment_analyser.analyse_batch(texts)

        # ── Annotate reviews ──────────────────────────────────────────
        annotated: list[dict] = []
        for raw, sent in zip(all_raw_reviews, sentiment_results):
            review = {
                **raw,
                "sentiment": sent.label,
                "sentiment_score": sent.score,
                "topics": review_topics(raw.get("text", "")),
                "is_fake_flag": fake_detector.is_fake(raw),
            }
            annotated.append(review)

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
            "high" if fake_count / total > 0.3
            else "medium" if fake_count / total > 0.1
            else "low"
        )

        topic_result = extract_topics(annotated)
        trend = rating_trend(annotated)
        overall_sentiment = compute_overall_sentiment(breakdown)
        scraped_at = now_iso()

        output = {
            "business_name": business_name,
            "location": full_location,
            "platforms_scraped": platforms_scraped,
            "total_reviews_analysed": total,
            "overall_sentiment": overall_sentiment,
            "sentiment_breakdown": breakdown,
            "rating_trend": trend,
            "average_rating": avg_rating,
            "top_complaints": topic_result.top_complaints,
            "top_praises": topic_result.top_praises,
            "top_keywords": topic_result.top_keywords,
            "fake_review_risk": fake_risk,
            "fake_review_count": fake_count,
            "reviews": annotated,
            "scraped_at": scraped_at,
        }

        # ── MongoDB storage ───────────────────────────────────────────
        storage.upsert_reviews(annotated)
        storage.save_result({k: v for k, v in output.items() if k != "reviews"})
        storage.close()

        # ── Push to Apify dataset ─────────────────────────────────────
        await Actor.push_data(output)
        logger.info("Pushed results to Apify dataset")

        # ── Export file (csv / json / xlsx) ───────────────────────────
        export_url: str | None = None
        export_bytes: bytes | None = None
        export_filename: str | None = None

        if do_export:
            store = await Actor.open_key_value_store()
            slug = business_name.lower().replace(" ", "_")
            if export_format == "json":
                export_bytes = export_json(output)
                export_filename = f"{slug}_reviews.json"
                content_type = "application/json"
            elif export_format == "xlsx":
                export_bytes = export_xlsx(annotated, output)
                export_filename = f"{slug}_reviews.xlsx"
                content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            else:  # default csv
                export_bytes = export_csv(annotated)
                export_filename = f"{slug}_reviews.csv"
                content_type = "text/csv"

            await store.set_value(export_filename, export_bytes, content_type=content_type)
            export_url = store.get_public_url(export_filename)
            logger.info("Export saved: %s  (%d bytes)", export_filename, len(export_bytes))

        # ── Discord notification ──────────────────────────────────────
        if discord_webhook:
            try:
                await send_discord_summary(
                    discord_webhook,
                    summary={k: v for k, v in output.items() if k != "reviews"},
                    export_url=export_url,
                    file_bytes=export_bytes if do_export else None,
                    file_name=export_filename if do_export else None,
                )
            except Exception as exc:
                logger.error("Discord notification failed: %s", exc)

        logger.info("Actor finished — %d reviews analysed across %d platforms", total, len(platforms_scraped))


if __name__ == "__main__":
    asyncio.run(main())
