from src.scrapers.trustpilot import TrustpilotScraper

SCRAPER_MAP = {
    "trustpilot": TrustpilotScraper,
}

__all__ = ["SCRAPER_MAP", "TrustpilotScraper"]
