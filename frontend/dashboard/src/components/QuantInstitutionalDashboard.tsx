import { QuantDashboardData } from '../api';

interface Props {
  data: QuantDashboardData | null;
  events: Array<{ type: string; event_id?: string; payload?: Record<string, unknown> }>;
}

function Panel({ title, children, className = '' }: { title: string; children: React.ReactNode; className?: string }) {
  return (
    <div className={`card terminal-panel quant-panel ${className}`}>
      <h2>{title}</h2>
      {children}
    </div>
  );
}

export function QuantInstitutionalDashboard({ data, events }: Props) {
  if (!data) {
    return (
      <section className="terminal-row quant-v3-row">
        <Panel title="Quant v3 · Institucional">
          <p className="empty">Execute uma análise para carregar dados quantitativos v3.</p>
        </Panel>
      </section>
    );
  }

  const calHistory = data.calibration?.history || [];
  const ensemble = data.ensemble;
  const weights = ensemble?.stacking_weights || {};
  const agents = Object.keys(weights);
  const maxWeight = Math.max(...Object.values(weights), 0.01);

  return (
    <>
      <section className="terminal-row quant-v3-row quant-top">
        <Panel title="AI Neural Activity">
          <div className="neural-grid">
            {(data.neural_activity || []).map((n) => (
              <div key={n.agent} className={`neural-cell ${n.status}`}>
                <span className="neural-agent">{n.agent}</span>
                <div className="neural-bar">
                  <div className="neural-fill" style={{ width: `${n.activity}%` }} />
                </div>
                <span className="neural-pct">{n.activity}%</span>
              </div>
            ))}
          </div>
        </Panel>

        <Panel title="Agent Consensus Matrix">
          {ensemble ? (
            <>
              <div className="matrix-decision">
                <span className={`decision-badge ${ensemble.final_decision.toLowerCase()}`}>
                  {ensemble.final_decision}
                </span>
                <span className="matrix-conf">{(ensemble.meta_confidence * 100).toFixed(1)}%</span>
              </div>
              <div className="consensus-matrix">
                {agents.map((agent) => (
                  <div key={agent} className="matrix-row">
                    <span>{agent}</span>
                    <div className="matrix-bar">
                      <div
                        className="matrix-fill"
                        style={{ width: `${(weights[agent] / maxWeight) * 100}%` }}
                      />
                    </div>
                    <span>{(weights[agent] * 100).toFixed(0)}%</span>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <p className="empty">Sem dados de ensemble</p>
          )}
        </Panel>

        <Panel title="GPU Monitor">
          <div className="gpu-stats">
            <div className="gpu-device">{data.gpu.device_name}</div>
            <div className="gpu-meta">{data.gpu.device}</div>
            <div className="gpu-vram">
              VRAM: {data.gpu.vram_used_mb.toFixed(0)} / {data.gpu.vram_total_mb.toFixed(0)} MB
            </div>
            <div className="gpu-bar">
              <div
                className="gpu-fill"
                style={{
                  width: `${data.gpu.vram_total_mb ? (data.gpu.vram_used_mb / data.gpu.vram_total_mb) * 100 : 0}%`,
                }}
              />
            </div>
            <span className={`gpu-status ${data.gpu.available ? 'online' : 'cpu'}`}>
              {data.gpu.available ? 'CUDA ATIVO' : 'CPU FALLBACK'}
            </span>
          </div>
        </Panel>
      </section>

      <section className="terminal-row quant-v3-row">
        <Panel title="Confidence Calibration">
          {data.calibration?.latest ? (
            <>
              <div className="calibration-compare">
                <div>
                  <span className="cal-label">Raw</span>
                  <span>{(data.calibration.latest.raw_confidence * 100).toFixed(1)}%</span>
                </div>
                <div>
                  <span className="cal-label">Calibrado</span>
                  <span className="cal-value">
                    {(data.calibration.latest.calibrated_confidence * 100).toFixed(1)}%
                  </span>
                </div>
                <div>
                  <span className="cal-label">Incerteza</span>
                  <span>{(data.calibration.latest.uncertainty * 100).toFixed(1)}%</span>
                </div>
              </div>
              <div className="calibration-chart">
                {calHistory.slice(0, 8).map((h, i) => (
                  <div key={i} className="cal-bar-group">
                    <div className="cal-bar raw" style={{ height: `${h.raw * 80}px` }} title={`Raw ${h.raw}`} />
                    <div className="cal-bar calibrated" style={{ height: `${h.calibrated * 80}px` }} />
                  </div>
                ))}
              </div>
            </>
          ) : (
            <p className="empty">Sem histórico de calibração</p>
          )}
        </Panel>

        <Panel title="Historical Similarity">
          {(data.similarity?.scenarios || []).length > 0 ? (
            <ul className="similarity-list">
              {data.similarity.scenarios.map((s, i) => (
                <li key={i}>
                  <strong>{s.label}</strong>
                  <span>{s.outcome || 'pendente'}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="empty">Cenários históricos serão indexados após análises</p>
          )}
        </Panel>

        <Panel title="Reinforcement Learning">
          {(data.rl?.policies || []).length > 0 ? (
            <div className="rl-list">
              {data.rl.policies.map((p, i) => (
                <div key={i} className="rl-item">
                  <span className="rl-algo">{p.algorithm}</span>
                  <span>Reward: {p.avg_reward.toFixed(2)}</span>
                  <span>{p.episodes} eps</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="empty">Nenhuma política RL treinada ainda</p>
          )}
        </Panel>
      </section>

      <section className="terminal-row quant-v3-row">
        <Panel title="Event Stream">
          <div className="event-stream">
            {events.length > 0 ? (
              events.slice(0, 12).map((e, i) => (
                <div key={i} className="event-row">
                  <span className="event-type">{e.type.replace('_event', '')}</span>
                  <span className="event-id">{e.event_id?.slice(0, 8) || '—'}</span>
                </div>
              ))
            ) : (
              <p className="empty">Aguardando eventos Redis Streams</p>
            )}
          </div>
        </Panel>

        <Panel title="Feature Store">
          <div className="feature-metrics">
            <div>TTL cache: {data.feature_store.cache_ttl}s</div>
            <div>Sentiment: {data.feature_store.sentiment_available ? '✓ online' : '— offline'}</div>
            <div className="feature-keys">
              {(data.feature_store.technical_keys || []).slice(0, 8).map((k) => (
                <span key={k} className="feature-tag">{k}</span>
              ))}
            </div>
          </div>
        </Panel>

        <Panel title="Drift Detection">
          <div className="drift-list">
            {(data.drift?.reports || []).map((d, i) => (
              <div key={i} className={`drift-item ${d.retrain ? 'critical' : ''}`}>
                <span>{d.agent}</span>
                <div className="drift-bar">
                  <div className="drift-fill" style={{ width: `${Math.min(d.drift_score * 100, 100)}%` }} />
                </div>
                <span>{(d.drift_score * 100).toFixed(0)}%</span>
                {d.retrain && <span className="retrain-tag">RETRAIN</span>}
              </div>
            ))}
          </div>
        </Panel>

        <Panel title="Temporal Memory Timeline">
          <div className="memory-timeline">
            {(data.temporal_memory?.entries || []).slice(0, 10).map((m, i) => (
              <div key={i} className="memory-entry">
                <span className="memory-time">{m.created_at?.slice(11, 19) || '—'}</span>
                <span className="memory-agent">{m.agent}</span>
                <span className="memory-decision">{m.decision || m.type}</span>
              </div>
            ))}
            {(data.temporal_memory?.entries || []).length === 0 && (
              <p className="empty">Memória temporal vazia</p>
            )}
          </div>
        </Panel>
      </section>
    </>
  );
}
