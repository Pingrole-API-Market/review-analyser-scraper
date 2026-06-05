"""Glassdoor company reviews scraper using Playwright."""
import logging
import re
from datetime import datetime

from playwright.async_api import Page, async_playwright

from src.utils import clean_text, random_delay, random_user_agent, random_viewport, retry

logger = logging.getLogger(__name__)

BASE_URL = "https://www.glassdoor.com"


class GlassdoorScraper:
    PLATFORM = "glassdoor"

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
                    lambda: self._scrape_all(page, business_name, location, limit, reviews),
                    retries=3,
                    label="glassdoor",
                )
            except Exception as exc:
                logger.error("[glassdoor] Fatal error: %s", exc)
            finally:
                await browser.close()
        logger.info("[glassdoor] Scraped %d reviews", len(reviews))
        return reviews

    async def _scrape_all(
        self, page: Page, business_name: str, location: str, limit: int, reviews: list[dict]
    ) -> None:
        search_url = (
            f"{BASE_URL}/Search/results.htm"
            f"?keyword={business_name.replace(' ', '+')}"
            f"&locKeyword={location.replace(' ', '+')}"
        )
        await page.goto(search_url, wait_until="domcontentloaded", timeout=30_000)
        await random_delay(1500, 2500)

        # Accept cookies / privacy banner
        try:
            cookie_btn = page.locator("button#onetrust-accept-btn-handler, button:has-text('Accept')").first
            if await cookie_btn.count() > 0:
                await cookie_btn.click()
                await random_delay()
        except Exception:
            pass

        # Click on first company result
        try:
            company_link = page.locator("a[href*='/Reviews/'], a[data-test='employer-link']").first
            await company_link.wait_for(timeout=10_000)
            href = await company_link.get_attribute("href")
            if not href:
                raise RuntimeError("No company link found")
            reviews_url = href if href.startswith("http") else f"{BASE_URL}{href}"
            # Ensure we land on the reviews page
            if "/Reviews/" not in reviews_url:
                reviews_url = re.sub(r"/Overview/", "/Reviews/", reviews_url)
        except Exception as exc:
            raise RuntimeError(f"Glassdoor company not found: {exc}") from exc

        page_num = 1
        seen_keys: set[str] = set()

        while len(reviews) < limit:
            url = reviews_url if page_num == 1 else f"{reviews_url}_P{page_num}.htm"
            await page.goto(url, wait_until="domcontentloaded", timeout=30_000)
            await random_delay(2000, 3500)

            # Handle sign-in wall — try to dismiss
            try:
                modal_close = page.locator("span.modal_closeIcon, button[alt='Close']").first
                if await modal_close.count() > 0:
                    await modal_close.click()
                    await random_delay()
            except Exception:
                pass

            cards = await page.locator("li[class*='ReviewsList__review'], div[id^='review_']").all()
            if not cards:
                logger.debug("[glassdoor] No cards on page %d", page_num)
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
                    logger.debug("[glassdoor] Card error: %s", exc)

            if len(reviews) == prev_len:
                break

            # Check for next page
            next_btn = page.locator("button[data-test='pagination-next'], a.nextButton").first
            if await next_btn.count() == 0:
                break
            page_num += 1

    async def _extract_card(self, card) -> dict | None:
        try:
            # Expand if collapsed
            show_more = card.locator("span.link:has-text('Show More')").first
            if await show_more.count() > 0:
                await show_more.click()
                await random_delay(300, 600)

            author_el = card.locator("span[class*='authorJobTitle'], div[class*='reviewer']").first
            author = clean_text(await author_el.inner_text()) if await author_el.count() > 0 else "Employee"

            rating_el = card.locator("span[class*='ratingNumber'], div[class*='starRating']").first
            rating = None
            if await rating_el.count() > 0:
                rating_text = clean_text(await rating_el.inner_text())
                m = re.search(r"(\d\.?\d?)", rating_text)
                if m:
                    rating = round(float(m.group(1)))

            title_el = card.locator("a.reviewLink, h2[class*='summary']").first
            title = clean_text(await title_el.inner_text()) if await title_el.count() > 0 else ""

            pros_el = card.locator("span[data-test='pros']").first
            cons_el = card.locator("span[data-test='cons']").first
            pros = clean_text(await pros_el.inner_text()) if await pros_el.count() > 0 else ""
            cons = clean_text(await cons_el.inner_text()) if await cons_el.count() > 0 else ""
            text_parts = [p for p in [title, pros, cons] if p]
            text = " | ".join(text_parts)

            date_el = card.locator("time, span[class*='reviewDate']").first
            date_raw = ""
            if await date_el.count() > 0:
                date_raw = (
                    await date_el.get_attribute("datetime")
                    or clean_text(await date_el.inner_text())
                )
            date = _parse_date(date_raw)

            return {
                "platform": "glassdoor",
                "author": author,
                "rating": rating,
                "text": text,
                "date": date,
            }
        except Exception as exc:
            logger.debug("[glassdoor] Card parse error: %s", exc)
            return None


def _parse_date(raw: str) -> str:
    if not raw:
        return ""
    for fmt in ("%b %d, %Y", "%Y-%m-%d", "%B %d, %Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(raw.strip()[:20], fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    iso = re.search(r"\d{4}-\d{2}-\d{2}", raw)
    return iso.group(0) if iso else raw[:10]
