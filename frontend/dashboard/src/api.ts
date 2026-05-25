const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';

export class AuthError extends Error {
  constructor(message = 'Sessão expirada. Faça login novamente.') {
    super(message);
    this.name = 'AuthError';
  }
}

export interface DashboardStats {
  total_pnl: number;
  paper_portfolio_value: number;
  paper_return_pct: number;
  open_positions: number;
  total_orders: number;
  ai_signal: string;
  ai_confidence: number;
  risk_status: {
    daily_pnl: number;
    max_daily_loss: number;
    total_exposure: number;
    max_exposure: number;
    trading_halted: boolean;
    circuit_breaker_active: boolean;
    paper_trading: boolean;
    live_trading_enabled: boolean;
  };
  system_status: string;
  auto_invest_interval_minutes?: number;
}

export interface Order {
  id: string;
  symbol: string;
  side: string;
  status: string;
  quantity: string;
  trading_mode: string;
  created_at: string;
}

export interface AuditLog {
  id: string;
  event_type: string;
  action: string;
  actor: string;
  created_at: string;
}

export interface HeatmapAsset {
  symbol: string;
  score: number;
  trend: string;
  change: number;
}

export interface ConsensusData {
  final_decision: string;
  confidence: number;
  agreement: number;
  disagreement: number;
  agent_votes?: Array<{ agent: string; decision: string; confidence: number }>;
  conflicts?: string[];
}

export interface ExplanationData {
  decision: string;
  confidence: number;
  reasons: string[];
  textual_explanation: string;
  feature_importance?: Record<string, number>;
}

export interface SentimentData {
  market_sentiment: string;
  score: number;
  confidence: number;
  bullish_pct?: number;
  bearish_pct?: number;
  panic_detected?: boolean;
}

export interface RegimeData {
  regime: string;
  confidence: number;
  volatility?: number;
  strategy_adjustment?: string;
}

export interface MacroData {
  outlook?: string;
  indicators: Array<{ name: string; value: number; change_pct?: number; impact?: string }>;
}

export interface QuantDashboardData {
  symbol: string;
  gpu: {
    available: boolean;
    device: string;
    device_name: string;
    vram_total_mb: number;
    vram_used_mb: number;
    cuda_version: string | null;
  };
  calibration: {
    history: Array<{ raw: number; calibrated: number; uncertainty: number; method: string }>;
    latest: {
      raw_confidence: number;
      calibrated_confidence: number;
      uncertainty: number;
      reliability_score: number;
    } | null;
  };
  ensemble: {
    final_decision: string;
    meta_confidence: number;
    stacking_weights: Record<string, number>;
    agent_predictions: Record<string, unknown>;
    method: string;
  } | null;
  similarity: { scenarios: Array<{ label: string; outcome: string | null; state: Record<string, unknown> }> };
  rl: { policies: Array<{ algorithm: string; avg_reward: number; episodes: number; metrics: Record<string, unknown> }> };
  drift: { reports: Array<{ agent: string; drift_score: number; retrain: boolean }> };
  temporal_memory: {
    entries: Array<{
      agent: string;
      type: string;
      decision: string | null;
      context: Record<string, unknown>;
      created_at: string | null;
    }>;
  };
  feature_store: { technical_keys: string[]; sentiment_available: boolean; cache_ttl: number };
  neural_activity: Array<{ agent: string; activity: number; status: string }>;
}

export interface QuantEvent {
  id: string;
  type: string;
  event_id?: string;
  payload?: Record<string, unknown>;
}

export interface V5DashboardData {
  ai_truth: Array<{
    symbol: string;
    truth_score: number;
    corrected_confidence: number;
    overconfidence: boolean;
  }>;
  drift: Array<{
    model: string;
    type: string;
    score: number;
    retrain: boolean;
  }>;
  model_ranking: Array<{
    model: string;
    regime: string;
    accuracy: number;
    sharpe: number | null;
  }>;
  prediction_accuracy: {
    avg_validation_score: number;
    recent: Array<{
      symbol: string;
      predicted: number;
      actual: number | null;
      correct: boolean | null;
      score: number;
    }>;
  };
  real_performance: {
    sharpe: number;
    sortino: number;
    max_drawdown: number;
    hit_rate: number;
    expected_vs_actual: number;
  } | null;
  self_improvement: Array<{
    action: string;
    target: string;
    improvement_pct: number | null;
  }>;
}

