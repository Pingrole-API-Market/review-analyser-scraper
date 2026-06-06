"""Trustpilot company reviews scraper."""
import logging
import re

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
            "rating_breakdown": None,
            "company_info": None,
            "reviews": [],
        }
        if browser is not None:
            await self._run(business_name, location, limit, browser, result)
        else:
            async with async_playwright() as pw:
                _b = await pw.chromium.launch(headless=True, args=["--no-sandbox"])
                await self._run(business_name, location, limit, _b, result)
                await _b.close()

        # Fallback: compute from scraped reviews when page selectors failed
        if result["total_reviews"] is None:
            result["total_reviews"] = len(result["reviews"])
        if result["rating_breakdown"] is None and result["reviews"]:
            bd: dict[str, int] = {f"{s}_star": 0 for s in range(1, 6)}
            for r in result["reviews"]:
                if r.get("rating"):
                    bd[f"{r['rating']}_star"] = bd.get(f"{r['rating']}_star", 0) + 1
            result["rating_breakdown"] = bd

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

        # Scrape company details (categories, description, address, phone, email, website)
        info_url = company_url.split("?")[0].rstrip("/") + "/info"
        await self._scrape_company_info(page, info_url, result)

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
        # Overall TrustScore — try data-attribute first, then broad text scan
        try:
            for sel in [
                "[data-rating-typography]",
                "[data-rating-value]",
                "div[class*='trustScore'] [class*='typography']",
                "div[class*='header'] [class*='rating'] p",
            ]:
                el = page.locator(sel).first
                if await el.count() > 0:
                    raw = clean_text(await el.inner_text())
                    m = re.search(r"(\d+[.,]\d+|\d+)", raw)
                    if m:
                        val = float(m.group(1).replace(",", "."))
                        if 1.0 <= val <= 5.0:
                            result["overall_rating"] = val
                            break
        except Exception:
            pass

        # Total review count — avoid "N reviews in the last 12 months" by targeting specific elements
        try:
            for sel in [
                "[data-reviews-count-typography]",
                "[class*='reviewsCount']",
                "a[href*='?languages=all']",       # "All reviews (N)" link
                "a[href*='?languages']:has-text('All')",
            ]:
                el = page.locator(sel).first
                if await el.count() > 0:
                    raw = clean_text(await el.inner_text())
                    # Prefer number in parentheses "(152)", else first bare number
                    m = re.search(r"\(([\d,]+)\)", raw) or re.search(r"([\d,]+)", raw)
                    if m:
                        result["total_reviews"] = int(m.group(1).replace(",", ""))
                        break
        except Exception:
            pass

        # Rating breakdown — parse histogram container text then compute counts from percentages
        try:
            total = result.get("total_reviews") or 0
            breakdown: dict[str, int] = {}

            histogram = page.locator(
                "div[class*='histogram'], [class*='ratingDistribution']"
            ).first
            if await histogram.count() > 0:
                full_text = clean_text(await histogram.inner_text())
                for m in re.finditer(r"([1-5])\s*[- ]?stars?\s+(\d+)\s*%", full_text, re.I):
                    pct = int(m.group(2))
                    breakdown[f"{m.group(1)}_star"] = round(pct / 100 * total) if total else pct

            if not breakdown:
                # Fallback: iterate individual bar elements
                for row in await page.locator(
                    "div[class*='histogramBar'], div[class*='histogram'] > div > div"
                ).all():
                    try:
                        text = clean_text(await row.inner_text())
                        sm = re.search(r"([1-5])\s*[- ]?stars?", text, re.I)
                        pm = re.search(r"(\d+)\s*%", text)
                        if sm and pm:
                            pct = int(pm.group(1))
                            breakdown[f"{sm.group(1)}_star"] = round(pct / 100 * total) if total else pct
                    except Exception:
                        continue

            if breakdown:
                for s in range(1, 6):
                    breakdown.setdefault(f"{s}_star", 0)
                result["rating_breakdown"] = breakdown
        except Exception:
            pass

    async def _scrape_company_info(self, page: Page, info_url: str, result: dict) -> None:
        info: dict = {
            "categories": [],
            "description": None,
            "address": None,
            "phone": None,
            "email": None,
            "website": None,
        }
        try:
            await page.goto(info_url, wait_until="domcontentloaded", timeout=30_000)
            await random_delay(1000, 1500)

            # Categories (tag pills)
            try:
                cat_els = await page.locator(
                    "[class*='categoryPill'], [class*='categoryTag'], "
                    "[class*='tag'][href*='category'], [class*='BusinessCategories'] a"
                ).all()
                info["categories"] = [
                    t for el in cat_els if (t := clean_text(await el.inner_text()))
                ]
            except Exception:
                pass

            # Description written by the company
            try:
                desc_el = page.locator(
                    "[class*='businessDescription'] p, "
                    "[class*='aboutUs'] p, "
                    "section:has(h2:has-text('Written by')) p"
                ).first
                if await desc_el.count() > 0:
                    info["description"] = clean_text(await desc_el.inner_text()) or None
            except Exception:
                pass

            # Phone
            try:
                ph_el = page.locator("a[href^='tel:']").first
                if await ph_el.count() > 0:
                    href = (await ph_el.get_attribute("href") or "").replace("tel:", "")
                    info["phone"] = clean_text(await ph_el.inner_text()) or href or None
            except Exception:
                pass

            # Email
            try:
                em_el = page.locator("a[href^='mailto:']").first
                if await em_el.count() > 0:
                    href = (await em_el.get_attribute("href") or "").replace("mailto:", "")
                    info["email"] = clean_text(await em_el.inner_text()) or href or None
            except Exception:
                pass

            # Website (external link, not trustpilot)
            try:
                web_el = page.locator(
                    "a[class*='website'], a[class*='websiteUrl'], "
                    "[class*='contactInfo'] a[href^='http']:not([href*='trustpilot.com'])"
                ).first
                if await web_el.count() > 0:
                    href = await web_el.get_attribute("href") or ""
                    if href and "trustpilot.com" not in href:
                        info["website"] = href
            except Exception:
                pass

            # Address
            try:
                addr_el = page.locator(
                    "[class*='address'], "
                    "[class*='contactInfo'] li:first-child span:not([class*='icon'])"
                ).first
                if await addr_el.count() > 0:
                    info["address"] = clean_text(await addr_el.inner_text()) or None
            except Exception:
                pass

        except Exception as exc:
            logger.debug("[trustpilot] Company info page failed: %s", exc)

        if any(v for v in info.values() if v):
            result["company_info"] = info

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

            # ── Feedback text ─────────────────────────────────────────
            body_el = card.locator(
                "p[data-service-review-text-typography], "
                "[data-service-review-text-typography]"
            ).first
            feedback_text = clean_text(await body_el.inner_text()) if await body_el.count() > 0 else ""

            # Fallback: collect all <p> text in card if still empty
            if not feedback_text:
                all_p = await card.locator("p").all()
                parts = [clean_text(await p.inner_text()) for p in all_p if len(clean_text(await p.inner_text())) > 3]
                feedback_text = " ".join(parts)

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
                "feedback_text": feedback_text,
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


