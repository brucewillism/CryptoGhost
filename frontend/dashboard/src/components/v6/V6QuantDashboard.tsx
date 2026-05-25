import { useEffect, useRef, useState } from 'react';
import { api } from '../../api';
import { ConsensusV3Panel } from './ConsensusV3Panel';
import { AgentAccuracyChart } from './AgentAccuracyChart';
import { RegimeTimeline } from './RegimeTimeline';
import { PortfolioHeatMap, RiskExposurePanel } from './PortfolioHeatMap';
import { BacktestingDashboard } from './BacktestingDashboard';
import { TradeMemoryExplorer } from './TradeMemoryExplorer';
import { CalibrationChart, DriftMonitor } from './CalibrationChart';

export function V6QuantDashboard() {
  const [consensus, setConsensus] = useState<Record<string, unknown> | null>(null);
  const [regime, setRegime] = useState<Record<string, unknown> | null>(null);
  const [learning, setLearning] = useState<Record<string, unknown> | null>(null);
  const [risk, setRisk] = useState<Record<string, unknown> | null>(null);
  const [agents, setAgents] = useState<Record<string, unknown> | null>(null);
  const [backtests, setBacktests] = useState<Array<Record<string, unknown>>>([]);
  const [freshCount, setFreshCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const [visible, setVisible] = useState(false);
  const sectionRef = useRef<HTMLElement>(null);
  const loaded = useRef(false);

  const load = async () => {
    setLoading(true);
    try {
      const [c, r, l, h, a, b, fresh] = await Promise.all([
        api.getV6Consensus('BTC/USDT').catch(() => null),
        api.getV6Regime('BTC/USDT').catch(() => null),
        api.getV6LearningMetrics().catch(() => null),
        api.getV6RiskHeat().catch(() => null),
        api.getV6AgentPerformance('BTC/USDT').catch(() => null),
        api.getV6BacktestRuns().catch(() => ({ runs: [] })),
        api.getV6FreshSignals().catch(() => ({ count: 0 })),
      ]);
      setConsensus(c);
      setRegime(r);
      setLearning(l);
      setRisk(h);
      setAgents(a);
      setBacktests(b?.runs || []);
      setFreshCount(fresh?.count ?? 0);
      loaded.current = true;
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const el = sectionRef.current;
    if (!el || typeof IntersectionObserver === 'undefined') {
      setVisible(true);
      return;
    }
    const observer = new IntersectionObserver(
      ([entry]) => { if (entry.isIntersecting) setVisible(true); },
      { rootMargin: '200px' },
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    if (!visible || loaded.current) return;
    const t = setTimeout(() => { load(); }, 300);
    return () => clearTimeout(t);
  }, [visible]);

  useEffect(() => {
    if (!visible || !loaded.current) return;
    const interval = setInterval(() => { load(); }, 10_000);
    return () => clearInterval(interval);
  }, [visible]);

  const agentRecords = (agents?.records as Array<{ agent: string; accuracy: number; weight: number; regime?: string }>) || [];

  return (
    <section className="terminal-row" ref={sectionRef}>
      <div className="card terminal-panel v6-panel">
        <div className="v6-header">
          <h2>Quant Platform v6</h2>
          <span className="v6-badge">{freshCount} sinais frescos</span>
          <button className="analyze-btn" onClick={load} disabled={loading || !visible}>
            {loading ? 'Atualizando...' : visible ? 'Atualizar v6' : 'Aguardando scroll...'}
          </button>
        </div>
        {!visible ? (
          <p className="v6-empty">Painel v6 carrega ao rolar até aqui (economiza recursos)</p>
        ) : (
          <>
            <div className="v6-grid">
              <div className="v6-card">
                <h3>Consensus V3</h3>
                <ConsensusV3Panel data={consensus} />
              </div>
              <div className="v6-card">
                <h3>Market Regime</h3>
                <RegimeTimeline regime={regime} />
              </div>
              <div className="v6-card">
                <h3>Learning v6</h3>
                <CalibrationChart learning={learning} />
                <DriftMonitor learning={learning} />
              </div>
              <div className="v6-card">
                <h3>Risk Heat</h3>
                <PortfolioHeatMap risk={risk} />
                <RiskExposurePanel risk={risk} />
              </div>
            </div>
            {agentRecords.length > 0 && (
              <div className="v6-agents">
                <h3>Agent Accuracy</h3>
                <AgentAccuracyChart
                  records={agentRecords}
                  weights={agents?.weights as Record<string, number> | undefined}
                />
              </div>
            )}
            <BacktestingDashboard runs={backtests} onRefresh={load} />
            <TradeMemoryExplorer />
          </>
        )}
      </div>
    </section>
  );
}
