"""CryptoGhost - News Intelligence."""

import re
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass

import httpx

from backend.shared.logging_config import get_logger

logger = get_logger("cryptoghost.news_intelligence")

NEWS_FEEDS = [
    ("CoinDesk", "https://www.coindesk.com/arc/outboundfeeds/rss/"),
    ("Cointelegraph", "https://cointelegraph.com/rss"),
    ("Federal Reserve", "https://www.federalreserve.gov/feeds/press_all.xml"),
]

IMPACT_KEYWORDS = {
    "high": ["hack", "ban", "regulation", "sec", "fed", "rate hike", "etf approval", "collapse", "bankruptcy"],
    "medium": ["partnership", "upgrade", "launch", "investigation", "warning"],
    "low": ["analysis", "opinion", "preview", "guide"],
}

DIRECTION_KEYWORDS = {
    "bullish": ["approval", "adoption", "surge", "rally", "record", "institutional", "etf", "bullish"],
    "bearish": ["hack", "ban", "crash", "lawsuit", "sec", "investigation", "bearish", "decline", "fraud"],
}


@dataclass
class NewsAnalysis:
    title: str
    source: str
    impact: str
    direction: str
    confidence: float
    categories: list[str]
    url: str | None
    summary: str


class NewsIntelligence:
    """Interpreta notícias financeiras e detecta impacto macro/micro."""

    def fetch_recent_news(self, limit: int = 20) -> list[dict]:
        articles = []
        with httpx.Client(timeout=15, follow_redirects=True) as client:
            for source, url in NEWS_FEEDS:
                try:
                    response = client.get(url, headers={"User-Agent": "CryptoGhost/1.0"})
                    response.raise_for_status()
                    root = ET.fromstring(response.text)
                    for item in root.findall(".//item")[:limit // len(NEWS_FEEDS)]:
                        title = item.findtext("title", "")
                        link = item.findtext("link", "")
                        desc = re.sub(r"<[^>]+>", "", item.findtext("description", ""))[:300]
                        if title:
                            articles.append({"title": title, "source": source, "url": link, "description": desc})
                except Exception as exc:
                    logger.warning("news_fetch_failed", source=source, error=str(exc))
        return articles

    def analyze_article(self, title: str, source: str, description: str = "", url: str | None = None) -> NewsAnalysis:
        text = f"{title} {description}".lower()
        impact = self._detect_impact(text)
        direction = self._detect_direction(text)
        categories = self._detect_categories(text)
        confidence = self._compute_confidence(text, impact, direction)

        return NewsAnalysis(
            title=title,
            source=source,
            impact=impact,
            direction=direction,
            confidence=round(confidence, 2),
            categories=categories,
            url=url,
            summary=description[:200] if description else title,
        )

    def analyze_batch(self, limit: int = 15) -> list[NewsAnalysis]:
        start = time.perf_counter()
        articles = self.fetch_recent_news(limit)
        results = [self.analyze_article(a["title"], a["source"], a.get("description", ""), a.get("url")) for a in articles]
        logger.info("news_analyzed", count=len(results), elapsed=round(time.perf_counter() - start, 2))
        return results

    @staticmethod
    def _detect_impact(text: str) -> str:
        for level, keywords in IMPACT_KEYWORDS.items():
            if any(kw in text for kw in keywords):
                return level
        return "low"

    @staticmethod
    def _detect_direction(text: str) -> str:
        bull = sum(1 for kw in DIRECTION_KEYWORDS["bullish"] if kw in text)
        bear = sum(1 for kw in DIRECTION_KEYWORDS["bearish"] if kw in text)
        if bull > bear:
            return "bullish"
        if bear > bull:
            return "bearish"
        return "neutral"

    @staticmethod
    def _detect_categories(text: str) -> list[str]:
        cats = []
        mapping = {
            "regulation": ["sec", "regulation", "ban", "law"],
            "macro": ["fed", "interest rate", "inflation", "treasury"],
            "security": ["hack", "exploit", "vulnerability"],
            "etf": ["etf", "approval", "blackrock"],
            "adoption": ["adoption", "institutional", "partnership"],
        }
        for cat, keywords in mapping.items():
            if any(kw in text for kw in keywords):
                cats.append(cat)
        return cats or ["general"]

    @staticmethod
    def _compute_confidence(text: str, impact: str, direction: str) -> float:
        base = 0.5
        if impact == "high":
            base += 0.2
        elif impact == "medium":
            base += 0.1
        if direction != "neutral":
            base += 0.15
        if len(text) > 100:
            base += 0.05
        return min(0.95, base)
