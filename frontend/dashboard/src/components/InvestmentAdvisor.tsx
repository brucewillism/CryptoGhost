import { useState } from 'react';
import { api, InvestmentRecommendation } from '../api';

interface Props {
  onInvested: () => void;
}

export function InvestmentAdvisor({ onInvested }: Props) {
  const [loading, setLoading] = useState(false);
  const [investing, setInvesting] = useState(false);
  const [rec, setRec] = useState<InvestmentRecommendation | null>(null);
  const [showModal, setShowModal] = useState(false);
  const [error, setError] = useState('');

  const loadRecommendation = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await api.getInvestmentRecommendation();
      setRec(data);
      if (data.status === 'ready' && data.proposed_order?.can_execute) {
        setShowModal(true);
      } else if (data.status === 'no_data') {
        setError(data.message || 'Execute uma análise IA primeiro.');
      }
    } catch {
      setError('Falha ao obter recomendação da IA.');
    } finally {
      setLoading(false);
    }
  };

  const approveInvestment = async () => {
    if (!rec?.proposed_order?.can_execute) return;
    setInvesting(true);
    setError('');
    try {
      const o = rec.proposed_order;
      await api.approveInvestment({
        user_confirmed: true,
        symbol: o.symbol,
        side: o.side,
        quantity: o.quantity,
        stop_loss: o.stop_loss,
        take_profit: o.take_profit,
      });
      setShowModal(false);
      onInvested();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Ordem rejeitada ou falhou.');
    } finally {
      setInvesting(false);
    }
  };

  const order = rec?.proposed_order;

  return (
    <section className="terminal-row investment-advisor-row">
      <div className="card terminal-panel investment-advisor-panel">
        <div className="advisor-header">
          <h2>💰 Onde Investir — IA CryptoGhost</h2>
          <button className="analyze-btn advisor-btn" onClick={loadRecommendation} disabled={loading}>
            {loading ? 'Analisando oportunidades...' : '🎯 Onde investir agora?'}
          </button>
        </div>

        {error && <p className="advisor-error">{error}</p>}

        {rec?.status === 'ready' && !showModal && (
          <div className="advisor-summary">
            <p className="advisor-text">{rec.ai_summary?.replace(/\*\*/g, '')}</p>
            <div className="advisor-metrics">
              <span><strong>{rec.best_symbol}</strong></span>
              <span>Retorno esp.: <strong>+{rec.expected_return_pct?.toFixed(1)}%</strong></span>
              <span>Lucro esp.: <strong>${rec.expected_profit_usdt?.toFixed(2)}</strong></span>
            </div>
            {order?.can_execute ? (
              <button className="approve-btn" onClick={() => setShowModal(true)}>
                Revisar e aprovar investimento (Paper)
              </button>
            ) : (
              <p className="advisor-hold">IA recomenda aguardar — sem ordem de compra no momento.</p>
            )}
          </div>
        )}

        {rec?.status === 'no_data' && (
          <p className="empty">Execute &quot;Analisar BTC/USDT&quot; antes para a IA rankear oportunidades.</p>
        )}
      </div>

      {showModal && rec && order && (
        <div className="approval-overlay" role="dialog" aria-modal="true">
          <div className="approval-modal">
            <h3>Confirmar investimento</h3>
            <p className="approval-disclaimer">{rec.disclaimer}</p>
            <dl className="approval-details">
              <dt>Ativo</dt><dd>{order.symbol}</dd>
              <dt>Operação</dt><dd>{order.side.toUpperCase()}</dd>
              <dt>Quantidade</dt><dd>{order.quantity}</dd>
              <dt>Preço mercado</dt><dd>${Number(order.price).toLocaleString()}</dd>
              <dt>Valor investido</dt><dd>${order.investment_usdt.toLocaleString()} USDT ({order.allocation_pct}%)</dd>
              <dt>Stop Loss</dt><dd>${Number(order.stop_loss).toLocaleString()}</dd>
              <dt>Take Profit</dt><dd>${Number(order.take_profit).toLocaleString()}</dd>
              <dt>Lucro esperado</dt><dd className="positive">+${rec.expected_profit_usdt?.toFixed(2)} ({rec.expected_return_pct?.toFixed(1)}%)</dd>
            </dl>
            <ul className="approval-reasons">
              {(rec.reasons || []).slice(0, 4).map((r, i) => <li key={i}>{r}</li>)}
            </ul>
            <div className="approval-actions">
              <button className="cancel-btn" onClick={() => setShowModal(false)} disabled={investing}>
                Cancelar
              </button>
              <button className="approve-btn" onClick={approveInvestment} disabled={investing}>
                {investing ? 'Executando...' : '✓ Aprovar e investir (Paper)'}
              </button>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
