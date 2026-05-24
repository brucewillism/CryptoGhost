"""CryptoGhost - Coletor de Dados de Mercado."""

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import ccxt
import pandas as pd

from backend.shared.circuit_breaker import CircuitBreaker, with_retry
from backend.shared.config import get_settings
from backend.shared.logging_config import get_logger

logger = get_logger("cryptoghost.data_collector")


class TechnicalIndicators:
    """Calcula indicadores técnicos para análise."""

    @staticmethod
    def compute(df: pd.DataFrame) -> dict[str, float]:
        if len(df) < 20:
            return {}

        close = df["close"].astype(float)
        indicators: dict[str, float] = {}

        # SMA
        indicators["sma_20"] = float(close.rolling(20).mean().iloc[-1])
        indicators["sma_50"] = float(close.rolling(min(50, len(close))).mean().iloc[-1])

        # RSI
        delta = close.diff()
        gain = delta.where(delta > 0, 0.0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0.0)).rolling(14).mean()
        rs = gain / loss.replace(0, 1e-10)
        indicators["rsi_14"] = float(100 - (100 / (1 + rs.iloc[-1])))

        # MACD
        ema12 = close.ewm(span=12).mean()
        ema26 = close.ewm(span=26).mean()
        macd = ema12 - ema26
        indicators["macd"] = float(macd.iloc[-1])
        indicators["macd_signal"] = float(macd.ewm(span=9).mean().iloc[-1])

        # Bollinger Bands
        sma = close.rolling(20).mean()
        std = close.rolling(20).std()
        indicators["bb_upper"] = float((sma + 2 * std).iloc[-1])
        indicators["bb_lower"] = float((sma - 2 * std).iloc[-1])

        return indicators


class ExchangeConnector:
    """Conector CCXT com rate limit e circuit breaker."""

    SUPPORTED_EXCHANGES = ["binance", "kraken", "coinbase", "bybit"]

    def __init__(self, exchange_id: str = "binance"):
        self.exchange_id = exchange_id
        self.settings = get_settings()
        self.circuit_breaker = CircuitBreaker(name=f"exchange_{exchange_id}")
        self._exchange: ccxt.Exchange | None = None

    def _get_exchange(self) -> ccxt.Exchange:
        if self._exchange is not None:
            return self._exchange

        exchange_class = getattr(ccxt, self.exchange_id)
        config: dict[str, Any] = {
            "enableRateLimit": True,
            "options": {"defaultType": "spot"},
        }

        if self.exchange_id == "binance" and self.settings.binance_api_key:
            config["apiKey"] = self.settings.binance_api_key
            config["secret"] = self.settings.binance_api_secret
            if self.settings.binance_testnet:
                config["sandbox"] = True

        self._exchange = exchange_class(config)
        return self._exchange

    @with_retry(max_attempts=3)
    def fetch_ticker(self, symbol: str) -> dict:
        def _fetch():
            exchange = self._get_exchange()
            return exchange.fetch_ticker(symbol)

        return self.circuit_breaker.call(_fetch)

    @with_retry(max_attempts=3)
    def fetch_order_book(self, symbol: str, limit: int = 20) -> dict:
        def _fetch():
            exchange = self._get_exchange()
            return exchange.fetch_order_book(symbol, limit)

        return self.circuit_breaker.call(_fetch)

    @with_retry(max_attempts=3)
    def fetch_ohlcv(self, symbol: str, timeframe: str = "1h", limit: int = 100) -> list:
        def _fetch():
            exchange = self._get_exchange()
            return exchange.fetch_ohlcv(symbol, timeframe, limit=limit)

        return self.circuit_breaker.call(_fetch)


class MarketDataCollector:
    """Coleta e processa dados de mercado de múltiplas exchanges."""

    DEFAULT_SYMBOLS = ["BTC/USDT", "ETH/USDT", "SOL/USDT"]

    def __init__(self, exchanges: list[str] | None = None):
        self.exchanges = exchanges or ["binance"]
        self.connectors = {ex: ExchangeConnector(ex) for ex in self.exchanges}

    def collect_snapshot(self, symbol: str) -> list[dict]:
        """Coleta snapshot de mercado de todas as exchanges configuradas."""
        snapshots = []

        for exchange_id, connector in self.connectors.items():
            try:
                ticker = connector.fetch_ticker(symbol)
                order_book = connector.fetch_order_book(symbol, limit=10)
                ohlcv = connector.fetch_ohlcv(symbol, "1h", limit=100)

                df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
                indicators = TechnicalIndicators.compute(df)

                bid = order_book["bids"][0][0] if order_book["bids"] else ticker.get("bid")
                ask = order_book["asks"][0][0] if order_book["asks"] else ticker.get("ask")

                snapshot = {
                    "exchange": exchange_id,
                    "symbol": symbol,
                    "timestamp": datetime.now(UTC),
                    "open": Decimal(str(ticker.get("open", 0))),
                    "high": Decimal(str(ticker.get("high", 0))),
                    "low": Decimal(str(ticker.get("low", 0))),
                    "close": Decimal(str(ticker.get("last", 0))),
                    "volume": Decimal(str(ticker.get("baseVolume", 0))),
                    "bid": Decimal(str(bid)) if bid else None,
                    "ask": Decimal(str(ask)) if ask else None,
                    "indicators": indicators,
                    "order_book_depth": {
                        "bid_volume": sum(b[1] for b in order_book["bids"][:5]),
                        "ask_volume": sum(a[1] for a in order_book["asks"][:5]),
                    },
                }
                snapshots.append(snapshot)
                logger.info("market_data_collected", exchange=exchange_id, symbol=symbol)

            except Exception as exc:
                logger.error("market_data_error", exchange=exchange_id, symbol=symbol, error=str(exc))

        return snapshots

    def collect_all(self) -> list[dict]:
        """Coleta dados para todos os símbolos padrão."""
        all_data = []
        for symbol in self.DEFAULT_SYMBOLS:
            all_data.extend(self.collect_snapshot(symbol))
        return all_data
