// VIO 83 AI ORCHESTRA — Dashboard: Command Center
import { motion } from 'framer-motion';
import { Activity, Clock, Cpu, DollarSign, TrendingUp, Zap } from 'lucide-react';
import { useEffect, useState } from 'react';
import { CATEGORY_TO_REQUEST_TYPE, getMetricsSnapshot, type MetricsSnapshot } from '../services/metrics/categoryTracker';
import { useAppStore } from '../stores/appStore';

const PROVIDER_COLORS: Record<string, string> = {
  claude: '#D97706',
  gpt4: '#10B981',
  grok: '#3B82F6',
  mistral: '#8B5CF6',
  deepseek: '#EC4899',
  gemini: '#06B6D4',
  groq: '#F97316',
  openrouter: '#A855F7',
  together: '#14B8A6',
  perplexity: '#60A5FA',
  ollama: '#00FF00',
};

const CATEGORY_LOAD = [
  { name: 'Code & Engineering', icon: '💻', count: 1234 },
  { name: 'Analisi Dati', icon: '📊', count: 867 },
  { name: 'Ricerca Scientifica', icon: '🔬', count: 645 },
  { name: 'Scrittura Creativa', icon: '✍️', count: 534 },
  { name: 'Conversazione', icon: '💬', count: 478 },
  { name: 'Traduzione', icon: '🌍', count: 312 },
  { name: 'Matematica & Logica', icon: '🧮', count: 201 },
  { name: 'Real-time Intelligence', icon: '⚡', count: 189 },
  { name: 'Local Privacy & Security', icon: '🔒', count: 567 },
  { name: 'Legal & Compliance', icon: '⚖️', count: 356 },
  { name: 'Medicina & Salute', icon: '🩺', count: 298 },
  { name: 'Business & Finanza', icon: '💼', count: 274 },
  { name: 'Productivity & Vita Quotidiana', icon: '🏡', count: 263 },
  { name: 'DevOps & SRE', icon: '🛠️', count: 244 },
  { name: 'Cybersecurity', icon: '🛡️', count: 239 },
  { name: 'Automazione & Agenti AI', icon: '🤖', count: 415 },
  { name: 'Education & Learning', icon: '🎓', count: 231 },
  { name: 'Ricerca Web & Fact-checking', icon: '🧭', count: 222 },
  { name: 'Hardware, IoT & Robotica', icon: '🦾', count: 184 },
  { name: 'Energia, Clima & Ambiente', icon: '🌱', count: 176 },
  { name: 'Arte, Design & Multimedia', icon: '🎨', count: 214 },
  { name: 'Policy, Governance & Public Sector', icon: '🏛️', count: 167 },
  { name: 'Open Source & GitHub Ops', icon: '🐙', count: 258 },
  { name: 'VS Code / Cowork Runtime', icon: '🧩', count: 193 },
];

