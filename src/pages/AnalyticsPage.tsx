// VIO 83 AI ORCHESTRA — Analytics: Performance Intelligence
import { useState } from 'react';
import { motion } from 'framer-motion';
import { BarChart3, TrendingUp, Clock, Coins, Brain, Gauge, Star, Zap } from 'lucide-react';

const PROVIDER_COLORS: Record<string, string> = {
  claude: '#D97706', gpt4: '#10B981', grok: '#3B82F6',
  mistral: '#8B5CF6', deepseek: '#EC4899', gemini: '#06B6D4', ollama: '#00FF00',
};

// Dati mock — in produzione da /metrics API
const modelStats = [
  { name: 'Claude Opus 4', id: 'claude', quality: 99, speed: 92, cost: 0.075, requests: 892, tokens: 234000 },
  { name: 'Claude Sonnet 4', id: 'claude', quality: 96, speed: 97, cost: 0.015, requests: 1456, tokens: 567000 },
  { name: 'GPT-4o', id: 'gpt4', quality: 94, speed: 95, cost: 0.015, requests: 723, tokens: 189000 },
  { name: 'Grok 3', id: 'grok', quality: 91, speed: 93, cost: 0.015, requests: 412, tokens: 98000 },
  { name: 'Gemini 2.0 Flash', id: 'gemini', quality: 92, speed: 96, cost: 0.008, requests: 334, tokens: 156000 },
  { name: 'Mistral Large', id: 'mistral', quality: 90, speed: 94, cost: 0.012, requests: 278, tokens: 67000 },
  { name: 'DeepSeek R1', id: 'deepseek', quality: 93, speed: 88, cost: 0.002, requests: 198, tokens: 45000 },
  { name: 'Ollama Locale', id: 'ollama', quality: 82, speed: 75, cost: 0, requests: 156, tokens: 89000 },
];

const categoryStats = [
  { name: 'Code & Engineering', icon: '💻', count: 1234, percentage: 28 },
  { name: 'Analisi Dati', icon: '📊', count: 867, percentage: 20 },
  { name: 'Ricerca Scientifica', icon: '🔬', count: 645, percentage: 15 },
  { name: 'Scrittura Creativa', icon: '✍️', count: 534, percentage: 12 },
  { name: 'Conversazione', icon: '💬', count: 478, percentage: 11 },
  { name: 'Traduzione', icon: '🌍', count: 312, percentage: 7 },
  { name: 'Matematica & Logica', icon: '🧮', count: 201, percentage: 5 },
  { name: 'Real-time', icon: '⚡', count: 89, percentage: 2 },
];

function Bar({ value, maxValue, color, label }: { value: number; maxValue: number; color: string; label: string }) {
  const pct = (value / maxValue) * 100;
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
      <span style={{ color: 'var(--vio-text-dim)', fontSize: '11px', width: '60px', flexShrink: 0, textAlign: 'right' }}>{label}</span>
      <div style={{ flex: 1, height: '8px', background: 'var(--vio-bg-tertiary)', borderRadius: '4px', overflow: 'hidden' }}>
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.8 }}
          style={{ height: '100%', background: color, borderRadius: '4px' }}
        />
      </div>
      <span style={{ color: 'var(--vio-text-primary)', fontSize: '11px', fontWeight: 600, width: '40px' }}>{value}</span>
    </div>
  );
}

