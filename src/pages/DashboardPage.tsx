// VIO 83 AI ORCHESTRA — Dashboard: Command Center
import { useState, useEffect } from 'react';
import { Activity, DollarSign, Zap, Clock, TrendingUp, Cpu } from 'lucide-react';
import { useAppStore } from '../stores/appStore';
import { motion } from 'framer-motion';

// Statistiche simulate (in produzione: da /metrics API)
const generateStats = () => ({
  totalTokens: Math.floor(Math.random() * 500000 + 100000),
  totalCost: parseFloat((Math.random() * 30 + 5).toFixed(2)),
  totalRequests: Math.floor(Math.random() * 2000 + 500),
  avgLatency: parseFloat((Math.random() * 2 + 0.5).toFixed(1)),
  uptime: 99.7,
  modelsActive: 7,
});

const PROVIDER_COLORS: Record<string, string> = {
  claude: '#D97706',
  gpt4: '#10B981',
  grok: '#3B82F6',
  mistral: '#8B5CF6',
  deepseek: '#EC4899',
  gemini: '#06B6D4',
  ollama: '#00FF00',
};

export default function DashboardPage() {
  const { conversations, settings } = useAppStore();
  const [stats] = useState(generateStats);
  const [recentActivity, setRecentActivity] = useState<Array<{ time: string; action: string; model: string }>>([]);

  useEffect(() => {
    // Genera attività recenti dalle conversazioni reali
    const activities = conversations.slice(0, 8).map(conv => ({
      time: new Date(conv.updatedAt).toLocaleTimeString('it-IT', { hour: '2-digit', minute: '2-digit' }),
      action: conv.title.slice(0, 60),
      model: conv.model || 'ollama',
    }));
    setRecentActivity(activities);
  }, [conversations]);

  const statCards = [
    { icon: Activity, label: 'Richieste Totali', value: stats.totalRequests.toLocaleString(), change: '+23%', color: 'var(--vio-green)' },
    { icon: Zap, label: 'Token Consumati', value: stats.totalTokens.toLocaleString(), change: '+12%', color: 'var(--vio-cyan)' },
    { icon: DollarSign, label: 'Costo Totale', value: `$${stats.totalCost}`, change: '-8%', color: 'var(--vio-magenta)' },
    { icon: Clock, label: 'Latenza Media', value: `${stats.avgLatency}s`, change: '-15%', color: 'var(--vio-yellow)' },
  ];

  const providers = [
    { id: 'claude', name: 'Claude Opus 4', usage: 34, status: 'online' },
    { id: 'gpt4', name: 'GPT-4o', usage: 22, status: 'online' },
    { id: 'grok', name: 'Grok 3', usage: 15, status: 'online' },
    { id: 'mistral', name: 'Mistral Large', usage: 10, status: 'online' },
    { id: 'deepseek', name: 'DeepSeek R1', usage: 8, status: 'online' },
    { id: 'gemini', name: 'Gemini 2.0 Flash', usage: 6, status: 'online' },
    { id: 'ollama', name: 'Ollama Locale', usage: 5, status: settings.orchestrator.mode === 'local' ? 'active' : 'standby' },
  ];

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
          Panoramica in tempo reale dell'orchestra AI — {stats.modelsActive} modelli attivi,{' '}
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
            {stats.uptime}% Uptime
          </div>
        </div>
      </motion.div>
    </div>
  );
}
