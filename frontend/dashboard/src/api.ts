const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';

export interface DashboardStats {
  total_pnl: number;
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
    const res = await fetch(`${API_URL}/api/v1/dashboard/stats`, { headers: this.headers() });
    if (!res.ok) throw new Error('Falha ao carregar stats');
    return res.json();
  }

  async getOrders(): Promise<Order[]> {
    const res = await fetch(`${API_URL}/api/v1/trading/orders`, { headers: this.headers() });
    if (!res.ok) throw new Error('Falha ao carregar ordens');
    return res.json();
  }

  async getAuditLogs(): Promise<AuditLog[]> {
    const res = await fetch(`${API_URL}/api/v1/dashboard/audit-logs?limit=50`, { headers: this.headers() });
    if (!res.ok) throw new Error('Falha ao carregar logs');
    return res.json();
  }

  async getHeatmap(): Promise<{ assets: HeatmapAsset[] }> {
    const res = await fetch(`${API_URL}/api/v1/intelligence/heatmap`, { headers: this.headers() });
    if (!res.ok) throw new Error('Falha ao carregar heatmap');
    return res.json();
  }

  async getConsensus(symbol: string): Promise<ConsensusData> {
    const res = await fetch(`${API_URL}/api/v1/intelligence/consensus/${encodeURIComponent(symbol)}`, { headers: this.headers() });
    if (!res.ok) throw new Error('Falha ao carregar consenso');
    return res.json();
  }

  async getExplanation(symbol: string): Promise<ExplanationData> {
    const res = await fetch(`${API_URL}/api/v1/intelligence/explanation/${encodeURIComponent(symbol)}`, { headers: this.headers() });
    if (!res.ok) throw new Error('Falha ao carregar explicação');
    return res.json();
  }

  async getSentiment(): Promise<SentimentData> {
    const res = await fetch(`${API_URL}/api/v1/intelligence/sentiment`, { headers: this.headers() });
    if (!res.ok) throw new Error('Falha ao carregar sentimento');
    return res.json();
  }

  async getRegime(symbol: string): Promise<RegimeData> {
    const res = await fetch(`${API_URL}/api/v1/intelligence/regime/${encodeURIComponent(symbol)}`, { headers: this.headers() });
    if (!res.ok) throw new Error('Falha ao carregar regime');
    return res.json();
  }

  async getMacro(): Promise<MacroData> {
    const res = await fetch(`${API_URL}/api/v1/intelligence/macro`, { headers: this.headers() });
    if (!res.ok) throw new Error('Falha ao carregar macro');
    return res.json();
  }

  async getNews(): Promise<{ news: NewsItem[] }> {
    const res = await fetch(`${API_URL}/api/v1/intelligence/news`, { headers: this.headers() });
    if (!res.ok) throw new Error('Falha ao carregar notícias');
    return res.json();
  }

  async analyzeSymbol(symbol: string): Promise<unknown> {
    const res = await fetch(`${API_URL}/api/v1/intelligence/analyze/${encodeURIComponent(symbol)}`, {
      method: 'POST',
      headers: this.headers(),
    });
    if (!res.ok) throw new Error('Falha na análise');
    return res.json();
  }

  async getQuantDashboard(symbol: string): Promise<QuantDashboardData> {
    const res = await fetch(
      `${API_URL}/api/v1/quant/dashboard/${encodeURIComponent(symbol)}`,
      { headers: this.headers() },
    );
    if (!res.ok) throw new Error('Falha ao carregar dashboard quant');
    return res.json();
  }

  async getQuantEvents(limit = 20): Promise<{ events: QuantEvent[] }> {
    const res = await fetch(`${API_URL}/api/v1/quant/events/stream?limit=${limit}`, {
      headers: this.headers(),
    });
    if (!res.ok) throw new Error('Falha ao carregar eventos');
    return res.json();
  }

  async getInvestmentDashboard(): Promise<InvestmentDashboardData> {
    const res = await fetch(`${API_URL}/api/v1/investment/dashboard`, { headers: this.headers() });
    if (!res.ok) throw new Error('Falha ao carregar dashboard investment');
    return res.json();
  }

  async runInvestmentRanking(): Promise<unknown> {
    const res = await fetch(`${API_URL}/api/v1/investment/best-opportunity`, { headers: this.headers() });
    if (!res.ok) throw new Error('Falha no ranking de investimentos');
    return res.json();
  }

  async getV5Dashboard(): Promise<V5DashboardData> {
    const res = await fetch(`${API_URL}/api/v1/v5/dashboard`, { headers: this.headers() });
    if (!res.ok) throw new Error('Falha ao carregar dashboard v5');
    return res.json();
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
      ws.send('subscribe:intelligence');
    };
    return ws;
  }
}

export const api = new ApiClient();
