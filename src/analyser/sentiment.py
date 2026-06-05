import logging
import re
from functools import lru_cache
from typing import NamedTuple

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline

logger = logging.getLogger(__name__)

MODEL_NAME = "cardiffnlp/twitter-roberta-base-sentiment"

# Mapping from model's LABEL_* to human-readable names
LABEL_MAP = {
    "LABEL_0": "negative",
    "LABEL_1": "neutral",
    "LABEL_2": "positive",
}


class SentimentResult(NamedTuple):
    label: str        # "positive" | "neutral" | "negative"
    score: float      # confidence 0–1


def _preprocess(text: str) -> str:
    """Normalise mentions and URLs before feeding to the model."""
    tokens = []
    for token in text.split():
        if token.startswith("@") and len(token) > 1:
            token = "@user"
        elif token.startswith("http"):
            token = "http"
        tokens.append(token)
    return " ".join(tokens)


class SentimentAnalyzer:
    """Loads the HuggingFace model once and reuses it across all reviews."""

    def __init__(self) -> None:
        logger.info("Loading sentiment model: %s", MODEL_NAME)
        device = 0 if torch.cuda.is_available() else -1
        self._pipe = pipeline(
            "sentiment-analysis",
            model=MODEL_NAME,
            tokenizer=MODEL_NAME,
            device=device,
            truncation=True,
            max_length=512,
        )
        logger.info("Sentiment model loaded (device=%s)", "cuda" if device == 0 else "cpu")

    def analyse(self, text: str) -> SentimentResult:
        if not text or not text.strip():
            return SentimentResult(label="neutral", score=0.5)
        processed = _preprocess(text)
        try:
            result = self._pipe(processed)[0]
            label = LABEL_MAP.get(result["label"], result["label"].lower())
            return SentimentResult(label=label, score=round(result["score"], 4))
        except Exception as exc:
            logger.warning("Sentiment inference failed: %s", exc)
            return SentimentResult(label="neutral", score=0.5)

    def analyse_batch(self, texts: list[str], batch_size: int = 32) -> list[SentimentResult]:
        results: list[SentimentResult] = []
        for i in range(0, len(texts), batch_size):
            chunk = [_preprocess(t or "") for t in texts[i : i + batch_size]]
            try:
                raw = self._pipe(chunk, truncation=True, max_length=512)
                for item in raw:
                    label = LABEL_MAP.get(item["label"], item["label"].lower())
                    results.append(SentimentResult(label=label, score=round(item["score"], 4)))
            except Exception as exc:
                logger.warning("Batch sentiment failed at index %d: %s", i, exc)
                results.extend([SentimentResult("neutral", 0.5)] * len(chunk))
        return results
