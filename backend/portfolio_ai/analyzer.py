"""CryptoGhost - Portfolio AI."""

from dataclasses import dataclass
from decimal import Decimal

import numpy as np
import pandas as pd

from backend.shared.logging_config import get_logger

logger = get_logger("cryptoghost.portfolio_ai")


@dataclass
class PortfolioRecommendation:
    action: str
    reason: str
    priority: str
    asset: str | None = None


@dataclass
class PortfolioAnalysis:
    total_value: Decimal
    sharpe_ratio: float
    sortino_ratio: float
    var_95: float
    max_concentration: float
    correlation_matrix: dict
    exposure_by_asset: dict
    recommendations: list[PortfolioRecommendation]
    risk_level: str


class PortfolioAI:
    """Gestão inteligente de portfólio com métricas institucionais."""

    def analyze(
        self,
        holdings: dict[str, float],
        price_history: dict[str, pd.DataFrame],
        portfolio_value: Decimal | None = None,
    ) -> PortfolioAnalysis:
        if not holdings:
            raise ValueError("Portfólio vazio")

        total = portfolio_value or Decimal(str(sum(holdings.values())))
        exposure = {asset: round(val / float(total) * 100, 2) for asset, val in holdings.items()}
        max_concentration = max(exposure.values())

        returns_matrix = self._build_returns_matrix(price_history, list(holdings.keys()))
        sharpe = self._sharpe_ratio(returns_matrix)
        sortino = self._sortino_ratio(returns_matrix)
        var_95 = self._var(returns_matrix, 0.95)
        corr = self._correlation_matrix(returns_matrix)

        recommendations = self._generate_recommendations(exposure, max_concentration, sharpe, var_95, corr)

        risk_level = "high" if max_concentration > 50 or var_95 > 5 else "medium" if var_95 > 2 else "low"

        logger.info("portfolio_analyzed", total=float(total), sharpe=sharpe, var_95=var_95)

        return PortfolioAnalysis(
            total_value=total,
            sharpe_ratio=round(sharpe, 4),
            sortino_ratio=round(sortino, 4),
            var_95=round(var_95, 4),
            max_concentration=round(max_concentration, 2),
            correlation_matrix=corr,
            exposure_by_asset=exposure,
            recommendations=recommendations,
            risk_level=risk_level,
        )

    @staticmethod
    def _build_returns_matrix(price_history: dict[str, pd.DataFrame], assets: list[str]) -> pd.DataFrame:
        series = {}
        for asset in assets:
            if asset in price_history and len(price_history[asset]) > 1:
                series[asset] = price_history[asset]["close"].astype(float).pct_change().dropna()
        if not series:
            return pd.DataFrame()
        return pd.DataFrame(series).dropna()

    @staticmethod
    def _sharpe_ratio(returns: pd.DataFrame, risk_free: float = 0.02) -> float:
        if returns.empty:
            return 0.0
        portfolio_returns = returns.mean(axis=1)
        excess = portfolio_returns.mean() * 252 - risk_free
        std = portfolio_returns.std() * np.sqrt(252)
        return float(excess / std) if std > 0 else 0.0

    @staticmethod
    def _sortino_ratio(returns: pd.DataFrame, risk_free: float = 0.02) -> float:
        if returns.empty:
            return 0.0
        portfolio_returns = returns.mean(axis=1)
        downside = portfolio_returns[portfolio_returns < 0]
        downside_std = downside.std() * np.sqrt(252)
        excess = portfolio_returns.mean() * 252 - risk_free
        return float(excess / downside_std) if downside_std > 0 else 0.0

    @staticmethod
    def _var(returns: pd.DataFrame, confidence: float) -> float:
        if returns.empty:
            return 0.0
        portfolio_returns = returns.mean(axis=1)
        return float(-np.percentile(portfolio_returns, (1 - confidence) * 100) * 100)

    @staticmethod
    def _correlation_matrix(returns: pd.DataFrame) -> dict:
        if returns.empty or returns.shape[1] < 2:
            return {}
        corr = returns.corr()
        return {a: {b: round(float(corr.loc[a, b]), 3) for b in corr.columns} for a in corr.index}

    @staticmethod
    def _generate_recommendations(
        exposure: dict, max_conc: float, sharpe: float, var_95: float, corr: dict
    ) -> list[PortfolioRecommendation]:
        recs: list[PortfolioRecommendation] = []

        if max_conc > 40:
            top_asset = max(exposure, key=exposure.get)  # type: ignore
            recs.append(PortfolioRecommendation(
                action="reduce_exposure",
                reason=f"Concentração em {top_asset} ({max_conc}%) acima do limite recomendado (40%)",
                priority="high",
                asset=top_asset,
            ))

        if var_95 > 3:
            recs.append(PortfolioRecommendation(
                action="increase_hedge",
                reason=f"VaR 95% de {var_95:.2f}% indica risco elevado de perda diária",
                priority="high",
            ))

        if sharpe < 0.5:
            recs.append(PortfolioRecommendation(
                action="rebalance",
                reason=f"Sharpe Ratio ({sharpe:.2f}) abaixo do mínimo recomendado (0.5)",
                priority="medium",
            ))

        high_corr_pairs = []
        for a, corrs in corr.items():
            for b, val in corrs.items():
                if a < b and val > 0.85:
                    high_corr_pairs.append((a, b, val))
        if high_corr_pairs:
            a, b, val = high_corr_pairs[0]
            recs.append(PortfolioRecommendation(
                action="reduce_volatility",
                reason=f"Alta correlação entre {a} e {b} ({val:.2f}) — diversificação insuficiente",
                priority="medium",
            ))

        if not recs:
            recs.append(PortfolioRecommendation(
                action="maintain",
                reason="Portfólio dentro dos parâmetros de risco recomendados",
                priority="low",
            ))

        return recs
