import { useCallback, useEffect, useState } from 'react';
import { api, PaperTrialStatus } from '../api';

interface Props {
  refreshKey?: number;
}

export function PaperTrialPanel({ refreshKey = 0 }: Props) {
  const [trial, setTrial] = useState<PaperTrialStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [learning, setLearning] = useState(false);

  const load = useCallback(async () => {
    try {
      const data = await api.getTrialStatus();
      setTrial(data);
    } catch {
      setTrial(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load, refreshKey]);

  const startTrial = async () => {
    setLoading(true);
    try {
      const data = await api.startPaperTrial();
      setTrial(data);
    } finally {
      setLoading(false);
    }
  };

  const runLearning = async () => {
    setLearning(true);
    try {
      const data = await api.runTrialLearning();
      setTrial(data.trial);
    } finally {
      setLearning(false);
    }
  };

  if (loading && !trial) {
    return (
      <section className="terminal-row">
        <div className="card terminal-panel paper-trial-panel">
          <p className="empty">Carregando período de teste...</p>
        </div>
      </section>
    );
  }

  if (trial?.status === 'not_started') {
    return (
      <section className="terminal-row">
        <div className="card terminal-panel paper-trial-panel">
          <h2>📅 Teste de 30 dias — Sem dinheiro real</h2>
          <p className="trial-intro">
            Use o modo <strong>PAPER</strong> por 30 dias. A IA analisa o mercado real, você aprova cada investimento,
            e o sistema aprende com acertos e erros antes de arriscar capital de verdade.
          </p>
          <ul className="trial-steps">
            <li>Análises e preços = mercado real (Binance)</li>
            <li>Ordens = simuladas (${trial.initial_capital_usdt?.toLocaleString()} USDT virtuais)</li>
            <li>IA valida previsões e ajusta pesos automaticamente</li>
          </ul>
          <button className="approve-btn" onClick={startTrial}>
            Iniciar meu teste de 30 dias
          </button>
        </div>
      </section>
    );
  }

  if (!trial || trial.status === 'not_started') return null;

  const p = trial.portfolio;
  const l = trial.learning;
  const r = trial.readiness;
  const progress = trial.days_total ? Math.min(100, (trial.days_elapsed / trial.days_total) * 100) : 0;

  return (
    <section className="terminal-row">
      <div className="card terminal-panel paper-trial-panel">
        <div className="trial-header">
          <h2>📅 Teste Paper — Dia {trial.days_elapsed} de {trial.days_total}</h2>
          <span className={`trial-badge ${trial.status}`}>
            {trial.days_remaining} dias restantes
          </span>
        </div>

        <div className="trial-progress">
          <div className="trial-progress-bar" style={{ width: `${progress}%` }} />
        </div>

        <div className="trial-grid">
          <div className="trial-stat">
            <span className="label">Portfólio paper</span>
            <span className="value">${p?.current_value_usdt.toLocaleString(undefined, { maximumFractionDigits: 2 })}</span>
            <span className={`sub ${(p?.return_pct ?? 0) >= 0 ? 'positive' : 'negative'}`}>
              {(p?.return_pct ?? 0) >= 0 ? '+' : ''}{p?.return_pct?.toFixed(2)}% ({p?.total_pnl_usdt?.toFixed(2)} USDT)
            </span>
          </div>
          <div className="trial-stat">
            <span className="label">Precisão IA</span>
            <span className="value">{((l?.direction_accuracy ?? 0) * 100).toFixed(0)}%</span>
            <span className="sub">{l?.validations_total ?? 0} validações</span>
          </div>
          <div className="trial-stat">
            <span className="label">Prontidão live</span>
            <span className="value">{r?.score ?? 0}/100</span>
            <span className={`sub ${r?.ready_for_live ? 'positive' : ''}`}>
              {r?.ready_for_live ? 'Pronto para considerar live' : 'Ainda aprendendo'}
            </span>
          </div>
          <div className="trial-stat">
            <span className="label">Operações</span>
            <span className="value">{p?.total_orders ?? 0}</span>
            <span className="sub">{p?.open_positions ?? 0} posições abertas</span>
          </div>
        </div>

        <p className="trial-rec">{r?.recommendation}</p>
        {r?.notes && r.notes.length > 0 && (
          <ul className="trial-notes">
            {r.notes.map((n, i) => <li key={i}>{n}</li>)}
          </ul>
        )}

        <div className="trial-actions">
          <button className="analyze-btn" onClick={runLearning} disabled={learning}>
            {learning ? 'IA aprendendo...' : '🧠 Rodar ciclo de aprendizado'}
          </button>
          <span className="trial-hint">Rode 1x por dia (ou após cada operação) para a IA calibrar</span>
        </div>
      </div>
    </section>
  );
}
