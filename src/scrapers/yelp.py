"""Yelp reviews scraper."""
import logging
import re
from datetime import datetime, timedelta, timezone

from playwright.async_api import Browser, Page, async_playwright

from src.utils import clean_text, random_delay, random_user_agent, random_viewport, retry

logger = logging.getLogger(__name__)

BASE_URL = "https://www.yelp.com"


class YelpScraper:
    PLATFORM = "yelp"

    async def scrape(
        self,
        business_name: str,
        location: str,
        limit: int = 100,
        browser: Browser | None = None,
    ) -> dict:
        result: dict = {
            "business_name": business_name,
            "platform": self.PLATFORM,
            "overall_rating": None,
            "total_reviews": None,
            "reviews_last_12_months": None,
            "rating_breakdown": None,
            "reviews": [],
        }
        if browser is not None:
            await self._run(business_name, location, limit, browser, result)
        else:
            async with async_playwright() as pw:
                _b = await pw.chromium.launch(headless=True, args=["--no-sandbox"])
                await self._run(business_name, location, limit, _b, result)
                await _b.close()

        result["reviews_last_12_months"] = _count_last_12_months(result["reviews"])
        logger.info("[yelp] Scraped %d reviews", len(result["reviews"]))
        return result

    # ------------------------------------------------------------------

    async def _run(
        self, business_name: str, location: str, limit: int,
        browser: Browser, result: dict,
    ) -> None:
        context = await browser.new_context(
            user_agent=random_user_agent(), viewport=random_viewport(), locale="en-US"
        )
        page = await context.new_page()
        try:
            await retry(
                lambda: self._scrape_all(page, business_name, location, limit, result),
                retries=3, label="yelp",
            )
        except Exception as exc:
            logger.error("[yelp] Fatal: %s", exc)
        finally:
            await context.close()

    async def _scrape_all(
        self, page: Page, business_name: str, location: str, limit: int, result: dict
    ) -> None:
        search_url = (
            f"{BASE_URL}/search"
            f"?find_desc={business_name.replace(' ', '+')}"
            f"&find_loc={location.replace(' ', '+')}"
        )
        await page.goto(search_url, wait_until="domcontentloaded", timeout=30_000)
        await random_delay(1500, 2500)

        # Navigate to first business result
        try:
            first_link = page.locator("a[href^='/biz/'], a[href*='yelp.com/biz/']").first
            await first_link.wait_for(timeout=15_000)
            biz_href = await first_link.get_attribute("href") or ""
            if not biz_href:
                raise RuntimeError("No business link found")
            biz_url = biz_href if biz_href.startswith("http") else f"{BASE_URL}{biz_href}"
        except Exception as exc:
            raise RuntimeError(f"Yelp business not found: {exc}") from exc

        await page.goto(biz_url, wait_until="domcontentloaded", timeout=30_000)
        await random_delay(2000, 3500)

        # Scrape business overview
        await self._scrape_overview(page, result)

        # Paginate through reviews
        offset = 0
        seen_keys: set[str] = set()

        while len(result["reviews"]) < limit:
            url = f"{biz_url}?start={offset}" if offset > 0 else biz_url
            if offset > 0:
                await page.goto(url, wait_until="domcontentloaded", timeout=30_000)
                await random_delay(2000, 3000)

            # Expand truncated reviews
            try:
                for btn in await page.locator("button:has-text('Read more'), button:has-text('more')").all():
                    await btn.click()
                    await random_delay(200, 500)
            except Exception:
                pass

            cards = await page.locator(
                "ul[class*='reviews'] li, "
                "section[aria-label*='Review'], "
                "div[data-review-id]"
            ).all()

            if not cards:
                scraped = await self._json_ld_reviews(page)
                for r in scraped:
                    key = f"{r['author']}|{r['date']}|{r['rating']}"
                    if key not in seen_keys and len(result["reviews"]) < limit:
                        seen_keys.add(key)
                        result["reviews"].append(r)
                break

            prev_len = len(result["reviews"])
            for card in cards:
                if len(result["reviews"]) >= limit:
                    break
                try:
                    review = await self._extract_review(card)
                    if review:
                        key = f"{review['author']}|{review['date']}|{review['rating']}"
                        if key not in seen_keys:
                            seen_keys.add(key)
                            result["reviews"].append(review)
                except Exception as exc:
                    logger.debug("[yelp] Card error: %s", exc)

            if len(result["reviews"]) == prev_len:
                break

            next_btn = page.locator("a:has-text('Next')").last
            if await next_btn.count() == 0:
                break
            next_href = await next_btn.get_attribute("href") or ""
            if not next_href:
                break
            m = re.search(r"start=(\d+)", next_href)
            offset = int(m.group(1)) if m else offset + 20

    async def _scrape_overview(self, page: Page, result: dict) -> None:
        try:
            rating_el = page.locator(
                "div[aria-label*='star rating'] span, "
                "span[class*='ratingValue'], "
                "div[data-testid='rating-value']"
            ).first
            if await rating_el.count() > 0:
                raw = clean_text(await rating_el.inner_text())
                m = re.search(r"(\d+\.?\d*)", raw)
                if m:
                    result["overall_rating"] = float(m.group(1))
        except Exception:
            pass

        try:
            count_el = page.locator(
                "a:has-text('reviews'), span:has-text('reviews')"
            ).first
            if await count_el.count() > 0:
                raw = clean_text(await count_el.inner_text())
                m = re.search(r"([\d,]+)", raw)
                if m:
                    result["total_reviews"] = int(m.group(1).replace(",", ""))
        except Exception:
            pass

        try:
            breakdown: dict[str, int] = {"5_star": 0, "4_star": 0, "3_star": 0, "2_star": 0, "1_star": 0}
            histogram = await page.locator(
                "div[class*='histogram'] div, div[class*='ratingHistogram'] li"
            ).all()
            for item in histogram:
                try:
                    text = clean_text(await item.inner_text())
                    stars_m = re.search(r"([1-5])\s*star", text, re.I)
                    count_m = re.search(r"([\d,]+)", text)
                    if stars_m and count_m:
                        breakdown[f"{stars_m.group(1)}_star"] = int(count_m.group(1).replace(",", ""))
                except Exception:
                    continue
            if any(breakdown.values()):
                result["rating_breakdown"] = breakdown
        except Exception:
            pass

    async def _extract_review(self, card) -> dict | None:
        try:
            # Author
            author_el = card.locator(
                "a[href*='/user_details'], span[class*='display-name'], "
                "div[class*='user-passport-info'] a"
            ).first
            author = clean_text(await author_el.inner_text()) if await author_el.count() > 0 else "Anonymous"

            # Rating
            rating_el = card.locator(
                "div[aria-label*='star rating'], div[class*='i-star-regular']"
            ).first
            rating: int | None = None
            if await rating_el.count() > 0:
                label = await rating_el.get_attribute("aria-label") or ""
                m = re.search(r"(\d)", label)
                if m:
                    rating = int(m.group(1))

            # Feedback text
            body_el = card.locator(
                "span[lang], p[class*='comment'], div[class*='comment'] p"
            ).first
            feedback_text = clean_text(await body_el.inner_text()) if await body_el.count() > 0 else ""

            # Date
            date_el = card.locator("span[class*='date'], time").first
            date_raw = ""
            if await date_el.count() > 0:
                date_raw = (
                    await date_el.get_attribute("datetime")
                    or clean_text(await date_el.inner_text())
                )

            return {
                "author": author,
                "author_country": None,
                "author_total_reviews": None,
                "rating": rating,
                "feedback_text": feedback_text,
                "date": _parse_date(date_raw),
                "verified": False,
                "unprompted": True,
            }
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
                        text = rev.get("description") or rev.get("reviewBody") or ""
                        rating_val = rev.get("reviewRating", {}).get("ratingValue")
                        reviews.append({
                            "author": rev.get("author", {}).get("name", "Anonymous"),
                            "author_country": None,
                            "author_total_reviews": None,
                            "rating": int(float(rating_val)) if rating_val else None,
                            "feedback_text": clean_text(text),
                            "date": (rev.get("datePublished") or "")[:10],
                            "verified": False,
                            "unprompted": True,
                        })
        except Exception as exc:
            logger.debug("[yelp] JSON-LD fallback error: %s", exc)
        return reviews


# ------------------------------------------------------------------

def _parse_date(raw: str) -> str:
    if not raw:
        return ""
    for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%B %d, %Y", "%b %d, %Y"):
        try:
            return datetime.strptime(raw.strip()[:20], fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    m = re.search(r"\d{4}-\d{2}-\d{2}", raw)
    return m.group(0) if m else raw[:10]


def _count_last_12_months(reviews: list[dict]) -> int:
    cutoff = (datetime.now(tz=timezone.utc) - timedelta(days=365)).strftime("%Y-%m-%d")
    return sum(1 for r in reviews if (r.get("date") or "") >= cutoff)
