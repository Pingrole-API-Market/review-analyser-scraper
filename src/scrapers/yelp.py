"""Yelp reviews scraper using Playwright."""
import logging
import re
from datetime import datetime

from playwright.async_api import Browser, Page, async_playwright

from src.utils import clean_text, random_delay, random_user_agent, random_viewport, retry

logger = logging.getLogger(__name__)

BASE_URL = "https://www.yelp.com"


class YelpScraper:
    PLATFORM = "yelp"

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
        logger.info("[yelp] Scraped %d reviews", len(reviews))
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
                lambda: self._scrape_all(page, business_name, location, limit, reviews),
                retries=3, label="yelp",
            )
        except Exception as exc:
            logger.error("[yelp] Fatal error: %s", exc)
        finally:
            await context.close()

    async def _scrape_all(
        self, page: Page, business_name: str, location: str, limit: int, reviews: list[dict]
    ) -> None:
        search_url = (
            f"{BASE_URL}/search"
            f"?find_desc={business_name.replace(' ', '+')}"
            f"&find_loc={location.replace(' ', '+')}"
        )
        await page.goto(search_url, wait_until="domcontentloaded", timeout=30_000)
        await random_delay(1500, 2500)

        try:
            first_link = page.locator("h3 a[href*='/biz/'], a[class*='businessName']").first
            await first_link.wait_for(timeout=10_000)
            biz_href = await first_link.get_attribute("href")
            if not biz_href:
                raise RuntimeError("No business link found")
            biz_url = biz_href if biz_href.startswith("http") else f"{BASE_URL}{biz_href}"
        except Exception as exc:
            raise RuntimeError(f"Yelp business not found: {exc}") from exc

        offset = 0
        seen_keys: set[str] = set()

        while len(reviews) < limit:
            url = f"{biz_url}?start={offset}"
            await page.goto(url, wait_until="domcontentloaded", timeout=30_000)
            await random_delay(2000, 3500)

            try:
                for btn in await page.locator("button:has-text('Read more')").all():
                    await btn.click()
                    await random_delay(200, 500)
            except Exception:
                pass

            cards = await page.locator(
                "ul[class*='reviews'] li, section[aria-label*='Review'], div[data-review-id]"
            ).all()

            if not cards:
                scraped = await self._json_ld_reviews(page)
                for r in scraped:
                    key = f"{r['author']}|{r['date']}|{r['text'][:30]}"
                    if key not in seen_keys:
                        seen_keys.add(key)
                        reviews.append(r)
                        if len(reviews) >= limit:
                            break
                break

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
                    logger.debug("[yelp] Card error: %s", exc)

            if len(reviews) == prev_len:
                break

            next_btn = page.locator("a:has-text('Next')").last
            if await next_btn.count() == 0:
                break
            next_href = await next_btn.get_attribute("href")
            if not next_href:
                break
            offset_m = re.search(r"start=(\d+)", next_href)
            offset = int(offset_m.group(1)) if offset_m else offset + 20

    async def _extract_card(self, card) -> dict | None:
        try:
            author_el = card.locator("a[href*='/user_details'], span[class*='display-name']").first
            author = clean_text(await author_el.inner_text()) if await author_el.count() > 0 else "Anonymous"

            rating_el = card.locator("div[aria-label*='star rating'], div[class*='i-star']").first
            rating = None
            if await rating_el.count() > 0:
                label = await rating_el.get_attribute("aria-label") or ""
                m = re.search(r"(\d)", label)
                if m:
                    rating = int(m.group(1))

            text_el = card.locator("span[lang], p[class*='comment'], div[class*='comment']").first
            text = clean_text(await text_el.inner_text()) if await text_el.count() > 0 else ""

            date_el = card.locator("span[class*='date'], time").first
            date_raw = ""
            if await date_el.count() > 0:
                date_raw = (
                    await date_el.get_attribute("datetime")
                    or clean_text(await date_el.inner_text())
                )

            return {"platform": "yelp", "author": author, "rating": rating, "text": text, "date": _parse_date(date_raw)}
        except Exception as exc:
            logger.debug("[yelp] Card parse error: %s", exc)
            return None

    async def _json_ld_reviews(self, page: Page) -> list[dict]:
        import json
        reviews = []
        try:
            for script in await page.locator("script[type='application/ld+json']").all():
                data = json.loads(await script.inner_text())
                for item in (data if isinstance(data, list) else [data]):
                    for rev in item.get("review", []):
                        text = rev.get("description", "") or rev.get("reviewBody", "")
                        rating_val = rev.get("reviewRating", {}).get("ratingValue")
                        reviews.append({
                            "platform": "yelp",
                            "author": rev.get("author", {}).get("name", "Anonymous"),
                            "rating": int(float(rating_val)) if rating_val else None,
                            "text": clean_text(text),
                            "date": (rev.get("datePublished") or "")[:10],
                        })
        except Exception as exc:
            logger.debug("[yelp] JSON-LD fallback error: %s", exc)
        return reviews


def _parse_date(raw: str) -> str:
    if not raw:
        return ""
    for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%B %d, %Y", "%b %d, %Y"):
        try:
            return datetime.strptime(raw.strip()[:20], fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    iso = re.search(r"\d{4}-\d{2}-\d{2}", raw)
    return iso.group(0) if iso else raw[:10]
