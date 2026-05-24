import { SentimentData } from '../api';

interface Props {
  sentiment: SentimentData | null;
}

export function SentimentPanel({ sentiment }: Props) {
  if (!sentiment) return <div className="card terminal-panel"><h2>Sentiment</h2><div className="empty">Carregando...</div></div>;

  const color = sentiment.market_sentiment === 'bullish' ? 'var(--accent)' :
    sentiment.market_sentiment === 'bearish' ? 'var(--danger)' : 'var(--warning)';

  return (
    <div className="card terminal-panel">
      <h2>Market Sentiment</h2>
      <div className="sentiment-display">
        <div className="sentiment-score" style={{ color }}>{sentiment.score.toFixed(0)}</div>
        <div className="sentiment-label" style={{ color }}>{sentiment.market_sentiment.toUpperCase()}</div>
        <div className="sentiment-bar">
          <div className="sentiment-bull" style={{ width: `${(sentiment.bullish_pct ?? 0.5) * 100}%` }} />
          <div className="sentiment-bear" style={{ width: `${(sentiment.bearish_pct ?? 0.5) * 100}%` }} />
        </div>
        {sentiment.panic_detected && <div className="alert-tag panic">PANIC DETECTED</div>}
        <div className="sentiment-conf">Confiança: {(sentiment.confidence * 100).toFixed(0)}%</div>
      </div>
    </div>
  );
}
