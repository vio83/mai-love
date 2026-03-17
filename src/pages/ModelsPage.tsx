// VIO 83 AI ORCHESTRA — Models Registry: Tutti i modelli AI
import { motion } from 'framer-motion';
import { Cpu, Eye, Star, Wifi, WifiOff, Wrench, Zap } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { useAppStore } from '../stores/appStore';
import type { AIModelInfo } from '../types';

type EliteStacksPayload = {
  status: string;
  generated_at: string;
  stacks: Record<string, {
    exact_replica_possible?: boolean;
    reason?: string;
    what_is_possible_now?: string;
    primary?: string[];
    secondary?: string[];
    local?: string[];
    best_for?: string[];
  }>;
  notes?: string[];
};

const ALL_MODELS: AIModelInfo[] = [
  {
    id: 'claude-opus-4-6', name: 'Claude Opus 4.6', provider: 'claude', mode: 'cloud',
    description: 'Flagship Anthropic per agenti, coding avanzato, ricerca multi-step e reasoning ad altissima affidabilità.',
    maxTokens: 128000, contextWindow: 1000000, costPer1kInput: 0.005, costPer1kOutput: 0.025,
    speedScore: 92, qualityScore: 99, specialties: ['Agents', 'Code', 'Research', 'Legal', 'Medical'],
    supportsVision: true, supportsTools: true, status: 'standby',
  },
  {
    id: 'claude-sonnet-4-6', name: 'Claude Sonnet 4.6', provider: 'claude', mode: 'cloud',
    description: 'Bilanciamento top fra velocità, tool use, scrittura professionale e sviluppo software serio.',
    maxTokens: 64000, contextWindow: 1000000, costPer1kInput: 0.003, costPer1kOutput: 0.015,
    speedScore: 97, qualityScore: 97, specialties: ['Fast Code', 'Writing', 'Analysis', 'Agents'],
    supportsVision: true, supportsTools: true, status: 'standby',
  },
  {
    id: 'gpt-5.4', name: 'GPT-5.4', provider: 'gpt4', mode: 'cloud',
    description: 'Flagship OpenAI per reasoning complesso, coding professionale, strumenti, MCP e workflow agentici.',
    maxTokens: 128000, contextWindow: 1000000, costPer1kInput: 0.0025, costPer1kOutput: 0.015,
    speedScore: 95, qualityScore: 98, specialties: ['Reasoning', 'Coding', 'Agents', 'Tools'],
    supportsVision: true, supportsTools: true, status: 'standby',
  },
  {
    id: 'gpt-5-mini', name: 'GPT-5 mini', provider: 'gpt4', mode: 'cloud',
    description: 'Variante OpenAI veloce e più economica per task ad alto volume senza scendere troppo di qualità.',
    maxTokens: 128000, contextWindow: 400000, costPer1kInput: 0.00025, costPer1kOutput: 0.002,
    speedScore: 98, qualityScore: 92, specialties: ['Fast General', 'Automation', 'Bulk Tasks'],
    supportsVision: true, supportsTools: true, status: 'standby',
  },
  {
    id: 'grok-4', name: 'Grok 4', provider: 'grok', mode: 'cloud',
    description: 'xAI punta su reasoning + tool use + contesto enorme. Molto forte per realtime se abbini ricerca server-side.',
    maxTokens: 8192, contextWindow: 2000000, costPer1kInput: 0.002, costPer1kOutput: 0.01,
    speedScore: 94, qualityScore: 94, specialties: ['Realtime', 'Research', 'Tool Use', 'Long Context'],
    supportsVision: true, supportsTools: true, status: 'standby',
  },
  {
    id: 'gemini-2-5-pro', name: 'Gemini 2.5 Pro', provider: 'gemini', mode: 'cloud',
    description: 'Google top model per ragionamento, coding, multimodalità e documenti lunghissimi.',
    maxTokens: 8192, contextWindow: 1000000, costPer1kInput: 0.00125, costPer1kOutput: 0.01,
    speedScore: 93, qualityScore: 96, specialties: ['Long Context', 'Coding', 'Research', 'Multimodal'],
    supportsVision: true, supportsTools: true, status: 'standby',
  },
  {
    id: 'gemini-2-5-flash', name: 'Gemini 2.5 Flash', provider: 'gemini', mode: 'cloud',
    description: 'Versione Google ad alto rapporto prezzo/prestazioni per workload rapidi, continui e multimodali.',
    maxTokens: 8192, contextWindow: 1000000, costPer1kInput: 0.000075, costPer1kOutput: 0.0003,
    speedScore: 98, qualityScore: 91, specialties: ['Fast Search', 'Long Context', 'High Volume'],
    supportsVision: true, supportsTools: true, status: 'standby',
  },
  {
    id: 'mistral-large-latest', name: 'Mistral Large (latest)', provider: 'mistral', mode: 'cloud',
    description: 'Stack Mistral top-tier per multilingua, enterprise EU, document understanding e contenuti complessi.',
    maxTokens: 8192, contextWindow: 128000, costPer1kInput: 0.002, costPer1kOutput: 0.006,
    speedScore: 94, qualityScore: 92, specialties: ['Multilingual', 'EU', 'Translation', 'Enterprise'],
    supportsVision: true, supportsTools: true, status: 'standby',
  },
  {
    id: 'deepseek-reasoner', name: 'DeepSeek R1 / Reasoner', provider: 'deepseek', mode: 'cloud',
    description: 'Molto forte per matematica, logica, coding e reasoning strutturato con costo aggressivo.',
    maxTokens: 64000, contextWindow: 128000, costPer1kInput: 0.00055, costPer1kOutput: 0.00219,
    speedScore: 88, qualityScore: 94, specialties: ['Math', 'Reasoning', 'Logic', 'Code'],
    supportsVision: false, supportsTools: true, status: 'standby',
  },
  {
    id: 'groq-gpt-oss-120b', name: 'Groq + GPT-OSS 120B', provider: 'groq', mode: 'cloud',
    description: 'Integrazione ultra-rapida per task agentici, reasoning e automazioni ad alta velocità.',
    maxTokens: 65536, contextWindow: 131072, costPer1kInput: 0.00015, costPer1kOutput: 0.0006,
    speedScore: 99, qualityScore: 90, specialties: ['Speed', 'Automation', 'Agents', 'Code'],
    supportsVision: false, supportsTools: true, status: 'standby',
  },
  {
    id: 'perplexity-pro-search', name: 'Perplexity Pro Search', provider: 'perplexity', mode: 'cloud',
    description: 'Ricerca web grounded, citazioni e analisi orientata a fact-finding e investigative workflows.',
    maxTokens: 32768, contextWindow: 262144, costPer1kInput: 0, costPer1kOutput: 0,
    speedScore: 93, qualityScore: 91, specialties: ['Web Research', 'Citations', 'Current Events'],
    supportsVision: false, supportsTools: true, status: 'standby',
  },
  {
    id: 'openrouter-llama-3-3-free', name: 'OpenRouter Llama 3.3 70B Free', provider: 'openrouter', mode: 'cloud',
    description: 'Ottimo canale elastico per fallback, testing multi-provider e accesso rapido a modelli community/partner.',
    maxTokens: 8192, contextWindow: 131072, costPer1kInput: 0, costPer1kOutput: 0,
    speedScore: 90, qualityScore: 87, specialties: ['Fallback', 'Multi-provider', 'Experiments'],
    supportsVision: false, supportsTools: true, status: 'standby',
  },
  {
    id: 'together-llama-3-3-70b', name: 'Together Llama 3.3 70B', provider: 'together', mode: 'cloud',
    description: 'Buona opzione economica per reasoning generalista e throughput cloud indipendente.',
    maxTokens: 8192, contextWindow: 131072, costPer1kInput: 0.00088, costPer1kOutput: 0.00088,
    speedScore: 89, qualityScore: 88, specialties: ['Budget Cloud', 'Generalist', 'Reasoning'],
    supportsVision: false, supportsTools: true, status: 'standby',
  },
  {
    id: 'ollama-local', name: 'Ollama Locale', provider: 'ollama', mode: 'local',
    description: 'Modelli locali su MacBook Air M1. Zero costi, zero dati trasmessi. Privacy totale.',
    maxTokens: 4096, contextWindow: 32000, costPer1kInput: 0, costPer1kOutput: 0,
    speedScore: 75, qualityScore: 82, specialties: ['Privacy', 'Offline', 'Code'],
    supportsVision: false, supportsTools: false, status: 'online',
  },
];

