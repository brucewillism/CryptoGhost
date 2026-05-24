import { V5DashboardData } from '../api';

interface Props {
  data: V5DashboardData | null;
}

function Panel({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="card terminal-panel quant-panel v5-panel">
      <h2>{title}</h2>
      {children}
    </div>
  );
}

export function SelfImprovingDashboard({ data }: Props) {
  if (!data) {
    return (
      <section className="terminal-row v5-row">
        <Panel title="Self-Improving AI v5">
          <p className="empty">Execute análise completa para ativar auto-evolução v5.</p>
        </Panel>
      </section>
    );
  }

  return (
    <>
      <section className="terminal-row v5-row v5-top">
        <Panel title="AI Truth Meter">
          {(data.ai_truth || []).slice(0, 4).map((t, i) => (
            <div key={i} className={`truth-row ${t.overconfidence ? 'warn' : ''}`}>
              <span>{t.symbol.split('/')[0]}</span>
              <div className="truth-bar"><div style={{ width: `${t.truth_score * 100}%` }} /></div>
              <span>{(t.truth_score * 100).toFixed(0)}%</span>
              {t.overconfidence && <span className="oc-tag">OVERCONF</span>}
            </div>
          ))}
        </Panel>

        <Panel title="Survival Risk Indicator">
          <div className="survival-display">
            <div className="survival-score">
              {data.real_performance ? `${(100 - (data.real_performance.max_drawdown || 0)).toFixed(0)}` : '—'}
            </div>
            <div className="survival-label">Capital Preservation Index</div>
            {data.drift?.some((d) => d.retrain) && (
              <div className="survival-alert">⚠ Retrain recomendado — drift detectado</div>
            )}
          </div>
        </Panel>

        <Panel title="Model Performance Ranking">
          {(data.model_ranking || []).map((m, i) => (
            <div key={i} className="model-rank-row">
              <span>#{i + 1} {m.model}</span>
              <span>{(m.accuracy * 100).toFixed(0)}%</span>
              <span className="regime-tag">{m.regime}</span>
            </div>
          ))}
        </Panel>
      </section>

      <section className="terminal-row v5-row">
        <Panel title="Drift Detection">
          {(data.drift || []).map((d, i) => (
            <div key={i} className={`drift-v5-row ${d.retrain ? 'critical' : ''}`}>
              <span>{d.model}</span>
              <span className="drift-type">{d.type}</span>
              <div className="drift-bar"><div style={{ width: `${Math.min(d.score * 100, 100)}%` }} /></div>
              {d.retrain && <span className="retrain-tag">RETRAIN</span>}
            </div>
          ))}
        </Panel>

        <Panel title="Prediction Accuracy Tracker">
          <div className="pred-accuracy-header">
            Score médio: <strong>{data.prediction_accuracy?.avg_validation_score?.toFixed(1) || '—'}</strong>
          </div>
          {(data.prediction_accuracy?.recent || []).map((p, i) => (
            <div key={i} className={`pred-row ${p.correct ? 'ok' : 'fail'}`}>
              <span>{p.symbol.split('/')[0]}</span>
              <span>pred {p.predicted?.toFixed(1)}%</span>
              <span>real {p.actual?.toFixed(1) ?? '—'}%</span>
              <span>{p.correct ? '✓' : '✗'}</span>
            </div>
          ))}
        </Panel>

        <Panel title="Real vs Expected Return">
          {data.real_performance ? (
            <div className="real-vs-exp">
              <div><span>Sharpe</span><strong>{data.real_performance.sharpe?.toFixed(2)}</strong></div>
              <div><span>Sortino</span><strong>{data.real_performance.sortino?.toFixed(2)}</strong></div>
              <div><span>Max DD</span><strong className="neg">{data.real_performance.max_drawdown?.toFixed(1)}%</strong></div>
              <div><span>Hit Rate</span><strong>{((data.real_performance.hit_rate || 0) * 100).toFixed(0)}%</strong></div>
              <div><span>Exp vs Real</span><strong>{data.real_performance.expected_vs_actual?.toFixed(1)}%</strong></div>
            </div>
          ) : (
            <p className="empty">Aguardando métricas de performance</p>
          )}
        </Panel>

        <Panel title="Self-Improvement Metrics">
          <div className="improvement-list">
            {(data.self_improvement || []).slice(0, 8).map((imp, i) => (
              <div key={i} className="imp-row">
                <span className="imp-action">{imp.action}</span>
                <span>{imp.target}</span>
                <span className={imp.improvement_pct && imp.improvement_pct > 0 ? 'pos' : 'neg'}>
                  {imp.improvement_pct?.toFixed(1) ?? '—'}%
                </span>
              </div>
            ))}
          </div>
        </Panel>
      </section>
    </>
  );
}
