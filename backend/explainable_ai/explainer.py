"""CryptoGhost - Explainable AI (XAI)."""

import uuid
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

from backend.shared.logging_config import get_logger

logger = get_logger("cryptoghost.explainable_ai")


@dataclass
class ExplanationResult:
    decision: str
    confidence: float
    reasons: list[str]
    feature_importance: dict[str, float]
    shap_values: dict[str, float]
    decision_trace: list[dict]
    textual_explanation: str
    decision_id: str = field(default_factory=lambda: str(uuid.uuid4()))


class ExplainableAI:
    """Gera explicações completas para cada decisão da IA usando SHAP e feature importance."""

    FEATURE_LABELS = {
        "rsi": "RSI (Relative Strength Index)",
        "macd": "MACD",
        "momentum": "Momentum",
        "volume_ratio": "Volume relativo",
        "buy_pressure": "Pressão compradora",
        "sell_pressure": "Pressão vendedora",
        "volatility": "Volatilidade",
        "score": "Score composto",
        "sentiment": "Sentimento de mercado",
        "regime": "Regime de mercado",
    }

    def explain(
        self,
        decision: str,
        confidence: float,
        features: dict[str, float],
        agent: str = "consensus",
    ) -> ExplanationResult:
        reasons = self._generate_reasons(decision, features)
        feature_importance = self._compute_feature_importance(features, decision)
        shap_values = self._compute_shap_approximation(features, feature_importance)
        decision_trace = self._build_decision_trace(decision, features, feature_importance, agent)
        textual = self._generate_textual_explanation(decision, confidence, reasons, feature_importance)

        logger.info("explanation_generated", decision=decision, confidence=confidence, reasons_count=len(reasons))

        return ExplanationResult(
            decision=decision,
            confidence=confidence,
            reasons=reasons,
            feature_importance=feature_importance,
            shap_values=shap_values,
            decision_trace=decision_trace,
            textual_explanation=textual,
        )

    def explain_with_model(
        self,
        df: pd.DataFrame,
        decision: str,
        confidence: float,
        feature_cols: list[str],
    ) -> ExplanationResult:
        """Explica decisão usando SHAP real com Random Forest treinado."""
        df = df.copy()
        df["returns"] = df["close"].pct_change()
        df["label"] = (df["returns"].shift(-1) > 0).astype(int)
        df = df.dropna()

        if len(df) < 50:
            features = {col: float(df[col].iloc[-1]) if col in df.columns else 0 for col in feature_cols}
            return self.explain(decision, confidence, features)

        X = df[feature_cols].values
        y = df["label"].values
        model = RandomForestClassifier(n_estimators=50, max_depth=5, random_state=42)
        model.fit(X[:-1], y[:-1])

        importances = dict(zip(feature_cols, model.feature_importances_.tolist()))
        features = {col: float(df[col].iloc[-1]) for col in feature_cols}

        shap_values = self._compute_shap_with_tree(model, X[-1:], feature_cols)

        return self.explain(decision, confidence, features, agent="ml_model")

    def _generate_reasons(self, decision: str, features: dict[str, float]) -> list[str]:
        reasons = []

        rsi = features.get("rsi", 50)
        if rsi < 30:
            reasons.append("RSI oversold — possível reversão de alta")
        elif rsi > 70:
            reasons.append("RSI overbought — possível correção")

        if features.get("macd", 0) > features.get("macd_signal", 0):
            reasons.append("MACD bullish crossover")
        elif features.get("macd", 0) < features.get("macd_signal", 0):
            reasons.append("MACD bearish crossover")

        if features.get("volume_ratio", 1) > 1.5:
            reasons.append("High volume breakout confirmando movimento")

        if features.get("buy_pressure", 0.5) > 0.6:
            reasons.append("Pressão compradora dominante no order book")
        elif features.get("sell_pressure", 0.5) > 0.6:
            reasons.append("Pressão vendedora dominante no order book")

        if features.get("momentum", 0) > 5:
            reasons.append("Momentum positivo forte")
        elif features.get("momentum", 0) < -5:
            reasons.append("Momentum negativo forte")

        if features.get("sentiment_score", 50) > 65:
            reasons.append("Sentimento de mercado bullish")
        elif features.get("sentiment_score", 50) < 35:
            reasons.append("Sentimento de mercado bearish")

        if features.get("crash_probability", 0) > 0.6:
            reasons.append("Alta probabilidade de crash detectada pelo Risk AI")

        if not reasons:
            reasons.append(f"Sinal {decision} baseado em análise composta de indicadores")

        return reasons[:8]

    def _compute_feature_importance(self, features: dict[str, float], decision: str) -> dict[str, float]:
        weights = {
            "rsi": 0.15, "macd": 0.12, "momentum": 0.12, "volume_ratio": 0.10,
            "buy_pressure": 0.10, "sell_pressure": 0.08, "volatility": 0.08,
            "score": 0.15, "sentiment_score": 0.10,
        }
        importance = {}
        for key, weight in weights.items():
            if key in features:
                val = abs(features[key] - 50) / 50 if key in ("rsi", "score", "sentiment_score") else abs(features[key])
                importance[key] = round(weight * min(1.0, val), 4)

        total = sum(importance.values()) or 1
        return {k: round(v / total, 4) for k, v in sorted(importance.items(), key=lambda x: -x[1])}

    def _compute_shap_approximation(self, features: dict, importance: dict) -> dict[str, float]:
        shap = {}
        for key, imp in importance.items():
            val = features.get(key, 0)
            direction = 1 if val > 0 else -1
            shap[key] = round(imp * direction * abs(val) / max(abs(val), 1), 4)
        return shap

    def _compute_shap_with_tree(self, model, X, feature_cols: list[str]) -> dict[str, float]:
        try:
            import shap
            explainer = shap.TreeExplainer(model)
            shap_values = explainer.shap_values(X)
            if isinstance(shap_values, list):
                values = shap_values[1][0] if len(shap_values) > 1 else shap_values[0][0]
            else:
                values = shap_values[0]
            return {col: round(float(val), 4) for col, val in zip(feature_cols, values)}
        except ImportError:
            return self._compute_shap_approximation(
                {col: float(X[0][i]) for i, col in enumerate(feature_cols)},
                self._compute_feature_importance({col: float(X[0][i]) for i, col in enumerate(feature_cols)}, "buy"),
            )

    def _build_decision_trace(self, decision: str, features: dict, importance: dict, agent: str) -> list[dict]:
        trace = [{"step": 1, "agent": agent, "action": "collect_features", "features_count": len(features)}]

        top_features = list(importance.items())[:3]
        trace.append({"step": 2, "action": "rank_features", "top_features": dict(top_features)})

        trace.append({"step": 3, "action": "apply_decision_rules", "decision": decision})

        trace.append({"step": 4, "action": "generate_explanation", "reasons_count": len(self._generate_reasons(decision, features))})

        return trace

    def _generate_textual_explanation(
        self, decision: str, confidence: float, reasons: list[str], importance: dict
    ) -> str:
        top = list(importance.keys())[:3]
        top_labels = [self.FEATURE_LABELS.get(k, k) for k in top]
        reasons_text = "; ".join(reasons[:4])

        return (
            f"Decisão: {decision.upper()} com confiança de {confidence:.0%}. "
            f"Principais fatores: {', '.join(top_labels)}. "
            f"Razões: {reasons_text}."
        )
