"""CryptoGhost - Sentiment Engine com NLP."""

import re
import time
from dataclasses import dataclass

from backend.sentiment_engine.sources import SentimentDataCollector
from backend.shared.config import get_settings
from backend.shared.logging_config import get_logger
from backend.shared.metrics import AI_CONFIDENCE_GAUGE, AI_LATENCY, SENTIMENT_SCORE_GAUGE

logger = get_logger("cryptoghost.sentiment")

BULLISH_WORDS = {
    "bull", "bullish", "surge", "rally", "breakout", "moon", "pump", "gain", "profit",
    "approval", "adoption", "institutional", "buy", "accumulation", "green", " ATH",
    "record high", "optimism", "growth",
}
BEARISH_WORDS = {
    "bear", "bearish", "crash", "dump", "hack", "scam", "ban", "regulation", "sec",
    "lawsuit", "fear", "panic", "sell", "liquidation", "red", "drop", "fall", "decline",
    "correction", "fraud", "collapse",
}


@dataclass
class SentimentResult:
    market_sentiment: str
    score: float
    confidence: float
    bullish_pct: float
    bearish_pct: float
    panic_detected: bool
    euphoria_detected: bool
    sources: dict
    whale_movement: bool


class SentimentEngine:
    """Analisa sentimento via FinBERT (se disponível) ou NLP léxico avançado."""

    def __init__(self):
        self.settings = get_settings()
        self.collector = SentimentDataCollector()
        self._finbert = None
        self._tokenizer = None
        if self.settings.finbert_enabled:
            self._load_finbert()

    def _load_finbert(self) -> None:
        try:
            from transformers import AutoModelForSequenceClassification, AutoTokenizer
            import torch

            model_name = "ProsusAI/finbert"
            self._tokenizer = AutoTokenizer.from_pretrained(model_name)
            self._finbert = AutoModelForSequenceClassification.from_pretrained(model_name)
            self._finbert.eval()
            self._torch = torch
            logger.info("finbert_loaded")
        except Exception as exc:
            logger.warning("finbert_unavailable", error=str(exc))

    def _score_text_finbert(self, text: str) -> tuple[float, float, float]:
        import torch

        inputs = self._tokenizer(text[:512], return_tensors="pt", truncation=True, padding=True)
        with torch.no_grad():
            outputs = self._finbert(**inputs)
            probs = torch.nn.functional.softmax(outputs.logits, dim=-1).numpy()[0]

        # FinBERT labels: positive, negative, neutral
        positive, negative, neutral = float(probs[0]), float(probs[1]), float(probs[2])
        score = (positive - negative + 1) / 2
        return score, positive, negative

    def _score_text_lexical(self, text: str) -> tuple[float, float, float]:
        text_lower = text.lower()
        bull = sum(1 for w in BULLISH_WORDS if w in text_lower)
        bear = sum(1 for w in BEARISH_WORDS if w in text_lower)
        total = bull + bear or 1
        bullish_pct = bull / total
        bearish_pct = bear / total
        score = (bull - bear + total) / (2 * total)
        return score, bullish_pct, bearish_pct

    def _score_text(self, text: str) -> tuple[float, float, float]:
        if self._finbert is not None:
            try:
                return self._score_text_finbert(text)
            except Exception:
                pass
        return self._score_text_lexical(text)

    def analyze(self, symbol: str | None = None) -> SentimentResult:
        start = time.perf_counter()
        source_data = self.collector.collect_all()

        all_scores: list[float] = []
        source_summary: dict = {}
        panic_keywords = 0
        euphoria_keywords = 0
        whale_keywords = 0

        for src in source_data:
            src_scores = []
            for text in src.texts:
                if not text.strip():
                    continue
                score, bull, bear = self._score_text(text)
                src_scores.append(score)
                all_scores.append(score)

                text_lower = text.lower()
                if any(w in text_lower for w in ["panic", "crash", "liquidation", "capitulation"]):
                    panic_keywords += 1
                if any(w in text_lower for w in ["euphoria", "mania", "all time high", "ath", "to the moon"]):
                    euphoria_keywords += 1
                if any(w in text_lower for w in ["whale", "large transfer", "million btc", "billion"]):
                    whale_keywords += 1

            if src_scores:
                source_summary[src.source] = {"avg_score": round(sum(src_scores) / len(src_scores), 3), "count": len(src_scores)}

        if not all_scores:
            return SentimentResult("neutral", 50.0, 0.5, 0.5, 0.5, False, False, {}, False)

        avg_score = sum(all_scores) / len(all_scores)
        score_100 = avg_score * 100
        bullish_pct = sum(1 for s in all_scores if s > 0.55) / len(all_scores)
        bearish_pct = sum(1 for s in all_scores if s < 0.45) / len(all_scores)

        if score_100 >= 60:
            sentiment = "bullish"
        elif score_100 <= 40:
            sentiment = "bearish"
        else:
            sentiment = "neutral"

        confidence = min(0.95, 0.5 + len(all_scores) / 100)
        panic = panic_keywords >= 2
        euphoria = euphoria_keywords >= 2
        whale = whale_keywords >= 1

        elapsed = time.perf_counter() - start
        AI_LATENCY.labels(agent="sentiment").observe(elapsed)
        AI_CONFIDENCE_GAUGE.labels(agent="sentiment").set(confidence)
        SENTIMENT_SCORE_GAUGE.labels(source="aggregate").set(score_100)

        return SentimentResult(
            market_sentiment=sentiment,
            score=round(score_100, 1),
            confidence=round(confidence, 2),
            bullish_pct=round(bullish_pct, 2),
            bearish_pct=round(bearish_pct, 2),
            panic_detected=panic,
            euphoria_detected=euphoria,
            sources=source_summary,
            whale_movement=whale,
        )
