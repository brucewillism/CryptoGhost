import { useCallback, useEffect, useState } from 'react';
import { api, AIMemoryDashboardData } from '../api';

interface Props {
  refreshKey?: number;
}

function pct(value: number | null | undefined): string {
  if (value == null) return '—';
  return `${(value * 100).toFixed(1)}%`;
}

export function AIMemoryPanel({ refreshKey = 0 }: Props) {
  const [data, setData] = useState<AIMemoryDashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    try {
      const panel = await api.getAIMemoryDashboard();
      setData(panel);
      setError('');
    } catch {
      setError('Não foi possível carregar a memória da IA.');
      setData(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
    const interval = setInterval(() => { load().catch(() => {}); }, 15_000);
    return () => clearInterval(interval);
  }, [load, refreshKey]);

  if (loading && !data) {
    return (
      <section className="terminal-row">
        <div className="card terminal-panel ai-memory-panel">
          <p className="empty">Carregando memória da IA...</p>
        </div>
      </section>
    );
  }

  if (error && !data) {
    return (
      <section className="terminal-row">
        <div className="card terminal-panel ai-memory-panel">
          <p className="empty">{error}</p>
        </div>
      </section>
    );
  }

  if (!data) return null;

  const { summary, last_lesson, recent_trades, recent_validations, learning_in_decisions } = data;

  return (
    <section className="terminal-row">
      <div className="card terminal-panel ai-memory-panel">
        <div className="ai-memory-header">
          <div>
            <h2>🧠 Memória da IA</h2>
            <p className="ai-memory-sub">
              Dados persistidos no PostgreSQL · atualiza a cada 15s e após cada ciclo autônomo
            </p>
          </div>
          <button className="analyze-btn small" onClick={load} disabled={loading}>
            {loading ? '...' : 'Atualizar'}
          </button>
        </div>

        <div className="ai-memory-stats">
          <div className="ai-stat">
            <span className="ai-stat-label">Trades memorizados</span>
            <strong>{summary.trades_memorized}</strong>
            <small>{summary.trades_open} abertos · {summary.trades_closed} fechados</small>
          </div>
          <div className="ai-stat">
            <span className="ai-stat-label">Validações</span>
            <strong>{summary.validations_total}</strong>
            <small>hit rate {pct(summary.validation_hit_rate)}</small>
          </div>
          <div className="ai-stat">
            <span className="ai-stat-label">Memória avaliada</span>
            <strong>{summary.memory_evaluated}</strong>
            <small>{summary.memory_pending} aguardando · hit {pct(summary.memory_hit_rate)}</small>
          </div>
          <div className="ai-stat highlight">
            <span className="ai-stat-label">Hit rate geral</span>
            <strong>{pct(summary.overall_hit_rate)}</strong>
            <small>{summary.agents_tracked} agentes calibrados</small>
          </div>
        </div>

        {last_lesson && (
          <div className="ai-last-lesson">
            <h3>Última lição aprendida</h3>
            <p className="lesson-text">{last_lesson.lesson}</p>
            <p className="lesson-meta">
              {last_lesson.symbol} · {last_lesson.decision} ·{' '}
              {last_lesson.was_correct ? '✓ acerto' : '✗ erro'} ·{' '}
              {last_lesson.performance_pct != null
                ? `${last_lesson.performance_pct >= 0 ? '+' : ''}${last_lesson.performance_pct.toFixed(2)}%`
                : '—'}
            </p>
          </div>
        )}

        <div className="ai-memory-grid">
          <div>
            <h4>Trades recentes</h4>
            {recent_trades.length === 0 && <p className="empty-inline">Nenhum trade memorizado ainda.</p>}
            {recent_trades.map((t, i) => (
              <div key={i} className="ai-memory-row">
                <span>{t.asset}</span>
                <span>{t.setup}</span>
                <span className={t.result === 'profit' ? 'pos' : t.result === 'loss' ? 'neg' : ''}>
                  {t.result}
                </span>
                <span>{t.pnl != null ? `${t.pnl >= 0 ? '+' : ''}${t.pnl.toFixed(2)}` : '—'}</span>
              </div>
            ))}
          </div>
          <div>
            <h4>Validações recentes</h4>
            {recent_validations.length === 0 && (
              <p className="empty-inline">Validações aparecem após ~24h das previsões.</p>
            )}
            {recent_validations.map((v, i) => (
              <div key={i} className="ai-memory-row">
                <span>{v.symbol}</span>
                <span>{v.direction_correct ? '✓' : '✗'}</span>
                <span>
                  {v.actual_return_pct != null
                    ? `${v.actual_return_pct >= 0 ? '+' : ''}${v.actual_return_pct.toFixed(2)}%`
                    : '—'}
                </span>
                <span>score {v.validation_score.toFixed(0)}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="ai-learning-applied">
          <h4>O que entra na decisão de investir</h4>
          <ul>
            <li className={learning_in_decisions.agent_performance_weights ? 'on' : 'off'}>
              Pesos dinâmicos dos agentes (consenso v3)
            </li>
            <li className={learning_in_decisions.prediction_validations ? 'on' : 'off'}>
              Histórico de validações de previsão
            </li>
            <li className={learning_in_decisions.calibrated_confidence ? 'on' : 'off'}>
              Confiança calibrada (quant v3)
            </li>
            <li className={learning_in_decisions.regime_policy ? 'on' : 'off'}>
              Política por regime de mercado
            </li>
            <li className={learning_in_decisions.risk_engine_v2 ? 'on' : 'off'}>
              Limites do Risk Engine v2
            </li>
            <li className={learning_in_decisions.trade_memory_recall ? 'on' : 'off'}>
              Recall de trades similares (bloqueio)
            </li>
          </ul>
          <p className="learning-note">{learning_in_decisions.note}</p>
        </div>
      </div>
    </section>
  );
}
