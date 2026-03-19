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

export type SupportedLocale = 'it' | 'en';

interface CategoryDefinition {
  id: string;
  requestType: string;
  icon: string;
  labels: Record<SupportedLocale, string>;
  subcategories: Record<SupportedLocale, string[]>;
}

export interface CategoryCatalogItem {
  id: string;
  name: string;
  icon: string;
  requestType: string;
  subcategories: string[];
}

const CATEGORY_DEFINITIONS: CategoryDefinition[] = [
  {
    id: 'code-engineering',
    requestType: 'code',
    icon: '💻',
    labels: { it: 'Code & Engineering', en: 'Code & Engineering' },
    subcategories: {
      it: ['TypeScript/React', 'Python/FastAPI', 'Rust/Tauri', 'Testing & QA', 'Architettura software'],
      en: ['TypeScript/React', 'Python/FastAPI', 'Rust/Tauri', 'Testing & QA', 'Software Architecture'],
    },
  },
  {
    id: 'data-analytics',
    requestType: 'analysis',
    icon: '📊',
    labels: { it: 'Analisi Dati', en: 'Data Analytics' },
    subcategories: {
      it: ['BI', 'Data Visualization', 'KPI & metriche', 'Forecasting', 'Statistica applicata'],
      en: ['BI', 'Data Visualization', 'KPI & Metrics', 'Forecasting', 'Applied Statistics'],
    },
  },
  {
    id: 'scientific-research',
    requestType: 'research',
    icon: '🔬',
    labels: { it: 'Ricerca Scientifica', en: 'Scientific Research' },
    subcategories: {
      it: ['Letteratura accademica', 'Peer review', 'Metodologia', 'Meta-analisi', 'Riproducibilità'],
      en: ['Academic Literature', 'Peer Review', 'Methodology', 'Meta-analysis', 'Reproducibility'],
    },
  },
  {
    id: 'creative-writing',
    requestType: 'creative',
    icon: '✍️',
    labels: { it: 'Scrittura Creativa', en: 'Creative Writing' },
    subcategories: {
      it: ['Storytelling', 'Copywriting', 'Script', 'Editing', 'Tone of voice'],
      en: ['Storytelling', 'Copywriting', 'Script', 'Editing', 'Tone of Voice'],
    },
  },
  {
    id: 'conversation',
    requestType: 'conversation',
    icon: '💬',
    labels: { it: 'Conversazione', en: 'Conversation' },
    subcategories: {
      it: ['Q&A generico', 'Brainstorming', 'Supporto personale', 'Decision support'],
      en: ['General Q&A', 'Brainstorming', 'Personal Support', 'Decision Support'],
    },
  },
  {
    id: 'translation',
    requestType: 'writing',
    icon: '🌍',
    labels: { it: 'Traduzione', en: 'Translation' },
    subcategories: {
      it: ['IT-EN', 'EN-IT', 'Localizzazione UX', 'Terminologia tecnica'],
      en: ['IT-EN', 'EN-IT', 'UX Localization', 'Technical Terminology'],
    },
  },
  {
    id: 'math-logic',
    requestType: 'reasoning',
    icon: '🧮',
    labels: { it: 'Matematica & Logica', en: 'Math & Logic' },
    subcategories: {
      it: ['Algebra', 'Calcolo', 'Logica formale', 'Ottimizzazione', 'Proof assistant'],
      en: ['Algebra', 'Calculus', 'Formal Logic', 'Optimization', 'Proof Assistant'],
    },
  },
  {
    id: 'realtime-intelligence',
    requestType: 'realtime',
    icon: '⚡',
    labels: { it: 'Real-time Intelligence', en: 'Real-time Intelligence' },
    subcategories: {
      it: ['Monitoraggio eventi', 'Alerting', 'Trend live', 'Decisioni time-critical'],
      en: ['Event Monitoring', 'Alerting', 'Live Trends', 'Time-critical Decisions'],
    },
  },
  {
    id: 'privacy-security-local',
    requestType: 'code',
    icon: '🔒',
    labels: { it: 'Local Privacy & Security', en: 'Local Privacy & Security' },
    subcategories: {
      it: ['Zero telemetry', 'Data minimization', 'Threat modeling', 'Hardening locale'],
      en: ['Zero Telemetry', 'Data Minimization', 'Threat Modeling', 'Local Hardening'],
    },
  },
  {
    id: 'legal-compliance',
    requestType: 'legal',
    icon: '⚖️',
    labels: { it: 'Legal & Compliance', en: 'Legal & Compliance' },
    subcategories: {
      it: ['GDPR', 'Contratti', 'Licensing OSS', 'Policy governance', 'Audit trail'],
      en: ['GDPR', 'Contracts', 'OSS Licensing', 'Policy Governance', 'Audit Trail'],
    },
  },
  {
    id: 'health-medicine',
    requestType: 'medical',
    icon: '🩺',
    labels: { it: 'Medicina & Salute', en: 'Health & Medicine' },
    subcategories: {
      it: ['Evidenza clinica', 'Prevenzione', 'Farmacologia', 'Linee guida', 'Triage informativo'],
      en: ['Clinical Evidence', 'Prevention', 'Pharmacology', 'Guidelines', 'Informational Triage'],
    },
  },
  {
    id: 'business-finance',
    requestType: 'analysis',
    icon: '💼',
    labels: { it: 'Business & Finanza', en: 'Business & Finance' },
    subcategories: {
      it: ['P&L', 'Go-to-market', 'Pricing', 'Operations', 'Risk management'],
      en: ['P&L', 'Go-to-market', 'Pricing', 'Operations', 'Risk Management'],
    },
  },
  {
    id: 'productivity-life',
    requestType: 'conversation',
    icon: '🏡',
    labels: { it: 'Productivity & Vita Quotidiana', en: 'Productivity & Daily Life' },
    subcategories: {
      it: ['Task planning', 'Personal knowledge', 'Routine design', 'Decision hygiene'],
      en: ['Task Planning', 'Personal Knowledge', 'Routine Design', 'Decision Hygiene'],
    },
  },
  {
    id: 'devops-sre',
    requestType: 'code',
    icon: '🛠️',
    labels: { it: 'DevOps & SRE', en: 'DevOps & SRE' },
    subcategories: {
      it: ['CI/CD', 'Observability', 'Incident response', 'Reliability engineering'],
      en: ['CI/CD', 'Observability', 'Incident Response', 'Reliability Engineering'],
    },
  },
  {
    id: 'cybersecurity',
    requestType: 'code',
    icon: '🛡️',
    labels: { it: 'Cybersecurity', en: 'Cybersecurity' },
    subcategories: {
      it: ['AppSec', 'Network security', 'Identity & access', 'Vulnerability management'],
      en: ['AppSec', 'Network Security', 'Identity & Access', 'Vulnerability Management'],
    },
  },
  {
    id: 'automation-agents',
    requestType: 'automation',
    icon: '🤖',
    labels: { it: 'Automazione & Agenti AI', en: 'Automation & AI Agents' },
    subcategories: {
      it: ['Workflow orchestration', 'Tool calling', 'MCP', 'Autonomous loops', 'RPA'],
      en: ['Workflow Orchestration', 'Tool Calling', 'MCP', 'Autonomous Loops', 'RPA'],
    },
  },
  {
    id: 'education-learning',
    requestType: 'reasoning',
    icon: '🎓',
    labels: { it: 'Education & Learning', en: 'Education & Learning' },
    subcategories: {
      it: ['Didattica', 'Lesson design', 'Assessment', 'Spaced repetition'],
      en: ['Teaching', 'Lesson Design', 'Assessment', 'Spaced Repetition'],
    },
  },
  {
    id: 'web-research-factcheck',
    requestType: 'research',
    icon: '🧭',
    labels: { it: 'Ricerca Web & Fact-checking', en: 'Web Research & Fact-checking' },
    subcategories: {
      it: ['Source triangulation', 'Claim verification', 'News intelligence', 'Citation quality'],
      en: ['Source Triangulation', 'Claim Verification', 'News Intelligence', 'Citation Quality'],
    },
  },
  {
    id: 'hardware-iot-robotics',
    requestType: 'code',
    icon: '🦾',
    labels: { it: 'Hardware, IoT & Robotica', en: 'Hardware, IoT & Robotics' },
    subcategories: {
      it: ['Embedded systems', 'Edge AI', 'Sensors', 'Industrial automation'],
      en: ['Embedded Systems', 'Edge AI', 'Sensors', 'Industrial Automation'],
    },
  },
  {
    id: 'energy-climate-environment',
    requestType: 'research',
    icon: '🌱',
    labels: { it: 'Energia, Clima & Ambiente', en: 'Energy, Climate & Environment' },
    subcategories: {
      it: ['Decarbonizzazione', 'Energy systems', 'Climate risk', 'Sustainability metrics'],
      en: ['Decarbonization', 'Energy Systems', 'Climate Risk', 'Sustainability Metrics'],
    },
  },
  {
    id: 'art-design-multimedia',
    requestType: 'creative',
    icon: '🎨',
    labels: { it: 'Arte, Design & Multimedia', en: 'Art, Design & Multimedia' },
    subcategories: {
      it: ['Visual design', 'UX writing', 'Audio/video', 'Creative direction'],
      en: ['Visual Design', 'UX Writing', 'Audio/Video', 'Creative Direction'],
    },
  },
  {
    id: 'policy-governance-public',
    requestType: 'legal',
    icon: '🏛️',
    labels: { it: 'Policy, Governance & Public Sector', en: 'Policy, Governance & Public Sector' },
    subcategories: {
      it: ['Public policy', 'Regulatory analysis', 'Digital government', 'Procurement'],
      en: ['Public Policy', 'Regulatory Analysis', 'Digital Government', 'Procurement'],
    },
  },
  {
    id: 'opensource-github-ops',
    requestType: 'code',
    icon: '🐙',
    labels: { it: 'Open Source & GitHub Ops', en: 'Open Source & GitHub Ops' },
    subcategories: {
      it: ['Repo strategy', 'Release engineering', 'Community ops', 'Issue triage'],
      en: ['Repo Strategy', 'Release Engineering', 'Community Ops', 'Issue Triage'],
    },
  },
  {
    id: 'vscode-runtime',
    requestType: 'automation',
    icon: '🧩',
    labels: { it: 'VS Code / Cowork Runtime', en: 'VS Code / Cowork Runtime' },
    subcategories: {
      it: ['Agent workflows', 'Editor automation', 'Tasks orchestration', 'Dev productivity'],
      en: ['Agent Workflows', 'Editor Automation', 'Tasks Orchestration', 'Dev Productivity'],
    },
  },
];

export function getCategoryCatalog(locale: SupportedLocale = 'it'): CategoryCatalogItem[] {
  return CATEGORY_DEFINITIONS.map((category) => ({
    id: category.id,
    name: category.labels[locale],
    icon: category.icon,
    requestType: category.requestType,
    subcategories: category.subcategories[locale],
  }));
}

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
    }).catch(() => { });
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

// Legacy map (compat): label display (IT/EN) → request type interno
export const CATEGORY_TO_REQUEST_TYPE: Record<string, string> = CATEGORY_DEFINITIONS.reduce<Record<string, string>>((acc, category) => {
  acc[category.labels.it] = category.requestType;
  acc[category.labels.en] = category.requestType;
  return acc;
}, {});

// Map inverso: da request type alle sue categorie display (IT)
export const REQUEST_TYPE_CATEGORIES: Record<string, string[]> = {};
for (const category of CATEGORY_DEFINITIONS) {
  const reqType = category.requestType;
  if (!REQUEST_TYPE_CATEGORIES[reqType]) REQUEST_TYPE_CATEGORIES[reqType] = [];
  REQUEST_TYPE_CATEGORIES[reqType].push(category.labels.it);
}
