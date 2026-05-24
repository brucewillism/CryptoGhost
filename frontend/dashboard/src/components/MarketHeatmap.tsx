import { HeatmapAsset } from '../api';

interface Props {
  assets: HeatmapAsset[];
}

export function MarketHeatmap({ assets }: Props) {
  const getColor = (score: number) => {
    if (score >= 70) return '#00d4aa';
    if (score >= 50) return '#ffa502';
    return '#ff4757';
  };

  return (
    <div className="card terminal-panel">
      <h2>Market Heatmap</h2>
      <div className="heatmap-grid">
        {assets.length === 0 ? (
          <div className="empty">Carregando heatmap...</div>
        ) : (
          assets.map((a) => (
            <div key={a.symbol} className="heatmap-cell" style={{ borderColor: getColor(a.score) }}>
              <div className="heatmap-symbol">{a.symbol.replace('/USDT', '')}</div>
              <div className="heatmap-score" style={{ color: getColor(a.score) }}>{a.score}</div>
              <div className="heatmap-trend">{a.trend}</div>
              <div className={`heatmap-change ${a.change >= 0 ? 'positive' : 'negative'}`}>
                {a.change >= 0 ? '+' : ''}{a.change.toFixed(2)}%
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
