"""CryptoGhost - Coletores de dados de sentimento."""

import xml.etree.ElementTree as ET
from dataclasses import dataclass

import httpx

from backend.shared.circuit_breaker import with_retry
from backend.shared.logging_config import get_logger

logger = get_logger("cryptoghost.sentiment.sources")

RSS_FEEDS = [
    ("CoinDesk", "https://www.coindesk.com/arc/outboundfeeds/rss/"),
    ("Cointelegraph", "https://cointelegraph.com/rss"),
    ("Decrypt", "https://decrypt.co/feed"),
]

REDDIT_URL = "https://www.reddit.com/r/cryptocurrency/hot.json?limit=25"
FEAR_GREED_URL = "https://api.alternative.me/fng/?limit=1"
BINANCE_ANNOUNCEMENTS = "https://www.binance.com/bapi/composite/v1/public/cms/article/list/query?type=1&pageSize=10&pageNo=1"


@dataclass
class SentimentSourceData:
    source: str
    texts: list[str]
    scores: list[float]
    metadata: dict


class SentimentDataCollector:
    """Coleta dados reais de múltiplas fontes públicas."""

    @with_retry(max_attempts=3)
    def fetch_fear_greed(self) -> SentimentSourceData:
        with httpx.Client(timeout=15) as client:
            response = client.get(FEAR_GREED_URL)
            response.raise_for_status()
            data = response.json()["data"][0]

        value = int(data["value"])
        score = value / 100.0
        classification = data.get("value_classification", "Neutral")
        return SentimentSourceData(
            source="fear_greed_index",
            texts=[f"Fear & Greed Index: {value} ({classification})"],
            scores=[score],
            metadata={"value": value, "classification": classification},
        )

    @with_retry(max_attempts=3)
    def fetch_rss_feeds(self) -> list[SentimentSourceData]:
        results = []
        with httpx.Client(timeout=15, follow_redirects=True) as client:
            for name, url in RSS_FEEDS:
                try:
                    response = client.get(url, headers={"User-Agent": "CryptoGhost/1.0"})
                    response.raise_for_status()
                    root = ET.fromstring(response.text)
                    texts = []
                    for item in root.findall(".//item")[:10]:
                        title = item.findtext("title", "")
                        desc = item.findtext("description", "")
                        texts.append(f"{title}. {desc[:200]}")
                    if texts:
                        results.append(SentimentSourceData(source=f"rss_{name.lower()}", texts=texts, scores=[], metadata={"count": len(texts)}))
                except Exception as exc:
                    logger.warning("rss_fetch_failed", source=name, error=str(exc))
        return results

    @with_retry(max_attempts=3)
    def fetch_reddit(self) -> SentimentSourceData:
        with httpx.Client(timeout=15, follow_redirects=True) as client:
            response = client.get(REDDIT_URL, headers={"User-Agent": "CryptoGhost/1.0 (sentiment analysis)"})
            response.raise_for_status()
            posts = response.json()["data"]["children"]

        texts = [f"{p['data']['title']}. {p['data'].get('selftext', '')[:150]}" for p in posts[:15]]
        return SentimentSourceData(source="reddit", texts=texts, scores=[], metadata={"subreddit": "cryptocurrency"})

    @with_retry(max_attempts=3)
    def fetch_binance_announcements(self) -> SentimentSourceData:
        with httpx.Client(timeout=15) as client:
            response = client.get(BINANCE_ANNOUNCEMENTS)
            response.raise_for_status()
            articles = response.json().get("data", {}).get("catalogs", [{}])[0].get("articles", [])

        texts = [a.get("title", "") for a in articles[:10] if a.get("title")]
        return SentimentSourceData(source="binance_announcements", texts=texts, scores=[], metadata={"count": len(texts)})

    def collect_all(self) -> list[SentimentSourceData]:
        sources = []
        for fetcher in [self.fetch_fear_greed, self.fetch_reddit, self.fetch_binance_announcements]:
            try:
                sources.append(fetcher())
            except Exception as exc:
                logger.error("sentiment_source_failed", fetcher=fetcher.__name__, error=str(exc))
        sources.extend(self.fetch_rss_feeds())
        return sources
