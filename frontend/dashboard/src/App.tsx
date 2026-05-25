import { useEffect, useState, useCallback, useRef } from 'react';
import {
  api, AuthError, DashboardStats, Order, AuditLog,
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
import { AutonomousInvestor } from './components/AutonomousInvestor';
import { PaperEarningsBanner } from './components/PaperEarningsBanner';
import { PaperTrialPanel } from './components/PaperTrialPanel';
import { AIMemoryPanel } from './components/AIMemoryPanel';
import { SelfImprovingDashboard } from './components/SelfImprovingDashboard';
import { V6QuantDashboard } from './components/v6/V6QuantDashboard';
import { ErrorBoundary } from './components/ErrorBoundary';
import { LoadingOverlay } from './components/LoadingOverlay';
import './App.css';

const PRIMARY_SYMBOL = 'BTC/USDT';
const CORE_POLL_MS = 8_000;
const FULL_POLL_MS = 15_000;

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
  const [autoRunning, setAutoRunning] = useState(false);
  const [initialLoading, setInitialLoading] = useState(true);
  const [trialRefresh, setTrialRefresh] = useState(0);
  const secondaryLoading = useRef(false);

  const applyLiveSnapshot = useCallback((data: Record<string, unknown>) => {
    setStats((prev) => {
      if (!prev) return prev;
      return {
        ...prev,
        open_positions: Number(data.open_positions ?? prev.open_positions),
        paper_portfolio_value: Number(data.paper_portfolio_value ?? prev.paper_portfolio_value),
        paper_return_pct: Number(data.paper_return_pct ?? prev.paper_return_pct),
        total_pnl: Number(data.total_pnl ?? prev.total_pnl),
      };
    });
    const c = data.consensus as { final_decision?: string; confidence?: number } | undefined;
    if (c?.final_decision) {
      setConsensus((prev) => ({
        final_decision: c.final_decision!,
        confidence: c.confidence ?? 0,
        agreement: prev?.agreement ?? 0,
        disagreement: prev?.disagreement ?? 0,
        agent_votes: prev?.agent_votes,
        conflicts: prev?.conflicts,
      }));
    }
    const s = data.sentiment as { score?: number; market_sentiment?: string } | undefined;
    if (s?.market_sentiment) {
      setSentiment((prev) => ({
        market_sentiment: s.market_sentiment!,
        score: s.score ?? prev?.score ?? 0,
        confidence: prev?.confidence ?? 0.5,
      }));
    }
  }, []);

  const applyAnalysisResult = useCallback((result: Record<string, unknown>) => {
    const consensusData = result.consensus as ConsensusData | undefined;
    const explanationData = result.explanation as ExplanationData | undefined;
    const sentimentData = result.sentiment as SentimentData | undefined;
    const regimeData = result.regime as RegimeData | undefined;

    if (consensusData?.final_decision) setConsensus(consensusData);
    if (explanationData?.reasons) setExplanation(explanationData);
    if (sentimentData) setSentiment(sentimentData);
    if (regimeData?.regime) setRegime(regimeData);
  }, []);

  const loadCore = useCallback(async () => {
    const [s, o, l] = await Promise.all([api.getStats(), api.getOrders(), api.getAuditLogs()]);
    setStats(s);
    setOrders(o);
    setLogs(l);
  }, []);

  const loadSecondary = useCallback(async () => {
    if (secondaryLoading.current) return;
    secondaryLoading.current = true;
    try {
      const [
        hm, con, exp, sent, reg, mac,
        quantDashboard, quantEventsRes,
        investment, v5,
      ] = await Promise.all([
        api.getHeatmap().catch(() => ({ assets: [] as HeatmapAsset[] })),
        api.getConsensus(PRIMARY_SYMBOL).catch(() => null),
        api.getExplanation(PRIMARY_SYMBOL).catch(() => null),
        api.getSentiment().catch(() => null),
        api.getRegime(PRIMARY_SYMBOL).catch(() => null),
        api.getMacro().catch(() => null),
        api.getQuantDashboard(PRIMARY_SYMBOL).catch(() => null),
        api.getQuantEvents(15).catch(() => ({ events: [] as QuantEvent[] })),
        api.getInvestmentDashboard().catch(() => null),
        api.getV5Dashboard().catch(() => null),
      ]);

      setHeatmap(hm?.assets || []);
      if (con?.final_decision) setConsensus(con);
      if (exp?.reasons) setExplanation(exp);
      if (sent) setSentiment(sent);
      if (reg?.regime) setRegime(reg);
      if (mac) setMacro(mac);
      if (quantDashboard) setQuantData(quantDashboard);
      setQuantEvents(quantEventsRes?.events || []);
      if (investment) setInvestmentData(investment);
      if (v5) setV5Data(v5);
    } finally {
      secondaryLoading.current = false;
    }
  }, []);

  const runAnalysis = async () => {
    setAnalyzing(true);
    setError('');
    try {
      const result = await api.analyzeSymbol(PRIMARY_SYMBOL) as Record<string, unknown>;
      applyAnalysisResult(result);
    } catch {
      setError('Falha ao executar análise IA');
    } finally {
      setAnalyzing(false);
    }
    loadSecondary().catch(() => { /* refresh em background */ });
  };

  useEffect(() => {
    api.setUnauthorizedHandler(() => {
      setAuthenticated(false);
      setError('Sessão expirada. Faça login novamente.');
    });
  }, []);

  useEffect(() => {
    if (!authenticated) return;

    let cancelled = false;
    setInitialLoading(true);

    (async () => {
      try {
        await loadCore();
        if (!cancelled) setInitialLoading(false);
        loadSecondary().catch(() => {});
      } catch (e) {
        if (!cancelled) {
          if (e instanceof AuthError) {
            setAuthenticated(false);
            setError(e.message);
          } else {
            setError('Erro ao carregar dados. Verifique se o backend está rodando.');
          }
          setInitialLoading(false);
        }
      }
    })();

    const coreInterval = setInterval(() => { loadCore().catch(() => {}); }, CORE_POLL_MS);
    const fullInterval = setInterval(() => { loadSecondary().catch(() => {}); }, FULL_POLL_MS);

    const ws = api.connectWebSocket((data) => {
      setWsStatus('conectado');
      if (typeof data !== 'object' || data === null || !('type' in data)) return;
      const msg = data as { type: string; data?: Record<string, unknown> };

      if (msg.type === 'dashboard_update' && msg.data) {
        applyLiveSnapshot(msg.data);
      }
      if (['intelligence_update', 'consensus_update', 'sentiment_update', 'quant_update', 'market_update'].includes(msg.type)) {
        loadSecondary().catch(() => {});
        if (msg.type !== 'dashboard_update') loadCore().catch(() => {});
      }
    });

    ws.onclose = () => setWsStatus('desconectado');
    return () => {
      cancelled = true;
      clearInterval(coreInterval);
      clearInterval(fullInterval);
      ws.close();
    };
  }, [authenticated, loadCore, loadSecondary, applyLiveSnapshot]);

  if (!authenticated) {
    return <LoginForm onLogin={() => { setAuthenticated(true); setError(''); }} sessionMessage={error} />;
  }

  return (
    <div className="app terminal-layout">
      {(initialLoading || analyzing || autoRunning) && (
        <LoadingOverlay
          message={
            analyzing
              ? 'Executando análise IA'
              : autoRunning
                ? 'Ciclo autônomo em execução'
                : 'Carregando dashboard'
          }
          submessage={
            analyzing
              ? 'Ollama remoto + pipelines v3–v5 · Redis offline adiciona ~30s'
              : autoRunning
                ? 'Analisando mercado · recomendando · investindo paper · aprendendo'
                : 'Carregando portfólio e ordens · inteligência em segundo plano'
          }
          showElapsed={analyzing || autoRunning}
        />
      )}
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
          <span className={`badge ws ${wsStatus === 'conectado' ? 'online' : ''}`}>
            {wsStatus === 'conectado' ? '● LIVE' : `WS: ${wsStatus}`}
          </span>
        </div>
      </header>

      {error && <div className="error-banner">{error}</div>}

      <main className="main terminal-main">
        {stats && <PaperEarningsBanner stats={stats} />}

        <PaperTrialPanel refreshKey={trialRefresh} />

        <AIMemoryPanel refreshKey={trialRefresh} />

        <AutonomousInvestor
          onCycleComplete={() => { loadCore().catch(() => {}); loadSecondary().catch(() => {}); setTrialRefresh((k) => k + 1); }}
          onRunningChange={setAutoRunning}
        />

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

        <ErrorBoundary>
          <V6QuantDashboard />
        </ErrorBoundary>

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
