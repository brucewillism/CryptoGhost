import { useState } from 'react';
import { api } from '../../api';

interface Props {
  runs: Array<Record<string, unknown>>;
  onRefresh: () => void;
}

export function BacktestingDashboard({ runs, onRefresh }: Props) {
  const [running, setRunning] = useState(false);

  const runBacktest = async () => {
    setRunning(true);
    try {
      await api.runV6Backtest(['BTC/USDT', 'ETH/USDT']);
      onRefresh();
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className="v6-backtests">
      <div className="v6-header-inline">
        <h3>Backtesting v6</h3>
        <button className="analyze-btn small" onClick={runBacktest} disabled={running}>
          {running ? 'Rodando...' : 'Novo backtest'}
        </button>
      </div>
      {runs.length === 0 ? (
        <p className="v6-empty">Nenhum backtest ainda</p>
      ) : (
        runs.slice(0, 5).map((b) => {
          const m = (b.metrics as Record<string, number>) || {};
          return (
            <p key={String(b.id)}>
              {String(b.name)} — Sharpe: {(m.sharpe_ratio ?? 0).toFixed(2)} · Win: {((m.win_rate ?? 0) * 100).toFixed(0)}%
            </p>
          );
        })
      )}
    </div>
  );
}
