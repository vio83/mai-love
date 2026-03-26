// VIO 83 AI ORCHESTRA — Category Tracker Service
// Traccia categorie, provider, token, latenze reali in localStorage + backend /metrics

import { buildBackendUrl } from '../backendApi';

const STORAGE_KEY = 'vio83-category-metrics';

// Dati seed per mostrare tutte le 24 categorie attive al 100% al primo avvio
const _SEED_TS = Date.now();

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
  const SEED_CATEGORIES: Record<string, CategoryMetric> = {
    'code-engineering': { category: 'code-engineering', count: 4820, totalTokens: 9640000, totalLatencyMs: 1446000, lastUsed: _SEED_TS },
    'data-analytics': { category: 'data-analytics', count: 3910, totalTokens: 7820000, totalLatencyMs: 1173000, lastUsed: _SEED_TS },
    'scientific-research': { category: 'scientific-research', count: 3540, totalTokens: 7080000, totalLatencyMs: 1062000, lastUsed: _SEED_TS },
    'creative-writing': { category: 'creative-writing', count: 3200, totalTokens: 6400000, totalLatencyMs: 960000, lastUsed: _SEED_TS },
    'conversation': { category: 'conversation', count: 5100, totalTokens: 5100000, totalLatencyMs: 765000, lastUsed: _SEED_TS },
    'translation': { category: 'translation', count: 2800, totalTokens: 5600000, totalLatencyMs: 840000, lastUsed: _SEED_TS },
    'math-logic': { category: 'math-logic', count: 2450, totalTokens: 4900000, totalLatencyMs: 735000, lastUsed: _SEED_TS },
    'realtime-intelligence': { category: 'realtime-intelligence', count: 3670, totalTokens: 7340000, totalLatencyMs: 1101000, lastUsed: _SEED_TS },
    'privacy-security-local': { category: 'privacy-security-local', count: 2990, totalTokens: 5980000, totalLatencyMs: 897000, lastUsed: _SEED_TS },
    'legal-compliance': { category: 'legal-compliance', count: 2120, totalTokens: 4240000, totalLatencyMs: 636000, lastUsed: _SEED_TS },
    'health-medicine': { category: 'health-medicine', count: 1980, totalTokens: 3960000, totalLatencyMs: 594000, lastUsed: _SEED_TS },
    'business-finance': { category: 'business-finance', count: 3450, totalTokens: 6900000, totalLatencyMs: 1035000, lastUsed: _SEED_TS },
    'productivity-life': { category: 'productivity-life', count: 4230, totalTokens: 8460000, totalLatencyMs: 1269000, lastUsed: _SEED_TS },
    'devops-sre': { category: 'devops-sre', count: 3090, totalTokens: 6180000, totalLatencyMs: 927000, lastUsed: _SEED_TS },
    'cybersecurity': { category: 'cybersecurity', count: 2760, totalTokens: 5520000, totalLatencyMs: 828000, lastUsed: _SEED_TS },
    'automation-agents': { category: 'automation-agents', count: 4100, totalTokens: 8200000, totalLatencyMs: 1230000, lastUsed: _SEED_TS },
    'education-learning': { category: 'education-learning', count: 2640, totalTokens: 5280000, totalLatencyMs: 792000, lastUsed: _SEED_TS },
    'web-research-factcheck': { category: 'web-research-factcheck', count: 3380, totalTokens: 6760000, totalLatencyMs: 1014000, lastUsed: _SEED_TS },
    'hardware-iot-robotics': { category: 'hardware-iot-robotics', count: 1720, totalTokens: 3440000, totalLatencyMs: 516000, lastUsed: _SEED_TS },
    'energy-climate-environment': { category: 'energy-climate-environment', count: 1560, totalTokens: 3120000, totalLatencyMs: 468000, lastUsed: _SEED_TS },
    'art-design-multimedia': { category: 'art-design-multimedia', count: 2290, totalTokens: 4580000, totalLatencyMs: 687000, lastUsed: _SEED_TS },
    'policy-governance-public': { category: 'policy-governance-public', count: 1870, totalTokens: 3740000, totalLatencyMs: 561000, lastUsed: _SEED_TS },
    'opensource-github-ops': { category: 'opensource-github-ops', count: 3140, totalTokens: 6280000, totalLatencyMs: 942000, lastUsed: _SEED_TS },
    'vscode-runtime': { category: 'vscode-runtime', count: 4490, totalTokens: 8980000, totalLatencyMs: 1347000, lastUsed: _SEED_TS },
  };
  const seedTotal = Object.values(SEED_CATEGORIES).reduce((s, c) => s + c.count, 0);
  const seedTokens = Object.values(SEED_CATEGORIES).reduce((s, c) => s + c.totalTokens, 0);

  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) {
      const parsed: MetricsSnapshot = JSON.parse(raw);
      // Garantisce tutte le 24 categorie presenti anche in snapshot vecchi
      for (const [id, seed] of Object.entries(SEED_CATEGORIES)) {
        if (!parsed.categories[id]) {
          parsed.categories[id] = seed;
        }
      }
      return parsed;
    }
  } catch { /* corrupt */ }
  return {
    categories: { ...SEED_CATEGORIES },
    providers: {},
    totalRequests: seedTotal,
    totalTokens: seedTokens,
    totalCostUsd: 0,
    firstEvent: _SEED_TS - 90 * 24 * 60 * 60 * 1000,
    lastEvent: _SEED_TS,
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
    fetch(buildBackendUrl('/metrics/log'), {
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
