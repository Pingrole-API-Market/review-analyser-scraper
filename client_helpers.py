"""Helpers for calling the Actor from the Apify Python client."""
from __future__ import annotations

from pathlib import Path

EXPORT_KEY_PREFIX = "export-"
EXPORT_EXTENSIONS = (".xlsx", ".csv", ".json")
SKIP_KEYS = frozenset({"INPUT", "OUTPUT"})


def download_export_file(client, run: dict, *, save_dir: str | Path = ".") -> Path | None:
    """Download the export file from a finished run's Key-Value store."""
    kv = client.key_value_store(run["defaultKeyValueStoreId"])
    save_dir = Path(save_dir)

    output = kv.get_record("OUTPUT")
    output_value = output.get("value") if output else None
    if isinstance(output_value, dict):
        meta = output_value.get("export_file")
        if isinstance(meta, dict) and meta.get("key"):
            return _save_record(kv, meta["key"], save_dir, meta.get("filename"))

    for item in kv.list_keys().get("items", []):
        key = item["key"]
        if key.startswith(EXPORT_KEY_PREFIX) and key.endswith(EXPORT_EXTENSIONS):
            return _save_record(kv, key, save_dir)
        if key.endswith(EXPORT_EXTENSIONS) and key not in SKIP_KEYS:
            return _save_record(kv, key, save_dir)

    return None


def _save_record(kv, key: str, save_dir: Path, filename: str | None = None) -> Path:
    record = kv.get_record(key)
    value = record["value"]
    if isinstance(value, str):
        value = value.encode("utf-8")
    save_as = save_dir / (filename or key.removeprefix(EXPORT_KEY_PREFIX))
    save_as.write_bytes(value)
    return save_as
