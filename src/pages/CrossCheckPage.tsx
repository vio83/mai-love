// VIO 83 AI ORCHESTRA — Cross-Check: Verifica Multi-Modello
import { useState } from 'react';
import { motion } from 'framer-motion';
import { CheckCircle, AlertTriangle, XCircle, Shield, Brain, Percent } from 'lucide-react';

const crossChecks = [
  {
    id: '1', query: 'Rust è memory-safe senza garbage collector?',
    models: ['Claude Opus 4', 'DeepSeek R1', 'GPT-4o'],
    concordanceScore: 99.2, level: 'full_agree' as const,
    verdict: 'Tutti i modelli confermano: Rust usa ownership + borrow checker per memory safety a compile time.',
    timestamp: Date.now() - 300000,
  },
  {
    id: '2', query: 'Miglior algoritmo di sorting per dati quasi ordinati?',
    models: ['Claude Sonnet 4', 'Grok 3', 'DeepSeek R1'],
    concordanceScore: 97.5, level: 'full_agree' as const,
    verdict: 'Consenso: Insertion Sort O(n) per quasi-ordinati, Timsort per caso generale.',
    timestamp: Date.now() - 900000,
  },
  {
    id: '3', query: 'I computer quantistici possono rompere RSA-2048 oggi?',
    models: ['Claude Opus 4', 'Grok 3', 'Mistral Large'],
    concordanceScore: 88.3, level: 'partial' as const,
    verdict: 'Parziale: D\'accordo che oggi no. Disaccordo sulla timeline (range 2030-2040).',
    timestamp: Date.now() - 3600000,
  },
  {
    id: '4', query: 'P = NP?',
    models: ['Claude Opus 4', 'DeepSeek R1', 'GPT-4o'],
    concordanceScore: 95.0, level: 'full_agree' as const,
    verdict: 'Consenso: Ampiamente ritenuto P ≠ NP, ma non dimostrato (Premio Millennium).',
    timestamp: Date.now() - 7200000,
  },
  {
    id: '5', query: 'Qual è il framework Python più veloce per API async?',
    models: ['Claude Sonnet 4', 'Gemini 2.0', 'DeepSeek R1'],
    concordanceScore: 92.1, level: 'full_agree' as const,
    verdict: 'Consenso su FastAPI (basato su Starlette/Uvicorn). Benchmark TechEmpower confermano.',
    timestamp: Date.now() - 14400000,
  },
  {
    id: '6', query: 'L\'AGI arriverà entro il 2030?',
    models: ['Claude Opus 4', 'GPT-4o', 'Grok 3'],
    concordanceScore: 62.4, level: 'disagree' as const,
    verdict: 'Disaccordo: Claude più cauto (post-2035), GPT-4o neutro, Grok ottimista (2028-2030).',
    timestamp: Date.now() - 28800000,
  },
];

const levelConfig = {
  full_agree: { icon: CheckCircle, label: 'Accordo Pieno', color: 'var(--vio-green)', bg: 'rgba(0,255,0,0.1)' },
  partial: { icon: AlertTriangle, label: 'Parziale', color: 'var(--vio-yellow)', bg: 'rgba(255,255,0,0.1)' },
  disagree: { icon: XCircle, label: 'Disaccordo', color: 'var(--vio-red)', bg: 'rgba(255,50,50,0.1)' },
};

