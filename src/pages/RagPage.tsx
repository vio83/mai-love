// VIO 83 AI ORCHESTRA — RAG Knowledge Base: Biblioteca Digitale
import { motion } from 'framer-motion';
import { Award, BookOpen, Clock, Database, FolderOpen, Search, Upload, Zap } from 'lucide-react';
import { Loader2 } from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';
import { useI18n } from '../hooks/useI18n';

interface KBSource {
  id: string;
  name: string;
  docs: number;
  status: 'indexed' | 'indexing' | 'queued' | 'error';
  quality: 'gold' | 'silver' | 'bronze' | 'unverified';
  icon: string;
  category: string;
}

interface KBStats {
  total_documents?: number;
  total_chunks?: number;
  index_size_bytes?: number;
  avg_retrieval_ms?: number;
  sources?: KBSource[];
  status?: string;
}

const FALLBACK_SOURCES: KBSource[] = [
  {
    id: '1',
    name: 'Documenti Locali',
    docs: 0,
    status: 'queued',
    quality: 'unverified',
    icon: '🏠',
    category: 'Privato',
  },
];

export default function RagPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [sources, setSources] = useState<KBSource[]>([]);
  const [stats, setStats] = useState<KBStats>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { t } = useI18n();

  const fetchKBStats = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const [kbRes, ragRes] = await Promise.allSettled([
        fetch('http://localhost:4000/kb/stats'),
        fetch('http://localhost:4000/rag/stats'),
      ]);

      let kbData: KBStats = {};
      if (kbRes.status === 'fulfilled' && kbRes.value.ok) {
        kbData = (await kbRes.value.json()) as KBStats;
      }

      let ragData: Record<string, unknown> = {};
      if (ragRes.status === 'fulfilled' && ragRes.value.ok) {
        ragData = (await ragRes.value.json()) as Record<string, unknown>;
      }

      const merged: KBStats = {
        total_documents:
          (kbData.total_documents ?? 0) +
          (typeof ragData.total_documents === 'number' ? ragData.total_documents : 0),
        total_chunks: kbData.total_chunks ?? 0,
        index_size_bytes: kbData.index_size_bytes ?? 0,
        avg_retrieval_ms: kbData.avg_retrieval_ms ?? 0,
        sources: kbData.sources ?? [],
        status: kbData.status ?? (ragData.status as string) ?? 'unknown',
      };

      setStats(merged);
      setSources(merged.sources?.length ? merged.sources : FALLBACK_SOURCES);
    } catch {
      setError('Backend non raggiungibile');
      setSources(FALLBACK_SOURCES);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchKBStats();
  }, [fetchKBStats]);

  const qualityConfig = {
    gold: { label: 'Gold', color: '#FBB924', desc: t('ragPage.qualityGoldDesc') },
    silver: { label: 'Silver', color: '#94A3B8', desc: t('ragPage.qualitySilverDesc') },
    bronze: { label: 'Bronze', color: '#D97706', desc: t('ragPage.qualityBronzeDesc') },
    unverified: { label: 'N/V', color: '#666', desc: t('ragPage.qualityUnverifiedDesc') },
  };

  const statusConfig = {
    indexed: {
      label: t('ragPage.statusIndexed'),
      color: 'var(--vio-green)',
      bg: 'rgba(0,255,0,0.1)',
    },
    indexing: {
      label: t('ragPage.statusIndexing'),
      color: 'var(--vio-cyan)',
      bg: 'rgba(0,255,255,0.1)',
    },
    queued: {
      label: t('ragPage.statusQueued'),
      color: 'var(--vio-text-dim)',
      bg: 'var(--vio-bg-tertiary)',
    },
    error: { label: t('ragPage.statusError'), color: 'var(--vio-red)', bg: 'rgba(255,50,50,0.1)' },
  };

  const totalDocs = stats.total_documents ?? sources.reduce((a, b) => a + b.docs, 0);
  const targetDocs = 100000;
  const progressPct = (totalDocs / targetDocs) * 100;
  const normalizedQuery = searchQuery.trim().toLowerCase();
  const filteredSources = sources.filter((source) => {
    return [source.name, source.category, source.quality, source.status]
      .join(' ')
      .toLowerCase()
      .includes(normalizedQuery);
  });

  return (
    <div style={{ padding: '28px 32px', overflowY: 'auto', height: '100%' }}>
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
        <h1
          style={{
            fontSize: '26px',
            fontWeight: 700,
            color: 'var(--vio-text-primary)',
            margin: '0 0 4px',
            letterSpacing: '-0.5px',
          }}
        >
          {t('ragPage.title')}
        </h1>
        <p style={{ color: 'var(--vio-text-dim)', fontSize: '13px', margin: '0 0 28px' }}>
          {t('ragPage.subtitle')}
        </p>
      </motion.div>

      {/* Stats */}
      {loading ? (
        <div style={{ display: 'flex', justifyContent: 'center', padding: '32px' }}>
          <Loader2 size={24} color="var(--vio-green)" style={{ animation: 'spin 1s linear infinite' }} />
        </div>
      ) : error ? (
        <div style={{
          background: 'rgba(255,50,50,0.1)', border: '1px solid var(--vio-red)',
          borderRadius: 'var(--vio-radius)', padding: '14px 18px', marginBottom: '24px',
          color: 'var(--vio-red)', fontSize: '13px',
        }}>
          ⚠️ {error}
        </div>
      ) : null}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(4, 1fr)',
          gap: '14px',
          marginBottom: '24px',
        }}
      >
        {[
          {
            icon: BookOpen,
            label: t('ragPage.documents'),
            value: totalDocs.toLocaleString(),
            color: 'var(--vio-green)',
          },
          {
            icon: Database,
            label: t('ragPage.embeddings'),
            value: stats.total_chunks ? `${(stats.total_chunks / 1000).toFixed(1)}K` : '—',
            color: 'var(--vio-cyan)',
          },
          {
            icon: FolderOpen,
            label: t('ragPage.indexSize'),
            value: stats.index_size_bytes
              ? `${(stats.index_size_bytes / (1024 * 1024 * 1024)).toFixed(1)} GB`
              : '—',
            color: 'var(--vio-magenta)',
          },
          {
            icon: Zap,
            label: t('ragPage.avgRetrieval'),
            value: stats.avg_retrieval_ms ? `${stats.avg_retrieval_ms}ms` : '—',
            color: 'var(--vio-yellow)',
          },
        ].map((s, i) => (
          <motion.div
            key={s.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.05 }}
            style={{
              background: 'var(--vio-bg-secondary)',
              borderRadius: 'var(--vio-radius-lg)',
              padding: '16px',
              border: '1px solid var(--vio-border)',
              textAlign: 'center',
            }}
          >
            <s.icon size={20} color={s.color} style={{ marginBottom: '6px' }} />
            <div style={{ color: 'var(--vio-text-primary)', fontSize: '20px', fontWeight: 700 }}>
              {s.value}
            </div>
            <div style={{ color: 'var(--vio-text-dim)', fontSize: '11px', marginTop: '2px' }}>
              {s.label}
            </div>
          </motion.div>
        ))}
      </div>

      {/* Search */}
      <div style={{ display: 'flex', gap: '10px', marginBottom: '20px' }}>
        <div style={{ flex: 1, position: 'relative' }}>
          <Search
            size={16}
            style={{
              position: 'absolute',
              left: '12px',
              top: '10px',
              color: 'var(--vio-text-dim)',
            }}
          />
          <input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder={t('ragPage.searchPlaceholder')}
            style={{
              width: '100%',
              padding: '10px 10px 10px 36px',
              borderRadius: 'var(--vio-radius)',
              border: '1px solid var(--vio-border)',
              background: 'var(--vio-bg-secondary)',
              color: 'var(--vio-text-primary)',
              fontSize: '13px',
              outline: 'none',
            }}
          />
        </div>
        <button
          style={{
            background: 'var(--vio-bg-secondary)',
            border: '1px solid var(--vio-border)',
            borderRadius: 'var(--vio-radius)',
            padding: '10px 16px',
            color: 'var(--vio-green)',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            fontSize: '13px',
          }}
        >
          <Upload size={14} /> {t('ragPage.import')}
        </button>
      </div>

      {/* Quality Legend */}
      <div style={{ display: 'flex', gap: '16px', marginBottom: '16px' }}>
        {Object.entries(qualityConfig).map(([key, cfg]) => (
          <div key={key} style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Award size={12} color={cfg.color} />
            <span style={{ color: 'var(--vio-text-dim)', fontSize: '11px' }}>
              {cfg.label}: {cfg.desc}
            </span>
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
            {t('ragPage.noResults')}{' '}
            <strong style={{ color: 'var(--vio-text-primary)' }}>{searchQuery}</strong>.
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
                background: 'var(--vio-bg-secondary)',
                borderRadius: 'var(--vio-radius)',
                padding: '14px 18px',
                border: '1px solid var(--vio-border)',
                display: 'flex',
                alignItems: 'center',
                gap: '14px',
              }}
            >
              <span style={{ fontSize: '26px' }}>{s.icon}</span>
              <div style={{ flex: 1 }}>
                <div
                  style={{ color: 'var(--vio-text-primary)', fontSize: '14px', fontWeight: 600 }}
                >
                  {s.name}
                </div>
                <div style={{ display: 'flex', gap: '10px', marginTop: '3px' }}>
                  <span style={{ color: 'var(--vio-text-dim)', fontSize: '11px' }}>
                    {s.docs.toLocaleString()} {t('ragPage.docsCount')}
                  </span>
                  <span style={{ color: 'var(--vio-text-dim)', fontSize: '11px' }}>•</span>
                  <span style={{ color: 'var(--vio-text-dim)', fontSize: '11px' }}>
                    {s.category}
                  </span>
                </div>
              </div>
              <span
                style={{
                  padding: '3px 10px',
                  borderRadius: '6px',
                  fontSize: '10px',
                  fontWeight: 700,
                  background: `${qcfg.color}22`,
                  color: qcfg.color,
                  border: `1px solid ${qcfg.color}40`,
                  textTransform: 'uppercase',
                }}
              >
                {qcfg.label}
              </span>
              <span
                style={{
                  padding: '3px 12px',
                  borderRadius: '6px',
                  fontSize: '10px',
                  fontWeight: 600,
                  background: scfg.bg,
                  color: scfg.color,
                }}
              >
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
          background: 'var(--vio-bg-secondary)',
          borderRadius: 'var(--vio-radius-lg)',
          padding: '20px 24px',
          border: '1px solid var(--vio-border)',
        }}
      >
        <h3
          style={{
            color: 'var(--vio-text-primary)',
            margin: '0 0 12px',
            fontSize: '14px',
            fontWeight: 600,
          }}
        >
          <Clock
            size={14}
            style={{ verticalAlign: 'middle', marginRight: '6px', color: 'var(--vio-green)' }}
          />
          {t('ragPage.progress')}
        </h3>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div
            style={{
              flex: 1,
              height: '12px',
              background: 'var(--vio-bg-tertiary)',
              borderRadius: '6px',
              overflow: 'hidden',
            }}
          >
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${progressPct}%` }}
              transition={{ duration: 1.5 }}
              style={{
                height: '100%',
                borderRadius: '6px',
                background: 'linear-gradient(90deg, var(--vio-green), var(--vio-cyan))',
              }}
            />
          </div>
          <span
            style={{
              color: 'var(--vio-text-primary)',
              fontSize: '13px',
              fontWeight: 700,
              whiteSpace: 'nowrap',
            }}
          >
            {totalDocs.toLocaleString()} / {targetDocs.toLocaleString()}
          </span>
        </div>
        <p style={{ color: 'var(--vio-text-dim)', fontSize: '12px', marginTop: '8px' }}>
          {t('ragPage.progressTarget')}
        </p>
      </motion.div>
    </div>
  );
}
