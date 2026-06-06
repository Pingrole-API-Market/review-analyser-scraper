import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def export_json(results: list[dict]) -> bytes:
    """Serialize the full list of platform results to JSON."""
    return json.dumps(results, indent=2, default=_serialise).encode("utf-8")


def _serialise(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serialisable")
