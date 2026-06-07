"""Apify Actor — Business Review Scraper."""
import asyncio
import logging
import re

from apify import Actor
from playwright.async_api import async_playwright

from src.delivery import deliver_file
from src.exporters import export_csv, export_json, export_xlsx
from src.scrapers import SCRAPER_MAP
from src.utils import now_iso

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger(__name__)

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _build_file(all_results: list[dict], export_format: str, slug: str) -> tuple[bytes, str]:
    if export_format == "json":
        return export_json(all_results), f"{slug}_reviews.json"
    if export_format == "csv":
        return export_csv(all_results), f"{slug}_reviews.csv"
    return export_xlsx(all_results), f"{slug}_reviews.xlsx"


async def main() -> None:
    async with Actor:
        actor_input: dict = await Actor.get_input() or {}
        logger.info("Input keys: %s", list(actor_input.keys()))

        business_name: str = actor_input.get("business_name", "")
        location: str = actor_input.get("location", "")
        zip_code: str = actor_input.get("zip_code", "")
        country: str = actor_input.get("country", "")
        platforms: list[str] = list(SCRAPER_MAP.keys())
        limit_per_platform: int = int(actor_input.get("limit_per_platform", 100))
        get_as_file: bool = bool(actor_input.get("get_as_file"))
        export_format: str = actor_input.get("export_format", "xlsx").lower()
        destination_platform: str = (actor_input.get("destination_platform") or "").strip().lower()
        destination_address: str = (actor_input.get("destination_address") or "").strip()

        if not business_name:
            await Actor.fail(status_message="business_name is required")
            return
        if not platforms:
            await Actor.fail(status_message="No valid platforms provided")
            return
        if get_as_file:
            if not destination_platform:
                await Actor.fail(status_message="destination_platform is required when get_as_file is enabled")
                return
            if not destination_address:
                await Actor.fail(status_message="destination_address is required when get_as_file is enabled")
                return
            if destination_platform == "email" and not _EMAIL_RE.match(destination_address):
                await Actor.fail(status_message="destination_address must be a valid email address")
                return
            if destination_platform not in ("email", "discord"):
                await Actor.fail(status_message="destination_platform must be 'email' or 'discord'")
                return

        full_location = ", ".join(p for p in [location, zip_code, country] if p)

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

        delivery_status: dict | None = None
        if get_as_file:
            slug = re.sub(r"[^\w]+", "_", business_name.lower()).strip("_")
            file_bytes, filename = _build_file(all_results, export_format, slug)
            review_count = sum(len(r.get("reviews", [])) for r in all_results)
            delivery_status = await deliver_file(
                destination_platform,
                destination_address,
                filename,
                file_bytes,
                {
                    "business_name": business_name,
                    "review_count": review_count,
                    "format": export_format,
                },
            )

        output = all_results[0] if len(all_results) == 1 else all_results
        if isinstance(output, dict):
            if delivery_status:
                output = {**output, "delivery_status": delivery_status}
        elif delivery_status:
            output = {"results": output, "delivery_status": delivery_status}

        kv = await Actor.open_key_value_store()
        await kv.set_value("OUTPUT", output, content_type="application/json")

        total_reviews = sum(len(r.get("reviews", [])) for r in all_results)
        logger.info("Done — %d reviews across %d platforms", total_reviews, len(all_results))


if __name__ == "__main__":
    asyncio.run(main())
