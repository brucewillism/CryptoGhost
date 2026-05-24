import { useEffect, useState, useCallback } from 'react';
import {
  api, DashboardStats, Order, AuditLog,
  HeatmapAsset, ConsensusData, ExplanationData,
  SentimentData, RegimeData, MacroData,
  QuantDashboardData, QuantEvent,
  InvestmentDashboardData,
  V5DashboardData,
} from './api';
import { StatsCards } from './components/StatsCards';
import { OrdersTable } from './components/OrdersTable';
import { AuditLogs } from './components/AuditLogs';
import { RiskPanel } from './components/RiskPanel';
import { LoginForm } from './components/LoginForm';
import { AIConfidenceMeter } from './components/AIConfidenceMeter';
import { MarketHeatmap } from './components/MarketHeatmap';
import { SentimentPanel } from './components/SentimentPanel';
import { RegimeIndicator } from './components/RegimeIndicator';
import { AIExplanationPanel } from './components/AIExplanationPanel';
import { MacroOverview } from './components/MacroOverview';
import { ConsensusPanel } from './components/ConsensusPanel';
import { RiskRadar } from './components/RiskRadar';
import { QuantInstitutionalDashboard } from './components/QuantInstitutionalDashboard';
import { InvestmentOpportunityDashboard } from './components/InvestmentOpportunityDashboard';
import { SelfImprovingDashboard } from './components/SelfImprovingDashboard';
import './App.css';

const PRIMARY_SYMBOL = 'BTC/USDT';