export default function CrossCheckPage() {
  const totalChecks = crossChecks.length;
  const fullAgree = crossChecks.filter(c => c.level === 'full_agree').length;
  const partial = crossChecks.filter(c => c.level === 'partial').length;
  const disagree = crossChecks.filter(c => c.level === 'disagree').length;

  return (
    <div style={{ padding: '28px 32px', overflowY: 'auto', height: '100%' }}>
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
        <h1 style={{ fontSize: '26px', fontWeight: 700, color: 'var(--vio-text-primary)', margin: '0 0 4px', letterSpacing: '-0.5px' }}>
          Cross-Check Verification
        </h1>
        <p style={{ color: 'var(--vio-text-dim)', fontSize: '13px', margin: '0 0 28px' }}>
          Validazione consenso multi-modello — fiducia attraverso verifica
        </p>
      </motion.div>

      {/* Stats */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '14px', marginBottom: '24px' }}>
        {[
          { icon: Shield, label: 'Verifiche Totali', value: `${totalChecks}`, color: 'var(--vio-green)' },
          { icon: CheckCircle, label: 'Accordo Pieno', value: `${((fullAgree / totalChecks) * 100).toFixed(0)}%`, color: 'var(--vio-green)' },
          { icon: AlertTriangle, label: 'Parziale', value: `${((partial / totalChecks) * 100).toFixed(0)}%`, color: 'var(--vio-yellow)' },
          { icon: XCircle, label: 'Disaccordo', value: `${((disagree / totalChecks) * 100).toFixed(0)}%`, color: 'var(--vio-red)' },
        ].map((s, i) => (
          <motion.div key={s.label} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.05 }}
            style={{ background: 'var(--vio-bg-secondary)', borderRadius: 'var(--vio-radius-lg)', padding: '16px', border: '1px solid var(--vio-border)', textAlign: 'center' }}
          >
            <s.icon size={18} color={s.color} style={{ marginBottom: '6px' }} />
            <div style={{ color: s.color, fontSize: '22px', fontWeight: 700 }}>{s.value}</div>
            <div style={{ color: 'var(--vio-text-dim)', fontSize: '11px', marginTop: '2px' }}>{s.label}</div>
          </motion.div>
        ))}
      </div>

      {/* Cross-check Results */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
        {crossChecks.map((c, i) => {
          const cfg = levelConfig[c.level];
          const LevelIcon = cfg.icon;

          return (
            <motion.div
              key={c.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.15 + i * 0.05 }}
              style={{
                background: 'var(--vio-bg-secondary)',
                borderRadius: 'var(--vio-radius-lg)',
                padding: '18px 22px',
                border: '1px solid var(--vio-border)',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '10px' }}>
                <div style={{ display: 'flex', alignItems: 'flex-start', gap: '10px', flex: 1 }}>
                  <LevelIcon size={18} color={cfg.color} style={{ flexShrink: 0, marginTop: '2px' }} />
                  <div style={{ color: 'var(--vio-text-primary)', fontSize: '14px', fontWeight: 600 }}>
                    "{c.query}"
                  </div>
                </div>
                <div style={{
                  padding: '4px 12px', borderRadius: '8px', marginLeft: '12px',
                  background: cfg.bg, display: 'flex', alignItems: 'center', gap: '4px',
                }}>
                  <Percent size={12} color={cfg.color} />
                  <span style={{ color: cfg.color, fontSize: '13px', fontWeight: 700 }}>{c.concordanceScore}%</span>
                </div>
              </div>

              <p style={{ color: 'var(--vio-text-secondary)', fontSize: '12px', margin: '0 0 10px', paddingLeft: '28px' }}>
                {c.verdict}
              </p>

              <div style={{ display: 'flex', gap: '6px', paddingLeft: '28px', flexWrap: 'wrap' }}>
                {c.models.map(m => (
                  <span key={m} style={{
                    background: 'var(--vio-bg-tertiary)', padding: '3px 10px', borderRadius: '6px',
                    color: 'var(--vio-text-dim)', fontSize: '10px', border: '1px solid var(--vio-border)',
                  }}>
                    <Brain size={10} style={{ verticalAlign: 'middle', marginRight: '3px' }} />
                    {m}
                  </span>
                ))}
                <span style={{ color: 'var(--vio-text-dim)', fontSize: '10px', marginLeft: 'auto', alignSelf: 'center' }}>
                  {new Date(c.timestamp).toLocaleString('it-IT', { hour: '2-digit', minute: '2-digit', day: '2-digit', month: 'short' })}
                </span>
              </div>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
