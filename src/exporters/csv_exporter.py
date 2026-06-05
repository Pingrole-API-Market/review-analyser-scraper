import csv
import io
import logging

logger = logging.getLogger(__name__)

_FIELDS = [
    "platform", "author", "rating", "date", "text",
    "sentiment", "sentiment_score", "topics", "is_fake_flag",
]


def export_csv(reviews: list[dict]) -> bytes:
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=_FIELDS, extrasaction="ignore")
    writer.writeheader()
    for r in reviews:
        row = dict(r)
        if isinstance(row.get("topics"), list):
            row["topics"] = ", ".join(row["topics"])
        writer.writerow(row)
    return buf.getvalue().encode("utf-8")
