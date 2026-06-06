import csv
import io
import logging

logger = logging.getLogger(__name__)

_FIELDS = [
    "platform", "business_name", "overall_rating", "total_reviews",
    "author", "author_country", "author_total_reviews",
    "rating", "title", "body", "date", "verified", "unprompted",
]


def export_csv(results: list[dict]) -> bytes:
    """Flatten all platform results into a single CSV — one row per review."""
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=_FIELDS, extrasaction="ignore")
    writer.writeheader()
    for result in results:
        base = {
            "platform":      result.get("platform", ""),
            "business_name": result.get("business_name", ""),
            "overall_rating": result.get("overall_rating"),
            "total_reviews":  result.get("total_reviews"),
        }
        for review in result.get("reviews", []):
            writer.writerow({**base, **review})
    return buf.getvalue().encode("utf-8")
