// VIO 83 AI ORCHESTRA — Models Registry: Tutti i modelli AI
import { motion } from 'framer-motion';
import { Cpu, Zap, Star, Eye, Wrench, Wifi, WifiOff } from 'lucide-react';
import type { AIModelInfo } from '../types';

const ALL_MODELS: AIModelInfo[] = [
  {
    id: 'claude-opus-4', name: 'Claude Opus 4', provider: 'claude', mode: 'cloud',
    description: 'Il modello più potente di Anthropic. Eccelle in analisi profonda, codice complesso, ragionamento multi-step e ricerca scientifica.',
    maxTokens: 32000, contextWindow: 200000, costPer1kInput: 0.015, costPer1kOutput: 0.075,
    speedScore: 92, qualityScore: 99, specialties: ['Deep Analysis', 'Code', 'Research', 'Math'],
    supportsVision: true, supportsTools: true, status: 'online',
  },
  {
    id: 'claude-sonnet-4', name: 'Claude Sonnet 4', provider: 'claude', mode: 'cloud',
    description: 'Veloce e potente. Ideale per coding quotidiano, chat rapida e task generali ad alta qualità.',
    maxTokens: 16000, contextWindow: 200000, costPer1kInput: 0.003, costPer1kOutput: 0.015,
    speedScore: 97, qualityScore: 96, specialties: ['Fast Code', 'Chat', 'General'],
    supportsVision: true, supportsTools: true, status: 'online',
  },
  {
    id: 'gpt-4o', name: 'GPT-4o', provider: 'gpt4', mode: 'cloud',
    description: 'Modello multimodale di OpenAI. Eccellente per creatività, traduzione e contenuti multimediali.',
    maxTokens: 16384, contextWindow: 128000, costPer1kInput: 0.005, costPer1kOutput: 0.015,
    speedScore: 95, qualityScore: 94, specialties: ['Creative', 'Multimodal', 'Translation'],
    supportsVision: true, supportsTools: true, status: 'online',
  },
  {
    id: 'grok-3', name: 'Grok 3', provider: 'grok', mode: 'cloud',
    description: 'Modello xAI con accesso real-time ai dati. Perfetto per ricerche attuali e analisi in tempo reale.',
    maxTokens: 16384, contextWindow: 131072, costPer1kInput: 0.005, costPer1kOutput: 0.015,
    speedScore: 93, qualityScore: 91, specialties: ['Real-time', 'Research', 'Current Events'],
    supportsVision: true, supportsTools: true, status: 'online',
  },
  {
    id: 'gemini-2-flash', name: 'Gemini 2.0 Flash', provider: 'gemini', mode: 'cloud',
    description: 'Modello Google con contesto da 1M token. Eccezionale per documenti lunghi, ricerca e analisi su larga scala.',
    maxTokens: 8192, contextWindow: 1000000, costPer1kInput: 0.002, costPer1kOutput: 0.008,
    speedScore: 96, qualityScore: 92, specialties: ['Long Context', 'Search', 'Analysis'],
    supportsVision: true, supportsTools: true, status: 'online',
  },
  {
    id: 'mistral-large-2', name: 'Mistral Large 2', provider: 'mistral', mode: 'cloud',
    description: 'Modello europeo con eccellente supporto multilingue. Ottimo per traduzioni e contenuti UE.',
    maxTokens: 8192, contextWindow: 128000, costPer1kInput: 0.004, costPer1kOutput: 0.012,
    speedScore: 94, qualityScore: 90, specialties: ['Multilingual', 'EU', 'Translation'],
    supportsVision: false, supportsTools: true, status: 'online',
  },
  {
    id: 'deepseek-r1', name: 'DeepSeek R1', provider: 'deepseek', mode: 'cloud',
    description: 'Specializzato in ragionamento e matematica. Costo ultra-basso con qualità eccellente su task logici.',
    maxTokens: 8192, contextWindow: 64000, costPer1kInput: 0.001, costPer1kOutput: 0.002,
    speedScore: 88, qualityScore: 93, specialties: ['Math', 'Reasoning', 'Logic', 'Code'],
    supportsVision: false, supportsTools: false, status: 'online',
  },
  {
    id: 'ollama-local', name: 'Ollama Locale', provider: 'ollama', mode: 'local',
    description: 'Modelli locali su MacBook Air M1. Zero costi, zero dati trasmessi. Privacy totale.',
    maxTokens: 4096, contextWindow: 32000, costPer1kInput: 0, costPer1kOutput: 0,
    speedScore: 75, qualityScore: 82, specialties: ['Privacy', 'Offline', 'Code'],
    supportsVision: false, supportsTools: false, status: 'standby',
  },
];

const PROVIDER_COLORS: Record<string, string> = {
  claude: '#D97706', gpt4: '#10B981', grok: '#3B82F6',
  mistral: '#8B5CF6', deepseek: '#EC4899', gemini: '#06B6D4', ollama: '#00FF00',
};

const PROVIDER_ICONS: Record<string, string> = {
  claude: '🧠', gpt4: '🌀', grok: '🔮', mistral: '🌊', deepseek: '🔬', gemini: '💎', ollama: '🏠',
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

export default function ModelsPage() {
  return (
    <div style={{ padding: '28px 32px', overflowY: 'auto', height: '100%' }}>
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
        <h1 style={{ fontSize: '26px', fontWeight: 700, color: 'var(--vio-text-primary)', margin: '0 0 4px', letterSpacing: '-0.5px' }}>
          AI Models Registry
        </h1>
        <p style={{ color: 'var(--vio-text-dim)', fontSize: '13px', margin: '0 0 28px' }}>
          8 modelli — 7 cloud + 1 locale — unificati via LiteLLM gateway
        </p>
      </motion.div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '16px' }}>
        {ALL_MODELS.map((m, i) => {
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
                  {m.supportsVision && <Eye size={12} color="var(--vio-cyan)" title="Supporta visione" />}
                  {m.supportsTools && <Wrench size={12} color="var(--vio-magenta)" title="Supporta tool" />}
                  {m.mode === 'local' ? <WifiOff size={12} color="var(--vio-green)" title="Locale" /> : <Wifi size={12} color="var(--vio-cyan)" title="Cloud" />}
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
