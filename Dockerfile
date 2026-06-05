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

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright Chromium browser
RUN playwright install chromium && playwright install-deps chromium

# Pre-download HuggingFace model to bake into image
# (avoids cold-start download on each actor run)
RUN python -c "\
from transformers import AutoTokenizer, AutoModelForSequenceClassification; \
AutoTokenizer.from_pretrained('cardiffnlp/twitter-roberta-base-sentiment'); \
AutoModelForSequenceClassification.from_pretrained('cardiffnlp/twitter-roberta-base-sentiment')"

COPY . .

# Apify SDK picks up APIFY_* env vars at runtime
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

CMD ["python", "-m", "src.main"]