export interface AIMemoryDashboardData {
  summary: {
    trades_memorized: number;
    trades_open: number;
    trades_closed: number;
    trade_hit_rate: number | null;
    validations_total: number;
    validation_hit_rate: number | null;
    memory_evaluated: number;
    memory_pending: number;
    memory_hit_rate: number | null;
    overall_hit_rate: number | null;
    agents_tracked: number;
  };
  last_lesson: {
    symbol: string;
    decision: string;
    outcome: string | null;
    performance_pct: number | null;
    was_correct: boolean | null;
    lesson: string;
    created_at: string | null;
  } | null;
  recent_trades: Array<{
    asset: string;
    regime: string;
    setup: string;
    result: string;
    pnl: number;
    confidence: number;
    final_score?: number;
    created_at: string | null;
  }>;
  recent_validations: Array<{
    symbol: string;
    predicted_return_pct: number;
    actual_return_pct: number | null;
    direction_correct: boolean | null;
    validation_score: number;
    created_at: string | null;
  }>;
  agent_weights: Array<{
    agent: string;
    regime: string;
    accuracy: number;
    dynamic_weight: number;
    sample_count: number;
  }>;
  learning_in_decisions: {
    agent_performance_weights: boolean;
    prediction_validations: boolean;
    calibrated_confidence: boolean;
    regime_policy: boolean;
    risk_engine_v2: boolean;
    trade_memory_recall: boolean;
    ai_memory_recall: boolean;
    note: string;
  };
}

export interface PaperTrialStatus {
  status: 'not_started' | 'active' | 'completed';
  message?: string;
  started_at?: string;
  days_elapsed?: number;
  days_remaining?: number;
  days_total?: number;
  ends_at?: string;
  paper_trading?: boolean;
  initial_capital_usdt?: number;
  trial_days?: number;
  portfolio?: {
    initial_capital_usdt: number;
    current_value_usdt: number;
    total_pnl_usdt: number;
    return_pct: number;
    open_positions: number;
    total_orders: number;
    exposure_usdt: number;
  };
  learning?: {
    validations_total: number;
    direction_accuracy: number;
    memory_evaluated: number | null;
    memory_accuracy: number | null;
    avg_validation_score: number;
  };
  readiness?: {
    score: number;
    ready_for_live: boolean;
    notes: string[];
    recommendation: string;
  };
  live_trading_allowed?: boolean;
}

export interface InvestmentRecommendation {
  status: string;
  message?: string;
  action_required?: string;
  ai_summary?: string;
  best_symbol?: string;
  recommendation?: string;
  priority_score?: number;
  expected_return_pct?: number;
  expected_profit_usdt?: number;
  confidence?: number;
  reasons?: string[];
  consensus?: { decision: string | null; confidence: number | null };
  ranking_preview?: Array<{
    symbol: string;
    rank: number;
    score: number;
    recommendation: string;
    expected_return: number;
  }>;
  proposed_order?: {
    symbol: string;
    side: string;
    quantity: string;
    price: string;
    investment_usdt: number;
    allocation_pct: number;
    stop_loss: string;
    take_profit: string;
    paper_trading: boolean;
    requires_approval: boolean;
    can_execute: boolean;
  };
  disclaimer?: string;
}

export interface InvestmentDashboardData {
  best_opportunity: {
    symbol: string;
    priority_score: number;
    expected_return: number;
    recommendation: string;
    confidence: number;
    reasons: string[];
  } | null;
  ranking: Array<{
    symbol: string;
    rank: number;
    score: number;
    expected_return: number;
    risk: number;
    recommendation: string;
  }>;
  allocation: {
    allocations: Record<string, number>;
    cash_pct: number;
    exposure_pct: number;
    regime: string | null;
  } | null;
  institutional_signals: Array<{
    symbol: string;
    type: string;
    strength: number;
    direction: string;
  }>;
  probabilities: Array<{
    symbol: string;
    bullish: number;
    bearish: number;
    uncertainty: number;
  }>;
}

export interface NewsItem {
  title: string;
  source: string;
  impact: string;
  direction: string;
  confidence: number;
}

class ApiClient {
  private token: string | null = localStorage.getItem('cryptoghost_token');
  private onUnauthorized: (() => void) | null = null;

  setUnauthorizedHandler(handler: () => void) {
    this.onUnauthorized = handler;
  }

  setToken(token: string) {
    this.token = token;
    localStorage.setItem('cryptoghost_token', token);
  }

  clearToken() {
    this.token = null;
    localStorage.removeItem('cryptoghost_token');
  }

  private headers(): HeadersInit {
    const h: HeadersInit = { 'Content-Type': 'application/json' };
    if (this.token) h['Authorization'] = `Bearer ${this.token}`;
    return h;
  }

