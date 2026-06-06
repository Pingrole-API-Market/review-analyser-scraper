"""
Keyword extraction and topic analysis using NLTK.

Improvements over the previous word-frequency approach:
- NLTK stopwords corpus (full English list) + domain extras
- POS tagging — only nouns (NN*) and adjectives (JJ*) kept as keywords
- Bigrams and trigrams for complaint/praise phrases instead of single words
"""
import logging
import re
from collections import Counter
from typing import NamedTuple

import nltk
from nltk import ngrams, pos_tag, word_tokenize
from nltk.corpus import stopwords

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# NLTK resource bootstrap
# ------------------------------------------------------------------
_RESOURCES = [
    ("tokenizers/punkt_tab",                "punkt_tab"),
    ("tokenizers/punkt",                    "punkt"),
    ("taggers/averaged_perceptron_tagger_eng", "averaged_perceptron_tagger_eng"),
    ("taggers/averaged_perceptron_tagger",  "averaged_perceptron_tagger"),
    ("corpora/stopwords",                   "stopwords"),
]

def _bootstrap() -> None:
    for path, name in _RESOURCES:
        try:
            nltk.data.find(path)
        except LookupError:
            try:
                nltk.download(name, quiet=True)
            except Exception:
                pass  # non-fatal — fallback path handles missing data

_bootstrap()

# ------------------------------------------------------------------
# Stop words
# ------------------------------------------------------------------
try:
    _STOP: set[str] = set(stopwords.words("english"))
except Exception:
    _STOP = set()

# Domain extras that survive the NLTK list but add noise in reviews
_STOP |= {
    "would", "could", "also", "even", "really", "just", "get", "got",
    "one", "two", "three", "time", "times", "back", "go", "went", "come",
    "us", "said", "told", "made", "make", "still", "always", "ever",
    "company", "replied", "see", "more", "like", "go", "going", "came",
    # NLTK tokeniser artefacts
    "n't", "'s", "'re", "'ve", "'ll", "ca", "wo", "u",
}

# POS tags worth keeping: nouns and adjectives only
_NOUN_TAGS = {"NN", "NNS", "NNP", "NNPS"}
_ADJ_TAGS  = {"JJ", "JJR", "JJS"}
_KEEP_POS  = _NOUN_TAGS | _ADJ_TAGS

# Per-review micro-topic buckets (unchanged — used in main.py)
_TOPIC_PHRASES = {
    "wait time":    ["wait", "waiting", "long wait", "slow"],
    "food quality": ["food", "taste", "flavor", "fresh", "cold", "stale", "raw", "burnt"],
    "service":      ["service", "staff", "server", "waiter", "waitress", "rude", "friendly"],
    "price":        ["price", "expensive", "cheap", "affordable", "value", "overpriced", "cost"],
    "cleanliness":  ["clean", "dirty", "hygiene", "mess", "spotless"],
    "atmosphere":   ["atmosphere", "ambiance", "decor", "cozy", "noisy", "loud", "quiet"],
    "delivery":     ["delivery", "deliver", "courier", "driver", "shipping"],
    "portions":     ["portion", "size", "small", "large", "filling", "enough"],
}


class TopicResult(NamedTuple):
    top_keywords:  list[str]
    top_complaints: list[str]
    top_praises:   list[str]


# ------------------------------------------------------------------
# Public API
# ------------------------------------------------------------------

def extract_topics(reviews: list[dict]) -> TopicResult:
    all_tokens:       list[str] = []
    complaint_tokens: list[str] = []
    praise_tokens:    list[str] = []

    for review in reviews:
        text      = review.get("text") or ""
        sentiment = review.get("sentiment", "neutral")
        tokens    = _pos_filter(text)

        all_tokens.extend(tokens)
        if sentiment == "negative":
            complaint_tokens.extend(tokens)
        elif sentiment == "positive":
            praise_tokens.extend(tokens)

    top_keywords   = [w for w, _ in Counter(all_tokens).most_common(30)][:10]
    top_complaints = _top_phrases(complaint_tokens, total_reviews=len(reviews))[:5]
    top_praises    = _top_phrases(praise_tokens,    total_reviews=len(reviews))[:5]

    return TopicResult(
        top_keywords=top_keywords,
        top_complaints=top_complaints,
        top_praises=top_praises,
    )


def review_topics(text: str) -> list[str]:
    """Assign micro-topic labels to a single review."""
    if not text:
        return []
    lower = text.lower()
    return [
        topic for topic, keywords in _TOPIC_PHRASES.items()
        if any(kw in lower for kw in keywords)
    ]


# ------------------------------------------------------------------
# Internals
# ------------------------------------------------------------------

def _pos_filter(text: str) -> list[str]:
    """Tokenise + POS-tag text; return only nouns and adjectives."""
    if not text:
        return []
    try:
        tokens = word_tokenize(text.lower())
        tagged = pos_tag(tokens)
        return [
            word for word, tag in tagged
            if tag in _KEEP_POS
            and word not in _STOP
            and word.isalpha()
            and len(word) > 2
        ]
    except Exception:
        # Fallback: simple whitespace split, no POS filter
        cleaned = re.sub(r"[^\w\s]", " ", text.lower())
        return [
            w for w in cleaned.split()
            if w not in _STOP and w.isalpha() and len(w) > 2
        ]


def _top_phrases(tokens: list[str], total_reviews: int = 0) -> list[str]:
    """Extract most common bigrams and trigrams as natural phrases.

    min_count scales with dataset size so small runs still return results.
    """
    if not tokens:
        return []

    # For tiny datasets every phrase counts; for large ones require repetition
    min_count = 2 if total_reviews >= 20 else 1

    phrase_freq: Counter = Counter()
    for n in (2, 3):
        for gram in ngrams(tokens, n):
            phrase_freq[" ".join(gram)] += 1

    return [
        phrase for phrase, count in phrase_freq.most_common(15)
        if count >= min_count
    ]
