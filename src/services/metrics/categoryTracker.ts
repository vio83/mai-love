// VIO 83 AI ORCHESTRA — Category Tracker Service
// Traccia categorie, provider, token, latenze reali in localStorage + backend /metrics

const STORAGE_KEY = 'vio83-category-metrics';

export interface CategoryMetric {
  category: string;
  count: number;
  totalTokens: number;
  totalLatencyMs: number;
  lastUsed: number;
}

export interface ProviderMetric {
  provider: string;
  model: string;
  count: number;
  totalTokens: number;
  totalLatencyMs: number;
  totalCostUsd: number;
  successes: number;
  failures: number;
}

export interface MetricsSnapshot {
  categories: Record<string, CategoryMetric>;
  providers: Record<string, ProviderMetric>;
  totalRequests: number;
  totalTokens: number;
  totalCostUsd: number;
  firstEvent: number;
  lastEvent: number;
}

function loadMetrics(): MetricsSnapshot {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) return JSON.parse(raw);
  } catch { /* corrupt */ }
  return {
    categories: {},
    providers: {},
    totalRequests: 0,
    totalTokens: 0,
    totalCostUsd: 0,
    firstEvent: Date.now(),
    lastEvent: Date.now(),
  };
}

function saveMetrics(data: MetricsSnapshot): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
  } catch { /* quota */ }
}

// Stima costo per provider ($/1K token input — semplificato)
const COST_PER_1K: Record<string, number> = {
  claude: 0.003, gpt4: 0.0025, grok: 0.002, mistral: 0.002,
  deepseek: 0.00027, gemini: 0.00125, groq: 0, openrouter: 0,
  together: 0.00088, perplexity: 0.001, ollama: 0,
};

/** Registra un evento dopo ogni risposta AI */
export function recordMetric(event: {
  category: string;
  provider: string;
  model: string;
  tokensUsed: number;
  latencyMs: number;
  success: boolean;
}): void {
  const data = loadMetrics();
  const now = Date.now();

  // Category
  const cat = data.categories[event.category] || {
    category: event.category, count: 0, totalTokens: 0, totalLatencyMs: 0, lastUsed: 0,
  };
  cat.count++;
  cat.totalTokens += event.tokensUsed;
  cat.totalLatencyMs += event.latencyMs;
  cat.lastUsed = now;
  data.categories[event.category] = cat;

  // Provider
  const key = event.provider;
  const prov = data.providers[key] || {
    provider: event.provider, model: event.model, count: 0,
    totalTokens: 0, totalLatencyMs: 0, totalCostUsd: 0, successes: 0, failures: 0,
  };
  prov.count++;
  prov.model = event.model; // last used model
  prov.totalTokens += event.tokensUsed;
  prov.totalLatencyMs += event.latencyMs;
  const costRate = COST_PER_1K[event.provider] || 0;
  prov.totalCostUsd += (event.tokensUsed / 1000) * costRate;
  if (event.success) prov.successes++; else prov.failures++;
  data.providers[key] = prov;

  // Global
  data.totalRequests++;
  data.totalTokens += event.tokensUsed;
  data.totalCostUsd += (event.tokensUsed / 1000) * costRate;
  data.lastEvent = now;

  saveMetrics(data);

  // Fire-and-forget backend sync
  try {
    fetch('http://localhost:4000/metrics/log', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        provider: event.provider,
        model: event.model,
        request_type: event.category,
        tokens_used: event.tokensUsed,
        latency_ms: event.latencyMs,
        success: event.success,
      }),
    }).catch(() => {});
  } catch { /* offline */ }
}

/** Leggi snapshot corrente */
export function getMetricsSnapshot(): MetricsSnapshot {
  return loadMetrics();
}

/** Reset metriche */
export function resetMetrics(): void {
  localStorage.removeItem(STORAGE_KEY);
}

// Map delle 24 categorie display → request type interno
export const CATEGORY_TO_REQUEST_TYPE: Record<string, string> = {
  'Code & Engineering': 'code',
  'Analisi Dati': 'analysis',
  'Ricerca Scientifica': 'research',
  'Scrittura Creativa': 'creative',
  'Conversazione': 'conversation',
  'Traduzione': 'writing',
  'Matematica & Logica': 'reasoning',
  'Real-time Intelligence': 'realtime',
  'Local Privacy & Security': 'code',
  'Legal & Compliance': 'legal',
  'Medicina & Salute': 'medical',
  'Business & Finanza': 'analysis',
  'Productivity & Vita Quotidiana': 'conversation',
  'DevOps & SRE': 'code',
  'Cybersecurity': 'code',
  'Automazione & Agenti AI': 'automation',
  'Education & Learning': 'reasoning',
  'Ricerca Web & Fact-checking': 'research',
  'Hardware, IoT & Robotica': 'code',
  'Energia, Clima & Ambiente': 'research',
  'Arte, Design & Multimedia': 'creative',
  'Policy, Governance & Public Sector': 'legal',
  'Open Source & GitHub Ops': 'code',
  'VS Code / Cowork Runtime': 'automation',
};

// Map inverso: da request type alle sue categorie display
export const REQUEST_TYPE_CATEGORIES: Record<string, string[]> = {};
for (const [display, reqType] of Object.entries(CATEGORY_TO_REQUEST_TYPE)) {
  if (!REQUEST_TYPE_CATEGORIES[reqType]) REQUEST_TYPE_CATEGORIES[reqType] = [];
  REQUEST_TYPE_CATEGORIES[reqType].push(display);
}
