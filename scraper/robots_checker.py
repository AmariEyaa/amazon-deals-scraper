"""Robots.txt checker for ethical scraping"""
import urllib.robotparser
from typing import Optional
from loguru import logger


class RobotsChecker:
    """Check robots.txt compliance"""
    
    def __init__(self, base_url: str, user_agent: str = "*"):
        self.base_url = base_url
        self.user_agent = user_agent
        self.parser = urllib.robotparser.RobotFileParser()
        self.parser.set_url(f"{base_url}/robots.txt")
        self._loaded = False
    
    def load(self) -> bool:
        """Load and parse robots.txt"""
        try:
            self.parser.read()
            self._loaded = True
            logger.info(f"✅ Loaded robots.txt from {self.base_url}")
            return True
        except Exception as e:
            logger.warning(f"⚠️ Could not load robots.txt: {e}")
            # If we can't load robots.txt, be conservative and allow
            self._loaded = False
            return False
    
    def can_fetch(self, url: str) -> bool:
        """Check if URL can be fetched according to robots.txt"""
        if not self._loaded:
            # If robots.txt not loaded, be conservative and allow
            # (Some sites block robots.txt itself)
            return True
        
        try:
            allowed = self.parser.can_fetch(self.user_agent, url)
            if not allowed:
                logger.warning(f"🚫 Blocked by robots.txt: {url}")
            return allowed
        except Exception as e:
            logger.warning(f"⚠️ Error checking robots.txt: {e}")
            return True  # Be permissive on errors
    
    def get_crawl_delay(self) -> Optional[float]:
        """Get crawl delay from robots.txt"""
        if not self._loaded:
            return None
        
        try:
            delay = self.parser.crawl_delay(self.user_agent)
            if delay:
                logger.info(f"⏱️ Crawl delay from robots.txt: {delay} seconds")
            return delay
        except:
            return None
