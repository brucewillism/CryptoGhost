"""CryptoGhost - Engine de Inteligência Artificial."""

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler

from backend.shared.logging_config import get_logger

logger = get_logger("cryptoghost.ai_engine")

MODELS_DIR = Path("models")


@dataclass
class PredictionResult:
    symbol: str
    signal: Literal["buy", "sell", "hold"]
    confidence: float
    predicted_price: float | None
    model_name: str
    metrics: dict
    explanation: str
    features: dict


class LSTMModel(nn.Module):
    """LSTM para previsão de tendências temporais."""

    def __init__(self, input_size: int = 5, hidden_size: int = 64, num_layers: int = 2):
        super().__init__()
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True, dropout=0.2)
        self.fc = nn.Linear(hidden_size, 3)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out, _ = self.lstm(x)
        return self.fc(out[:, -1, :])


class HybridAISignalGenerator:
    """Gerador híbrido: LSTM + Random Forest + regras técnicas."""

    MODEL_SELECTION_REASON = (
        "Modelo híbrido: LSTM (temporal) + RF (não-linear) + regras (interpretável)."
    )

    def __init__(self):
        self.lstm = LSTMModel()
        self.rf_classifier = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
        self.scaler = StandardScaler()
        self._rf_trained = False
        MODELS_DIR.mkdir(exist_ok=True)

    def prepare_features(self, df: pd.DataFrame) -> np.ndarray:
        features = df[["open", "high", "low", "close", "volume"]].astype(float).values
        if len(features) < 2:
            return features
        return self.scaler.fit_transform(features)

    def train_random_forest(self, df: pd.DataFrame) -> dict:
        if len(df) < 50:
            return {"status": "insufficient_data", "samples": len(df)}

        df = df.copy()
        df["returns"] = df["close"].pct_change()
        df["label"] = (df["returns"].shift(-1) > 0).astype(int)
        df = df.dropna()

        feature_cols = ["open", "high", "low", "close", "volume"]
        X = df[feature_cols].values
        y = df["label"].values
        X_scaled = self.scaler.fit_transform(X)

        split = int(len(X) * 0.8)
        self.rf_classifier.fit(X_scaled[:split], y[:split])
        self._rf_trained = True

        train_score = self.rf_classifier.score(X_scaled[:split], y[:split])
        test_score = self.rf_classifier.score(X_scaled[split:], y[split:])
        return {"train_accuracy": train_score, "test_accuracy": test_score, "samples": len(df)}

    def predict_lstm(self, features: np.ndarray) -> tuple[str, float]:
        self.lstm.eval()
        if len(features) < 10:
            return "hold", 0.5

        seq = torch.FloatTensor(features[-30:]).unsqueeze(0)
        with torch.no_grad():
            output = self.lstm(seq)
            probs = torch.softmax(output, dim=1).numpy()[0]

        signals = ["buy", "sell", "hold"]
        idx = int(np.argmax(probs))
        return signals[idx], float(probs[idx])

    def predict_rf(self, features: np.ndarray) -> tuple[str, float]:
        if not self._rf_trained or len(features) == 0:
            return "hold", 0.5

        pred = self.rf_classifier.predict(features[-1:])
        proba = self.rf_classifier.predict_proba(features[-1:])[0]
        signal = "buy" if pred[0] == 1 else "sell"
        return signal, float(max(proba))

    def rule_based_signal(self, indicators: dict) -> tuple[str, float]:
        rsi = indicators.get("rsi_14", 50)
        macd = indicators.get("macd", 0)
        macd_signal = indicators.get("macd_signal", 0)

        if rsi < 30 and macd > macd_signal:
            return "buy", 0.7
        if rsi > 70 and macd < macd_signal:
            return "sell", 0.7
        return "hold", 0.6

    def generate_signal(self, symbol: str, df: pd.DataFrame, indicators: dict | None = None) -> PredictionResult:
        indicators = indicators or {}
        features = self.prepare_features(df)

        lstm_signal, lstm_conf = self.predict_lstm(features)
        rf_signal, rf_conf = self.predict_rf(features)
        rule_signal, rule_conf = self.rule_based_signal(indicators)

        votes = {"buy": 0.0, "sell": 0.0, "hold": 0.0}
        votes[lstm_signal] += lstm_conf * 0.4
        votes[rf_signal] += rf_conf * 0.35
        votes[rule_signal] += rule_conf * 0.25

        final_signal = max(votes, key=votes.get)  # type: ignore
        confidence = votes[final_signal]
        predicted_price = float(df["close"].iloc[-1] * (1.01 if final_signal == "buy" else 0.99))

        return PredictionResult(
            symbol=symbol,
            signal=final_signal,  # type: ignore
            confidence=confidence,
            predicted_price=predicted_price,
            model_name="CryptoGhost-Hybrid-v1",
            metrics=self.calculate_metrics(df),
            explanation=(
                f"Sinal {final_signal} para {symbol}. LSTM={lstm_signal}, RF={rf_signal}, "
                f"Regras={rule_signal}. Confiança={confidence:.2f}"
            ),
            features=indicators,
        )

    @staticmethod
    def calculate_metrics(df: pd.DataFrame) -> dict:
        if len(df) < 2:
            return {}

        returns = df["close"].pct_change().dropna()
        cumulative = (1 + returns).cumprod()
        peak = cumulative.cummax()
        drawdown = (cumulative - peak) / peak
        sharpe = float(returns.mean() / returns.std() * np.sqrt(252)) if returns.std() > 0 else 0.0

        return {
            "sharpe_ratio": round(sharpe, 4),
            "max_drawdown": round(float(drawdown.min()), 4),
            "volatility": round(float(returns.std() * np.sqrt(252)), 4),
            "total_return": round(float(cumulative.iloc[-1] - 1), 4) if len(cumulative) > 0 else 0.0,
        }
