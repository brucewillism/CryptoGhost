import { DashboardStats } from '../api';

interface Props {
  stats: DashboardStats;
}

export function StatsCards({ stats }: Props) {
  const signalColor = stats.ai_signal === 'buy' ? 'positive' : stats.ai_signal === 'sell' ? 'negative' : 'neutral';
  const pnlPositive = stats.total_pnl >= 0;

  return (
    <div className="stats-grid">
      <div className="stat-card highlight">
        <div className="stat-label">Rendimento Paper</div>
        <div className={`stat-value ${pnlPositive ? 'positive' : 'negative'}`}>
          {pnlPositive ? '+' : ''}{stats.total_pnl.toFixed(2)} USDT
        </div>
      </div>
      <div className="stat-card">
        <div className="stat-label">Portfólio Virtual</div>
        <div className="stat-value positive">
          ${stats.paper_portfolio_value.toLocaleString(undefined, { maximumFractionDigits: 0 })}
        </div>
      </div>
      <div className="stat-card">
        <div className="stat-label">Posições Abertas</div>
        <div className="stat-value neutral">{stats.open_positions}</div>
      </div>
      <div className="stat-card">
        <div className="stat-label">Sinal IA</div>
        <div className={`stat-value ${signalColor}`}>{stats.ai_signal.toUpperCase()}</div>
      </div>
      <div className="stat-card">
        <div className="stat-label">Confiança IA</div>
        <div className="stat-value neutral">{(stats.ai_confidence * 100).toFixed(1)}%</div>
      </div>
    </div>
  );
}
