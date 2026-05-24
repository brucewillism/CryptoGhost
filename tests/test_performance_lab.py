"""Testes do AI Performance Lab v3."""

from backend.ai_performance_lab.lab import AIPerformanceLab


def test_benchmark_agent():
    lab = AIPerformanceLab()
    bench = lab.benchmark_agent("analyst", [1, 1, 0, 1, 1], [1, 0, 0, 1, 1])
    assert bench.agent == "analyst"
    assert 0 <= bench.accuracy <= 1


def test_rank_agents():
    lab = AIPerformanceLab()
    benchmarks = [
        lab.benchmark_agent("a", [1, 1, 1, 1], [1, 1, 1, 1]),
        lab.benchmark_agent("b", [1, 0, 0, 0], [1, 0, 0, 0]),
    ]
    ranked = lab.rank_agents(benchmarks)
    assert ranked[0].rank == 1
    assert ranked[0].accuracy >= ranked[1].accuracy


def test_detect_drift():
    lab = AIPerformanceLab()
    drift = lab.detect_drift("analyst", [1, 1, 0, 1, 1, 0], [1, 0, 0, 1, 1, 0], baseline_accuracy=0.8)
    assert drift.agent_name == "analyst"
    assert drift.drift_score >= 0