function App() {
  const [authenticated, setAuthenticated] = useState(!!localStorage.getItem('cryptoghost_token'));
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [orders, setOrders] = useState<Order[]>([]);
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [heatmap, setHeatmap] = useState<HeatmapAsset[]>([]);
  const [consensus, setConsensus] = useState<ConsensusData | null>(null);
  const [explanation, setExplanation] = useState<ExplanationData | null>(null);
  const [sentiment, setSentiment] = useState<SentimentData | null>(null);
  const [regime, setRegime] = useState<RegimeData | null>(null);
  const [macro, setMacro] = useState<MacroData | null>(null);
  const [quantData, setQuantData] = useState<QuantDashboardData | null>(null);
  const [quantEvents, setQuantEvents] = useState<QuantEvent[]>([]);
  const [investmentData, setInvestmentData] = useState<InvestmentDashboardData | null>(null);
  const [v5Data, setV5Data] = useState<V5DashboardData | null>(null);
  const [wsStatus, setWsStatus] = useState('desconectado');
  const [error, setError] = useState('');
  const [analyzing, setAnalyzing] = useState(false);

  const loadV5 = useCallback(async () => {
    try {
      const data = await api.getV5Dashboard();
      setV5Data(data);
    } catch {
      /* v5 optional until analysis */
    }
  }, []);

  const loadInvestment = useCallback(async () => {
    try {
      const data = await api.getInvestmentDashboard();
      setInvestmentData(data);
      await loadV5();
    } catch {
      /* investment data optional */
    }
  }, [loadV5]);

  const loadQuant = useCallback(async () => {
    try {
      const [dashboard, events] = await Promise.all([
        api.getQuantDashboard(PRIMARY_SYMBOL),
        api.getQuantEvents(15),
      ]);
      setQuantData(dashboard);
      setQuantEvents(events.events || []);
      await loadInvestment();
    } catch {
      /* quant data optional until first analysis */
    }
  }, [loadInvestment]);

  const loadIntelligence = useCallback(async () => {
    try {
      const [hm, con, exp, sent, reg, mac] = await Promise.all([
        api.getHeatmap(),
        api.getConsensus(PRIMARY_SYMBOL),
        api.getExplanation(PRIMARY_SYMBOL),
        api.getSentiment(),
        api.getRegime(PRIMARY_SYMBOL),
        api.getMacro(),
      ]);
      setHeatmap(hm.assets || []);
      if (con.final_decision) setConsensus(con);
      if (exp.reasons) setExplanation(exp);
      setSentiment(sent);
      if (reg.regime) setRegime(reg);
      setMacro(mac);
      await loadQuant();
    } catch {
      /* intelligence data may not exist yet */
    }
  }, [loadQuant]);

  const loadData = useCallback(async () => {
    try {
      const [s, o, l] = await Promise.all([api.getStats(), api.getOrders(), api.getAuditLogs()]);
      setStats(s);
      setOrders(o);
      setLogs(l);
      await loadIntelligence();
      setError('');
    } catch {
      setError('Erro ao carregar dados. Verifique se o backend está rodando.');
    }
  }, [loadIntelligence]);

  const runAnalysis = async () => {
    setAnalyzing(true);
    try {
      await api.analyzeSymbol(PRIMARY_SYMBOL);
      await loadIntelligence();
    } catch {
      setError('Falha ao executar análise IA');
    } finally {
      setAnalyzing(false);
    }
  };

  useEffect(() => {
    if (!authenticated) return;
    loadData();
    const interval = setInterval(loadData, 15000);

    const ws = api.connectWebSocket((data) => {
      setWsStatus('conectado');
      if (typeof data === 'object' && data !== null && 'type' in data) {
        const msg = data as { type: string };
        if (['system_status', 'intelligence_update', 'consensus_update', 'sentiment_update'].includes(msg.type)) {
          loadData();
        }
      }
    });

    ws.onclose = () => setWsStatus('desconectado');
    return () => { clearInterval(interval); ws.close(); };
  }, [authenticated, loadData]);

  if (!authenticated) {
    return <LoginForm onLogin={() => setAuthenticated(true)} />;
  }

  return (
    <div className="app terminal-layout">
      <header className="header terminal-header">
        <div className="header-brand">
          <span className="logo">👻</span>
          <div>
            <h1>CryptoGhost</h1>
            <p className="subtitle">Self-Improving Quant AI v5 · Priorização · Auto-Evolução · Survival</p>
          </div>
        </div>
        <div className="header-actions">
          <button className="analyze-btn" onClick={runAnalysis} disabled={analyzing}>
            {analyzing ? 'Analisando...' : '⚡ Analisar BTC/USDT'}
          </button>
          <span className={`badge ${stats?.risk_status.paper_trading ? 'paper' : 'live'}`}>
            {stats?.risk_status.paper_trading ? 'PAPER' : 'LIVE'}
          </span>
          <span className={`badge ws ${wsStatus === 'conectado' ? 'online' : ''}`}>WS: {wsStatus}</span>
        </div>
      </header>

      {error && <div className="error-banner">{error}</div>}

      <main className="main terminal-main">
        <section className="terminal-row top-row">
          {stats && <StatsCards stats={stats} />}
          <AIConfidenceMeter consensus={consensus} />
        </section>

        <section className="terminal-row intelligence-row">
          <MarketHeatmap assets={heatmap} />
          <SentimentPanel sentiment={sentiment} />
          <RegimeIndicator regime={regime} />
        </section>

        <section className="terminal-row analysis-row">
          <ConsensusPanel consensus={consensus} />
          <AIExplanationPanel explanation={explanation} />
          {stats && <RiskRadar risk={stats.risk_status} />}
        </section>

        <section className="terminal-row macro-row">
          <MacroOverview macro={macro} />
          {stats && <RiskPanel risk={stats.risk_status} />}
        </section>

        <QuantInstitutionalDashboard data={quantData} events={quantEvents} />

        <InvestmentOpportunityDashboard data={investmentData} />

        <SelfImprovingDashboard data={v5Data} />

        <section className="terminal-row bottom-row">
          <OrdersTable orders={orders} />
          <AuditLogs logs={logs} />
        </section>
      </main>

      <footer className="footer">
        CryptoGhost v5.0 · Self-Improving Quant Platform · Capital Preservation First
      </footer>
    </div>
  );
}

export default App;
