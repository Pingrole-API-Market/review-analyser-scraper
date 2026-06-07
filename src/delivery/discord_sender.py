"""Discord bot DM delivery with file attachment."""
from __future__ import annotations

import json
import logging
import os
import re
from typing import Any

import httpx

logger = logging.getLogger(__name__)

DISCORD_API = "https://discord.com/api/v10"
JOIN_SERVER_URL = "https://discord.gg/p5aCRvkHWE"
NUMERIC_ID_RE = re.compile(r"^\d{17,20}$")


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bot {token}"}


def _mime_type(filename: str) -> str:
    if filename.endswith(".csv"):
        return "text/csv"
    if filename.endswith(".xlsx"):
        return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    return "application/json"


def _build_message(summary: dict[str, Any]) -> str:
    business = summary.get("business_name", "Unknown")
    reviews = summary.get("review_count", 0)
    fmt = summary.get("format", "file")
    return (
        f"**Trustpilot Review Report**\n"
        f"Business: **{business}**\n"
        f"Reviews scraped: **{reviews}**\n"
        f"Attached: `{fmt.upper()}` file"
    )


async def send_infra_alert(message: str) -> None:
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL", "").strip()
    if not webhook_url:
        return
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            await client.post(webhook_url, json={"content": message[:1900]})
    except Exception as exc:
        logger.error("Infra webhook alert failed: %s", exc)


async def _guild_id(client: httpx.AsyncClient, token: str, channel_id: str) -> str | None:
    response = await client.get(
        f"{DISCORD_API}/channels/{channel_id}",
        headers=_headers(token),
    )
    if response.status_code != 200:
        return None
    return response.json().get("guild_id")


def _matches_username(member: dict, query: str) -> bool:
    user = member.get("user") or {}
    q = query.lower().lstrip("@")
    candidates = {
        (user.get("username") or "").lower(),
        (user.get("global_name") or "").lower(),
    }
    return q in candidates


async def _resolve_user_id(
    client: httpx.AsyncClient,
    token: str,
    guild_id: str,
    username_or_id: str,
) -> str | None:
    s = (username_or_id or "").strip().lstrip("@")
    if not s:
        return None
    if NUMERIC_ID_RE.match(s):
        return s

    response = await client.get(
        f"{DISCORD_API}/guilds/{guild_id}/members/search",
        headers=_headers(token),
        params={"query": s, "limit": 10},
    )
    if response.status_code != 200:
        logger.error("Discord member search failed: %d %s", response.status_code, response.text)
        return None

    for member in response.json():
        if _matches_username(member, s):
            return str((member.get("user") or {}).get("id"))

    return None


async def send_discord_dm_with_file(
    username_or_id: str,
    filename: str,
    file_bytes: bytes,
    summary: dict[str, Any],
) -> tuple[bool, str | None]:
    token = os.environ.get("DISCORD_TOKEN", "").strip()
    channel_id = os.environ.get("DISCORD_INFRA_CHANNEL_ID", "").strip()
    if not token or not channel_id:
        return False, "DISCORD_TOKEN or DISCORD_INFRA_CHANNEL_ID is not configured"

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            guild_id = await _guild_id(client, token, channel_id)
            if not guild_id:
                return False, "Could not resolve Discord guild from DISCORD_INFRA_CHANNEL_ID"

            user_id = await _resolve_user_id(client, token, guild_id, username_or_id)
            if not user_id:
                return False, (
                    f"Discord user '{username_or_id}' not found in the server. "
                    f"Join first: {JOIN_SERVER_URL}"
                )

            dm_response = await client.post(
                f"{DISCORD_API}/users/@me/channels",
                headers=_headers(token),
                json={"recipient_id": user_id},
            )
            if dm_response.status_code not in (200, 201):
                logger.error("Discord DM channel create failed: %d %s", dm_response.status_code, dm_response.text)
                return False, f"Could not open Discord DM (HTTP {dm_response.status_code})"

            dm_channel_id = dm_response.json()["id"]
            message = _build_message(summary)
            msg_response = await client.post(
                f"{DISCORD_API}/channels/{dm_channel_id}/messages",
                headers=_headers(token),
                data={"payload_json": json.dumps({"content": message})},
                files={"files[0]": (filename, file_bytes, _mime_type(filename))},
            )
            if msg_response.status_code not in (200, 201):
                logger.error("Discord DM send failed: %d %s", msg_response.status_code, msg_response.text)
                return False, f"Discord DM send failed (HTTP {msg_response.status_code})"

        logger.info("Discord DM sent to %s with attachment %s", username_or_id, filename)
        return True, None
    except Exception as exc:
        logger.error("Discord DM error: %s", exc)
        await send_infra_alert(f"Discord delivery failed for {username_or_id}: {exc}")
        return False, str(exc)
