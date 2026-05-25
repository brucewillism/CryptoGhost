import { useEffect, useState } from 'react';
import { api } from '../../api';

interface Trade {
  asset: string;
  regime: string;
  setup: string;
  pnl: number | null;
  result: string;
  confidence: number;
}

export function TradeMemoryExplorer() {
  const [trades, setTrades] = useState<Trade[]>([]);
  const [similar, setSimilar] = useState<Trade[]>([]);
  const [loading, setLoading] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const [mem, sim] = await Promise.all([
        api.getV6TradeMemory('BTC/USDT').catch(() => ({ trades: [] })),
        api.getV6SimilarTrades('BTC/USDT').catch(() => ({ similar: [] })),
      ]);
      setTrades((mem.trades as Trade[]) || []);
      setSimilar((sim.similar as Trade[]) || []);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  return (
    <div className="v6-memory">
      <div className="v6-header-inline">
        <h3>Trade Memory</h3>
        <button className="analyze-btn small" onClick={load} disabled={loading}>Atualizar</button>
      </div>
      <div className="v6-memory-grid">
        <div>
          <h4>Histórico</h4>
          {trades.slice(0, 5).map((t, i) => (
            <p key={i}>{t.setup} · {t.result} · PnL {t.pnl?.toFixed(2) ?? '—'}</p>
          ))}
        </div>
        <div>
          <h4>Setups similares</h4>
          {similar.slice(0, 5).map((t, i) => (
            <p key={i}>{t.regime} · {t.result} · conf {(t.confidence * 100).toFixed(0)}%</p>
          ))}
        </div>
      </div>
    </div>
  );
}
