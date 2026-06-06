import logging
from typing import NamedTuple

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

logger = logging.getLogger(__name__)


class SentimentResult(NamedTuple):
    label: str    # "positive" | "neutral" | "negative"
    score: float  # dominant class probability 0–1


class SentimentAnalyzer:
    """Rule-based sentiment using VADER.

    VADER is purpose-built for short social/review text.  It runs in
    microseconds per review with no GPU or heavy model weights, making it
    suitable for Apify's CPU-constrained environment.

    Output is deliberately identical to the previous transformer-based
    interface so the rest of the pipeline is unchanged.
    """

    def __init__(self) -> None:
        self._vader = SentimentIntensityAnalyzer()
        logger.info("VADER sentiment analyser ready")

    def analyse(self, text: str) -> SentimentResult:
        return self._score(text or "")

    def analyse_batch(self, texts: list[str], batch_size: int = 0) -> list[SentimentResult]:
        # batch_size kept for interface compatibility — VADER needs no batching
        return [self._score(t or "") for t in texts]

    # ------------------------------------------------------------------
    def _score(self, text: str) -> SentimentResult:
        if not text.strip():
            return SentimentResult("neutral", 0.5)

        scores = self._vader.polarity_scores(text)
        # compound: -1 (most negative) to +1 (most positive)
        compound = scores["compound"]

        if compound >= 0.05:
            return SentimentResult("positive", round(scores["pos"], 4))
        if compound <= -0.05:
            return SentimentResult("negative", round(scores["neg"], 4))
        return SentimentResult("neutral", round(scores["neu"], 4))
