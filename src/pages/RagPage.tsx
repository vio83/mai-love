// VIO 83 AI ORCHESTRA — RAG Knowledge Base: Biblioteca Digitale
import { motion } from 'framer-motion';
import { Award, BookOpen, Clock, Database, FolderOpen, Search, Upload, Zap } from 'lucide-react';
import { useState } from 'react';

const ragSources = [
  { id: '1', name: 'ArXiv Papers (CS & AI)', docs: 4230, status: 'indexed' as const, quality: 'gold' as const, icon: '📄', category: 'Informatica' },
  { id: '2', name: 'Documentazione Ufficiale', docs: 2890, status: 'indexed' as const, quality: 'gold' as const, icon: '📚', category: 'Tech Docs' },
  { id: '3', name: 'Stack Overflow (Top Answers)', docs: 1560, status: 'indexing' as const, quality: 'silver' as const, icon: '💬', category: 'Q&A' },
  { id: '4', name: 'GitHub Repos (Top 1K)', docs: 890, status: 'queued' as const, quality: 'silver' as const, icon: '🐙', category: 'Code' },
  { id: '5', name: 'Wikipedia Scienze', docs: 3200, status: 'indexed' as const, quality: 'bronze' as const, icon: '🌐', category: 'Enciclopedia' },
  { id: '6', name: 'Documenti Locali', docs: 156, status: 'indexed' as const, quality: 'gold' as const, icon: '🏠', category: 'Privato' },
  { id: '7', name: 'Nature + Science Papers', docs: 780, status: 'queued' as const, quality: 'gold' as const, icon: '🔬', category: 'Scienze' },
  { id: '8', name: 'Libri Tecnici (O\'Reilly)', docs: 340, status: 'indexed' as const, quality: 'silver' as const, icon: '📕', category: 'Libri' },
];

const qualityConfig = {
  gold: { label: 'Gold', color: '#FBB924', desc: 'Peer-reviewed, documentazione ufficiale' },
  silver: { label: 'Silver', color: '#94A3B8', desc: 'Fonti affidabili, non peer-reviewed' },
  bronze: { label: 'Bronze', color: '#D97706', desc: 'Community-sourced, verificato' },
  unverified: { label: 'N/V', color: '#666', desc: 'Non ancora verificato' },
};

const statusConfig = {
  indexed: { label: '✓ Indicizzato', color: 'var(--vio-green)', bg: 'rgba(0,255,0,0.1)' },
  indexing: { label: '⟳ Indicizzando...', color: 'var(--vio-cyan)', bg: 'rgba(0,255,255,0.1)' },
  queued: { label: '⏳ In Coda', color: 'var(--vio-text-dim)', bg: 'var(--vio-bg-tertiary)' },
  error: { label: '✕ Errore', color: 'var(--vio-red)', bg: 'rgba(255,50,50,0.1)' },
};

