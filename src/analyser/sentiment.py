import logging
import re
from typing import NamedTuple

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline

logger = logging.getLogger(__name__)

MODEL_NAME = "cardiffnlp/twitter-roberta-base-sentiment"

LABEL_MAP = {
    "LABEL_0": "negative",
    "LABEL_1": "neutral",
    "LABEL_2": "positive",
}


class SentimentResult(NamedTuple):
    label: str
    score: float


def _preprocess(text: str) -> str:
    tokens = []
    for token in text.split():
        if token.startswith("@") and len(token) > 1:
            token = "@user"
        elif token.startswith("http"):
            token = "http"
        tokens.append(token)
    return " ".join(tokens)


class SentimentAnalyzer:
    """Loads the HuggingFace model once and reuses it across all reviews.

    Uses dynamic INT8 quantisation on CPU to cut memory ~4× vs FP32.
    Falls back to unquantised if quantisation is unavailable.
    """

    def __init__(self) -> None:
        logger.info("Loading sentiment model: %s", MODEL_NAME)
        use_cuda = torch.cuda.is_available()

        tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        model = AutoModelForSequenceClassification.from_pretrained(
            MODEL_NAME,
            low_cpu_mem_usage=True,
        )

        if not use_cuda:
            # INT8 quantisation: ~125 MB vs ~500 MB FP32 — safe on CPU.
            # fbgemm = Linux/x86 (Apify), qnnpack = macOS/ARM.
            quantised = False
            for engine in ("fbgemm", "qnnpack"):
                try:
                    torch.backends.quantized.engine = engine
                    model = torch.quantization.quantize_dynamic(
                        model, {torch.nn.Linear}, dtype=torch.qint8
                    )
                    logger.info("Model quantised to INT8 (engine=%s)", engine)
                    quantised = True
                    break
                except Exception:
                    continue
            if not quantised:
                logger.warning("INT8 quantisation unavailable — using FP32")

        device = 0 if use_cuda else -1
        self._pipe = pipeline(
            "sentiment-analysis",
            model=model,
            tokenizer=tokenizer,
            device=device,
            truncation=True,
            max_length=512,
        )
        logger.info("Sentiment model loaded (device=%s)", "cuda" if use_cuda else "cpu")

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
