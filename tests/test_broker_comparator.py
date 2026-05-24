"""Testes do BrokerComparator CryptoGhost."""

from backend.broker_comparator.comparator import BrokerComparator, BrokerMetrics


def test_broker_ranking():
    comparator = BrokerComparator()
    brokers = [
        BrokerMetrics("binance", "BTC/USDT", 0.001, 0.0001, 90, 0.0001, 50, 99.9, 1e9),
        BrokerMetrics("kraken", "BTC/USDT", 0.002, 0.0003, 70, 0.0002, 120, 99.0, 5e8),
    ]
    ranking = comparator.compare(brokers)
    assert len(ranking) == 2
    assert ranking[0]["is_selected"] is True
    assert ranking[0]["total_score"] >= ranking[1]["total_score"]


def test_from_market_snapshots():
    snapshots = [
        {
            "exchange": "binance",
            "symbol": "BTC/USDT",
            "close": 65000,
            "bid": 64990,
            "ask": 65010,
            "volume": 1000,
            "order_book_depth": {"bid_volume": 50, "ask_volume": 50},
        }
    ]
    metrics = BrokerComparator.from_market_snapshots(snapshots)
    assert len(metrics) == 1
    assert metrics[0].broker == "binance"
