import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def export_json(output: dict) -> bytes:
    return json.dumps(output, indent=2, default=_default_serialiser).encode("utf-8")


def _default_serialiser(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serialisable")
