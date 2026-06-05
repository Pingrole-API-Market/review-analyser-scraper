import re
import string
from collections import Counter
from typing import NamedTuple

# Stopwords — lightweight, no NLTK dependency
_STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "was", "are", "were", "be", "been",
    "have", "has", "had", "do", "did", "will", "would", "could", "should",
    "this", "that", "these", "those", "it", "its", "i", "my", "me", "we",
    "our", "you", "your", "he", "she", "they", "them", "their", "not",
    "very", "so", "just", "also", "here", "there", "when", "where", "how",
    "what", "which", "who", "than", "more", "most", "much", "many", "some",
    "all", "no", "any", "each", "few", "been", "then", "up", "out", "if",
    "about", "over", "after", "before", "other", "can", "even", "only",
    "us", "get", "got", "go", "went", "come", "back", "really", "too",
    "time", "times",
}

# Complaint and praise seed vocabulary for topic mapping
_COMPLAINT_SEEDS = {
    "slow", "wait", "waiting", "long", "cold", "dirty", "rude", "wrong",
    "bad", "terrible", "horrible", "awful", "worse", "worst", "never",
    "never again", "disappointing", "disappointed", "mediocre", "overpriced",
    "expensive", "stale", "old", "burnt", "raw", "undercooked", "mistake",
    "order", "incorrect", "missing", "late", "delay", "delayed", "broken",
    "disgusting", "poor", "horrible", "unprofessional", "ignored", "unfriendly",
}

_PRAISE_SEEDS = {
    "great", "excellent", "amazing", "fantastic", "wonderful", "best",
    "love", "loved", "delicious", "fresh", "friendly", "helpful",
    "professional", "quick", "fast", "efficient", "clean", "nice",
    "perfect", "beautiful", "cozy", "warm", "recommend", "recommended",
    "outstanding", "superb", "exceptional", "tasty", "yummy", "good",
    "happy", "satisfied", "worth", "reasonable", "affordable",
}

_TOPIC_PHRASES = {
    "wait time": ["wait", "waiting", "long wait", "slow"],
    "food quality": ["food", "taste", "flavor", "fresh", "cold", "stale", "raw", "burnt"],
    "service": ["service", "staff", "server", "waiter", "waitress", "rude", "friendly"],
    "price": ["price", "expensive", "cheap", "affordable", "value", "overpriced", "cost"],
    "cleanliness": ["clean", "dirty", "hygiene", "mess", "spotless"],
    "atmosphere": ["atmosphere", "ambiance", "decor", "cozy", "noisy", "loud", "quiet"],
    "delivery": ["delivery", "deliver", "courier", "driver", "shipping"],
    "portions": ["portion", "size", "small", "large", "filling", "enough"],
    "parking": ["parking", "park", "lot"],
}


class TopicResult(NamedTuple):
    top_keywords: list[str]
    top_complaints: list[str]
    top_praises: list[str]


def _tokenise(text: str) -> list[str]:
    text = text.lower()
    text = re.sub(r"[" + re.escape(string.punctuation) + r"]", " ", text)
    return [w for w in text.split() if w not in _STOPWORDS and len(w) > 2]


def extract_topics(reviews: list[dict]) -> TopicResult:
    all_words: Counter = Counter()
    complaint_words: Counter = Counter()
    praise_words: Counter = Counter()

    for review in reviews:
        text = review.get("text") or ""
        sentiment = review.get("sentiment", "neutral")
        tokens = _tokenise(text)
        all_words.update(tokens)
        if sentiment == "negative":
            complaint_words.update(tokens)
        elif sentiment == "positive":
            praise_words.update(tokens)

    top_keywords = [w for w, _ in all_words.most_common(20) if w not in _STOPWORDS]

    # Map frequent complaint tokens to human-readable topics
    top_complaints = _map_to_topics(complaint_words, _COMPLAINT_SEEDS)
    top_praises = _map_to_topics(praise_words, _PRAISE_SEEDS)

    return TopicResult(
        top_keywords=top_keywords[:10],
        top_complaints=top_complaints[:5],
        top_praises=top_praises[:5],
    )


def _map_to_topics(counter: Counter, seeds: set[str]) -> list[str]:
    """Return seed words that appear in the counter, sorted by frequency."""
    matched = [(word, counter[word]) for word in seeds if counter[word] > 0]
    matched.sort(key=lambda x: x[1], reverse=True)
    return [word for word, _ in matched]


def review_topics(text: str) -> list[str]:
    """Assign micro-topics to a single review text."""
    if not text:
        return []
    lower = text.lower()
    found = []
    for topic, keywords in _TOPIC_PHRASES.items():
        if any(kw in lower for kw in keywords):
            found.append(topic)
    return found
