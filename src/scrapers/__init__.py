from src.scrapers.glassdoor import GlassdoorScraper
from src.scrapers.google import GoogleScraper
from src.scrapers.trustpilot import TrustpilotScraper
from src.scrapers.yelp import YelpScraper

SCRAPER_MAP = {
    "google": GoogleScraper,
    "trustpilot": TrustpilotScraper,
    "glassdoor": GlassdoorScraper,
    "yelp": YelpScraper,
}

__all__ = ["SCRAPER_MAP", "GoogleScraper", "TrustpilotScraper", "GlassdoorScraper", "YelpScraper"]
