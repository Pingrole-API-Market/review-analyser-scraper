"""Deliver generated report files via email or Discord."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from src.delivery.discord_sender import send_discord_dm_with_file, send_infra_alert
from src.delivery.email_sender import send_email_with_attachment

logger = logging.getLogger(__name__)


async def deliver_file(
    platform: str,
    address: str,
    filename: str,
    file_bytes: bytes,
    summary: dict[str, Any],
) -> dict[str, Any]:
    platform = (platform or "").strip().lower()
    address = (address or "").strip()
    result: dict[str, Any] = {
        "success": False,
        "platform": platform,
        "destination": address,
        "filename": filename,
        "error": None,
    }

    if platform == "email":
        success, error = await asyncio.to_thread(
            send_email_with_attachment, address, filename, file_bytes, summary,
        )
    elif platform == "discord":
        success, error = await send_discord_dm_with_file(
            address, filename, file_bytes, summary,
        )
    else:
        error = f"Unknown destination platform: {platform}"
        success = False

    result["success"] = success
    result["error"] = error

    if not success and error:
        logger.warning("File delivery failed (%s → %s): %s", platform, address, error)
        await send_infra_alert(f"Review scraper delivery failed ({platform} → {address}): {error}")

    return result
