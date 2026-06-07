"""Office365 email delivery with file attachment."""
from __future__ import annotations

import logging
import os
import smtplib
from email.message import EmailMessage
from typing import Any

logger = logging.getLogger(__name__)


def _attachment_parts(filename: str) -> tuple[str, str]:
    if filename.endswith(".csv"):
        return "text", "csv"
    if filename.endswith(".xlsx"):
        return "application", "vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    return "application", "json"


def _build_html(summary: dict[str, Any]) -> str:
    business = summary.get("business_name", "Unknown")
    reviews = summary.get("review_count", 0)
    fmt = summary.get("format", "file")
    return f"""
    <html><body>
      <h2>Trustpilot Review Report</h2>
      <p><strong>Business:</strong> {business}</p>
      <p><strong>Reviews scraped:</strong> {reviews}</p>
      <p>Your {fmt.upper()} report is attached.</p>
    </body></html>
    """


def send_email_with_attachment(
    to_email: str,
    filename: str,
    file_bytes: bytes,
    summary: dict[str, Any],
) -> tuple[bool, str | None]:
    sender = os.environ.get("PINGROLE_EMAIL", "").strip()
    password = os.environ.get("PINGROLE_PASSWORD", "").strip()
    if not sender or not password:
        return False, "PINGROLE_EMAIL or PINGROLE_PASSWORD is not configured"

    subject = f"Trustpilot review report — {summary.get('business_name', 'Unknown')}"
    html = _build_html(summary)

    try:
        msg = EmailMessage()
        msg["From"] = sender
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.set_content("Your email client does not support HTML.")
        msg.add_alternative(html, subtype="html")
        maintype, subtype = _attachment_parts(filename)
        msg.add_attachment(file_bytes, maintype=maintype, subtype=subtype, filename=filename)

        with smtplib.SMTP("smtp.office365.com", 587, timeout=20) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.ehlo()
            smtp.login(sender, password)
            smtp.send_message(msg)

        logger.info("Email sent to %s with attachment %s", to_email, filename)
        return True, None
    except Exception as exc:
        logger.error("Office365 SMTP error: %s", exc)
        return False, str(exc)
