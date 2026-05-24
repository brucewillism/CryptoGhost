import { RegimeData } from '../api';

interface Props {
  regime: RegimeData | null;
}

const REGIME_LABELS: Record<string, string> = {
  bull_market: 'Bull Market',
  bear_market: 'Bear Market',
  sideways: 'Sideways',
  high_volatility: 'Alta Volatilidade',
  low_volatility: 'Baixa Volatilidade',
  accumulation: 'Acumulação',
  distribution: 'Distribuição',
};

export function RegimeIndicator({ regime }: Props) {
  if (!regime || regime.regime === undefined) {
    return <div className="card terminal-panel"><h2>Market Regime</h2><div className="empty">Sem dados</div></div>;
  }

  return (
    <div className="card terminal-panel">
      <h2>Market Regime</h2>
      <div className="regime-display">
        <div className="regime-name">{REGIME_LABELS[regime.regime] || regime.regime}</div>
        <div className="regime-confidence">{(regime.confidence * 100).toFixed(0)}% confiança</div>
        {regime.volatility !== undefined && (
          <div className="regime-vol">Volatilidade: {regime.volatility.toFixed(1)}%</div>
        )}
        {regime.strategy_adjustment && (
          <div className="regime-strategy">Estratégia: {regime.strategy_adjustment.replace(/_/g, ' ')}</div>
        )}
      </div>
    </div>
  );
}
