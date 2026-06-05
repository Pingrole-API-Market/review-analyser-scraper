import logging
import os
from datetime import datetime

from pymongo import MongoClient, UpdateOne
from pymongo.errors import BulkWriteError, ConnectionFailure

logger = logging.getLogger(__name__)

_DB_NAME = "review_analyser"
_REVIEWS_COLL = "reviews"
_RESULTS_COLL = "analysed_results"


class MongoStorage:
    def __init__(self, uri: str | None = None) -> None:
        uri = uri or os.environ.get("MONGODB_URI", "")
        if not uri:
            logger.warning("MONGODB_URI not set — MongoDB storage disabled")
            self._client = None
            self._db = None
            return
        try:
            self._client = MongoClient(uri, serverSelectionTimeoutMS=5000)
            # Verify connection
            self._client.admin.command("ping")
            self._db = self._client[_DB_NAME]
            self._ensure_indexes()
            logger.info("MongoDB connected: %s", _DB_NAME)
        except ConnectionFailure as exc:
            logger.error("MongoDB connection failed: %s", exc)
            self._client = None
            self._db = None

    # ------------------------------------------------------------------
    def _ensure_indexes(self) -> None:
        if self._db is None:
            return
        # Unique composite key per review to prevent duplicates
        self._db[_REVIEWS_COLL].create_index(
            [("platform", 1), ("author", 1), ("date", 1), ("text_hash", 1)],
            unique=True,
            name="unique_review",
        )
        self._db[_RESULTS_COLL].create_index(
            [("business_name", 1), ("scraped_at", -1)],
            name="business_time",
        )

    # ------------------------------------------------------------------
    def upsert_reviews(self, reviews: list[dict]) -> int:
        if self._db is None or not reviews:
            return 0
        ops = []
        for r in reviews:
            key = {
                "platform": r.get("platform"),
                "author": r.get("author"),
                "date": r.get("date"),
                "text_hash": _short_hash(r.get("text", "")),
            }
            ops.append(
                UpdateOne(
                    key,
                    {"$set": {**r, **key, "updated_at": datetime.utcnow().isoformat()}},
                    upsert=True,
                )
            )
        try:
            result = self._db[_REVIEWS_COLL].bulk_write(ops, ordered=False)
            inserted = result.upserted_count + result.modified_count
            logger.info("MongoDB: %d review ops completed", inserted)
            return inserted
        except BulkWriteError as bwe:
            logger.warning("MongoDB bulk write partial error: %s", bwe.details)
            return 0

    def save_result(self, result: dict) -> None:
        if self._db is None:
            return
        try:
            self._db[_RESULTS_COLL].insert_one(
                {**result, "stored_at": datetime.utcnow().isoformat()}
            )
        except Exception as exc:
            logger.error("MongoDB save_result failed: %s", exc)

    def close(self) -> None:
        if self._client:
            self._client.close()


def _short_hash(text: str) -> str:
    import hashlib
    return hashlib.md5((text or "").encode("utf-8", errors="ignore")).hexdigest()[:16]