  private async request(url: string, init?: RequestInit): Promise<Response> {
    const res = await fetch(url, {
      ...init,
      headers: { ...this.headers(), ...(init?.headers || {}) },
    });
    if (res.status === 401) {
      this.clearToken();
      this.onUnauthorized?.();
      throw new AuthError();
    }
    return res;
  }

  private async json<T>(url: string, init?: RequestInit, errorMsg = 'Falha na requisição'): Promise<T> {
    const res = await this.request(url, init);
    if (!res.ok) throw new Error(errorMsg);
    return res.json();
  }

  async login(username: string, password: string): Promise<boolean> {
    const res = await fetch(`${API_URL}/api/v1/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    });
    if (!res.ok) return false;
    const data = await res.json();
    this.setToken(data.access_token);
    return true;
  }

  async getStats(): Promise<DashboardStats> {
    return this.json(`${API_URL}/api/v1/dashboard/stats`, undefined, 'Falha ao carregar stats');
  }

  async getOrders(): Promise<Order[]> {
    return this.json(`${API_URL}/api/v1/trading/orders`, undefined, 'Falha ao carregar ordens');
  }

  async getAuditLogs(): Promise<AuditLog[]> {
    return this.json(`${API_URL}/api/v1/dashboard/audit-logs?limit=50`, undefined, 'Falha ao carregar logs');
  }

  async getHeatmap(): Promise<{ assets: HeatmapAsset[] }> {
    return this.json(`${API_URL}/api/v1/intelligence/heatmap`, undefined, 'Falha ao carregar heatmap');
  }

  async getConsensus(symbol: string): Promise<ConsensusData> {
    const params = new URLSearchParams({ symbol });
    return this.json(`${API_URL}/api/v1/intelligence/consensus?${params}`, undefined, 'Falha ao carregar consenso');
  }

  async getExplanation(symbol: string): Promise<ExplanationData> {
    const params = new URLSearchParams({ symbol });
    return this.json(`${API_URL}/api/v1/intelligence/explanation?${params}`, undefined, 'Falha ao carregar explicação');
  }

  async getSentiment(): Promise<SentimentData> {
    return this.json(`${API_URL}/api/v1/intelligence/sentiment`, undefined, 'Falha ao carregar sentimento');
  }

  async getRegime(symbol: string): Promise<RegimeData> {
    const params = new URLSearchParams({ symbol });
    return this.json(`${API_URL}/api/v1/intelligence/regime?${params}`, undefined, 'Falha ao carregar regime');
  }

  async getMacro(): Promise<MacroData> {
    return this.json(`${API_URL}/api/v1/intelligence/macro`, undefined, 'Falha ao carregar macro');
  }

  async getNews(): Promise<{ news: NewsItem[] }> {
    return this.json(`${API_URL}/api/v1/intelligence/news`, undefined, 'Falha ao carregar notícias');
  }

  async analyzeSymbol(symbol: string): Promise<unknown> {
    const params = new URLSearchParams({ symbol });
    return this.json(`${API_URL}/api/v1/intelligence/analyze?${params}`, { method: 'POST' }, 'Falha na análise');
  }

  async getQuantDashboard(symbol: string): Promise<QuantDashboardData> {
    const params = new URLSearchParams({ symbol });
    return this.json(`${API_URL}/api/v1/quant/dashboard?${params}`, undefined, 'Falha ao carregar dashboard quant');
  }

  async getQuantEvents(limit = 20): Promise<{ events: QuantEvent[] }> {
    return this.json(`${API_URL}/api/v1/quant/events/stream?limit=${limit}`, undefined, 'Falha ao carregar eventos');
  }

  async getInvestmentDashboard(): Promise<InvestmentDashboardData> {
    return this.json(`${API_URL}/api/v1/investment/dashboard`, undefined, 'Falha ao carregar dashboard investment');
  }

  async runInvestmentRanking(): Promise<unknown> {
    return this.json(`${API_URL}/api/v1/investment/best-opportunity`, undefined, 'Falha no ranking de investimentos');
  }

  async getInvestmentRecommendation(): Promise<InvestmentRecommendation> {
    return this.json(`${API_URL}/api/v1/investment/recommendation`, undefined, 'Falha ao obter recomendação');
  }

  async approveInvestment(payload: {
    user_confirmed: boolean;
    symbol: string;
    side: string;
    quantity: string;
    stop_loss?: string;
    take_profit?: string;
  }): Promise<Order> {
    const res = await this.request(`${API_URL}/api/v1/trading/approve-investment`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Falha ao executar investimento');
    }
    return res.json();
  }

  async runAutonomousCycle(): Promise<{
    status: string;
    recommendation?: { symbol?: string; recommendation?: string; expected_return_pct?: number; ai_summary?: string };
    order?: { executed?: boolean; status?: string; symbol?: string; quantity?: string };
    learning?: { validated?: number; memory_updated?: number };
    trial?: PaperTrialStatus;
  }> {
    return this.json(`${API_URL}/api/v1/investment/auto-run`, { method: 'POST' }, 'Falha no ciclo autônomo');
  }

  async getTrialStatus(): Promise<PaperTrialStatus> {
    return this.json(`${API_URL}/api/v1/trial/status`, undefined, 'Falha ao carregar trial');
  }

  async startPaperTrial(): Promise<PaperTrialStatus> {
    return this.json(`${API_URL}/api/v1/trial/start`, { method: 'POST' }, 'Falha ao iniciar trial');
  }

  async runTrialLearning(): Promise<{ learning_cycle: unknown; trial: PaperTrialStatus }> {
    return this.json(`${API_URL}/api/v1/trial/learn`, { method: 'POST' }, 'Falha no aprendizado');
  }

  async getV5Dashboard(): Promise<V5DashboardData> {
    return this.json(`${API_URL}/api/v1/v5/dashboard`, undefined, 'Falha ao carregar dashboard v5');
  }

  async getV6Consensus(symbol: string): Promise<Record<string, unknown>> {
    return this.json(`${API_URL}/api/v1/v6/consensus/${encodeURIComponent(symbol)}`);
  }

  async getV6Regime(symbol: string): Promise<Record<string, unknown>> {
    return this.json(`${API_URL}/api/v1/v6/regime/${encodeURIComponent(symbol)}`);
  }

  async getV6AgentPerformance(symbol = 'BTC/USDT'): Promise<Record<string, unknown>> {
    const params = new URLSearchParams({ symbol });
    return this.json(`${API_URL}/api/v1/v6/agent-performance?${params}`);
  }

  async getV6LearningMetrics(): Promise<Record<string, unknown>> {
    return this.json(`${API_URL}/api/v1/v6/learning/metrics`);
  }

  async getV6RiskHeat(): Promise<Record<string, unknown>> {
    return this.json(`${API_URL}/api/v1/v6/risk/heat`);
  }

  async getV6BacktestRuns(): Promise<{ runs: Array<Record<string, unknown>> }> {
    return this.json(`${API_URL}/api/v1/v6/backtest/runs`);
  }

  async runV6Backtest(symbols?: string[]): Promise<Record<string, unknown>> {
    const q = symbols?.length ? `?symbols=${symbols.join(',')}` : '';
    return this.json(`${API_URL}/api/v1/v6/backtest/run${q}`, { method: 'POST' });
  }

  async getV6FreshSignals(symbol?: string): Promise<{ signals: unknown[]; count: number }> {
    const q = symbol ? `?symbol=${encodeURIComponent(symbol)}` : '';
    return this.json(`${API_URL}/api/v1/v6/signals/fresh${q}`);
  }

  async getV6TradeMemory(asset = 'BTC/USDT'): Promise<{ trades: unknown[] }> {
    return this.json(`${API_URL}/api/v1/v6/trade-memory?asset=${encodeURIComponent(asset)}`);
  }

  async getV6SimilarTrades(asset = 'BTC/USDT'): Promise<{ similar: unknown[] }> {
    return this.json(`${API_URL}/api/v1/v6/trade-memory/similar?asset=${encodeURIComponent(asset)}`);
  }

  async getAIMemoryDashboard(): Promise<AIMemoryDashboardData> {
    return this.json(`${API_URL}/api/v1/v6/ai-memory/dashboard`, undefined, 'Falha ao carregar memória da IA');
  }

  async getV6Config(): Promise<{ auto_invest_interval_minutes: number }> {
    return this.json(`${API_URL}/api/v1/v6/config`);
  }

  connectWebSocket(onMessage: (data: unknown) => void): WebSocket {
    const ws = new WebSocket(`${WS_URL}/ws`);
    ws.onmessage = (event) => {
      try {
        onMessage(JSON.parse(event.data));
      } catch { /* ignore */ }
    };
    ws.onopen = () => {
      ws.send('ping');
      ws.send('subscribe:all');
    };
    return ws;
  }
}

export const api = new ApiClient();
