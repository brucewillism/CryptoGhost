"""CryptoGhost - Intelligence Orchestrator."""

import asyncio
import time
import uuid
from dataclasses import asdict

import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession

from backend.ai_consensus_engine.consensus import AIConsensusEngine
from backend.ai_memory.service import AIMemoryService, MemoryEntry
from backend.explainable_ai.explainer import ExplainableAI
from backend.macro_analysis.analyzer import MacroAnalyzer
from backend.market_ai_analyst.analyst import MarketAIAnalyst
from backend.market_regime.detector import MarketRegimeDetector
from backend.news_intelligence.analyzer import NewsIntelligence
from backend.portfolio_ai.analyzer import PortfolioAI
from backend.risk_ai.detector import RiskAI
from backend.sentiment_engine.analyzer import SentimentEngine
from backend.shared.logging_config import get_logger
from backend.shared.models_intelligence import (
    AIConsensusRecord,
    AIExplanation,
    AssetAnalysisRecord,
    MacroIndicatorRecord,
    MarketRegimeRecord,
    NewsAnalysisRecord,
    SentimentHistory,
)
from backend.shared.redis_streams import get_stream_publisher

logger = get_logger("cryptoghost.intelligence.orchestrator")


class IntelligenceOrchestrator:
    """Orquestra todos os agentes de IA e produz consenso explicável."""

    def __init__(self):
        self.analyst = MarketAIAnalyst()
        self.sentiment = SentimentEngine()
        self.portfolio = PortfolioAI()
        self.explainer = ExplainableAI()
        self.risk_ai = RiskAI()
        self.regime = MarketRegimeDetector()
        self.consensus_engine = AIConsensusEngine()
        self.memory = AIMemoryService()
        self.news = NewsIntelligence()
        self.macro = MacroAnalyzer()
        self.stream = get_stream_publisher()

    async def analyze_symbol(self, session: AsyncSession, symbol: str) -> dict:
        start = time.perf_counter()

        df = await asyncio.to_thread(self.analyst.fetch_ohlcv_dataframe, symbol)
        analysis = await asyncio.to_thread(self.analyst.analyze, symbol, df)
        sentiment = await asyncio.to_thread(self.sentiment.analyze, symbol)
        risk = await asyncio.to_thread(self.risk_ai.assess, df, analysis.buy_pressure, analysis.liquidity_score)
        regime = await asyncio.to_thread(self.regime.detect, df, symbol)

        holdings = {symbol: float(analysis.indicators.get("sma_20", 1000))}
        price_history = {symbol: df}
        portfolio = await asyncio.to_thread(self.portfolio.analyze, holdings, price_history)

        votes = [
            AIConsensusEngine.vote_from_analyst(analysis.recommendation, analysis.confidence),
            AIConsensusEngine.vote_from_risk(risk.overall_risk, risk.crash_probability),
            AIConsensusEngine.vote_from_sentiment(sentiment.market_sentiment, sentiment.score, sentiment.confidence),
            AIConsensusEngine.vote_from_regime(regime.regime, regime.confidence),
            AIConsensusEngine.vote_from_portfolio(
                portfolio.risk_level,
                portfolio.recommendations[0].action if portfolio.recommendations else "maintain",
            ),
        ]
        consensus = self.consensus_engine.build_consensus(symbol, votes)

        features = {
            **analysis.indicators,
            "score": analysis.score,
            "buy_pressure": analysis.buy_pressure,
            "sell_pressure": analysis.sell_pressure,
            "volatility": analysis.volatility,
            "momentum": analysis.momentum,
            "sentiment_score": sentiment.score,
            "crash_probability": risk.crash_probability,
            "regime": regime.regime,
        }
        explanation = self.explainer.explain(consensus.final_decision, consensus.confidence, features)

        asset_record = AssetAnalysisRecord(
            symbol=symbol, score=analysis.score, trend=analysis.trend, risk=analysis.risk,
            confidence=analysis.confidence, recommendation=analysis.recommendation,
            indicators=analysis.indicators, strength_score=analysis.strength_score,
            reversal_probability=analysis.reversal_probability,
        )
        session.add(asset_record)

        sentiment_record = SentimentHistory(
            symbol=symbol, market_sentiment=sentiment.market_sentiment, score=sentiment.score,
            confidence=sentiment.confidence, sources=sentiment.sources,
            bullish_pct=sentiment.bullish_pct, bearish_pct=sentiment.bearish_pct,
            panic_detected=sentiment.panic_detected, euphoria_detected=sentiment.euphoria_detected,
        )
        session.add(sentiment_record)

        regime_record = MarketRegimeRecord(
            symbol=symbol, regime=regime.regime, confidence=regime.confidence,
            volatility=regime.volatility, trend_strength=regime.trend_strength,
            features=regime.features, strategy_adjustment=regime.strategy_adjustment,
        )
        session.add(regime_record)

        explanation_record = AIExplanation(
            decision_id=uuid.UUID(explanation.decision_id),
            symbol=symbol, decision=consensus.final_decision, confidence=consensus.confidence,
            reasons=explanation.reasons, feature_importance=explanation.feature_importance,
            shap_values=explanation.shap_values, decision_trace=explanation.decision_trace,
            textual_explanation=explanation.textual_explanation,
        )
        session.add(explanation_record)
        await session.flush()

        consensus_record = AIConsensusRecord(
            symbol=symbol, final_decision=consensus.final_decision, confidence=consensus.confidence,
            agreement=consensus.agreement, disagreement=consensus.disagreement,
            agent_votes=[asdict(v) for v in consensus.agent_votes],
            conflicts=consensus.conflicts, explanation_id=explanation_record.id,
        )
        session.add(consensus_record)

        memory_entry = MemoryEntry(
            symbol=symbol, decision=consensus.final_decision,
            market_context={"regime": regime.regime, "sentiment": sentiment.market_sentiment, "score": analysis.score},
        )
        await self.memory.store(session, memory_entry)

        agreement_ratio = consensus.agreement / max(consensus.agreement + consensus.disagreement, 1)

        result = {
            "symbol": symbol,
            "analysis": {
                "score": analysis.score, "trend": analysis.trend, "risk": analysis.risk,
                "confidence": analysis.confidence, "recommendation": analysis.recommendation,
                "strength_score": analysis.strength_score, "reversal_probability": analysis.reversal_probability,
                "indicators": analysis.indicators,
            },
            "sentiment": {
                "market_sentiment": sentiment.market_sentiment, "score": sentiment.score,
                "confidence": sentiment.confidence, "panic_detected": sentiment.panic_detected,
                "whale_movement": sentiment.whale_movement,
            },
            "risk": {
                "overall_risk": risk.overall_risk, "crash_probability": risk.crash_probability,
                "instability_score": risk.instability_score, "warnings": risk.warnings,
            },
            "regime": {
                "regime": regime.regime, "confidence": regime.confidence,
                "strategy_adjustment": regime.strategy_adjustment,
            },
            "consensus": {
                "final_decision": consensus.final_decision, "confidence": consensus.confidence,
                "agreement": consensus.agreement, "disagreement": consensus.disagreement,
                "conflicts": consensus.conflicts, "weighted_scores": consensus.weighted_scores,
            },
            "explanation": {
                "decision": explanation.decision, "confidence": explanation.confidence,
                "reasons": explanation.reasons, "textual_explanation": explanation.textual_explanation,
                "feature_importance": explanation.feature_importance,
            },
            "elapsed_ms": round((time.perf_counter() - start) * 1000, 1),
        }

        try:
            from backend.quant.pipeline import QuantPipeline
            quant = QuantPipeline()
            result["quant_v3"] = await quant.enhance_analysis(
                session, symbol, result, df, regime.regime, agreement_ratio,
            )
        except Exception as exc:
            logger.warning("quant_pipeline_failed", error=str(exc))
            result["quant_v3"] = {"status": "unavailable", "error": str(exc)}

        try:
            from backend.investment.pipeline import InvestmentPipeline
            inv = InvestmentPipeline()
            ctx = inv.build_context(
                symbol, df, result, result.get("quant_v3"),
                liquidity_score=min(1.0, float(analysis.indicators.get("volume_ratio", 1)) / 3),
            )
            result["investment_v4"] = await inv.analyze_symbol(session, ctx)
        except Exception as exc:
            logger.warning("investment_pipeline_failed", error=str(exc))
            result["investment_v4"] = {"status": "unavailable", "error": str(exc)}

        try:
            from backend.self_improving.pipeline import SelfImprovingPipeline
            si = SelfImprovingPipeline()
            si_ctx = si.build_context(symbol, df, result, result.get("quant_v3"), result.get("investment_v4"))
            result["self_improving_v5"] = await si.enhance(session, si_ctx)
        except Exception as exc:
            logger.warning("self_improving_pipeline_failed", error=str(exc))
            result["self_improving_v5"] = {"status": "unavailable", "error": str(exc)}

        try:
            from backend.shared.config import get_settings
            settings = get_settings()
            if settings.v6_enabled and settings.consensus_v3_enabled:
                from backend.app.ai.consensus_v3.engine import ConsensusEngineV3
                from backend.app.ai.regime.service import RegimeDetectionService
                from backend.app.auto_invest.signal_freshness import SignalFreshnessValidator

                regime_svc = RegimeDetectionService()
                regime_enum, policy, _ = await regime_svc.detect_and_persist(session, symbol, df)
                c3_engine = ConsensusEngineV3()
                weights = await c3_engine.performance.compute_weights(session, symbol, regime_enum.value)
                calibrated = result.get("quant_v3", {}).get("calibration", {}).get("calibrated_confidence", consensus.confidence)
                c3 = c3_engine.build_from_votes(
                    symbol, votes,
                    calibrated_confidence=float(calibrated or 0.5),
                    technical_score=float(analysis.score),
                    sentiment_score=float(sentiment.score),
                    regime=regime_enum,
                    policy=policy,
                    agent_weights=weights,
                )
                result["consensus_v3"] = ConsensusEngineV3.to_dict(c3)
                result["consensus"] = {
                    "final_decision": c3.final_decision,
                    "confidence": c3.consensus,
                    "agreement": c3.agreement,
                    "disagreement": c3.disagreement,
                    "conflicts": c3.conflicts,
                    "agent_votes": result["consensus_v3"]["agent_votes"],
                    "final_score": c3.final_score,
                    "classification": c3.classification.value,
                    "can_execute": c3.can_execute,
                }
                await SignalFreshnessValidator().persist_signal(session, c3, regime_enum.value)

                from backend.app.ai.quant_models.ensemble import QuantEnsemble
                from backend.app.features.calculators.technical import compute_all_features
                feat = compute_all_features(df)
                result["quant_ml"] = __import__("dataclasses").asdict(
                    QuantEnsemble().predict(df, feat)
                )
        except Exception as exc:
            logger.warning("consensus_v3_failed", error=str(exc))
            result["consensus_v3"] = {"status": "unavailable", "error": str(exc)}

        try:
            self.stream.publish_sync(
                "intelligence_update",
                {"symbol": symbol, "consensus": result["consensus"], "analysis": result["analysis"]},
            )
            from backend.api.websocket import broadcast_intelligence_update, broadcast_consensus_update
            await broadcast_intelligence_update({"symbol": symbol, "consensus": result.get("consensus"), "analysis": result.get("analysis")})
            await broadcast_consensus_update({"symbol": symbol, "consensus": result.get("consensus"), "consensus_v3": result.get("consensus_v3")})
        except Exception as exc:
            logger.warning("stream_publish_failed", error=str(exc))

        logger.info("intelligence_complete", symbol=symbol, decision=consensus.final_decision, elapsed_ms=result["elapsed_ms"])
        return result

    async def analyze_macro_and_news(self, session: AsyncSession) -> dict:
        macro = await asyncio.to_thread(self.macro.analyze)
        news_items = await asyncio.to_thread(self.news.analyze_batch, 10)

        for ind in macro.indicators:
            session.add(MacroIndicatorRecord(
                indicator_name=ind.name, value=ind.value, change_pct=ind.change_pct,
                impact=ind.impact, metadata_=ind.metadata,
            ))

        for item in news_items:
            session.add(NewsAnalysisRecord(
                title=item.title, source=item.source, impact=item.impact,
                direction=item.direction, confidence=item.confidence,
                categories=item.categories, url=item.url, summary=item.summary,
            ))

        result = {
            "macro": {"outlook": macro.market_outlook, "summary": macro.summary, "indicators": [asdict(i) for i in macro.indicators]},
            "news": [{"title": n.title, "impact": n.impact, "direction": n.direction, "confidence": n.confidence} for n in news_items[:5]],
        }
        try:
            self.stream.publish_sync("macro_news_update", result)
        except Exception as exc:
            logger.warning("stream_publish_failed", error=str(exc))
        return result

    async def get_market_heatmap(self, symbols: list[str]) -> list[dict]:
        results = []
        for symbol in symbols:
            try:
                analysis = await asyncio.to_thread(self.analyst.analyze, symbol)
                results.append({"symbol": symbol, "score": analysis.score, "trend": analysis.trend, "change": analysis.momentum})
            except Exception as exc:
                logger.warning("heatmap_failed", symbol=symbol, error=str(exc))
        return results
