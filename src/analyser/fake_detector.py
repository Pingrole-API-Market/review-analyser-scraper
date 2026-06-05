import logging
import re
from collections import defaultdict
from datetime import datetime, timedelta

from src.utils import word_count

logger = logging.getLogger(__name__)

# Burst window: if the same author posts >N reviews within this many days → suspicious
_BURST_DAYS = 7
_BURST_THRESHOLD = 3

# Generic filler phrases common in fake reviews
_GENERIC_PHRASES = [
    "great place", "highly recommend", "best ever", "worst ever",
    "five stars", "one star", "amazing service", "terrible service",
    "will be back", "never going back", "love this place", "hate this place",
]


class FakeReviewDetector:
    def __init__(self) -> None:
        # author → list of ISO date strings, built per-run
        self._author_dates: dict[str, list[str]] = defaultdict(list)

    def register_batch(self, reviews: list[dict]) -> None:
        """Pre-scan a batch to build per-author date index for burst detection."""
        for r in reviews:
            author = (r.get("author") or "").strip().lower()
            date = r.get("date") or ""
            if author and date:
                self._author_dates[author].append(date)

    def is_fake(self, review: dict) -> bool:
        text = (review.get("text") or "").strip()
        rating = review.get("rating")
        author = (review.get("author") or "").strip().lower()
        date = review.get("date") or ""

        # Rule 1: text shorter than 10 words
        if word_count(text) < 10:
            return True

        # Rule 2: 5-star (or 1-star) rating with empty text
        if rating in (5, 1) and not text:
            return True

        # Rule 3: pure generic filler with no specific detail
        if text and self._is_generic_only(text):
            return True

        # Rule 4: author burst — many reviews in a short window
        if author and self._is_burst_author(author, date):
            return True

        return False

    # ------------------------------------------------------------------
    def _is_generic_only(self, text: str) -> bool:
        lower = text.lower()
        for phrase in _GENERIC_PHRASES:
            if phrase in lower:
                # If the entire review is basically just the phrase
                if word_count(lower) <= word_count(phrase) + 3:
                    return True
        return False

    def _is_burst_author(self, author: str, current_date_str: str) -> bool:
        if not current_date_str:
            return False
        dates = self._author_dates.get(author, [])
        if len(dates) < _BURST_THRESHOLD:
            return False
        try:
            current_dt = _parse_date(current_date_str)
            if current_dt is None:
                return False
            window_start = current_dt - timedelta(days=_BURST_DAYS)
            nearby = [
                d for d_str in dates
                if (d := _parse_date(d_str)) is not None
                and window_start <= d <= current_dt + timedelta(days=_BURST_DAYS)
            ]
            return len(nearby) >= _BURST_THRESHOLD
        except Exception:
            return False


def _parse_date(date_str: str) -> datetime | None:
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d/%m/%Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(date_str[:10], fmt)
        except ValueError:
            continue
    return None
