import { DashboardStats } from '../api';

interface Props {
  stats: DashboardStats;
}

export function StatsCards({ stats }: Props) {
  const signalColor = stats.ai_signal === 'buy' ? 'positive' : stats.ai_signal === 'sell' ? 'negative' : 'neutral';

  return (
    <div className="stats-grid">
      <div className="stat-card">
        <div className="stat-label">Posições Abertas</div>
        <div className="stat-value neutral">{stats.open_positions}</div>
      </div>
      <div className="stat-card">
        <div className="stat-label">Total de Ordens</div>
        <div className="stat-value neutral">{stats.total_orders}</div>
      </div>
      <div className="stat-card">
        <div className="stat-label">Sinal IA</div>
        <div className={`stat-value ${signalColor}`}>{stats.ai_signal.toUpperCase()}</div>
      </div>
      <div className="stat-card">
        <div className="stat-label">Confiança IA</div>
        <div className="stat-value neutral">{(stats.ai_confidence * 100).toFixed(1)}%</div>
      </div>
      <div className="stat-card">
        <div className="stat-label">P&L Diário</div>
        <div className={`stat-value ${stats.risk_status.daily_pnl >= 0 ? 'positive' : 'negative'}`}>
          {stats.risk_status.daily_pnl.toFixed(2)}
        </div>
      </div>
    </div>
  );
}
