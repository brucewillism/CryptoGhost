"""CryptoGhost v5 - Premium data connectors."""

import httpx

from backend.shared.config import get_settings
from backend.shared.logging_config import get_logger

logger = get_logger("cryptoghost.premium_data")


class PremiumDataHub:
    """Integração com APIs premium (graceful fallback quando sem API key)."""

    def __init__(self) -> None:
        self.settings = get_settings()

    async def fetch_macro_fred(self, series_id: str = "DFF") -> dict | None:
        api_key = getattr(self.settings, "fred_api_key", "") or ""
        if not api_key:
            return None
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                r = await client.get(
                    "https://api.stlouisfed.org/fred/series/observations",
                    params={"series_id": series_id, "api_key": api_key, "file_type": "json", "limit": 5, "sort_order": "desc"},
                )
                if r.status_code == 200:
                    obs = r.json().get("observations", [])
                    if obs:
                        return {"source": "fred", "series": series_id, "value": float(obs[0]["value"]), "date": obs[0]["date"]}
        except Exception as exc:
            logger.debug("fred_fetch_failed", error=str(exc))
        return None

    async def fetch_glassnode_metric(self, symbol: str = "BTC", metric: str = "addresses/active_count") -> dict | None:
        api_key = getattr(self.settings, "glassnode_api_key", "") or ""
        if not api_key:
            return None
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                r = await client.get(
                    f"https://api.glassnode.com/v1/metrics/{metric}",
                    params={"a": symbol, "api_key": api_key, "i": "24h"},
                )
                if r.status_code == 200:
                    data = r.json()
                    if data:
                        return {"source": "glassnode", "metric": metric, "value": data[-1].get("v"), "timestamp": data[-1].get("t")}
        except Exception as exc:
            logger.debug("glassnode_fetch_failed", error=str(exc))
        return None

    async def fetch_coinglass_liquidations(self, symbol: str = "BTC") -> dict | None:
        api_key = getattr(self.settings, "coinglass_api_key", "") or ""
        if not api_key:
            return None
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                r = await client.get(
                    "https://open-api.coinglass.com/public/v2/liquidation_history",
                    headers={"coinglassSecret": api_key},
                    params={"symbol": symbol, "time_type": "h1"},
                )
                if r.status_code == 200:
                    return {"source": "coinglass", "data": r.json()}
        except Exception as exc:
            logger.debug("coinglass_fetch_failed", error=str(exc))
        return None

    async def fetch_alphavantage_quote(self, symbol: str = "IBM") -> dict | None:
        api_key = getattr(self.settings, "alphavantage_api_key", "") or ""
        if not api_key:
            return None
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                r = await client.get(
                    "https://www.alphavantage.co/query",
                    params={"function": "GLOBAL_QUOTE", "symbol": symbol, "apikey": api_key},
                )
                if r.status_code == 200:
                    q = r.json().get("Global Quote", {})
                    if q:
                        return {"source": "alphavantage", "price": q.get("05. price"), "change_pct": q.get("10. change percent")}
        except Exception as exc:
            logger.debug("alphavantage_fetch_failed", error=str(exc))
        return None

    async def aggregate(self, symbol: str) -> dict:
        base = symbol.split("/")[0]
        results = {}
        for name, coro in [
            ("fred", self.fetch_macro_fred()),
            ("glassnode", self.fetch_glassnode_metric(base)),
            ("coinglass", self.fetch_coinglass_liquidations(base)),
        ]:
            try:
                data = await coro
                if data:
                    results[name] = data
            except Exception:
                pass
        return results