export default function DashboardPage() {
  const { conversations, settings } = useAppStore();
  const [metrics, setMetrics] = useState<MetricsSnapshot>(getMetricsSnapshot);
  const [recentActivity, setRecentActivity] = useState<Array<{ time: string; action: string; model: string }>>([]);

  // Refresh metrics ogni 5 secondi per catturare nuove chat in tempo reale
  useEffect(() => {
    const interval = setInterval(() => setMetrics(getMetricsSnapshot()), 5000);
    return () => clearInterval(interval);
  }, []);

  const configuredProviders = settings.apiKeys.length;
  const cloudDependencyScore = settings.orchestrator.mode === 'cloud'
    ? Math.min(15, configuredProviders * 5)
    : 15;
  const orchestrationReadiness = Math.min(
    100,
    30
    + (settings.orchestrator.autoRouting ? 20 : 0)
    + (settings.orchestrator.crossCheckEnabled ? 20 : 0)
    + (settings.orchestrator.ragEnabled ? 15 : 0)
    + cloudDependencyScore
  );

  // Calcola metriche reali
  const totalRequests = metrics.totalRequests;
  const totalTokens = metrics.totalTokens;
  const totalCost = metrics.totalCostUsd;
  const avgLatency = totalRequests > 0
    ? (Object.values(metrics.providers) as Array<{totalLatencyMs: number; count: number}>).reduce((acc, p) => acc + p.totalLatencyMs, 0) / Math.max(1, (Object.values(metrics.providers) as Array<{count: number}>).reduce((acc, p) => acc + p.count, 0)) / 1000
    : 0;

  // Categorie con conteggi reali
  const categoriesWithRealCounts = CATEGORY_LOAD.map(cat => {
    const reqType = CATEGORY_TO_REQUEST_TYPE[cat.name] || 'conversation';
    const metric = metrics.categories[reqType];
    return { ...cat, count: metric?.count || 0 };
  }).sort((a, b) => b.count - a.count);

  // Provider con usage reale
  const providerEntries = Object.values(metrics.providers) as Array<{provider: string; count: number}>;
  const totalProviderCount = providerEntries.reduce((acc, p) => acc + p.count, 0) || 1;
  const providers = [
    { id: 'claude', name: 'Claude Sonnet 4', usage: 0, status: 'online' as const },
    { id: 'gpt4', name: 'GPT-4o', usage: 0, status: 'online' as const },
    { id: 'grok', name: 'Grok 2', usage: 0, status: 'online' as const },
    { id: 'mistral', name: 'Mistral Large', usage: 0, status: 'online' as const },
    { id: 'deepseek', name: 'DeepSeek R1', usage: 0, status: 'online' as const },
    { id: 'gemini', name: 'Gemini 2.5 Pro', usage: 0, status: 'online' as const },
    { id: 'groq', name: 'Groq', usage: 0, status: 'online' as const },
    { id: 'ollama', name: 'Ollama Locale', usage: 0, status: (settings.orchestrator.mode === 'local' ? 'active' : 'standby') as string },
  ].map(p => {
    const pm = (metrics.providers as Record<string, {count: number}>)[p.id];
    return { ...p, usage: pm ? Math.round((pm.count / totalProviderCount) * 100) : 0 };
  });

  useEffect(() => {
    const activities = conversations.slice(0, 8).map(conv => ({
      time: new Date(conv.updatedAt).toLocaleTimeString('it-IT', { hour: '2-digit', minute: '2-digit' }),
      action: conv.title.slice(0, 60),
      model: conv.model || 'ollama',
    }));
    setRecentActivity(activities);
  }, [conversations]);

  const statCards = [
    { icon: Activity, label: 'Richieste Totali', value: totalRequests.toLocaleString(), change: totalRequests > 0 ? `${totalRequests} reali` : 'nessuna ancora', color: 'var(--vio-green)' },
    { icon: Zap, label: 'Token Consumati', value: totalTokens.toLocaleString(), change: totalTokens > 0 ? 'tracciato' : 'in attesa', color: 'var(--vio-cyan)' },
    { icon: DollarSign, label: 'Costo Totale', value: `$${totalCost.toFixed(2)}`, change: totalCost === 0 ? 'locale gratis' : 'reale', color: 'var(--vio-magenta)' },
    { icon: Clock, label: 'Latenza Media', value: `${avgLatency.toFixed(1)}s`, change: avgLatency > 0 ? 'calcolata' : 'n/a', color: 'var(--vio-yellow)' },
  ];

  // (providers calcolati sopra da realProviders con metriche reali)

  return (
    <div style={{ padding: '28px 32px', overflowY: 'auto', height: '100%' }}>
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
      >
        <h1 style={{
          fontSize: '26px', fontWeight: 700, color: 'var(--vio-text-primary)',
          margin: '0 0 4px', letterSpacing: '-0.5px',
        }}>
          Command Center
        </h1>
        <p style={{ color: 'var(--vio-text-dim)', fontSize: '13px', margin: '0 0 28px' }}>
          Panoramica in tempo reale dell'orchestra AI — 7 modelli attivi,{' '}
          {settings.orchestrator.mode === 'cloud' ? 'modalità cloud' : 'modalità locale'}
        </p>
      </motion.div>

      {/* Stat Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '14px', marginBottom: '28px' }}>
        {statCards.map((card, i) => (
          <motion.div
            key={card.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: i * 0.05 }}
            style={{
              background: 'var(--vio-bg-secondary)',
              borderRadius: 'var(--vio-radius-lg)',
              padding: '18px 20px',
              border: '1px solid var(--vio-border)',
              position: 'relative',
              overflow: 'hidden',
            }}
          >
            <div style={{
              position: 'absolute', top: -8, right: -8, opacity: 0.06,
            }}>
              <card.icon size={64} />
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
              <card.icon size={16} color={card.color} />
              <span style={{ color: 'var(--vio-text-dim)', fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                {card.label}
              </span>
            </div>
            <div style={{ fontSize: '24px', fontWeight: 700, color: 'var(--vio-text-primary)', letterSpacing: '-0.5px' }}>
              {card.value}
            </div>
            <div style={{
              fontSize: '11px', marginTop: '6px',
              color: card.change.startsWith('+') ? 'var(--vio-green)' : 'var(--vio-cyan)',
            }}>
              <TrendingUp size={11} style={{ verticalAlign: 'middle', marginRight: '3px' }} />
              {card.change} vs settimana scorsa
            </div>
          </motion.div>
        ))}
      </div>

      {/* Two columns */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '18px' }}>
        {/* Model Distribution */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.4, delay: 0.2 }}
          style={{
            background: 'var(--vio-bg-secondary)',
            borderRadius: 'var(--vio-radius-lg)',
            padding: '20px 24px',
            border: '1px solid var(--vio-border)',
          }}
        >
          <h3 style={{ color: 'var(--vio-text-primary)', fontSize: '15px', fontWeight: 600, margin: '0 0 16px' }}>
            <Cpu size={16} style={{ verticalAlign: 'middle', marginRight: '8px', color: 'var(--vio-green)' }} />
            Distribuzione Modelli
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {providers.map(p => (
              <div key={p.id} style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: PROVIDER_COLORS[p.id], flexShrink: 0 }} />
                <span style={{ color: 'var(--vio-text-secondary)', fontSize: '13px', width: '140px', flexShrink: 0 }}>
                  {p.name}
                </span>
                <div style={{ flex: 1, height: '6px', background: 'var(--vio-bg-tertiary)', borderRadius: '3px', overflow: 'hidden' }}>
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${p.usage}%` }}
                    transition={{ duration: 0.8, delay: 0.3 }}
                    style={{ height: '100%', background: PROVIDER_COLORS[p.id], borderRadius: '3px' }}
                  />
                </div>
                <span style={{ color: 'var(--vio-text-dim)', fontSize: '12px', width: '32px', textAlign: 'right' }}>
                  {p.usage}%
                </span>
                <span style={{
                  width: '6px', height: '6px', borderRadius: '50%',
                  background: p.status === 'active' ? 'var(--vio-green)' : p.status === 'online' ? 'var(--vio-cyan)' : 'var(--vio-text-dim)',
                  boxShadow: p.status === 'active' ? '0 0 6px var(--vio-green)' : 'none',
                }} />
              </div>
            ))}
          </div>
        </motion.div>

        {/* Recent Activity */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.4, delay: 0.3 }}
          style={{
            background: 'var(--vio-bg-secondary)',
            borderRadius: 'var(--vio-radius-lg)',
            padding: '20px 24px',
            border: '1px solid var(--vio-border)',
          }}
        >
          <h3 style={{ color: 'var(--vio-text-primary)', fontSize: '15px', fontWeight: 600, margin: '0 0 16px' }}>
            <Activity size={16} style={{ verticalAlign: 'middle', marginRight: '8px', color: 'var(--vio-magenta)' }} />
            Attività Recente
          </h3>
          {recentActivity.length === 0 ? (
            <p style={{ color: 'var(--vio-text-dim)', fontSize: '13px', textAlign: 'center', padding: '30px 0' }}>
              Nessuna attività recente. Inizia una conversazione!
            </p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {recentActivity.map((act, i) => (
                <div key={i} style={{
                  display: 'flex', alignItems: 'center', gap: '10px',
                  padding: '8px 10px', borderRadius: '8px',
                  background: 'var(--vio-bg-tertiary)',
                }}>
                  <span style={{ color: 'var(--vio-text-dim)', fontSize: '11px', width: '40px', flexShrink: 0 }}>
                    {act.time}
                  </span>
                  <span style={{
                    flex: 1, color: 'var(--vio-text-secondary)', fontSize: '12px',
                    overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                  }}>
                    {act.action}
                  </span>
                  <span style={{
                    fontSize: '10px', padding: '2px 8px', borderRadius: '10px',
                    background: `${PROVIDER_COLORS[act.model] || 'var(--vio-green)'}20`,
                    color: PROVIDER_COLORS[act.model] || 'var(--vio-green)',
                    border: `1px solid ${PROVIDER_COLORS[act.model] || 'var(--vio-green)'}40`,
                  }}>
                    {act.model}
                  </span>
                </div>
              ))}
            </div>
          )}
        </motion.div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '18px', marginTop: '18px' }}>
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.35 }}
          style={{
            background: 'var(--vio-bg-secondary)',
            borderRadius: 'var(--vio-radius-lg)',
            padding: '20px 24px',
            border: '1px solid var(--vio-border)',
          }}
        >
          <h3 style={{ color: 'var(--vio-text-primary)', fontSize: '15px', fontWeight: 600, margin: '0 0 16px' }}>
            Stato Orchestrazione
          </h3>
          <div style={{ marginBottom: '14px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
              <span style={{ color: 'var(--vio-text-secondary)', fontSize: '12px' }}>Readiness reale</span>
              <span style={{ color: 'var(--vio-green)', fontSize: '12px', fontWeight: 700 }}>{orchestrationReadiness}%</span>
            </div>
            <div style={{ height: '8px', background: 'var(--vio-bg-tertiary)', borderRadius: '999px', overflow: 'hidden' }}>
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${orchestrationReadiness}%` }}
                transition={{ duration: 0.9, delay: 0.45 }}
                style={{ height: '100%', background: 'linear-gradient(90deg, var(--vio-green), var(--vio-cyan))' }}
              />
            </div>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
            {[
              { label: 'Auto-routing', value: settings.orchestrator.autoRouting ? 'ON' : 'OFF', color: settings.orchestrator.autoRouting ? 'var(--vio-green)' : 'var(--vio-text-dim)' },
              { label: 'Cross-check', value: settings.orchestrator.crossCheckEnabled ? 'ON' : 'OFF', color: settings.orchestrator.crossCheckEnabled ? 'var(--vio-cyan)' : 'var(--vio-text-dim)' },
              { label: 'RAG', value: settings.orchestrator.ragEnabled ? 'ON' : 'OFF', color: settings.orchestrator.ragEnabled ? 'var(--vio-magenta)' : 'var(--vio-text-dim)' },
              {
                label: 'Cloud keys',
                value: settings.orchestrator.mode === 'cloud' ? `${configuredProviders}` : 'N/A local',
                color: settings.orchestrator.mode === 'cloud'
                  ? (configuredProviders > 0 ? 'var(--vio-yellow)' : 'var(--vio-text-dim)')
                  : 'var(--vio-green)',
              },
            ].map((item) => (
              <div key={item.label} style={{ padding: '12px', borderRadius: '10px', background: 'var(--vio-bg-tertiary)' }}>
                <div style={{ color: 'var(--vio-text-dim)', fontSize: '11px', marginBottom: '4px' }}>{item.label}</div>
                <div style={{ color: item.color, fontSize: '15px', fontWeight: 700 }}>{item.value}</div>
              </div>
            ))}
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.4 }}
          style={{
            background: 'var(--vio-bg-secondary)',
            borderRadius: 'var(--vio-radius-lg)',
            padding: '20px 24px',
            border: '1px solid var(--vio-border)',
          }}
        >
          <h3 style={{ color: 'var(--vio-text-primary)', fontSize: '15px', fontWeight: 600, margin: '0 0 16px' }}>
            Categorie Più Richieste
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {categoriesWithRealCounts.map((category) => (
              <div key={category.name}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
                  <span>{category.icon}</span>
                  <span style={{ color: 'var(--vio-text-secondary)', fontSize: '12px', flex: 1 }}>{category.name}</span>
                  <span style={{ color: 'var(--vio-text-dim)', fontSize: '11px' }}>{category.count}</span>
                </div>
                <div style={{ height: '6px', background: 'var(--vio-bg-tertiary)', borderRadius: '999px', overflow: 'hidden' }}>
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${Math.min(100, (category.count / Math.max(1, categoriesWithRealCounts[0]?.count || 1)) * 100)}%` }}
                    transition={{ duration: 0.8 }}
                    style={{ height: '100%', background: 'linear-gradient(90deg, var(--vio-cyan), var(--vio-green))' }}
                  />
                </div>
              </div>
            ))}
          </div>
        </motion.div>
      </div>

      {/* Quick Actions */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay: 0.4 }}
        style={{ marginTop: '18px' }}
      >
        <div style={{
          background: 'linear-gradient(135deg, rgba(0,255,0,0.05), rgba(0,255,255,0.05))',
          borderRadius: 'var(--vio-radius-lg)',
          padding: '20px 24px',
          border: '1px solid var(--vio-border)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}>
          <div>
            <h3 style={{ color: 'var(--vio-text-primary)', fontSize: '15px', fontWeight: 600, margin: '0 0 4px' }}>
              Vio AI Orchestra v2.0
            </h3>
            <p style={{ color: 'var(--vio-text-dim)', fontSize: '12px', margin: 0 }}>
              La piattaforma di orchestrazione multi-AI più potente al mondo — by vio83
            </p>
          </div>
          <div style={{
            padding: '6px 16px', borderRadius: '20px',
            background: 'rgba(0,255,0,0.1)',
            border: '1px solid var(--vio-green-dim)',
            color: 'var(--vio-green)', fontSize: '12px', fontWeight: 600,
          }}>
            99.9% Uptime
          </div>
        </div>
      </motion.div>
    </div>
  );
}
