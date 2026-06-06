"""Trustpilot company reviews scraper."""
import logging
import re
from datetime import datetime, timedelta, timezone

from playwright.async_api import Browser, Page, async_playwright

from src.utils import clean_text, random_delay, random_user_agent, random_viewport, retry

logger = logging.getLogger(__name__)

BASE_URL = "https://www.trustpilot.com"


class TrustpilotScraper:
    PLATFORM = "trustpilot"

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
        logger.info("[trustpilot] Scraped %d reviews", len(result["reviews"]))
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
                retries=3, label="trustpilot",
            )
        except Exception as exc:
            logger.error("[trustpilot] Fatal: %s", exc)
            raise
        finally:
            await context.close()

    async def _scrape_all(
        self, page: Page, business_name: str, location: str, limit: int, result: dict
    ) -> None:
        slug = _to_slug(f"{business_name} {location}")
        await page.goto(f"{BASE_URL}/search?query={slug}", wait_until="domcontentloaded", timeout=30_000)
        await random_delay(1000, 2000)

        # Dismiss cookie banner
        try:
            btn = page.locator("#onetrust-accept-btn-handler, button:has-text('Accept all')").first
            if await btn.count() > 0:
                await btn.click()
                await random_delay(500, 1000)
        except Exception:
            pass

        # Navigate to company page
        try:
            biz_link = page.locator("a[href*='/review/']").first
            await biz_link.wait_for(state="attached", timeout=8_000)
            biz_href = await biz_link.get_attribute("href") or ""
            company_url = f"{BASE_URL}{biz_href}" if biz_href.startswith("/") else biz_href
            await page.goto(company_url, wait_until="domcontentloaded", timeout=30_000)
            await random_delay(1500, 2500)
        except Exception as exc:
            raise RuntimeError(f"Business not found on Trustpilot: {exc}") from exc

        # Scrape business overview from the company landing page
        await self._scrape_overview(page, result)

        # Navigate to reviews tab
        try:
            reviews_link = page.locator("a[href*='/review/'][href*='?']", ).first
            if await reviews_link.count() == 0:
                reviews_link = page.locator("a:has-text('Reviews')").first
            if await reviews_link.count() > 0:
                await reviews_link.click()
                await random_delay(1500, 2500)
        except Exception:
            pass  # may already be on the reviews page

        # Paginate and collect reviews
        page_num = 1
        seen_keys: set[str] = set()

        while len(result["reviews"]) < limit:
            cards = await page.locator("article[class*='review'], div[data-service-review-card-paper]").all()
            if not cards:
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
                    logger.debug("[trustpilot] Card error: %s", exc)

            if len(result["reviews"]) == prev_len:
                break

            # Next page
            try:
                next_btn = page.locator("a[name='pagination-button-next']").first
                if await next_btn.count() == 0:
                    break
                next_href = await next_btn.get_attribute("href") or ""
                if not next_href:
                    break
                page_num += 1
                url = f"{BASE_URL}{next_href}" if next_href.startswith("/") else next_href
                await page.goto(url, wait_until="domcontentloaded", timeout=30_000)
                await random_delay(1500, 2500)
            except Exception:
                break

    async def _scrape_overview(self, page: Page, result: dict) -> None:
        try:
            # Overall TrustScore
            rating_el = page.locator(
                "span[data-rating-typography], "
                "p[class*='displayRating'], "
                "div[class*='trustScore'] span"
            ).first
            if await rating_el.count() > 0:
                raw = clean_text(await rating_el.inner_text())
                m = re.search(r"(\d+\.?\d*)", raw)
                if m:
                    result["overall_rating"] = float(m.group(1))
        except Exception:
            pass

        try:
            # Total review count
            count_el = page.locator(
                "span[data-reviews-count-typography], "
                "p[class*='reviewsCount'], "
                "span:has-text('reviews')"
            ).first
            if await count_el.count() > 0:
                raw = clean_text(await count_el.inner_text())
                m = re.search(r"([\d,]+)", raw)
                if m:
                    result["total_reviews"] = int(m.group(1).replace(",", ""))
        except Exception:
            pass

        try:
            # Rating breakdown (histogram bars)
            breakdown: dict[str, int] = {"5_star": 0, "4_star": 0, "3_star": 0, "2_star": 0, "1_star": 0}
            star_rows = await page.locator(
                "div[class*='histogram'] div[class*='row'], "
                "div[class*='ratingDistribution'] div[class*='bar']"
            ).all()
            for row in star_rows:
                try:
                    text = clean_text(await row.inner_text())
                    stars_m = re.search(r"([1-5])\s*star", text, re.I)
                    count_m = re.search(r"([\d,]+)\s*$", text)
                    if stars_m and count_m:
                        key = f"{stars_m.group(1)}_star"
                        breakdown[key] = int(count_m.group(1).replace(",", ""))
                except Exception:
                    continue
            if any(breakdown.values()):
                result["rating_breakdown"] = breakdown
        except Exception:
            pass

    async def _extract_review(self, card) -> dict | None:
        try:
            # ── Author ────────────────────────────────────────────────
            author_el = card.locator(
                "span[data-consumer-name-typography], "
                "a[name='consumer-profile'] span, "
                "div[class*='consumerInfo'] span[class*='name']"
            ).first
            author = clean_text(await author_el.inner_text()) if await author_el.count() > 0 else "Anonymous"

            # ── Author country ────────────────────────────────────────
            country_el = card.locator(
                "div[class*='consumerInfo'] span[class*='location'], "
                "span[data-consumer-country-typography]"
            ).first
            author_country: str | None = None
            if await country_el.count() > 0:
                author_country = clean_text(await country_el.inner_text()) or None

            # ── Author total reviews ──────────────────────────────────
            author_reviews_el = card.locator(
                "span[data-consumer-reviews-count-typography], "
                "span[class*='reviewsCount']"
            ).first
            author_total_reviews: int | None = None
            if await author_reviews_el.count() > 0:
                raw = clean_text(await author_reviews_el.inner_text())
                m = re.search(r"(\d+)", raw)
                if m:
                    author_total_reviews = int(m.group(1))

            # ── Rating ────────────────────────────────────────────────
            rating_el = card.locator(
                "div[data-service-review-rating], img[alt*='Rated']"
            ).first
            rating: int | None = None
            if await rating_el.count() > 0:
                raw = (
                    await rating_el.get_attribute("data-service-review-rating")
                    or await rating_el.get_attribute("alt")
                    or ""
                )
                m = re.search(r"(\d)", raw)
                if m:
                    rating = int(m.group(1))

            # ── Title ─────────────────────────────────────────────────
            title_el = card.locator(
                "h2[data-service-review-title-typography], h2[class*='title']"
            ).first
            title = clean_text(await title_el.inner_text()) if await title_el.count() > 0 else ""

            # ── Body ──────────────────────────────────────────────────
            body_el = card.locator(
                "p[data-service-review-text-typography], "
                "[data-service-review-text-typography]"
            ).first
            body = clean_text(await body_el.inner_text()) if await body_el.count() > 0 else ""

            # Fallback: collect all <p> text in card if still empty
            if not body and not title:
                all_p = await card.locator("p").all()
                parts = [clean_text(await p.inner_text()) for p in all_p if len(clean_text(await p.inner_text())) > 3]
                body = " ".join(parts)

            # ── Date ──────────────────────────────────────────────────
            date_el = card.locator("time").first
            date_raw = await date_el.get_attribute("datetime") if await date_el.count() > 0 else ""
            date = _parse_iso_date(date_raw)

            # ── Verified ──────────────────────────────────────────────
            verified_el = card.locator(
                "span[class*='verifiedOrder'], div[class*='verified']"
            ).first
            verified = await verified_el.count() > 0

            # ── Unprompted (not an "invited" review) ──────────────────
            invited_el = card.locator(
                "span[class*='invited'], div[class*='invited'], "
                "a[href*='invited']"
            ).first
            unprompted = await invited_el.count() == 0

            return {
                "author": author,
                "author_country": author_country,
                "author_total_reviews": author_total_reviews,
                "rating": rating,
                "title": title,
                "body": body,
                "date": date,
                "verified": verified,
                "unprompted": unprompted,
            }
        except Exception as exc:
            logger.debug("[trustpilot] Card parse error: %s", exc)
            return None


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _to_slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "+", name.lower()).strip("+")


def _parse_iso_date(raw: str) -> str:
    if not raw:
        return ""
    m = re.search(r"\d{4}-\d{2}-\d{2}", raw)
    return m.group(0) if m else raw[:10]


def _count_last_12_months(reviews: list[dict]) -> int:
    cutoff = (datetime.now(tz=timezone.utc) - timedelta(days=365)).strftime("%Y-%m-%d")
    return sum(1 for r in reviews if (r.get("date") or "") >= cutoff)