const PROVIDER_COLORS: Record<string, string> = {
  claude: '#D97706', gpt4: '#10B981', grok: '#3B82F6',
  mistral: '#8B5CF6', deepseek: '#EC4899', gemini: '#06B6D4', groq: '#F97316', openrouter: '#A855F7', together: '#14B8A6', perplexity: '#60A5FA', ollama: '#00FF00',
};

const PROVIDER_ICONS: Record<string, string> = {
  claude: '🧠', gpt4: '🌀', grok: '🔮', mistral: '🌊', deepseek: '🔬', gemini: '💎', groq: '⚡', openrouter: '🛣️', together: '🤝', perplexity: '🧭', ollama: '🏠',
};

function ProgressBar({ value, color, height = 5 }: { value: number; color: string; height?: number }) {
  return (
    <div style={{ height, background: 'var(--vio-bg-tertiary)', borderRadius: height / 2, overflow: 'hidden', flex: 1 }}>
      <motion.div
        initial={{ width: 0 }}
        animate={{ width: `${value}%` }}
        transition={{ duration: 0.8 }}
        style={{ height: '100%', background: color, borderRadius: height / 2 }}
      />
    </div>
  );
}

function prettyStackKey(raw: string): string {
  return raw
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

export default function ModelsPage() {
  const settings = useAppStore(s => s.settings);
  const isCloud = settings.orchestrator.mode === 'cloud';

  const models = useMemo(() => ALL_MODELS.map(m => {
    if (m.mode === 'local') return m;
    const activeProvider = settings.orchestrator.primaryProvider;
    const status = isCloud && m.provider === activeProvider ? 'online' : 'standby';
    return { ...m, status };
  }), [settings.orchestrator.primaryProvider, isCloud]);

  const [eliteStacks, setEliteStacks] = useState<EliteStacksPayload | null>(null);
  const [eliteLoading, setEliteLoading] = useState(true);
  const [eliteError, setEliteError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    const loadEliteStacks = async () => {
      setEliteLoading(true);
      setEliteError(null);

      try {
        const response = await fetch('http://localhost:4000/orchestration/elite-stacks');
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json() as EliteStacksPayload;
        if (!cancelled) {
          setEliteStacks(data);
        }
      } catch (error: unknown) {
        if (!cancelled) {
          setEliteError((error as { message?: string })?.message || 'Errore sconosciuto');
        }
      } finally {
        if (!cancelled) {
          setEliteLoading(false);
        }
      }
    };

    void loadEliteStacks();
    return () => { cancelled = true; };
  }, []);

  const eliteEntries = eliteStacks?.stacks
    ? Object.entries(eliteStacks.stacks).filter(([k]) => k !== 'replica_honesty')
    : [];

  return (
    <div style={{ padding: '28px 32px', overflowY: 'auto', height: '100%' }}>
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
        <h1 style={{ fontSize: '26px', fontWeight: 700, color: 'var(--vio-text-primary)', margin: '0 0 4px', letterSpacing: '-0.5px' }}>
          AI Models Registry
        </h1>
        <p style={{ color: 'var(--vio-text-dim)', fontSize: '13px', margin: '0 0 28px' }}>
          {isCloud
            ? `Registro modelli — Cloud attivo (${settings.orchestrator.primaryProvider}), locale disponibile`
            : 'Registro modelli — Ollama locale attivo, modelli cloud disponibili'}
        </p>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 14 }}
        animate={{ opacity: 1, y: 0 }}
        style={{
          background: 'var(--vio-bg-secondary)',
          borderRadius: 'var(--vio-radius-lg)',
          padding: '18px',
          border: '1px solid var(--vio-border)',
          marginBottom: '18px',
        }}
      >
        <h2 style={{ color: 'var(--vio-text-primary)', fontSize: '16px', margin: '0 0 8px', fontWeight: 700 }}>
          Elite Stacks · Best by Task
        </h2>
        <p style={{ color: 'var(--vio-text-dim)', fontSize: '12px', margin: '0 0 14px' }}>
          Fonte live: <code style={{ color: 'var(--vio-cyan)' }}>/orchestration/elite-stacks</code>
        </p>

        {eliteLoading && (
          <div style={{ color: 'var(--vio-cyan)', fontSize: '12px' }}>Caricamento stack elite…</div>
        )}

        {!eliteLoading && eliteError && (
          <div style={{ color: 'var(--vio-red)', fontSize: '12px' }}>
            Impossibile caricare gli elite stacks: {eliteError}
          </div>
        )}

        {!eliteLoading && !eliteError && eliteEntries.length > 0 && (
          <>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: '12px' }}>
              {eliteEntries.map(([stackKey, stack]) => (
                <div
                  key={stackKey}
                  style={{
                    background: 'var(--vio-bg-tertiary)',
                    border: '1px solid var(--vio-border)',
                    borderRadius: '10px',
                    padding: '12px',
                  }}
                >
                  <div style={{ color: 'var(--vio-text-primary)', fontSize: '13px', fontWeight: 700, marginBottom: '8px' }}>
                    {prettyStackKey(stackKey)}
                  </div>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    {stack.primary && stack.primary.length > 0 && (
                      <div>
                        <div style={{ color: 'var(--vio-green)', fontSize: '10px', marginBottom: '4px', fontWeight: 600 }}>PRIMARY</div>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                          {stack.primary.map((item) => (
                            <span key={item} style={{ fontSize: '10px', padding: '2px 7px', borderRadius: '999px', background: 'rgba(0,255,0,0.09)', color: 'var(--vio-green)', border: '1px solid rgba(0,255,0,0.25)' }}>
                              {item}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {stack.secondary && stack.secondary.length > 0 && (
                      <div>
                        <div style={{ color: 'var(--vio-cyan)', fontSize: '10px', marginBottom: '4px', fontWeight: 600 }}>SECONDARY</div>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                          {stack.secondary.map((item) => (
                            <span key={item} style={{ fontSize: '10px', padding: '2px 7px', borderRadius: '999px', background: 'rgba(0,255,255,0.09)', color: 'var(--vio-cyan)', border: '1px solid rgba(0,255,255,0.25)' }}>
                              {item}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {stack.local && stack.local.length > 0 && (
                      <div>
                        <div style={{ color: 'var(--vio-yellow)', fontSize: '10px', marginBottom: '4px', fontWeight: 600 }}>LOCAL</div>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                          {stack.local.map((item) => (
                            <span key={item} style={{ fontSize: '10px', padding: '2px 7px', borderRadius: '999px', background: 'rgba(255,255,0,0.09)', color: 'var(--vio-yellow)', border: '1px solid rgba(255,255,0,0.25)' }}>
                              {item}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {stack.best_for && stack.best_for.length > 0 && (
                      <div>
                        <div style={{ color: 'var(--vio-text-dim)', fontSize: '10px', marginBottom: '4px', fontWeight: 600 }}>BEST FOR</div>
                        <div style={{ color: 'var(--vio-text-secondary)', fontSize: '11px', lineHeight: 1.5 }}>
                          {stack.best_for.join(' · ')}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>

            {eliteStacks?.notes && eliteStacks.notes.length > 0 && (
              <div style={{ marginTop: '12px', color: 'var(--vio-text-dim)', fontSize: '11px', lineHeight: 1.5 }}>
                {eliteStacks.notes.map((note, idx) => (
                  <div key={`${note}-${idx}`}>• {note}</div>
                ))}
              </div>
            )}
          </>
        )}
      </motion.div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '16px' }}>
        {models.map((m, i) => {
          const color = PROVIDER_COLORS[m.provider] || '#888';
          const icon = PROVIDER_ICONS[m.provider] || '🤖';

          return (
            <motion.div
              key={m.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, delay: i * 0.05 }}
              style={{
                background: 'var(--vio-bg-secondary)',
                borderRadius: 'var(--vio-radius-lg)',
                padding: '20px',
                border: '1px solid var(--vio-border)',
                position: 'relative',
                overflow: 'hidden',
              }}
            >
              {/* Decorative icon */}
              <div style={{ position: 'absolute', top: -10, right: -10, fontSize: '56px', opacity: 0.05 }}>{icon}</div>

              {/* Header */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '12px' }}>
                <div style={{
                  width: '38px', height: '38px', borderRadius: '10px',
                  background: `${color}22`, display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: '18px',
                }}>
                  {icon}
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ color: 'var(--vio-text-primary)', fontSize: '15px', fontWeight: 700 }}>{m.name}</div>
                  <div style={{ color, fontSize: '11px', fontWeight: 600 }}>{m.provider.toUpperCase()}</div>
                </div>
                <div style={{
                  width: '10px', height: '10px', borderRadius: '50%',
                  background: m.status === 'online' ? 'var(--vio-green)' : m.status === 'standby' ? 'var(--vio-yellow)' : 'var(--vio-red)',
                  boxShadow: m.status === 'online' ? '0 0 8px var(--vio-green)' : 'none',
                }} />
              </div>

              {/* Description */}
              <p style={{ color: 'var(--vio-text-dim)', fontSize: '12px', lineHeight: '1.5', marginBottom: '14px', minHeight: '36px' }}>
                {m.description}
              </p>

              {/* Specialties */}
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px', marginBottom: '14px' }}>
                {m.specialties.map(s => (
                  <span key={s} style={{
                    fontSize: '10px', padding: '2px 8px', borderRadius: '8px',
                    background: `${color}15`, color, border: `1px solid ${color}30`,
                  }}>
                    {s}
                  </span>
                ))}
              </div>

              {/* Bars */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginBottom: '14px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Star size={12} color="var(--vio-text-dim)" />
                  <span style={{ color: 'var(--vio-text-dim)', fontSize: '10px', width: '50px' }}>Qualità</span>
                  <ProgressBar value={m.qualityScore} color={color} />
                  <span style={{ color: 'var(--vio-text-primary)', fontSize: '11px', fontWeight: 600, width: '28px', textAlign: 'right' }}>{m.qualityScore}</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Zap size={12} color="var(--vio-text-dim)" />
                  <span style={{ color: 'var(--vio-text-dim)', fontSize: '10px', width: '50px' }}>Velocità</span>
                  <ProgressBar value={m.speedScore} color="var(--vio-cyan)" />
                  <span style={{ color: 'var(--vio-text-primary)', fontSize: '11px', fontWeight: 600, width: '28px', textAlign: 'right' }}>{m.speedScore}</span>
                </div>
              </div>

              {/* Footer */}
              <div style={{
                display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                paddingTop: '12px', borderTop: '1px solid var(--vio-border)',
              }}>
                <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                  <span style={{ color: 'var(--vio-text-dim)', fontSize: '11px' }}>
                    <Cpu size={11} style={{ verticalAlign: 'middle', marginRight: '3px' }} />
                    {m.contextWindow >= 1000000 ? `${(m.contextWindow / 1000000).toFixed(0)}M` : `${(m.contextWindow / 1000).toFixed(0)}K`} ctx
                  </span>
                  {m.supportsVision && <span title="Supporta visione"><Eye size={12} color="var(--vio-cyan)" /></span>}
                  {m.supportsTools && <span title="Supporta tool"><Wrench size={12} color="var(--vio-magenta)" /></span>}
                  {m.mode === 'local'
                    ? <span title="Locale"><WifiOff size={12} color="var(--vio-green)" /></span>
                    : <span title="Cloud"><Wifi size={12} color="var(--vio-cyan)" /></span>}
                </div>
                <span style={{
                  color: m.costPer1kOutput === 0 ? 'var(--vio-green)' : 'var(--vio-text-dim)',
                  fontSize: '11px', fontWeight: m.costPer1kOutput === 0 ? 700 : 400,
                }}>
                  {m.costPer1kOutput === 0 ? 'GRATIS' : `$${m.costPer1kOutput}/1K tok`}
                </span>
              </div>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