export default function AnalyticsPage() {
  const [timeRange, setTimeRange] = useState<'7d' | '30d' | '90d'>('30d');

  const totalRequests = modelStats.reduce((a, b) => a + b.requests, 0);
  const totalTokens = modelStats.reduce((a, b) => a + b.tokens, 0);
  const totalCost = modelStats.reduce((a, b) => a + (b.tokens / 1000) * b.cost, 0);
  const avgLatency = 1.4;

  return (
    <div style={{ padding: '28px 32px', overflowY: 'auto', height: '100%' }}>
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '28px' }}>
          <div>
            <h1 style={{ fontSize: '26px', fontWeight: 700, color: 'var(--vio-text-primary)', margin: '0 0 4px', letterSpacing: '-0.5px' }}>
              Analytics & Intelligence
            </h1>
            <p style={{ color: 'var(--vio-text-dim)', fontSize: '13px', margin: 0 }}>
              Performance profonda di tutti i modelli AI
            </p>
          </div>
          <div style={{ display: 'flex', gap: '4px', background: 'var(--vio-bg-secondary)', borderRadius: '8px', padding: '3px', border: '1px solid var(--vio-border)' }}>
            {(['7d', '30d', '90d'] as const).map(r => (
              <button key={r} onClick={() => setTimeRange(r)} style={{
                padding: '5px 12px', borderRadius: '6px', border: 'none', cursor: 'pointer',
                background: timeRange === r ? 'var(--vio-green)' : 'transparent',
                color: timeRange === r ? '#000' : 'var(--vio-text-dim)',
                fontSize: '11px', fontWeight: 600,
              }}>
                {r}
              </button>
            ))}
          </div>
        </div>
      </motion.div>

      {/* Summary Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '14px', marginBottom: '24px' }}>
        {[
          { icon: BarChart3, label: 'Richieste', value: totalRequests.toLocaleString(), color: 'var(--vio-green)' },
          { icon: Brain, label: 'Token', value: `${(totalTokens / 1000000).toFixed(1)}M`, color: 'var(--vio-cyan)' },
          { icon: Coins, label: 'Costo', value: `$${totalCost.toFixed(2)}`, color: 'var(--vio-magenta)' },
          { icon: Gauge, label: 'Latenza Media', value: `${avgLatency}s`, color: 'var(--vio-yellow)' },
        ].map((card, i) => (
          <motion.div key={card.label} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.05 }}
            style={{
              background: 'var(--vio-bg-secondary)', borderRadius: 'var(--vio-radius-lg)',
              padding: '16px 18px', border: '1px solid var(--vio-border)', textAlign: 'center',
            }}
          >
            <card.icon size={18} color={card.color} style={{ marginBottom: '6px' }} />
            <div style={{ color: 'var(--vio-text-primary)', fontSize: '22px', fontWeight: 700 }}>{card.value}</div>
            <div style={{ color: 'var(--vio-text-dim)', fontSize: '11px', marginTop: '2px' }}>{card.label}</div>
          </motion.div>
        ))}
      </div>

      {/* Model Comparison */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '18px', marginBottom: '18px' }}>
        <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.2 }}
          style={{ background: 'var(--vio-bg-secondary)', borderRadius: 'var(--vio-radius-lg)', padding: '20px 24px', border: '1px solid var(--vio-border)' }}
        >
          <h3 style={{ color: 'var(--vio-text-primary)', fontSize: '15px', fontWeight: 600, margin: '0 0 16px' }}>
            <Star size={16} style={{ verticalAlign: 'middle', marginRight: '8px', color: 'var(--vio-green)' }} />
            Qualità per Modello
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {modelStats.sort((a, b) => b.quality - a.quality).map(m => (
              <Bar key={m.name} value={m.quality} maxValue={100} color={PROVIDER_COLORS[m.id] || '#888'} label={m.name.split(' ')[0]} />
            ))}
          </div>
        </motion.div>

        <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.3 }}
          style={{ background: 'var(--vio-bg-secondary)', borderRadius: 'var(--vio-radius-lg)', padding: '20px 24px', border: '1px solid var(--vio-border)' }}
        >
          <h3 style={{ color: 'var(--vio-text-primary)', fontSize: '15px', fontWeight: 600, margin: '0 0 16px' }}>
            <Zap size={16} style={{ verticalAlign: 'middle', marginRight: '8px', color: 'var(--vio-cyan)' }} />
            Velocità per Modello
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {modelStats.sort((a, b) => b.speed - a.speed).map(m => (
              <Bar key={m.name} value={m.speed} maxValue={100} color={PROVIDER_COLORS[m.id] || '#888'} label={m.name.split(' ')[0]} />
            ))}
          </div>
        </motion.div>
      </div>

      {/* Category Distribution */}
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.4 }}
        style={{ background: 'var(--vio-bg-secondary)', borderRadius: 'var(--vio-radius-lg)', padding: '20px 24px', border: '1px solid var(--vio-border)' }}
      >
        <h3 style={{ color: 'var(--vio-text-primary)', fontSize: '15px', fontWeight: 600, margin: '0 0 16px' }}>
          <TrendingUp size={16} style={{ verticalAlign: 'middle', marginRight: '8px', color: 'var(--vio-magenta)' }} />
          Distribuzione per Categoria (1,082 sotto-discipline)
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: '10px' }}>
          {categoryStats.map((cat, i) => (
            <div key={cat.name} style={{
              display: 'flex', alignItems: 'center', gap: '10px',
              padding: '10px 12px', borderRadius: '8px', background: 'var(--vio-bg-tertiary)',
            }}>
              <span style={{ fontSize: '20px' }}>{cat.icon}</span>
              <div style={{ flex: 1 }}>
                <div style={{ color: 'var(--vio-text-secondary)', fontSize: '12px', fontWeight: 500 }}>{cat.name}</div>
                <div style={{ height: '4px', background: 'var(--vio-bg-primary)', borderRadius: '2px', marginTop: '4px', overflow: 'hidden' }}>
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${cat.percentage}%` }}
                    transition={{ duration: 0.6, delay: 0.5 + i * 0.05 }}
                    style={{ height: '100%', background: 'var(--vio-green)', borderRadius: '2px' }}
                  />
                </div>
              </div>
              <span style={{ color: 'var(--vio-text-dim)', fontSize: '11px' }}>{cat.count}</span>
            </div>
          ))}
        </div>
      </motion.div>
    </div>
  );
}

