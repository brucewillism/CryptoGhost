"""Premium data providers — CryptoPanic, Fear&Greed, AlphaVantage."""

from typing import Any

import httpx

from backend.app.data.providers.base import BaseDataProvider
from backend.app.data.providers.retry import retry_with_backoff
from backend.shared.config import get_settings


class FearGreedProvider(BaseDataProvider):
    name = "fear_greed"
    URL = "https://api.alternative.me/fng/?limit=1"

    def fetch(self, symbol: str = "", **kwargs: Any) -> dict[str, Any]:
        def _get():
            r = httpx.get(self.URL, timeout=10)
            r.raise_for_status()
            data = r.json().get("data", [{}])[0]
            value = int(data.get("value", 50))
            return {"score": (value - 50) / 50, "value": value, "classification": data.get("value_classification", "")}

        return retry_with_backoff(_get)


class CryptoPanicProvider(BaseDataProvider):
    name = "cryptopanic"

    def fetch(self, symbol: str = "BTC", **kwargs: Any) -> dict[str, Any]:
        settings = get_settings()
        if not settings.cryptopanic_api_key:
            return {"news": [], "score": 0.0, "count": 0}

        currency = symbol.split("/")[0] if "/" in symbol else symbol

        def _get():
            r = httpx.get(
                "https://cryptopanic.com/api/v1/posts/",
                params={"auth_token": settings.cryptopanic_api_key, "currencies": currency, "filter": "hot"},
                timeout=10,
            )
            r.raise_for_status()
            posts = r.json().get("results", [])[:10]
            bullish = sum(1 for p in posts if p.get("votes", {}).get("positive", 0) > p.get("votes", {}).get("negative", 0))
            score = (bullish / max(len(posts), 1)) * 2 - 1
            return {"news": [p.get("title", "") for p in posts[:5]], "score": score, "count": len(posts)}

        return retry_with_backoff(_get)


class AlphaVantageProvider(BaseDataProvider):
    name = "alphavantage"

    def fetch(self, symbol: str = "", **kwargs: Any) -> dict[str, Any]:
        settings = get_settings()
        if not settings.alphavantage_api_key:
            return {"indicators": [], "score": 0.0}

        def _get():
            r = httpx.get(
                "https://www.alphavantage.co/query",
                params={"function": "GLOBAL_QUOTE", "symbol": "SPY", "apikey": settings.alphavantage_api_key},
                timeout=15,
            )
            r.raise_for_status()
            quote = r.json().get("Global Quote", {})
            change = float(quote.get("10. change percent", "0").replace("%", "") or 0)
            return {"indicators": [{"name": "SPY", "change_pct": change}], "score": max(-1, min(1, change / 5))}

        return retry_with_backoff(_get)
