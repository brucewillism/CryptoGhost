import { DashboardStats } from '../api';

interface Props {
  stats: DashboardStats;
}

export function PaperEarningsBanner({ stats }: Props) {
  const pnl = stats.total_pnl;
  const positive = pnl >= 0;
  const portfolio = stats.paper_portfolio_value || 10000;
  const ret = stats.paper_return_pct ?? 0;

  return (
    <section className="earnings-banner">
      <div className="earnings-main">
        <span className="earnings-label">💰 Seu rendimento paper (simulado)</span>
        <span className={`earnings-value ${positive ? 'positive' : 'negative'}`}>
          {positive ? '+' : ''}{pnl.toFixed(2)} USDT
        </span>
        <span className={`earnings-pct ${positive ? 'positive' : 'negative'}`}>
          ({positive ? '+' : ''}{ret.toFixed(2)}%)
        </span>
      </div>
      <div className="earnings-side">
        <div>
          <span className="sub-label">Portfólio virtual</span>
          <span className="sub-value">${portfolio.toLocaleString(undefined, { maximumFractionDigits: 2 })}</span>
        </div>
        <div>
          <span className="sub-label">Posições abertas</span>
          <span className="sub-value">{stats.open_positions}</span>
        </div>
      </div>
    </section>
  );
}
