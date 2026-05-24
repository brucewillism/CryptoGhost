import { DashboardStats } from '../api';

interface Props {
  risk: DashboardStats['risk_status'];
}

export function RiskPanel({ risk }: Props) {
  const halted = risk.trading_halted || risk.circuit_breaker_active;

  return (
    <div className="card">
      <h2>Gestão de Risco</h2>
      <div className="risk-grid">
        <div>
          <div className="risk-item">
            <span>Exposição Total</span>
            <span>{risk.total_exposure.toFixed(2)} / {risk.max_exposure.toFixed(2)}</span>
          </div>
          <div className="risk-item">
            <span>Perda Diária Máx.</span>
            <span>{risk.max_daily_loss.toFixed(2)}</span>
          </div>
        </div>
        <div>
          <div className="risk-item">
            <span>Paper Trading</span>
            <span>{risk.paper_trading ? 'Ativo' : 'Inativo'}</span>
          </div>
          <div className="risk-item">
            <span>Live Trading</span>
            <span>{risk.live_trading_enabled ? 'Habilitado' : 'Desabilitado'}</span>
          </div>
        </div>
      </div>
      {halted && (
        <div className="risk-alert">
          ⚠️ Trading interrompido — Circuit breaker ou limite de perda atingido
        </div>
      )}
    </div>
  );
}
