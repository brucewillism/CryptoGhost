"""CryptoGhost - Comparador Inteligente de Corretoras."""

from dataclasses import dataclass

from backend.shared.logging_config import get_logger

logger = get_logger("cryptoghost.broker_comparator")


@dataclass
class BrokerMetrics:
    broker: str
    symbol: str
    fee_pct: float
    spread_pct: float
    liquidity_score: float
    avg_slippage_pct: float
    execution_ms: float
    api_uptime_pct: float
    volume_24h: float


@dataclass
class ComparisonWeights:
    fee: float = 0.20
    spread: float = 0.20
    liquidity: float = 0.20
    slippage: float = 0.15
    execution: float = 0.15
    api_stability: float = 0.10


class BrokerComparator:
    """Compara corretoras e seleciona a melhor automaticamente."""

    def __init__(self, weights: ComparisonWeights | None = None):
        self.weights = weights or ComparisonWeights()

    def score_broker(self, metrics: BrokerMetrics) -> dict:
        fee_score = max(0, 100 - metrics.fee_pct * 1000)
        spread_score = max(0, 100 - metrics.spread_pct * 5000)
        liquidity_score = min(100, metrics.liquidity_score)
        slippage_score = max(0, 100 - metrics.avg_slippage_pct * 2000)
        execution_score = max(0, 100 - metrics.execution_ms / 10)
        api_score = metrics.api_uptime_pct

        total = (
            fee_score * self.weights.fee
            + spread_score * self.weights.spread
            + liquidity_score * self.weights.liquidity
            + slippage_score * self.weights.slippage
            + execution_score * self.weights.execution
            + api_score * self.weights.api_stability
        )

        return {
            "broker": metrics.broker,
            "symbol": metrics.symbol,
            "fee_score": round(fee_score, 2),
            "spread_score": round(spread_score, 2),
            "liquidity_score": round(liquidity_score, 2),
            "slippage_score": round(slippage_score, 2),
            "execution_score": round(execution_score, 2),
            "api_stability_score": round(api_score, 2),
            "total_score": round(total, 2),
            "details": {
                "fee_pct": metrics.fee_pct,
                "spread_pct": metrics.spread_pct,
                "avg_slippage_pct": metrics.avg_slippage_pct,
                "execution_ms": metrics.execution_ms,
                "volume_24h": metrics.volume_24h,
            },
        }

    def compare(self, brokers: list[BrokerMetrics]) -> list[dict]:
        scores = [self.score_broker(b) for b in brokers]
        scores.sort(key=lambda x: x["total_score"], reverse=True)

        if scores:
            scores[0]["is_selected"] = True
            logger.info("broker_selected", broker=scores[0]["broker"], score=scores[0]["total_score"])

        for i, score in enumerate(scores):
            score["rank"] = i + 1
            if "is_selected" not in score:
                score["is_selected"] = False

        return scores

    def select_best(self, brokers: list[BrokerMetrics]) -> dict | None:
        ranked = self.compare(brokers)
        return ranked[0] if ranked else None

    @staticmethod
    def from_market_snapshots(snapshots: list[dict]) -> list[BrokerMetrics]:
        metrics = []
        for snap in snapshots:
            bid = float(snap.get("bid") or snap["close"])
            ask = float(snap.get("ask") or snap["close"])
            spread = (ask - bid) / bid if bid > 0 else 0
            depth = snap.get("order_book_depth", {})
            liquidity = min(100, (depth.get("bid_volume", 0) + depth.get("ask_volume", 0)) / 10)

            metrics.append(
                BrokerMetrics(
                    broker=snap["exchange"],
                    symbol=snap["symbol"],
                    fee_pct=0.001,
                    spread_pct=spread,
                    liquidity_score=liquidity,
                    avg_slippage_pct=spread * 0.5,
                    execution_ms=100.0,
                    api_uptime_pct=99.5,
                    volume_24h=float(snap.get("volume", 0)),
                )
            )
        return metrics
