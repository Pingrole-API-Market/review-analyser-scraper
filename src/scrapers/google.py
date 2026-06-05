"""Google Maps reviews scraper using Playwright."""
import logging
import re
from datetime import datetime, timedelta

from playwright.async_api import Browser, Page, async_playwright

from src.utils import clean_text, random_delay, random_user_agent, random_viewport, retry

logger = logging.getLogger(__name__)


class GoogleScraper:
    PLATFORM = "google"

    async def scrape(
        self, business_name: str, location: str, limit: int = 100,
        browser: Browser | None = None,
    ) -> list[dict]:
        reviews: list[dict] = []
        if browser is not None:
            await self._run(business_name, location, limit, browser, reviews)
        else:
            async with async_playwright() as pw:
                _b = await pw.chromium.launch(headless=True, args=["--no-sandbox"])
                await self._run(business_name, location, limit, _b, reviews)
                await _b.close()
        logger.info("[google] Scraped %d reviews", len(reviews))
        return reviews

    async def _run(
        self, business_name: str, location: str, limit: int,
        browser: Browser, reviews: list[dict],
    ) -> None:
        context = await browser.new_context(
            user_agent=random_user_agent(), viewport=random_viewport(), locale="en-US"
        )
        page = await context.new_page()
        try:
            await retry(
                lambda: self._scrape_page(page, business_name, location, limit, reviews),
                retries=3, label="google",
            )
        except Exception as exc:
            logger.error("[google] Fatal error: %s", exc)
        finally:
            await context.close()

    async def _scrape_page(
        self, page: Page, business_name: str, location: str, limit: int, reviews: list[dict]
    ) -> None:
        query = f"{business_name} {location}"
        await page.goto(
            f"https://www.google.com/maps/search/{query.replace(' ', '+')}",
            wait_until="domcontentloaded", timeout=30_000,
        )
        await random_delay(1500, 3000)

        try:
            accept_btn = page.locator("button:has-text('Accept all'), button:has-text('Agree')")
            if await accept_btn.count() > 0:
                await accept_btn.first.click()
                await random_delay()
        except Exception:
            pass

        try:
            first_result = page.locator("a[href*='/maps/place/']").first
            await first_result.wait_for(timeout=10_000)
            await first_result.click()
            await random_delay(2000, 3500)
        except Exception as exc:
            raise RuntimeError(f"Could not find business listing: {exc}") from exc

        try:
            reviews_tab = page.locator("button[aria-label*='Reviews'], button[data-tab-index='1']").first
            await reviews_tab.wait_for(timeout=8_000)
            await reviews_tab.click()
            await random_delay(1500, 2500)
        except Exception:
            try:
                await page.locator("div[role='tablist'] button").nth(1).click()
                await random_delay(1500, 2500)
            except Exception as exc2:
                raise RuntimeError(f"Reviews tab unreachable: {exc2}") from exc2

        try:
            sort_btn = page.locator("button[aria-label*='Sort'], button[data-value='Sort']").first
            if await sort_btn.count() > 0:
                await sort_btn.click()
                await random_delay(800, 1500)
                newest = page.locator("li:has-text('Newest'), div[data-index='1']").first
                if await newest.count() > 0:
                    await newest.click()
                    await random_delay(1500, 2500)
        except Exception:
            pass

        scrollable = page.locator("div[aria-label*='Reviews']").first
        seen_keys: set[str] = set()
        no_new_count = 0

        while len(reviews) < limit and no_new_count < 5:
            await scrollable.evaluate("el => el.scrollBy(0, 2000)")
            await random_delay(1200, 2000)

            cards = await page.locator("div[data-review-id]").all()
            prev_len = len(reviews)

            for card in cards:
                if len(reviews) >= limit:
                    break
                try:
                    review = await self._extract_card(card)
                    if review:
                        key = f"{review['author']}|{review['date']}|{review['text'][:30]}"
                        if key not in seen_keys:
                            seen_keys.add(key)
                            reviews.append(review)
                except Exception as exc:
                    logger.debug("[google] Card extraction error: %s", exc)

            no_new_count = 0 if len(reviews) > prev_len else no_new_count + 1

    async def _extract_card(self, card) -> dict | None:
        try:
            more_btn = card.locator("button:has-text('More'), button[aria-label*='More']")
            if await more_btn.count() > 0:
                await more_btn.first.click()
                await random_delay(300, 700)

            author_el = card.locator("div[class*='reviewer'] span, a[href*='contrib']").first
            author = clean_text(await author_el.inner_text()) if await author_el.count() > 0 else "Anonymous"

            rating_el = card.locator("span[aria-label*='star']").first
            rating_raw = await rating_el.get_attribute("aria-label") if await rating_el.count() > 0 else ""
            rating = _parse_star_rating(rating_raw)

            text_el = card.locator("span[data-expandable-section], span.wiI7pd").first
            text = clean_text(await text_el.inner_text()) if await text_el.count() > 0 else ""

            date_el = card.locator("span[class*='date'], span.rsqaWe").first
            date_raw = clean_text(await date_el.inner_text()) if await date_el.count() > 0 else ""
            date = _parse_relative_date(date_raw)

            return {"platform": "google", "author": author, "rating": rating, "text": text, "date": date}
        except Exception as exc:
            logger.debug("[google] Card parse error: %s", exc)
            return None


def _parse_star_rating(label: str) -> int | None:
    match = re.search(r"(\d+)", label or "")
    return int(match.group(1)) if match else None


def _parse_relative_date(raw: str) -> str:
    raw = raw.lower().strip()
    now = datetime.utcnow()
    if "hour" in raw or "minute" in raw:
        return now.strftime("%Y-%m-%d")
    m = re.search(r"(\d+)\s+(day|week|month|year)", raw)
    if not m:
        date_match = re.search(r"\d{4}-\d{2}-\d{2}", raw)
        return date_match.group(0) if date_match else now.strftime("%Y-%m-%d")
    qty, unit = int(m.group(1)), m.group(2)
    delta_map = {"day": 1, "week": 7, "month": 30, "year": 365}
    return (now - timedelta(days=qty * delta_map[unit])).strftime("%Y-%m-%d")
