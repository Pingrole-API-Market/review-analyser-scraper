import asyncio
import logging
import random
import re
from datetime import datetime
from typing import Any, Callable, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 OPR/110.0.0.0",
]

VIEWPORTS = [
    {"width": 1920, "height": 1080},
    {"width": 1440, "height": 900},
    {"width": 1366, "height": 768},
    {"width": 1280, "height": 800},
    {"width": 1536, "height": 864},
]


def random_user_agent() -> str:
    return random.choice(USER_AGENTS)


def random_viewport() -> dict:
    return random.choice(VIEWPORTS)


async def random_delay(min_ms: int = 800, max_ms: int = 2500) -> None:
    await asyncio.sleep(random.randint(min_ms, max_ms) / 1000)


async def retry(
    fn: Callable[[], Any],
    retries: int = 3,
    delay_s: float = 2.0,
    label: str = "",
) -> Any:
    last_exc: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            return await fn()
        except Exception as exc:
            last_exc = exc
            logger.warning(
                "Attempt %d/%d failed%s: %s",
                attempt,
                retries,
                f" [{label}]" if label else "",
                exc,
            )
            if attempt < retries:
                await asyncio.sleep(delay_s * attempt)
    raise last_exc  # type: ignore[misc]


def clean_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text or "")
    return text.strip()


def word_count(text: str) -> int:
    return len(text.split()) if text else 0


def now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"


def rating_trend(reviews: list[dict]) -> str:
    """Determine trend from chronologically ordered reviews."""
    dated = [r for r in reviews if r.get("date")]
    if len(dated) < 6:
        return "insufficient_data"
    try:
        dated_sorted = sorted(dated, key=lambda r: r["date"])
        half = len(dated_sorted) // 2
        old_avg = sum(r.get("rating", 0) or 0 for r in dated_sorted[:half]) / half
        new_avg = sum(r.get("rating", 0) or 0 for r in dated_sorted[half:]) / half
        diff = new_avg - old_avg
        if diff > 0.3:
            return "improving"
        if diff < -0.3:
            return "declining"
        return "stable"
    except Exception:
        return "unknown"


def compute_overall_sentiment(breakdown: dict) -> str:
    pos = breakdown.get("positive", 0)
    neg = breakdown.get("negative", 0)
    if pos >= neg * 1.5:
        return "positive"
    if neg >= pos * 1.5:
        return "negative"
    return "neutral"
