import io
import logging

import openpyxl
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

logger = logging.getLogger(__name__)

_REVIEW_HEADERS = [
    "Platform", "Author", "Rating", "Date", "Text",
    "Sentiment", "Sentiment Score", "Topics", "Fake Flag",
]
_REVIEW_KEYS = [
    "platform", "author", "rating", "date", "text",
    "sentiment", "sentiment_score", "topics", "is_fake_flag",
]

_HEADER_FILL = PatternFill("solid", fgColor="4472C4")
_HEADER_FONT = Font(bold=True, color="FFFFFF")


def export_xlsx(reviews: list[dict], summary: dict) -> bytes:
    wb = openpyxl.Workbook()

    # ── Summary sheet ────────────────────────────────────────────────
    ws_sum = wb.active
    ws_sum.title = "Summary"
    summary_rows = [
        ("Business", summary.get("business_name", "")),
        ("Location", summary.get("location", "")),
        ("Platforms Scraped", ", ".join(summary.get("platforms_scraped", []))),
        ("Total Reviews Analysed", summary.get("total_reviews_analysed", 0)),
        ("Overall Sentiment", summary.get("overall_sentiment", "")),
        ("Average Rating", summary.get("average_rating", "")),
        ("Rating Trend", summary.get("rating_trend", "")),
        ("Positive %", summary.get("sentiment_breakdown", {}).get("positive", 0)),
        ("Neutral %", summary.get("sentiment_breakdown", {}).get("neutral", 0)),
        ("Negative %", summary.get("sentiment_breakdown", {}).get("negative", 0)),
        ("Top Complaints", ", ".join(summary.get("top_complaints", []))),
        ("Top Praises", ", ".join(summary.get("top_praises", []))),
        ("Top Keywords", ", ".join(summary.get("top_keywords", []))),
        ("Fake Review Risk", summary.get("fake_review_risk", "")),
        ("Fake Review Count", summary.get("fake_review_count", 0)),
        ("Scraped At", summary.get("scraped_at", "")),
    ]
    ws_sum.column_dimensions["A"].width = 26
    ws_sum.column_dimensions["B"].width = 55
    for row_data in summary_rows:
        ws_sum.append(row_data)
    for cell in ws_sum["A"]:
        cell.font = Font(bold=True)

    # ── Reviews sheet ────────────────────────────────────────────────
    ws_rev = wb.create_sheet("Reviews")
    ws_rev.append(_REVIEW_HEADERS)
    for col_idx, _ in enumerate(_REVIEW_HEADERS, start=1):
        cell = ws_rev.cell(row=1, column=col_idx)
        cell.fill = _HEADER_FILL
        cell.font = _HEADER_FONT

    for review in reviews:
        row = []
        for key in _REVIEW_KEYS:
            val = review.get(key, "")
            if isinstance(val, list):
                val = ", ".join(str(v) for v in val)
            row.append(val)
        ws_rev.append(row)

    # Auto-width
    for col_idx, _ in enumerate(_REVIEW_HEADERS, start=1):
        col_letter = get_column_letter(col_idx)
        max_len = max(
            (len(str(ws_rev.cell(r, col_idx).value or "")) for r in range(1, ws_rev.max_row + 1)),
            default=10,
        )
        ws_rev.column_dimensions[col_letter].width = min(max_len + 4, 60)

    # Wrap text in "Text" column (index 5)
    text_col = get_column_letter(5)
    for row_idx in range(2, ws_rev.max_row + 1):
        ws_rev[f"{text_col}{row_idx}"].alignment = Alignment(wrap_text=True)

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()
