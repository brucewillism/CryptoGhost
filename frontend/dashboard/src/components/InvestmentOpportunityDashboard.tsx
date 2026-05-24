import { InvestmentDashboardData } from '../api';

interface Props {
  data: InvestmentDashboardData | null;
}

function Panel({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="card terminal-panel quant-panel investment-panel">
      <h2>{title}</h2>
      {children}
    </div>
  );
}

export function InvestmentOpportunityDashboard({ data }: Props) {
  if (!data) {
    return (
      <section className="terminal-row investment-v4-row">
        <Panel title="Investment Intelligence v4">
          <p className="empty">Execute ranking de investimentos para ver oportunidades.</p>
        </Panel>
      </section>
    );
  }

  const best = data.best_opportunity;
  const allocation = data.allocation;

  return (
    <>
      <section className="terminal-row investment-v4-row investment-hero">
        <Panel title="★ Best Opportunity NOW">
          {best ? (
            <div className="best-opportunity">
              <div className="best-symbol">{best.symbol}</div>
              <div className="best-score">{best.priority_score.toFixed(0)}</div>
              <div className={`best-rec ${best.recommendation.toLowerCase()}`}>{best.recommendation}</div>
              <div className="best-metrics">
                <span>Retorno esp.: <strong>{best.expected_return.toFixed(1)}%</strong></span>
                <span>Confiança: <strong>{(best.confidence * 100).toFixed(0)}%</strong></span>
              </div>
              <ul className="best-reasons">
                {(best.reasons || []).slice(0, 4).map((r, i) => <li key={i}>{r}</li>)}
              </ul>
            </div>
          ) : (
            <p className="empty">Nenhuma oportunidade de alta prioridade</p>
          )}
        </Panel>

        <Panel title="Profit Probability Meter">
          {best ? (
            <div className="profit-meter">
              <div className="profit-ring" style={{ '--pct': `${best.confidence * 100}%` } as React.CSSProperties}>
                <span>{(best.confidence * 100).toFixed(0)}%</span>
              </div>
              <div className="profit-label">Confiança calibrada</div>
            </div>
          ) : null}
          <div className="prob-list">
            {(data.probabilities || []).slice(0, 4).map((p, i) => (
              <div key={i} className="prob-row">
                <span>{p.symbol.split('/')[0]}</span>
                <div className="prob-bar">
                  <div className="prob-bull" style={{ width: `${p.bullish * 100}%` }} />
                </div>
                <span>{(p.bullish * 100).toFixed(0)}%</span>
              </div>
            ))}
          </div>
        </Panel>

        <Panel title="Smart Capital Allocation">
          {allocation ? (
            <div className="allocation-chart">
              {Object.entries(allocation.allocations).map(([asset, pct]) => (
                <div key={asset} className="alloc-row">
                  <span>{asset}</span>
                  <div className="alloc-bar"><div style={{ width: `${pct}%` }} /></div>
                  <span>{pct}%</span>
                </div>
              ))}
              <div className="alloc-meta">Exposição: {allocation.exposure_pct}% · Caixa: {allocation.cash_pct}%</div>
            </div>
          ) : (
            <p className="empty">Alocação pendente</p>
          )}
        </Panel>
      </section>

      <section className="terminal-row investment-v4-row">
        <Panel title="AI Investment Ranking">
          <div className="ranking-table">
            {(data.ranking || []).map((r) => (
              <div key={r.symbol} className="rank-row">
                <span className="rank-pos">#{r.rank}</span>
                <span className="rank-sym">{r.symbol}</span>
                <span className="rank-score">{r.score.toFixed(0)}</span>
                <span className={`rank-rec ${r.recommendation.includes('BUY') ? 'buy' : 'hold'}`}>{r.recommendation}</span>
                <span className="rank-ret">+{r.expected_return.toFixed(1)}%</span>
              </div>
            ))}
          </div>
        </Panel>

        <Panel title="Risk vs Reward Matrix">
          <div className="rr-matrix">
            {(data.ranking || []).slice(0, 6).map((r) => (
              <div key={r.symbol} className="rr-cell">
                <span>{r.symbol.split('/')[0]}</span>
                <div className="rr-bars">
                  <div className="rr-reward" style={{ width: `${Math.min(100, r.expected_return * 3)}%` }} title="Retorno" />
                  <div className="rr-risk" style={{ width: `${r.risk}%` }} title="Risco" />
                </div>
              </div>
            ))}
          </div>
        </Panel>

        <Panel title="Institutional Flow Tracker">
          <div className="flow-list">
            {(data.institutional_signals || []).slice(0, 8).map((s, i) => (
              <div key={i} className={`flow-row ${s.direction}`}>
                <span>{s.symbol.split('/')[0]}</span>
                <span className="flow-type">{s.type.replace(/_/g, ' ')}</span>
                <span>{(s.strength * 100).toFixed(0)}%</span>
              </div>
            ))}
            {(data.institutional_signals || []).length === 0 && (
              <p className="empty">Aguardando sinais institucionais</p>
            )}
          </div>
        </Panel>

        <Panel title="Expected Return Heatmap">
          <div className="return-heatmap">
            {(data.ranking || []).map((r) => (
              <div
                key={r.symbol}
                className="return-cell"
                style={{ opacity: 0.4 + (r.expected_return / 30) }}
              >
                <span>{r.symbol.split('/')[0]}</span>
                <strong>{r.expected_return > 0 ? '+' : ''}{r.expected_return.toFixed(1)}%</strong>
              </div>
            ))}
          </div>
        </Panel>
      </section>
    </>
  );
}
