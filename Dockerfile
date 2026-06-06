# syntax=docker/dockerfile:1
FROM python:3.12-slim

# System deps for Playwright + Chromium
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget curl gnupg ca-certificates \
    libglib2.0-0 libnss3 libnspr4 libdbus-1-3 \
    libatk1.0-0 libatk-bridge2.0-0 libcups2 \
    libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 \
    libxfixes3 libxrandr2 libgbm1 libasound2 \
    libpango-1.0-0 libcairo2 libxshmfence1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /usr/src/app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download NLTK corpora so the actor never hits the network at runtime
RUN python -c "\
import nltk; \
nltk.download('stopwords',                      quiet=True); \
nltk.download('punkt_tab',                      quiet=True); \
nltk.download('punkt',                          quiet=True); \
nltk.download('averaged_perceptron_tagger_eng', quiet=True); \
nltk.download('averaged_perceptron_tagger',     quiet=True)"

# Install Playwright Chromium browser
RUN playwright install chromium && playwright install-deps chromium

COPY . .

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

CMD ["python", "-m", "src.main"]
