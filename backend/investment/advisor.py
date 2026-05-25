"""CryptoGhost - Recomendação de investimento acionável com proposta de ordem."""

from decimal import Decimal, ROUND_DOWN

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.data_collector.collector import ExchangeConnector
from backend.shared.config import get_settings
from backend.shared.models_investment import AdaptiveAllocationRecord, InvestmentRankingRecord, OpportunityScoreRecord
from backend.shared.models_intelligence import AIConsensusRecord

BUY_LABELS = {"HIGH_PRIORITY_BUY", "STRONG_BUY", "MODERATE_BUY", "BUY", "ACCUMULATE"}
PAPER_PORTFOLIO_USDT = Decimal("10000")


def _live_price(symbol: str) -> Decimal:
    connector = ExchangeConnector("binance")
    ticker = connector.fetch_ticker(symbol)
    last = ticker.get("last") or ticker.get("close")
    if not last:
        raise ValueError(f"Preço indisponível para {symbol}")
    return Decimal(str(last))


async def build_investment_recommendation(session: AsyncSession) -> dict:
    """Monta recomendação a partir do ranking persistido + consenso IA."""
    settings = get_settings()
    portfolio_usdt = Decimal(str(settings.paper_portfolio_usdt))

    ranking_r = await session.execute(
        select(InvestmentRankingRecord).order_by(InvestmentRankingRecord.created_at.desc()).limit(10)
    )
    rankings = ranking_r.scalars().all()

    if not rankings:
        opp_r = await session.execute(
            select(OpportunityScoreRecord).order_by(OpportunityScoreRecord.opportunity_score.desc()).limit(5)
        )
        opps = opp_r.scalars().all()
        if opps:
            best_opp = opps[0]
            consensus_r = await session.execute(
                select(AIConsensusRecord)
                .where(AIConsensusRecord.symbol == best_opp.symbol)
                .order_by(AIConsensusRecord.created_at.desc())
                .limit(1)
            )
            consensus = consensus_r.scalar_one_or_none()
            rec_label = "MODERATE_BUY" if best_opp.opportunity_score >= 55 else "HOLD"
            if consensus and consensus.final_decision.upper() in ("BUY", "STRONG_BUY"):
                rec_label = "STRONG_BUY"
            fake_rank = type("Rank", (), {
                "symbol": best_opp.symbol,
                "priority_score": best_opp.opportunity_score,
                "expected_return_pct": min(15.0, best_opp.opportunity_score / 5),
                "confidence": consensus.confidence if consensus else 0.5,
                "recommendation": rec_label,
                "reasons": [f"Score oportunidade {best_opp.opportunity_score:.0f}", f"Classificação {best_opp.classification}"],
                "rank_position": 1,
            })()
            rankings = [fake_rank]

    alloc_r = await session.execute(
        select(AdaptiveAllocationRecord).order_by(AdaptiveAllocationRecord.created_at.desc()).limit(1)
    )
    allocation = alloc_r.scalar_one_or_none()

    consensus_r = await session.execute(
        select(AIConsensusRecord).order_by(AIConsensusRecord.created_at.desc()).limit(5)
    )
    consensus_rows = consensus_r.scalars().all()

    if not rankings:
        return {
            "status": "no_data",
            "message": "Execute uma análise IA primeiro para gerar ranking de investimentos.",
            "action_required": "analyze",
        }

    best = rankings[0]
    consensus = next((c for c in consensus_rows if c.symbol == best.symbol), consensus_rows[0] if consensus_rows else None)

    alloc_pct = float(allocation.allocations.get(best.symbol.split("/")[0], 0)) if allocation else 0.0
    if alloc_pct <= 0:
        alloc_pct = min(float(settings.max_exposure_pct), max(2.0, best.priority_score / 15))

    try:
        price = _live_price(best.symbol)
    except Exception as exc:
        return {"status": "error", "message": f"Não foi possível obter preço de mercado: {exc}"}

    investment_usdt = (portfolio_usdt * Decimal(str(alloc_pct)) / Decimal("100")).quantize(Decimal("0.01"))
    quantity = (investment_usdt / price).quantize(Decimal("0.000001"), rounding=ROUND_DOWN)

    stop_pct = Decimal(str(settings.default_stop_loss_pct))
    tp_pct = Decimal(str(settings.default_take_profit_pct))
    stop_loss = (price * (1 - stop_pct / 100)).quantize(Decimal("0.01"))
    take_profit = (price * (1 + tp_pct / 100)).quantize(Decimal("0.01"))

    can_invest = best.recommendation in BUY_LABELS and quantity > 0
    expected_profit_usdt = (investment_usdt * Decimal(str(best.expected_return_pct)) / Decimal("100")).quantize(Decimal("0.01"))

    ai_summary = (
        f"A IA recomenda **{best.symbol}** como melhor oportunidade agora "
        f"({best.recommendation}, score {best.priority_score:.0f}/100). "
        f"Retorno esperado ~{best.expected_return_pct:.1f}% em horizon de curto prazo. "
    )
    if consensus:
        ai_summary += (
            f"Consenso multi-agente: {consensus.final_decision} "
            f"({consensus.confidence * 100:.0f}% confiança). "
        )
    ai_summary += (
        f"Alocação sugerida: {alloc_pct:.1f}% do portfólio paper "
        f"(${float(investment_usdt):,.2f} USDT)."
    )

    return {
        "status": "ready",
        "ai_summary": ai_summary,
        "best_symbol": best.symbol,
        "recommendation": best.recommendation,
        "priority_score": best.priority_score,
        "expected_return_pct": best.expected_return_pct,
        "expected_profit_usdt": float(expected_profit_usdt),
        "confidence": best.confidence,
        "reasons": best.reasons or [],
        "consensus": {
            "decision": consensus.final_decision if consensus else None,
            "confidence": consensus.confidence if consensus else None,
        },
        "ranking_preview": [
            {
                "symbol": r.symbol,
                "rank": r.rank_position,
                "score": r.priority_score,
                "recommendation": r.recommendation,
                "expected_return": r.expected_return_pct,
            }
            for r in rankings[:5]
        ],
        "proposed_order": {
            "symbol": best.symbol,
            "side": "buy" if can_invest else "hold",
            "quantity": str(quantity),
            "price": str(price),
            "investment_usdt": float(investment_usdt),
            "allocation_pct": round(alloc_pct, 2),
            "stop_loss": str(stop_loss),
            "take_profit": str(take_profit),
            "paper_trading": settings.paper_trading,
            "requires_approval": True,
            "can_execute": can_invest,
        },
        "disclaimer": (
            "Modo PAPER — nenhum dinheiro real é movimentado. "
            "Lucros são simulados com preços reais de mercado. "
            "Confirme apenas se concordar com a recomendação."
        ),
    }
