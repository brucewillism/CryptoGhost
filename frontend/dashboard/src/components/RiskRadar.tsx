import { DashboardStats } from '../api';

interface Props {
  risk: DashboardStats['risk_status'];
}

export function RiskRadar({ risk }: Props) {
  const metrics = [
    { label: 'Exposição', value: risk.total_exposure, max: risk.max_exposure },
    { label: 'P&L Diário', value: Math.abs(risk.daily_pnl), max: risk.max_daily_loss },
  ];

  return (
    <div className="card terminal-panel">
      <h2>Risk Radar</h2>
      <div className="risk-radar">
        {metrics.map((m) => {
          const pct = m.max > 0 ? Math.min(100, (m.value / m.max) * 100) : 0;
          const level = pct > 80 ? 'critical' : pct > 50 ? 'warning' : 'safe';
          return (
            <div key={m.label} className="radar-item">
              <div className="radar-label">{m.label}</div>
              <div className="radar-track">
                <div className={`radar-fill ${level}`} style={{ width: `${pct}%` }} />
              </div>
              <div className="radar-value">{m.value.toFixed(2)} / {m.max.toFixed(2)}</div>
            </div>
          );
        })}
        {(risk.trading_halted || risk.circuit_breaker_active) && (
          <div className="radar-alert">⚠ CIRCUIT BREAKER ATIVO</div>
        )}
      </div>
    </div>
  );
}
