"""CryptoGhost v3 - AI Performance Lab."""

from dataclasses import dataclass
from datetime import UTC, datetime

import numpy as np
from sqlalchemy.orm import Session

from backend.shared.logging_config import get_logger
from backend.shared.models_quant import DriftReportRecord

logger = get_logger("cryptoghost.ai_performance_lab")


@dataclass
class AgentBenchmark:
    agent: str
    accuracy: float
    precision: float
    recall: float
    false_positive_rate: float
    rank: int
    drift_score: float
    retrain_recommended: bool


@dataclass
class DriftReport:
    agent_name: str
    drift_score: float
    accuracy_current: float
    accuracy_baseline: float
    false_positive_rate: float
    retrain_recommended: bool
    details: dict


class AIPerformanceLab:
    """Benchmark, drift detection e ranking de agentes."""

    DRIFT_THRESHOLD = 0.15
    ACCURACY_DEGRADATION_THRESHOLD = 0.1

    def benchmark_agent(self, agent: str, predictions: list[int], outcomes: list[int]) -> AgentBenchmark:
        if not predictions or len(predictions) != len(outcomes):
            return AgentBenchmark(agent, 0, 0, 0, 0, 0, 0, False)

        preds = np.array(predictions)
        outs = np.array(outcomes)
        accuracy = float((preds == outs).mean())

        tp = float(((preds == 1) & (outs == 1)).sum())
        fp = float(((preds == 1) & (outs == 0)).sum())
        fn = float(((preds == 0) & (outs == 1)).sum())
        precision = tp / max(tp + fp, 1)
        recall = tp / max(tp + fn, 1)
        fpr = fp / max(fp + (outs == 0).sum(), 1)

        return AgentBenchmark(
            agent=agent, accuracy=round(accuracy, 4), precision=round(precision, 4),
            recall=round(recall, 4), false_positive_rate=round(fpr, 4),
            rank=0, drift_score=0, retrain_recommended=False,
        )

    def rank_agents(self, benchmarks: list[AgentBenchmark]) -> list[AgentBenchmark]:
        scored = sorted(benchmarks, key=lambda b: b.accuracy * (1 - b.false_positive_rate), reverse=True)
        for i, b in enumerate(scored):
            b.rank = i + 1
        return scored

    def detect_drift(
        self,
        agent_name: str,
        recent_predictions: list[int],
        recent_outcomes: list[int],
        baseline_accuracy: float = 0.6,
    ) -> DriftReport:
        if len(recent_predictions) < 5:
            return DriftReport(agent_name, 0, 0, baseline_accuracy, 0, False, {"status": "insufficient_data"})

        current_accuracy = sum(p == o for p, o in zip(recent_predictions, recent_outcomes)) / len(recent_predictions)
        fp = sum(1 for p, o in zip(recent_predictions, recent_outcomes) if p == 1 and o == 0)
        fpr = fp / max(len(recent_predictions), 1)

        drift_score = abs(baseline_accuracy - current_accuracy)
        retrain = drift_score > self.DRIFT_THRESHOLD or current_accuracy < baseline_accuracy - self.ACCURACY_DEGRADATION_THRESHOLD

        return DriftReport(
            agent_name=agent_name, drift_score=round(drift_score, 4),
            accuracy_current=round(current_accuracy, 4), accuracy_baseline=baseline_accuracy,
            false_positive_rate=round(fpr, 4), retrain_recommended=retrain,
            details={"samples": len(recent_predictions), "degradation": round(baseline_accuracy - current_accuracy, 4)},
        )

    def persist_drift_report(self, session: Session, report: DriftReport) -> DriftReportRecord:
        record = DriftReportRecord(
            agent_name=report.agent_name, drift_score=report.drift_score,
            accuracy_current=report.accuracy_current, accuracy_baseline=report.accuracy_baseline,
            false_positive_rate=report.false_positive_rate, retrain_recommended=report.retrain_recommended,
            details=report.details,
        )
        session.add(record)
        session.flush()
        logger.info("drift_report_saved", agent=report.agent_name, drift=report.drift_score, retrain=report.retrain_recommended)
        return record