export default function RagPage() {
  const [searchQuery, setSearchQuery] = useState('');

  const totalDocs = ragSources.reduce((a, b) => a + b.docs, 0);
  const targetDocs = 100000;
  const progressPct = (totalDocs / targetDocs) * 100;
  const normalizedQuery = searchQuery.trim().toLowerCase();
  const filteredSources = ragSources.filter(source => {
    if (!normalizedQuery) return true;

    return [source.name, source.category, source.quality, source.status]
      .join(' ')
      .toLowerCase()
      .includes(normalizedQuery);
  });

  return (
    <div style={{ padding: '28px 32px', overflowY: 'auto', height: '100%' }}>
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
        <h1 style={{ fontSize: '26px', fontWeight: 700, color: 'var(--vio-text-primary)', margin: '0 0 4px', letterSpacing: '-0.5px' }}>
          RAG Knowledge Base
        </h1>
        <p style={{ color: 'var(--vio-text-dim)', fontSize: '13px', margin: '0 0 28px' }}>
          Retrieval-Augmented Generation con fonti certificate — ChromaDB + SQLite FTS5
        </p>
      </motion.div>

      {/* Stats */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '14px', marginBottom: '24px' }}>
        {[
          { icon: BookOpen, label: 'Documenti', value: totalDocs.toLocaleString(), color: 'var(--vio-green)' },
          { icon: Database, label: 'Embedding Vettoriali', value: '2.1M', color: 'var(--vio-cyan)' },
          { icon: FolderOpen, label: 'Dimensione Index', value: '4.7 GB', color: 'var(--vio-magenta)' },
          { icon: Zap, label: 'Retrieval Medio', value: '47ms', color: 'var(--vio-yellow)' },
        ].map((s, i) => (
          <motion.div key={s.label} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.05 }}
            style={{ background: 'var(--vio-bg-secondary)', borderRadius: 'var(--vio-radius-lg)', padding: '16px', border: '1px solid var(--vio-border)', textAlign: 'center' }}
          >
            <s.icon size={20} color={s.color} style={{ marginBottom: '6px' }} />
            <div style={{ color: 'var(--vio-text-primary)', fontSize: '20px', fontWeight: 700 }}>{s.value}</div>
            <div style={{ color: 'var(--vio-text-dim)', fontSize: '11px', marginTop: '2px' }}>{s.label}</div>
          </motion.div>
        ))}
      </div>

      {/* Search */}
      <div style={{ display: 'flex', gap: '10px', marginBottom: '20px' }}>
        <div style={{ flex: 1, position: 'relative' }}>
          <Search size={16} style={{ position: 'absolute', left: '12px', top: '10px', color: 'var(--vio-text-dim)' }} />
          <input
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            placeholder="Cerca nella Knowledge Base..."
            style={{
              width: '100%', padding: '10px 10px 10px 36px', borderRadius: 'var(--vio-radius)',
              border: '1px solid var(--vio-border)', background: 'var(--vio-bg-secondary)',
              color: 'var(--vio-text-primary)', fontSize: '13px', outline: 'none',
            }}
          />
        </div>
        <button style={{
          background: 'var(--vio-bg-secondary)', border: '1px solid var(--vio-border)',
          borderRadius: 'var(--vio-radius)', padding: '10px 16px', color: 'var(--vio-green)',
          cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px', fontSize: '13px',
        }}>
          <Upload size={14} /> Importa
        </button>
      </div>

      {/* Quality Legend */}
      <div style={{ display: 'flex', gap: '16px', marginBottom: '16px' }}>
        {Object.entries(qualityConfig).map(([key, cfg]) => (
          <div key={key} style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Award size={12} color={cfg.color} />
            <span style={{ color: 'var(--vio-text-dim)', fontSize: '11px' }}>{cfg.label}: {cfg.desc}</span>
          </div>
        ))}
      </div>

      {/* Sources List */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginBottom: '24px' }}>
        {filteredSources.length === 0 && (
          <div
            style={{
              background: 'var(--vio-bg-secondary)',
              borderRadius: 'var(--vio-radius)',
              padding: '18px',
              border: '1px solid var(--vio-border)',
              color: 'var(--vio-text-dim)',
              fontSize: '13px',
            }}
          >
            Nessuna fonte trovata per <strong style={{ color: 'var(--vio-text-primary)' }}>{searchQuery}</strong>.
          </div>
        )}
        {filteredSources.map((s, i) => {
          const qcfg = qualityConfig[s.quality];
          const scfg = statusConfig[s.status];
          return (
            <motion.div
              key={s.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.2 + i * 0.04 }}
              style={{
                background: 'var(--vio-bg-secondary)', borderRadius: 'var(--vio-radius)',
                padding: '14px 18px', border: '1px solid var(--vio-border)',
                display: 'flex', alignItems: 'center', gap: '14px',
              }}
            >
              <span style={{ fontSize: '26px' }}>{s.icon}</span>
              <div style={{ flex: 1 }}>
                <div style={{ color: 'var(--vio-text-primary)', fontSize: '14px', fontWeight: 600 }}>{s.name}</div>
                <div style={{ display: 'flex', gap: '10px', marginTop: '3px' }}>
                  <span style={{ color: 'var(--vio-text-dim)', fontSize: '11px' }}>{s.docs.toLocaleString()} documenti</span>
                  <span style={{ color: 'var(--vio-text-dim)', fontSize: '11px' }}>•</span>
                  <span style={{ color: 'var(--vio-text-dim)', fontSize: '11px' }}>{s.category}</span>
                </div>
              </div>
              <span style={{
                padding: '3px 10px', borderRadius: '6px', fontSize: '10px', fontWeight: 700,
                background: `${qcfg.color}22`, color: qcfg.color, border: `1px solid ${qcfg.color}40`,
                textTransform: 'uppercase',
              }}>
                {qcfg.label}
              </span>
              <span style={{
                padding: '3px 12px', borderRadius: '6px', fontSize: '10px', fontWeight: 600,
                background: scfg.bg, color: scfg.color,
              }}>
                {scfg.label}
              </span>
            </motion.div>
          );
        })}
      </div>

      {/* Progress to 100K */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.6 }}
        style={{
          background: 'var(--vio-bg-secondary)', borderRadius: 'var(--vio-radius-lg)',
          padding: '20px 24px', border: '1px solid var(--vio-border)',
        }}
      >
        <h3 style={{ color: 'var(--vio-text-primary)', margin: '0 0 12px', fontSize: '14px', fontWeight: 600 }}>
          <Clock size={14} style={{ verticalAlign: 'middle', marginRight: '6px', color: 'var(--vio-green)' }} />
          Progresso Knowledge Base
        </h3>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{ flex: 1, height: '12px', background: 'var(--vio-bg-tertiary)', borderRadius: '6px', overflow: 'hidden' }}>
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${progressPct}%` }}
              transition={{ duration: 1.5 }}
              style={{
                height: '100%', borderRadius: '6px',
                background: 'linear-gradient(90deg, var(--vio-green), var(--vio-cyan))',
              }}
            />
          </div>
          <span style={{ color: 'var(--vio-text-primary)', fontSize: '13px', fontWeight: 700, whiteSpace: 'nowrap' }}>
            {totalDocs.toLocaleString()} / {targetDocs.toLocaleString()}
          </span>
        </div>
        <p style={{ color: 'var(--vio-text-dim)', fontSize: '12px', marginTop: '8px' }}>
          Target: 100K documenti verificati su 42 categorie di conoscenza (1,082 sotto-discipline)
        </p>
      </motion.div>
    </div>
  );
}
