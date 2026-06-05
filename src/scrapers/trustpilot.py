"""Trustpilot reviews scraper using Playwright."""
import logging
import re

from playwright.async_api import Page, async_playwright

from src.utils import clean_text, random_delay, random_user_agent, random_viewport, retry

logger = logging.getLogger(__name__)

BASE_URL = "https://www.trustpilot.com"


class TrustpilotScraper:
    PLATFORM = "trustpilot"

    async def scrape(
        self, business_name: str, location: str, limit: int = 100
    ) -> list[dict]:
        reviews: list[dict] = []
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True, args=["--no-sandbox"])
            context = await browser.new_context(
                user_agent=random_user_agent(),
                viewport=random_viewport(),
                locale="en-US",
            )
            page = await context.new_page()
            try:
                await retry(
                    lambda: self._scrape_all(page, business_name, limit, reviews),
                    retries=3,
                    label="trustpilot",
                )
            except Exception as exc:
                logger.error("[trustpilot] Fatal error: %s", exc)
            finally:
                await browser.close()
        logger.info("[trustpilot] Scraped %d reviews", len(reviews))
        return reviews

    async def _scrape_all(
        self, page: Page, business_name: str, limit: int, reviews: list[dict]
    ) -> None:
        # Search for the business
        slug = _to_slug(business_name)
        search_url = f"{BASE_URL}/search?query={slug}"
        await page.goto(search_url, wait_until="domcontentloaded", timeout=30_000)
        await random_delay(1000, 2000)

        # Accept cookies
        try:
            cookie_btn = page.locator("#onetrust-accept-btn-handler, button:has-text('Accept all')").first
            if await cookie_btn.count() > 0:
                await cookie_btn.click()
                await random_delay()
        except Exception:
            pass

        # Click first business result
        try:
            biz_link = page.locator("a[href*='/review/']").first
            await biz_link.wait_for(timeout=8_000)
            biz_href = await biz_link.get_attribute("href")
            if not biz_href:
                raise RuntimeError("No business link found")
            await page.goto(f"{BASE_URL}{biz_href}", wait_until="domcontentloaded", timeout=30_000)
            await random_delay(1500, 2500)
        except Exception as exc:
            raise RuntimeError(f"Business not found on Trustpilot: {exc}") from exc

        page_num = 1
        seen_keys: set[str] = set()

        while len(reviews) < limit:
            cards = await page.locator("article[class*='review']").all()
            if not cards:
                # Fallback selector
                cards = await page.locator("div[data-service-review-card-paper]").all()

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
                    logger.debug("[trustpilot] Card error: %s", exc)

            # Pagination
            try:
                next_btn = page.locator("a[name='pagination-button-next'], a[href*='?page=']").last
                next_href = await next_btn.get_attribute("href")
                if not next_href or "page" not in next_href:
                    break
                page_num += 1
                await page.goto(
                    f"{BASE_URL}{next_href}" if next_href.startswith("/") else next_href,
                    wait_until="domcontentloaded",
                    timeout=30_000,
                )
                await random_delay(1500, 2500)
            except Exception:
                break  # No more pages

            if len(reviews) == prev_len:
                break  # Stuck

    async def _extract_card(self, card) -> dict | None:
        try:
            # Author — try attribute-based selector first, fall back to any name-like span
            author_el = card.locator(
                "span[data-consumer-name-typography], "
                "span[class*='consumerName'], "
                "a[name='consumer-profile'] span, "
                "div[class*='consumerInfo'] span"
            ).first
            author = clean_text(await author_el.inner_text()) if await author_el.count() > 0 else "Anonymous"

            # Rating — attribute or star-image alt text
            rating_el = card.locator(
                "div[data-service-review-rating], "
                "img[alt*='Rated'], "
                "div[class*='starRating'], "
                "span[class*='stars']"
            ).first
            rating = None
            if await rating_el.count() > 0:
                rating_raw = (
                    await rating_el.get_attribute("data-service-review-rating")
                    or await rating_el.get_attribute("alt")
                    or await rating_el.get_attribute("aria-label")
                    or ""
                )
                rating = _parse_rating(rating_raw)

            # Title — h2 with data attr or any h2 inside card
            title_el = card.locator(
                "h2[data-service-review-title-typography], "
                "h2[class*='title'], "
                "h3[class*='title']"
            ).first
            title = clean_text(await title_el.inner_text()) if await title_el.count() > 0 else ""

            # Body — try data attr first, then any paragraph or div with review text
            body_el = card.locator(
                "p[data-service-review-text-typography], "
                "[data-service-review-text-typography], "
                "p[class*='reviewContent'], "
                "div[class*='reviewContent'] p, "
                "section[class*='content'] p"
            ).first
            body = clean_text(await body_el.inner_text()) if await body_el.count() > 0 else ""

            # If both title and body are still empty, grab all paragraph text from card
            if not title and not body:
                all_p = await card.locator("p").all()
                parts = []
                for p in all_p:
                    t = clean_text(await p.inner_text())
                    if t and len(t) > 3:
                        parts.append(t)
                body = " ".join(parts)

            text = f"{title} {body}".strip() if title else body

            date_el = card.locator("time").first
            date_raw = await date_el.get_attribute("datetime") if await date_el.count() > 0 else ""
            date = _parse_iso_date(date_raw)

            return {
                "platform": "trustpilot",
                "author": author,
                "rating": rating,
                "text": text,
                "date": date,
            }
        except Exception as exc:
            logger.debug("[trustpilot] Card parse error: %s", exc)
            return None


def _to_slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "+", name.lower()).strip("+")


def _parse_rating(raw: str) -> int | None:
    match = re.search(r"(\d)", raw or "")
    return int(match.group(1)) if match else None


def _parse_iso_date(raw: str) -> str:
    if not raw:
        return ""
    match = re.search(r"\d{4}-\d{2}-\d{2}", raw)
    return match.group(0) if match else raw[:10]
