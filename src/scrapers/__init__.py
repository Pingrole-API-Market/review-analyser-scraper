from src.scrapers.trustpilot import TrustpilotScraper
from src.scrapers.yelp import YelpScraper

SCRAPER_MAP = {
    "trustpilot": TrustpilotScraper,
    "yelp": YelpScraper,
}

__all__ = ["SCRAPER_MAP", "TrustpilotScraper", "YelpScraper"]
