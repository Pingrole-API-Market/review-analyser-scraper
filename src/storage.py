import hashlib
import logging
import os
from datetime import datetime

from pymongo import MongoClient, UpdateOne
from pymongo.errors import BulkWriteError, ConnectionFailure

logger = logging.getLogger(__name__)

_DB_NAME      = "review_analyser"
_REVIEWS_COLL = "reviews"
_RESULTS_COLL = "platform_results"


class MongoStorage:
    def __init__(self, uri: str | None = None) -> None:
        uri = uri or os.environ.get("MONGODB_URI", "")
        if not uri:
            logger.warning("MONGODB_URI not set — MongoDB storage disabled")
            self._db = None
            self._client = None
            return
        try:
            self._client = MongoClient(uri, serverSelectionTimeoutMS=5_000)
            self._client.admin.command("ping")
            self._db = self._client[_DB_NAME]
            self._ensure_indexes()
            logger.info("MongoDB connected: %s", _DB_NAME)
        except ConnectionFailure as exc:
            logger.error("MongoDB connection failed: %s", exc)
            self._client = None
            self._db = None

    def _ensure_indexes(self) -> None:
        if self._db is None:
            return
        self._db[_REVIEWS_COLL].create_index(
            [("platform", 1), ("author", 1), ("date", 1), ("body_hash", 1)],
            unique=True,
            name="unique_review",
        )
        self._db[_RESULTS_COLL].create_index(
            [("business_name", 1), ("platform", 1), ("scraped_at", -1)],
            name="biz_platform_time",
        )

    def save_platform_result(self, result: dict) -> None:
        if self._db is None:
            return
        reviews = result.get("reviews", [])
        # Upsert individual reviews
        if reviews:
            ops = []
            for r in reviews:
                key = {
                    "platform":  result.get("platform"),
                    "author":    r.get("author"),
                    "date":      r.get("date"),
                    "body_hash": _hash(r.get("body", "")),
                }
                ops.append(UpdateOne(
                    key,
                    {"$set": {**r, **key, "business_name": result.get("business_name"),
                              "updated_at": datetime.utcnow().isoformat()}},
                    upsert=True,
                ))
            try:
                self._db[_REVIEWS_COLL].bulk_write(ops, ordered=False)
            except BulkWriteError as e:
                logger.warning("MongoDB bulk write partial error: %s", e.details)

        # Save platform-level result (without the reviews array to keep it lean)
        try:
            summary = {k: v for k, v in result.items() if k != "reviews"}
            summary["review_count"] = len(reviews)
            summary["stored_at"] = datetime.utcnow().isoformat()
            self._db[_RESULTS_COLL].insert_one(summary)
        except Exception as exc:
            logger.error("MongoDB save_platform_result failed: %s", exc)

    def close(self) -> None:
        if self._client:
            self._client.close()


def _hash(text: str) -> str:
    return hashlib.md5((text or "").encode("utf-8", errors="ignore")).hexdigest()[:16]
