"""Apify Actor — Business Review Scraper."""
import asyncio
import logging
import re

from apify import Actor
from playwright.async_api import async_playwright

from src.exporters import export_csv, export_json, export_xlsx
from src.scrapers import SCRAPER_MAP
from src.utils import now_iso

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger(__name__)


async def main() -> None:
    async with Actor:
        actor_input: dict = await Actor.get_input() or {}
        logger.info("Input keys: %s", list(actor_input.keys()))

        business_name: str   = actor_input.get("business_name", "")
        location: str        = actor_input.get("location", "")
        zip_code: str        = actor_input.get("zip_code", "")
        country: str         = actor_input.get("country", "")
        platforms: list[str] = list(SCRAPER_MAP.keys())  # always trustpilot
        limit_per_platform: int = int(actor_input.get("limit_per_platform", 100))
        export_as_file: bool    = bool(
            actor_input.get("export_as_file") or actor_input.get("export", False)
        )
        export_format: str      = actor_input.get("export_format", "xlsx").lower()

        if not business_name:
            await Actor.fail(status_message="business_name is required")
            return
        if not platforms:
            await Actor.fail(status_message="No valid platforms provided")
            return

        full_location = ", ".join(p for p in [location, zip_code, country] if p)

        # ── Scrape — one shared browser, platforms run sequentially ──
        all_results: list[dict] = []

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
                        result["scraped_at"] = now_iso()
                        all_results.append(result)

                        # Push one dataset item per platform (nested reviews array)
                        await Actor.push_data(result)
                        logger.info("[%s] Pushed %d reviews to dataset",
                                    platform, len(result.get("reviews", [])))

                    except Exception as exc:
                        logger.error("[%s] Scrape failed: %s", platform, exc)
                        await Actor.push_data({
                            "business_name": business_name,
                            "platform": platform,
                            "error": str(exc),
                            "scraped_at": now_iso(),
                        })
            finally:
                await browser.close()

        if not all_results:
            logger.warning("No results from any platform")
            return

        # ── Optional file export ──────────────────────────────────────
        export_bytes: bytes | None   = None
        export_filename: str | None  = None
        export_file_url: str | None  = None

        if export_as_file:
            try:
                store = await Actor.open_key_value_store()
                slug  = re.sub(r"[^\w]+", "_", business_name.lower()).strip("_")

                if export_format == "json":
                    export_bytes    = export_json(all_results)
                    export_filename = f"{slug}_reviews.json"
                    content_type    = "application/json"
                elif export_format == "csv":
                    export_bytes    = export_csv(all_results)
                    export_filename = f"{slug}_reviews.csv"
                    content_type    = "text/csv"
                else:  # xlsx default
                    export_bytes    = export_xlsx(all_results)
                    export_filename = f"{slug}_reviews.xlsx"
                    content_type    = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

                await store.set_value(export_filename, export_bytes, content_type=content_type)
                export_file_url = await store.get_public_url(export_filename)
                logger.info("Export saved: %s (%d bytes)  url=%s",
                            export_filename, len(export_bytes), export_file_url)
            except Exception as exc:
                logger.error("File export failed: %s", exc)

        # Always write the full results to the OUTPUT key (shows as pretty JSON in the console)
        output = all_results[0] if len(all_results) == 1 else all_results
        kv = await Actor.open_key_value_store()
        await kv.set_value("OUTPUT", output, content_type="application/json")

        total_reviews = sum(len(r.get("reviews", [])) for r in all_results)
        logger.info("Done — %d reviews across %d platforms", total_reviews, len(all_results))


if __name__ == "__main__":
    asyncio.run(main())
