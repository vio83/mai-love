import { motion } from 'framer-motion';
import { Activity, AlertTriangle, Bot, CheckCircle2, CircleAlert, Clock3, Cpu, Gauge, Globe, Link2, PlayCircle, Power, RefreshCw, ShieldCheck, Wifi } from 'lucide-react';
import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  ERROR_RATE_WINDOW_MINUTES,
  getRuntimeAutopilotState,
  runRuntimeOptimizationTick,
  type RuntimeAutopilotState,
  type RuntimeTarget,
  setRuntimeTargetAutoOptimize,
  setRuntimeTickInterval
} from '../runtime/runtimeAutopilot';
import { useAppStore } from '../stores/appStore';

function latencyColor(ms: number, reachable: boolean) {
  if (!reachable || ms === 0) return 'var(--vio-text-dim)';
  if (ms < 250) return 'var(--vio-green)';
  if (ms < 900) return 'var(--vio-yellow)';
  return 'var(--vio-red)';
}

const AGENT_REPLICAS = [
  { id: 'router', name: 'AI Router Replica', stack: 'LiteLLM + Local Proxy', mode: 'local' },
  { id: 'validator', name: 'Cross-Check Replica', stack: 'Multi-model consensus', mode: 'local' },
  { id: 'automator', name: 'Automation Replica', stack: 'n8n cron/webhook orchestration', mode: 'local-proxy' },
  { id: 'legal', name: 'LegalRoom Replica', stack: 'Context + workflow pipeline', mode: 'local-proxy' },
  { id: 'openclaw', name: 'OpenClaw Tooling Replica', stack: 'Agent tools + task ops', mode: 'local-proxy' },
];

const statusColor: Record<RuntimeTarget['status'], string> = {
  online: 'var(--vio-green)',
  degraded: 'var(--vio-yellow)',
  offline: 'var(--vio-red)',
};

function formatInterval(ms: number) {
  if (ms >= 3_600_000) return `${Math.round(ms / 3_600_000)}h`;
  if (ms >= 60_000) return `${Math.round(ms / 60_000)}m`;
  return `${Math.round(ms / 1000)}s`;
}

interface ClaudeExtensionsPayload {
  status: string;
  count: number;
  detected_at?: string;
  preferences: Record<string, unknown>;
  extensions: { id: string; name: string; version: string; description: string; tool_count: number; tools: string[] }[];
}

interface ClaudeActivityPayload {
  status: string;
  detected_at?: string;
  sessions?: {
    workspace_count: number;
    session_count: number;
    indexed_sessions: number;
    audit_files: number;
    latest_session_id?: string | null;
    latest_session_updated_at?: string | null;
  };
}

interface KnowledgeRegistryPayload {
  status: string;
  version: string;
  domains: Array<{
    id: string;
    name: string;
    subdomains: string[];
    trusted_sources: string[];
    reliability?: {
      id: string;
      name: string;
      coverage_score: number;
      freshness_score: number;
      watch_health_score: number;
      reliability_score: number;
      status: 'high' | 'medium' | 'low';
    };
  }>;
  coverage: {
    domain_count: number;
    subdomain_count: number;
    trusted_source_count: number;
    trusted_sources: string[];
  };
  scores?: {
    domains: Array<{
      id: string;
      name: string;
      coverage_score: number;
      freshness_score: number;
      watch_health_score: number;
      reliability_score: number;
      status: 'high' | 'medium' | 'low';
    }>;
    average_reliability: number;
    minimum_required: number;
  };
  policy?: {
    strict_evidence_mode: boolean;
    refresh_interval_hours: number;
    minimum_domain_score: number;
    last_policy_update_at?: string | null;
    next_scheduled_refresh_at?: string | null;
  };
  legal_watch_jurisdictions: string[];
  last_generated_at: string;
}

interface KnowledgeWatchPayload {
  status: string;
  jurisdiction: string;
  sources: Array<{ name: string; url: string; scope: string }>;
  refresh_state?: {
    last_refresh_at?: string | null;
    jurisdiction?: string | null;
    source_count?: number;
    reachable_count?: number;
    fail_count?: number;
  };
}

interface DomainScoresPayload {
  status: string;
  scores: Array<{
    id: string;
    name: string;
    coverage_score: number;
    freshness_score: number;
    watch_health_score: number;
    reliability_score: number;
    status: 'high' | 'medium' | 'low';
  }>;
  average_reliability: number;
  minimum_required: number;
  strict_evidence_mode: boolean;
  detected_at?: string;
}

interface KnowledgeSchedulerPayload {
  status: string;
  scheduler: {
    refresh_interval_hours: number;
    next_scheduled_refresh_at?: string | null;
    last_refresh_at?: string | null;
  };
  policy: {
    strict_evidence_mode: boolean;
    minimum_domain_score: number;
    last_policy_update_at?: string | null;
  };
}

function computeErrorRate(errors: { ts: string }[], minutes: number) {
  const windowMs = minutes * 60 * 1000;
  const now = Date.now();
  const inWindow = errors.filter((err) => now - new Date(err.ts).getTime() <= windowMs).length;
  const perHour = Math.round(((inWindow / Math.max(minutes, 1)) * 60) * 10) / 10;
  return { count: inWindow, perHour };
}

function buildSparklinePoints(values: number[], width = 120, height = 26) {
  if (values.length === 0) return '';
  if (values.length === 1) {
    const y = Math.round(height * 0.6);
    return `0,${y} ${width},${y}`;
  }

  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = Math.max(1, max - min);

  return values
    .map((value, index) => {
      const x = (index / (values.length - 1)) * width;
      const y = height - ((value - min) / range) * (height - 4) - 2;
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(' ');
}

function formatAuditTimestamp(iso: string) {
  return iso.replace(/[:.]/g, '-');
}

type ToastKind = 'success' | 'error' | 'info';

interface ToastState {
  message: string;
  kind: ToastKind;
}

function getScoreSemantic(score: number) {
  if (score >= 85) {
    return {
      label: 'ALTO',
      color: 'var(--vio-green)',
      border: 'rgba(0,255,0,0.35)',
      background: 'rgba(0,255,0,0.12)',
    };
  }
  if (score >= 70) {
    return {
      label: 'MEDIO',
      color: 'var(--vio-yellow)',
      border: 'rgba(255,255,0,0.35)',
      background: 'rgba(255,255,0,0.12)',
    };
  }
  return {
    label: 'BASSO',
    color: 'var(--vio-red)',
    border: 'rgba(255,60,60,0.35)',
    background: 'rgba(255,60,60,0.12)',
  };
}

export default function OrchestraRuntimePage() {
  const [state, setState] = useState<RuntimeAutopilotState>(() => getRuntimeAutopilotState());
  const [runningTick, setRunningTick] = useState(false);
  const [claudeExts, setClaudeExts] = useState<ClaudeExtensionsPayload | null>(null);
  const [claudeActivity, setClaudeActivity] = useState<ClaudeActivityPayload | null>(null);
  const [knowledgeRegistry, setKnowledgeRegistry] = useState<KnowledgeRegistryPayload | null>(null);
  const [knowledgeWatch, setKnowledgeWatch] = useState<KnowledgeWatchPayload | null>(null);
  const [knowledgeScores, setKnowledgeScores] = useState<DomainScoresPayload | null>(null);
  const [knowledgeScheduler, setKnowledgeScheduler] = useState<KnowledgeSchedulerPayload | null>(null);
  const [refreshingKnowledge, setRefreshingKnowledge] = useState(false);
  const [updatingKnowledgePolicy, setUpdatingKnowledgePolicy] = useState(false);
  const [exportingAudit, setExportingAudit] = useState(false);
  const [toast, setToast] = useState<ToastState | null>(null);
  const { settings, activateFullOrchestration, updateSettings } = useAppStore();

  const notify = (message: string, kind: ToastKind = 'success') => {
    setToast({ message, kind });
  };

  const syncStrictWithStore = useCallback((strictValue: boolean) => {
    const current = useAppStore.getState().settings.orchestrator;
    if ((current.strictEvidenceMode ?? true) !== strictValue) {
      updateSettings({
        orchestrator: {
          ...current,
          strictEvidenceMode: strictValue,
        },
      });
    }
  }, [updateSettings]);

  useEffect(() => {
    if (!toast) return;
    const id = window.setTimeout(() => setToast(null), 2600);
    return () => window.clearTimeout(id);
  }, [toast]);

  useEffect(() => {
    const refresh = () => setState(getRuntimeAutopilotState());
    const id = window.setInterval(refresh, 3000);
    return () => window.clearInterval(id);
  }, []);

  useEffect(() => {
    let cancelled = false;

    const fetchJson = async (url: string) => {
      try {
        const response = await fetch(url);
        if (!response.ok) return null;
        return await response.json();
      } catch {
        return null;
      }
    };

    const bootstrap = async () => {
      const [exts, activity, registry, watch, scores, scheduler] = await Promise.all([
        fetchJson('http://localhost:4000/claude/extensions'),
        fetchJson('http://localhost:4000/claude/activity-summary'),
        fetchJson('http://localhost:4000/knowledge/registry'),
        fetchJson('http://localhost:4000/knowledge/legal-watch?jurisdiction=all'),
        fetchJson('http://localhost:4000/knowledge/domain-scores'),
        fetchJson('http://localhost:4000/knowledge/scheduler'),
      ]);

      if (cancelled) return;

      if (exts?.status === 'ok') setClaudeExts(exts as ClaudeExtensionsPayload);
      if (activity?.status === 'ok') setClaudeActivity(activity as ClaudeActivityPayload);
      if (registry?.status === 'ok') setKnowledgeRegistry(registry as KnowledgeRegistryPayload);
      if (watch?.status === 'ok') setKnowledgeWatch(watch as KnowledgeWatchPayload);
      if (scores?.status === 'ok') setKnowledgeScores(scores as DomainScoresPayload);
      if (scheduler?.status === 'ok') setKnowledgeScheduler(scheduler as KnowledgeSchedulerPayload);

      const strictFromBackend = scheduler?.policy?.strict_evidence_mode ?? scores?.strict_evidence_mode;
      if (typeof strictFromBackend === 'boolean') {
        syncStrictWithStore(strictFromBackend);
      }
    };

    void bootstrap();
    return () => { cancelled = true; };
  }, [updateSettings, syncStrictWithStore]);

  const avgOptimization = useMemo(() => {
    if (state.targets.length === 0) return 0;
    const total = state.targets.reduce((sum, target) => sum + target.optimizationScore, 0);
    return Math.round((total / state.targets.length) * 10) / 10;
  }, [state.targets]);

  const globalErrorRate30m = useMemo(() => {
    const total = state.targets.reduce((sum, target) => sum + computeErrorRate(target.errorHistory ?? [], ERROR_RATE_WINDOW_MINUTES).count, 0);
    const perHour = Math.round(((total / Math.max(ERROR_RATE_WINDOW_MINUTES, 1)) * 60) * 10) / 10;
    return { total, perHour };
  }, [state.targets]);

  const onlineCount = state.targets.filter((target) => target.status === 'online').length;
  const strictEvidenceMode = settings.orchestrator.strictEvidenceMode ?? true;
  const orchestrationAllOn = settings.orchestrator.autoRouting && settings.orchestrator.crossCheckEnabled && settings.orchestrator.ragEnabled;

  const runNow = async () => {
    if (runningTick) return;
    setRunningTick(true);
    try {
      const next = await runRuntimeOptimizationTick();
      setState(next);
    } finally {
      setRunningTick(false);
    }
  };

  const activateAll = async () => {
    activateFullOrchestration();
    await runNow();
  };

  const updateTickInterval = (hours: number) => {
    const next = setRuntimeTickInterval(hours * 60 * 60 * 1000);
    setState(next);
  };

  const toggleAutoOptimize = (target: RuntimeTarget) => {
    const next = setRuntimeTargetAutoOptimize(target.id, !target.autoOptimize);
    setState(next);
  };

  const refreshKnowledgeStack = async () => {
    if (refreshingKnowledge) return;
    setRefreshingKnowledge(true);
    try {
      await fetch('http://localhost:4000/knowledge/refresh?jurisdiction=all', { method: 'POST' });

      const [watch, registry] = await Promise.all([
        fetch('http://localhost:4000/knowledge/legal-watch?jurisdiction=all').then((r) => r.ok ? r.json() : null).catch(() => null),
        fetch('http://localhost:4000/knowledge/registry').then((r) => r.ok ? r.json() : null).catch(() => null),
      ]);

      const [scores, scheduler] = await Promise.all([
        fetch('http://localhost:4000/knowledge/domain-scores').then((r) => r.ok ? r.json() : null).catch(() => null),
        fetch('http://localhost:4000/knowledge/scheduler').then((r) => r.ok ? r.json() : null).catch(() => null),
      ]);

      if (watch?.status === 'ok') setKnowledgeWatch(watch as KnowledgeWatchPayload);
      if (registry?.status === 'ok') setKnowledgeRegistry(registry as KnowledgeRegistryPayload);
      if (scores?.status === 'ok') setKnowledgeScores(scores as DomainScoresPayload);
      if (scheduler?.status === 'ok') {
        setKnowledgeScheduler(scheduler as KnowledgeSchedulerPayload);
        syncStrictWithStore(Boolean(scheduler.policy.strict_evidence_mode));
      }

      notify('Knowledge stack aggiornato con successo', 'success');
    } catch {
      notify('Aggiornamento knowledge stack fallito', 'error');
    } finally {
      setRefreshingKnowledge(false);
    }
  };

  const updateKnowledgeScheduler = async (hours: number) => {
    if (updatingKnowledgePolicy) return;
    setUpdatingKnowledgePolicy(true);
    try {
      const response = await fetch(`http://localhost:4000/knowledge/scheduler?refresh_interval_hours=${hours}`, {
        method: 'PUT',
      });
      if (response.ok) {
        const scheduler = await fetch('http://localhost:4000/knowledge/scheduler')
          .then((r) => r.ok ? r.json() : null)
          .catch(() => null);
        if (scheduler?.status === 'ok') {
          setKnowledgeScheduler(scheduler as KnowledgeSchedulerPayload);
          syncStrictWithStore(Boolean(scheduler.policy.strict_evidence_mode));
          notify(`Scheduler aggiornato: refresh ogni ${hours}h`, 'success');
        }
      } else {
        notify('Impossibile aggiornare lo scheduler', 'error');
      }
    } catch {
      notify('Errore rete durante update scheduler', 'error');
    } finally {
      setUpdatingKnowledgePolicy(false);
    }
  };

  const updateKnowledgePolicy = async (nextStrict: boolean, nextMinScore: number) => {
    if (updatingKnowledgePolicy) return;
    setUpdatingKnowledgePolicy(true);
    try {
      const response = await fetch(
        `http://localhost:4000/knowledge/policy?strict_evidence_mode=${nextStrict}&minimum_domain_score=${nextMinScore}`,
        { method: 'PUT' },
      );

      if (response.ok) {
        const [scores, scheduler, registry] = await Promise.all([
          fetch('http://localhost:4000/knowledge/domain-scores').then((r) => r.ok ? r.json() : null).catch(() => null),
          fetch('http://localhost:4000/knowledge/scheduler').then((r) => r.ok ? r.json() : null).catch(() => null),
          fetch('http://localhost:4000/knowledge/registry').then((r) => r.ok ? r.json() : null).catch(() => null),
        ]);

        if (scores?.status === 'ok') setKnowledgeScores(scores as DomainScoresPayload);
        if (scheduler?.status === 'ok') setKnowledgeScheduler(scheduler as KnowledgeSchedulerPayload);
        if (registry?.status === 'ok') setKnowledgeRegistry(registry as KnowledgeRegistryPayload);

        syncStrictWithStore(nextStrict);
        notify(`Policy aggiornata: strict ${nextStrict ? 'ON' : 'OFF'}, soglia ≥ ${nextMinScore}`, 'success');
      } else {
        notify('Aggiornamento policy fallito', 'error');
      }
    } catch {
      notify('Errore rete durante update policy', 'error');
    } finally {
      setUpdatingKnowledgePolicy(false);
    }
  };

  const exportRuntimeAudit = async () => {
    if (exportingAudit) return;
    setExportingAudit(true);

    try {
      const nowIso = new Date().toISOString();

      const [coreStatus, freshActivity] = await Promise.all([
        fetch('http://localhost:4000/core/status').then((r) => r.ok ? r.json() : null).catch(() => null),
        fetch('http://localhost:4000/claude/activity-summary').then((r) => r.ok ? r.json() : null).catch(() => null),
      ]);

      const runtimeDerived = state.targets.map((target) => {
        const trendValues = (target.latencyTrend ?? []).map((sample) => sample.reachable ? sample.latencyMs : Math.max(sample.latencyMs, 2200));
        const avgLatency20 = trendValues.length > 0
          ? Math.round((trendValues.reduce((sum, value) => sum + value, 0) / trendValues.length) * 10) / 10
          : 0;
        const errorRate30m = computeErrorRate(target.errorHistory ?? [], ERROR_RATE_WINDOW_MINUTES);

        return {
          id: target.id,
          name: target.name,
          avgLatency20,
          errorRate30m,
          trendPoints: trendValues.length,
        };
      });

      const payload = {
        generatedAt: nowIso,
        runtime: state,
        orchestratorSettings: settings.orchestrator,
        claudeExtensions: claudeExts,
        claudeActivity: (freshActivity?.status === 'ok' ? freshActivity : null) ?? claudeActivity,
        knowledgeRegistry,
        knowledgeWatch,
        coreStatus,
        derived: {
          globalErrorRate30m,
          runtimeDerived,
        },
      };

      const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `vio-runtime-audit-${formatAuditTimestamp(nowIso)}.json`;
      a.click();
      window.setTimeout(() => URL.revokeObjectURL(url), 1500);
    } finally {
      setExportingAudit(false);
    }
  };

  return (
    <div style={{ padding: '28px 32px', overflowY: 'auto', height: '100%' }}>
      {toast && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          style={{
            position: 'fixed',
            top: 16,
            right: 18,
            zIndex: 50,
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '10px 12px',
            borderRadius: '10px',
            border: toast.kind === 'success'
              ? '1px solid rgba(0,255,0,0.35)'
              : toast.kind === 'error'
                ? '1px solid rgba(255,60,60,0.35)'
                : '1px solid rgba(0,255,255,0.35)',
            background: toast.kind === 'success'
              ? 'rgba(0,255,0,0.12)'
              : toast.kind === 'error'
                ? 'rgba(255,60,60,0.12)'
                : 'rgba(0,255,255,0.12)',
            color: toast.kind === 'success'
              ? 'var(--vio-green)'
              : toast.kind === 'error'
                ? 'var(--vio-red)'
                : 'var(--vio-cyan)',
            fontSize: '12px',
            fontWeight: 600,
          }}
        >
          {toast.kind === 'success' ? <CheckCircle2 size={14} /> : <CircleAlert size={14} />}
          <span>{toast.message}</span>
        </motion.div>
      )}

      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
        <h1 style={{ fontSize: '26px', fontWeight: 700, color: 'var(--vio-text-primary)', margin: '0 0 4px', letterSpacing: '-0.5px' }}>
          VioAiOrchestra Runtime 360
        </h1>
        <p style={{ color: 'var(--vio-text-dim)', fontSize: '13px', margin: '0 0 24px' }}>
          Runtime operativo locale/proxy con autopilot di ottimizzazione per Ollama, OpenClaw, LegalRoom e n8n.
        </p>
      </motion.div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(170px, 1fr))', gap: '12px', marginBottom: '18px' }}>
        {[
          { icon: ShieldCheck, label: 'Target online', value: `${onlineCount}/${state.targets.length}`, color: 'var(--vio-green)' },
          { icon: Gauge, label: 'Score medio', value: `${avgOptimization}%`, color: 'var(--vio-cyan)' },
          { icon: AlertTriangle, label: `Errori ${ERROR_RATE_WINDOW_MINUTES}m`, value: `${globalErrorRate30m.total} (${globalErrorRate30m.perHour}/h)`, color: 'var(--vio-red)' },
          { icon: Clock3, label: 'Tick interval', value: formatInterval(state.tickIntervalMs), color: 'var(--vio-magenta)' },
          { icon: RefreshCw, label: 'Last optimization', value: new Date(state.lastOptimizationAt).toLocaleTimeString('it-IT', { hour: '2-digit', minute: '2-digit' }), color: 'var(--vio-yellow)' },
        ].map((item, index) => (
          <motion.div
            key={item.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.05 }}
            style={{
              background: 'var(--vio-bg-secondary)',
              borderRadius: 'var(--vio-radius-lg)',
              padding: '14px 16px',
              border: '1px solid var(--vio-border)',
              textAlign: 'center',
            }}
          >
            <item.icon size={16} color={item.color} style={{ marginBottom: '6px' }} />
            <div style={{ color: 'var(--vio-text-primary)', fontWeight: 700, fontSize: '20px' }}>{item.value}</div>
            <div style={{ color: 'var(--vio-text-dim)', fontSize: '11px', marginTop: '2px' }}>{item.label}</div>
          </motion.div>
        ))}
      </div>

      <div style={{ display: 'flex', gap: '10px', marginBottom: '20px', flexWrap: 'wrap' }}>
        <button
          onClick={activateAll}
          style={{
            border: `1px solid ${orchestrationAllOn ? 'var(--vio-green-dim)' : 'var(--vio-yellow)'}`,
            background: orchestrationAllOn ? 'rgba(0,255,0,0.12)' : 'rgba(255,255,0,0.08)',
            color: orchestrationAllOn ? 'var(--vio-green)' : 'var(--vio-yellow)',
            padding: '8px 14px',
            borderRadius: '8px',
            cursor: 'pointer',
            display: 'flex',
            gap: '6px',
            alignItems: 'center',
            fontSize: '12px',
            fontWeight: 700,
          }}
        >
          <Power size={14} /> {orchestrationAllOn ? 'STACK COMPLETO ATTIVO' : 'ATTIVA TUTTO SU ON'}
        </button>
        <button
          onClick={runNow}
          disabled={runningTick}
          style={{
            border: '1px solid var(--vio-green-dim)',
            background: 'rgba(0,255,0,0.08)',
            color: 'var(--vio-green)',
            padding: '8px 14px',
            borderRadius: '8px',
            cursor: runningTick ? 'not-allowed' : 'pointer',
            display: 'flex',
            gap: '6px',
            alignItems: 'center',
            fontSize: '12px',
            fontWeight: 600,
            opacity: runningTick ? 0.6 : 1,
          }}
        >
          <PlayCircle size={14} /> {runningTick ? 'Ottimizzazione in corso…' : 'Esegui ottimizzazione ora'}
        </button>
        <button
          onClick={exportRuntimeAudit}
          disabled={exportingAudit}
          style={{
            border: '1px solid rgba(99,102,241,0.45)',
            background: 'rgba(99,102,241,0.12)',
            color: '#a5b4fc',
            padding: '8px 14px',
            borderRadius: '8px',
            cursor: exportingAudit ? 'not-allowed' : 'pointer',
            display: 'flex',
            gap: '6px',
            alignItems: 'center',
            fontSize: '12px',
            fontWeight: 600,
            opacity: exportingAudit ? 0.65 : 1,
          }}
        >
          <Cpu size={14} /> {exportingAudit ? 'Export audit…' : 'Export JSON audit'}
        </button>
        <button
          onClick={refreshKnowledgeStack}
          disabled={refreshingKnowledge}
          style={{
            border: '1px solid rgba(0,255,255,0.35)',
            background: 'rgba(0,255,255,0.08)',
            color: 'var(--vio-cyan)',
            padding: '8px 14px',
            borderRadius: '8px',
            cursor: refreshingKnowledge ? 'not-allowed' : 'pointer',
            display: 'flex',
            gap: '6px',
            alignItems: 'center',
            fontSize: '12px',
            fontWeight: 600,
            opacity: refreshingKnowledge ? 0.65 : 1,
          }}
        >
          <Globe size={14} /> {refreshingKnowledge ? 'Aggiornamento fonti…' : 'Refresh Knowledge Stack'}
        </button>
        {[1, 6, 24].map((hours) => (
          <button
            key={hours}
            onClick={() => updateTickInterval(hours)}
            style={{
              border: `1px solid ${state.tickIntervalMs === hours * 60 * 60 * 1000 ? 'var(--vio-cyan)' : 'var(--vio-border)'}`,
              background: state.tickIntervalMs === hours * 60 * 60 * 1000 ? 'rgba(0,255,255,0.08)' : 'var(--vio-bg-secondary)',
              color: state.tickIntervalMs === hours * 60 * 60 * 1000 ? 'var(--vio-cyan)' : 'var(--vio-text-secondary)',
              padding: '8px 12px',
              borderRadius: '8px',
              cursor: 'pointer',
              fontSize: '12px',
            }}
          >
            Tick {hours}h
          </button>
        ))}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1.4fr 1fr', gap: '16px' }}>
        <div style={{ background: 'var(--vio-bg-secondary)', border: '1px solid var(--vio-border)', borderRadius: 'var(--vio-radius-lg)', padding: '18px' }}>
          <h3 style={{ color: 'var(--vio-text-primary)', margin: '0 0 12px', fontSize: '15px' }}>
            <Link2 size={14} style={{ verticalAlign: 'middle', marginRight: '6px' }} />
            Integrazioni runtime attive
          </h3>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {state.targets.map((target) => (
              <div
                key={target.id}
                style={{
                  border: '1px solid var(--vio-border)',
                  background: 'var(--vio-bg-tertiary)',
                  borderRadius: '10px',
                  padding: '12px',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
                  <span style={{ color: 'var(--vio-text-primary)', fontWeight: 600, fontSize: '13px', flex: 1 }}>{target.name}</span>
                  <span style={{ color: statusColor[target.status], fontSize: '11px', fontWeight: 700, textTransform: 'uppercase' }}>{target.status}</span>
                </div>
                <div style={{ color: 'var(--vio-text-dim)', fontSize: '11px', marginBottom: '6px' }}>
                  {target.mode} • {target.endpoint}
                </div>
                <div style={{ height: '6px', borderRadius: '999px', background: 'var(--vio-bg-primary)', overflow: 'hidden', marginBottom: '8px' }}>
                  <div
                    style={{
                      height: '100%',
                      width: `${target.optimizationScore}%`,
                      background: 'linear-gradient(90deg, var(--vio-cyan), var(--vio-green))',
                    }}
                  />
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  {(() => {
                    const semantic = getScoreSemantic(target.optimizationScore);
                    return (
                      <span
                        style={{
                          border: `1px solid ${semantic.border}`,
                          borderRadius: '999px',
                          padding: '2px 8px',
                          fontSize: '9px',
                          fontWeight: 700,
                          color: semantic.color,
                          background: semantic.background,
                        }}
                      >
                        {semantic.label}
                      </span>
                    );
                  })()}
                  <span style={{ color: 'var(--vio-text-dim)', fontSize: '10px', flex: 1 }}>
                    score: {target.optimizationScore}% • hb: {new Date(target.lastHeartbeat).toLocaleTimeString('it-IT', { hour: '2-digit', minute: '2-digit' })}
                  </span>
                  <button
                    onClick={() => toggleAutoOptimize(target)}
                    style={{
                      border: '1px solid var(--vio-border)',
                      borderRadius: '999px',
                      padding: '2px 8px',
                      fontSize: '10px',
                      cursor: 'pointer',
                      background: target.autoOptimize ? 'rgba(0,255,0,0.08)' : 'transparent',
                      color: target.autoOptimize ? 'var(--vio-green)' : 'var(--vio-text-dim)',
                    }}
                  >
                    {target.autoOptimize ? 'AUTO ON' : 'AUTO OFF'}
                  </button>
                </div>
                <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', marginTop: '8px' }}>
                  {target.capabilities.map((capability) => (
                    <span
                      key={capability}
                      style={{
                        border: '1px solid var(--vio-border)',
                        borderRadius: '999px',
                        padding: '2px 8px',
                        color: 'var(--vio-text-dim)',
                        fontSize: '10px',
                      }}
                    >
                      {capability}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>

        <div style={{ background: 'var(--vio-bg-secondary)', border: '1px solid var(--vio-border)', borderRadius: 'var(--vio-radius-lg)', padding: '18px' }}>
          <h3 style={{ color: 'var(--vio-text-primary)', margin: '0 0 12px', fontSize: '15px' }}>
            <Bot size={14} style={{ verticalAlign: 'middle', marginRight: '6px' }} />
            Repliche agenti locali
          </h3>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {AGENT_REPLICAS.map((replica) => (
              <div key={replica.id} style={{ border: '1px solid var(--vio-border)', borderRadius: '10px', padding: '10px', background: 'var(--vio-bg-tertiary)' }}>
                <div style={{ color: 'var(--vio-text-primary)', fontWeight: 600, fontSize: '12px' }}>{replica.name}</div>
                <div style={{ color: 'var(--vio-text-dim)', fontSize: '11px', marginTop: '3px' }}>{replica.stack}</div>
                <div style={{ color: 'var(--vio-cyan)', fontSize: '10px', marginTop: '4px', textTransform: 'uppercase' }}>{replica.mode}</div>
              </div>
            ))}
          </div>

          <p style={{ color: 'var(--vio-text-dim)', fontSize: '11px', lineHeight: 1.5, marginTop: '12px' }}>
            Ciclo continuo verificabile di monitoraggio e tuning — vedi Health Panel qui sotto per latenza e storico errori.
          </p>
        </div>
      </div>

      {/* ── Health Panel dettagliato ── */}
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        style={{ marginTop: '20px', background: 'var(--vio-bg-secondary)', border: '1px solid var(--vio-border)', borderRadius: 'var(--vio-radius-lg)', padding: '18px' }}
      >
        <h3 style={{ color: 'var(--vio-text-primary)', margin: '0 0 14px', fontSize: '15px', display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Activity size={14} /> Health Panel — Latenza & Storico Errori
        </h3>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(270px, 1fr))', gap: '12px' }}>
          {state.targets.map((target) => {
            const isOnline = target.status === 'online';
            const isOff = target.status === 'offline';
            const lColor = latencyColor(target.latencyMs, isOnline);
            const errors = target.errorHistory ?? [];
            const lastErrors = errors.slice(-5).reverse();
            const semantic = getScoreSemantic(target.optimizationScore);
            const trendValues = (target.latencyTrend ?? []).map((sample) => sample.reachable ? sample.latencyMs : Math.max(sample.latencyMs, 2200));
            const sparklinePoints = buildSparklinePoints(trendValues);
            const avgLatency20 = trendValues.length > 0
              ? Math.round((trendValues.reduce((sum, value) => sum + value, 0) / trendValues.length) * 10) / 10
              : 0;
            const errorRate30m = computeErrorRate(errors, ERROR_RATE_WINDOW_MINUTES);

            return (
              <div
                key={target.id}
                style={{
                  border: `1px solid ${isOnline ? 'rgba(0,255,136,0.2)' : isOff ? 'rgba(255,60,60,0.2)' : 'rgba(255,200,0,0.2)'}`,
                  borderRadius: '10px',
                  padding: '14px',
                  background: 'var(--vio-bg-tertiary)',
                }}
              >
                {/* Header */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                  <span style={{ color: 'var(--vio-text-primary)', fontWeight: 700, fontSize: '12px' }}>{target.name}</span>
                  <span
                    style={{
                      color: statusColor[target.status],
                      fontSize: '10px',
                      fontWeight: 700,
                      textTransform: 'uppercase',
                      border: `1px solid ${statusColor[target.status]}44`,
                      padding: '2px 7px',
                      borderRadius: '999px',
                    }}
                  >
                    {target.status}
                  </span>
                </div>

                {/* Latency metric */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '10px' }}>
                  <Wifi size={12} color={lColor} />
                  <span style={{ color: lColor, fontWeight: 700, fontSize: '20px', fontVariantNumeric: 'tabular-nums' }}>
                    {isOnline && target.latencyMs > 0 ? `${target.latencyMs}` : '—'}
                  </span>
                  {isOnline && target.latencyMs > 0 && (
                    <span style={{ color: 'var(--vio-text-dim)', fontSize: '11px' }}>ms</span>
                  )}
                  <span style={{ color: 'var(--vio-text-dim)', fontSize: '10px', marginLeft: 'auto' }}>
                    score: <span style={{ color: 'var(--vio-cyan)', fontWeight: 600 }}>{target.optimizationScore}%</span>
                  </span>
                  <span
                    style={{
                      marginLeft: '6px',
                      border: `1px solid ${semantic.border}`,
                      borderRadius: '999px',
                      padding: '2px 7px',
                      fontSize: '9px',
                      fontWeight: 700,
                      color: semantic.color,
                      background: semantic.background,
                    }}
                  >
                    {semantic.label}
                  </span>
                </div>

                {/* Latency bar */}
                <div style={{ height: '4px', borderRadius: '999px', background: 'var(--vio-bg-primary)', marginBottom: '10px', overflow: 'hidden' }}>
                  <div
                    style={{
                      height: '100%',
                      width: isOnline && target.latencyMs > 0 ? `${Math.min(100, (target.latencyMs / 2000) * 100)}%` : '0%',
                      background: `linear-gradient(90deg, ${lColor}, ${lColor}88)`,
                      transition: 'width 0.5s ease',
                    }}
                  />
                </div>

                {/* Trend latenza mini sparkline (20 tick) */}
                <div style={{ marginBottom: '10px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                    <span style={{ color: 'var(--vio-text-dim)', fontSize: '10px' }}>Trend latenza (20 tick)</span>
                    <span style={{ color: 'var(--vio-cyan)', fontSize: '10px' }}>avg20: {avgLatency20 || 0}ms</span>
                  </div>
                  <svg width="120" height="26" viewBox="0 0 120 26" role="img" aria-label={`Sparkline latenza ${target.name}`}>
                    <rect x="0" y="0" width="120" height="26" rx="4" fill="rgba(255,255,255,0.02)" />
                    {sparklinePoints ? (
                      <polyline
                        points={sparklinePoints}
                        fill="none"
                        stroke={lColor}
                        strokeWidth="2"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      />
                    ) : (
                      <line x1="6" y1="18" x2="114" y2="18" stroke="var(--vio-border)" strokeWidth="1.5" strokeDasharray="4 3" />
                    )}
                  </svg>
                </div>

                {/* Endpoint */}
                <div style={{ color: 'var(--vio-text-dim)', fontSize: '10px', marginBottom: '8px', fontFamily: 'monospace' }}>
                  {target.endpoint}
                </div>

                {/* Error history */}
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '5px', marginBottom: '5px' }}>
                    <AlertTriangle size={10} color={errors.length > 0 ? 'var(--vio-yellow)' : 'var(--vio-text-dim)'} />
                    <span style={{ color: 'var(--vio-text-dim)', fontSize: '10px', fontWeight: 600 }}>
                      Error-rate {ERROR_RATE_WINDOW_MINUTES}m: {errorRate30m.count} ({errorRate30m.perHour}/h)
                    </span>
                  </div>
                  {lastErrors.length === 0 ? (
                    <div style={{ color: 'var(--vio-green)', fontSize: '10px', opacity: 0.7 }}>Nessun errore registrato ✓</div>
                  ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '3px' }}>
                      {lastErrors.map((err, idx) => (
                        <div
                          key={idx}
                          style={{
                            display: 'flex',
                            gap: '6px',
                            fontSize: '10px',
                            padding: '3px 6px',
                            borderRadius: '4px',
                            background: 'rgba(255,60,60,0.07)',
                            border: '1px solid rgba(255,60,60,0.15)',
                          }}
                        >
                          <span style={{ color: 'var(--vio-text-dim)', fontVariantNumeric: 'tabular-nums', flexShrink: 0 }}>
                            {new Date(err.ts).toLocaleTimeString('it-IT', { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                          </span>
                          <span style={{ color: 'var(--vio-red)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                            {err.msg}
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </motion.div>

      {/* ── Knowledge Stack globale verificato ── */}
      {knowledgeRegistry && (
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.24 }}
          style={{ marginTop: '20px', background: 'var(--vio-bg-secondary)', border: '1px solid rgba(0,255,255,0.28)', borderRadius: 'var(--vio-radius-lg)', padding: '18px' }}
        >
          <h3 style={{ color: 'var(--vio-text-primary)', margin: '0 0 12px', fontSize: '15px', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Globe size={14} color="var(--vio-cyan)" /> Global Verified Knowledge Stack
            <span style={{ marginLeft: 'auto', color: 'var(--vio-text-dim)', fontSize: '10px', fontWeight: 400 }}>
              {knowledgeRegistry.version}
            </span>
          </h3>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(170px, 1fr))', gap: '10px', marginBottom: '12px' }}>
            <div style={{ border: '1px solid var(--vio-border)', borderRadius: '10px', padding: '10px', background: 'var(--vio-bg-tertiary)' }}>
              <div style={{ color: 'var(--vio-text-dim)', fontSize: '10px' }}>Domini</div>
              <div style={{ color: 'var(--vio-cyan)', fontSize: '16px', fontWeight: 700 }}>{knowledgeRegistry.coverage.domain_count}</div>
            </div>
            <div style={{ border: '1px solid var(--vio-border)', borderRadius: '10px', padding: '10px', background: 'var(--vio-bg-tertiary)' }}>
              <div style={{ color: 'var(--vio-text-dim)', fontSize: '10px' }}>Sotto-domini</div>
              <div style={{ color: 'var(--vio-green)', fontSize: '16px', fontWeight: 700 }}>{knowledgeRegistry.coverage.subdomain_count}</div>
            </div>
            <div style={{ border: '1px solid var(--vio-border)', borderRadius: '10px', padding: '10px', background: 'var(--vio-bg-tertiary)' }}>
              <div style={{ color: 'var(--vio-text-dim)', fontSize: '10px' }}>Fonti certificate</div>
              <div style={{ color: 'var(--vio-yellow)', fontSize: '16px', fontWeight: 700 }}>{knowledgeRegistry.coverage.trusted_source_count}</div>
            </div>
            <div style={{ border: '1px solid var(--vio-border)', borderRadius: '10px', padding: '10px', background: 'var(--vio-bg-tertiary)' }}>
              <div style={{ color: 'var(--vio-text-dim)', fontSize: '10px' }}>Legal watch</div>
              <div style={{ color: 'var(--vio-magenta)', fontSize: '16px', fontWeight: 700 }}>{knowledgeRegistry.legal_watch_jurisdictions.length} aree</div>
            </div>
            <div style={{ border: '1px solid var(--vio-border)', borderRadius: '10px', padding: '10px', background: 'var(--vio-bg-tertiary)' }}>
              <div style={{ color: 'var(--vio-text-dim)', fontSize: '10px' }}>Affidabilità media</div>
              <div style={{ color: 'var(--vio-green)', fontSize: '16px', fontWeight: 700 }}>
                {(knowledgeScores?.average_reliability ?? knowledgeRegistry.scores?.average_reliability ?? 0).toFixed(1)}%
              </div>
            </div>
            <div style={{ border: '1px solid var(--vio-border)', borderRadius: '10px', padding: '10px', background: 'var(--vio-bg-tertiary)' }}>
              <div style={{ color: 'var(--vio-text-dim)', fontSize: '10px' }}>Policy evidence</div>
              <div style={{ color: strictEvidenceMode ? 'var(--vio-green)' : 'var(--vio-yellow)', fontSize: '16px', fontWeight: 700 }}>
                {strictEvidenceMode ? 'STRICT ON' : 'STRICT OFF'}
              </div>
            </div>
          </div>

          <div style={{ border: '1px solid var(--vio-border)', borderRadius: '10px', padding: '10px', background: 'var(--vio-bg-tertiary)', marginBottom: '10px' }}>
            <div style={{ color: 'var(--vio-text-primary)', fontSize: '11px', fontWeight: 700, marginBottom: '8px' }}>
              Scheduler & Policy governance
            </div>

            <div style={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: '8px', marginBottom: '8px' }}>
              <span style={{ color: 'var(--vio-text-dim)', fontSize: '10px' }}>Refresh auto:</span>
              {[1, 3, 6, 12, 24].map((hours) => {
                const active = (knowledgeScheduler?.scheduler.refresh_interval_hours ?? 6) === hours;
                return (
                  <button
                    key={`knowledge-refresh-${hours}`}
                    onClick={() => updateKnowledgeScheduler(hours)}
                    disabled={updatingKnowledgePolicy}
                    style={{
                      border: `1px solid ${active ? 'var(--vio-cyan)' : 'var(--vio-border)'}`,
                      borderRadius: '999px',
                      padding: '3px 8px',
                      fontSize: '10px',
                      color: active ? 'var(--vio-cyan)' : 'var(--vio-text-dim)',
                      background: active ? 'rgba(0,255,255,0.08)' : 'transparent',
                      cursor: updatingKnowledgePolicy ? 'not-allowed' : 'pointer',
                      opacity: updatingKnowledgePolicy ? 0.6 : 1,
                    }}
                  >
                    {hours}h
                  </button>
                );
              })}
            </div>

            <div style={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: '8px', marginBottom: '8px' }}>
              <span style={{ color: 'var(--vio-text-dim)', fontSize: '10px' }}>Min score:</span>
              {[60, 70, 80, 90].map((score) => {
                const active = Math.round(knowledgeScheduler?.policy.minimum_domain_score ?? knowledgeScores?.minimum_required ?? 70) === score;
                const strict = strictEvidenceMode;
                return (
                  <button
                    key={`knowledge-score-${score}`}
                    onClick={() => updateKnowledgePolicy(strict, score)}
                    disabled={updatingKnowledgePolicy}
                    style={{
                      border: `1px solid ${active ? 'var(--vio-yellow)' : 'var(--vio-border)'}`,
                      borderRadius: '999px',
                      padding: '3px 8px',
                      fontSize: '10px',
                      color: active ? 'var(--vio-yellow)' : 'var(--vio-text-dim)',
                      background: active ? 'rgba(255,255,0,0.08)' : 'transparent',
                      cursor: updatingKnowledgePolicy ? 'not-allowed' : 'pointer',
                      opacity: updatingKnowledgePolicy ? 0.6 : 1,
                    }}
                  >
                    ≥{score}
                  </button>
                );
              })}
            </div>

            <div style={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: '8px' }}>
              <span style={{ color: 'var(--vio-text-dim)', fontSize: '10px' }}>Strict evidence:</span>
              <button
                onClick={() => updateKnowledgePolicy(
                  !strictEvidenceMode,
                  knowledgeScheduler?.policy.minimum_domain_score ?? knowledgeScores?.minimum_required ?? 70,
                )}
                disabled={updatingKnowledgePolicy}
                style={{
                  border: `1px solid ${strictEvidenceMode ? 'rgba(0,255,0,0.4)' : 'var(--vio-border)'}`,
                  borderRadius: '999px',
                  padding: '3px 10px',
                  fontSize: '10px',
                  color: strictEvidenceMode ? 'var(--vio-green)' : 'var(--vio-text-dim)',
                  background: strictEvidenceMode ? 'rgba(0,255,0,0.08)' : 'transparent',
                  cursor: updatingKnowledgePolicy ? 'not-allowed' : 'pointer',
                  opacity: updatingKnowledgePolicy ? 0.6 : 1,
                  fontWeight: 700,
                }}
              >
                {strictEvidenceMode ? 'ON' : 'OFF'}
              </button>

              <span style={{ color: 'var(--vio-text-dim)', fontSize: '10px', marginLeft: 'auto' }}>
                next refresh: {knowledgeScheduler?.scheduler.next_scheduled_refresh_at
                  ? new Date(knowledgeScheduler.scheduler.next_scheduled_refresh_at).toLocaleString('it-IT')
                  : 'n/d'}
              </span>
            </div>
          </div>

          {knowledgeWatch?.refresh_state && (
            <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginBottom: '10px' }}>
              <span style={{ border: '1px solid var(--vio-border)', borderRadius: '999px', padding: '3px 8px', fontSize: '10px', color: 'var(--vio-text-dim)' }}>
                reachability: {knowledgeWatch.refresh_state.reachable_count ?? 0}/{knowledgeWatch.refresh_state.source_count ?? 0}
              </span>
              <span style={{ border: '1px solid var(--vio-border)', borderRadius: '999px', padding: '3px 8px', fontSize: '10px', color: 'var(--vio-text-dim)' }}>
                fail: {knowledgeWatch.refresh_state.fail_count ?? 0}
              </span>
              <span style={{ border: '1px solid var(--vio-border)', borderRadius: '999px', padding: '3px 8px', fontSize: '10px', color: 'var(--vio-text-dim)' }}>
                last refresh: {knowledgeWatch.refresh_state.last_refresh_at ? new Date(knowledgeWatch.refresh_state.last_refresh_at).toLocaleString('it-IT') : 'n/d'}
              </span>
            </div>
          )}

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: '8px' }}>
            {knowledgeRegistry.domains.slice(0, 8).map((domain) => (
              <div key={domain.id} style={{ border: '1px solid var(--vio-border)', borderRadius: '10px', padding: '10px', background: 'var(--vio-bg-tertiary)' }}>
                <div style={{ color: 'var(--vio-text-primary)', fontSize: '12px', fontWeight: 700, marginBottom: '4px' }}>{domain.name}</div>
                <div style={{ color: 'var(--vio-text-dim)', fontSize: '10px', marginBottom: '6px' }}>
                  {domain.subdomains.length} sub-domini
                </div>
                {domain.reliability && (
                  <div style={{ marginBottom: '6px' }}>
                    {(() => {
                      const semantic = getScoreSemantic(domain.reliability.reliability_score);
                      return (
                        <span
                          style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '4px',
                            borderRadius: '999px',
                            padding: '2px 8px',
                            border: `1px solid ${semantic.border}`,
                            color: semantic.color,
                            background: semantic.background,
                            fontSize: '10px',
                            fontWeight: 700,
                          }}
                        >
                          reliability {domain.reliability.reliability_score.toFixed(1)}% · {semantic.label}
                        </span>
                      );
                    })()}
                  </div>
                )}
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                  {domain.trusted_sources.slice(0, 4).map((source) => (
                    <span key={source} style={{ fontSize: '9px', color: 'var(--vio-text-dim)', border: '1px solid var(--vio-border)', borderRadius: '999px', padding: '2px 6px' }}>
                      {source}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </motion.div>
      )}

      {/* ── Claude Desktop Extensions panel ── */}
      {claudeExts && claudeExts.count > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          style={{ marginTop: '20px', background: 'var(--vio-bg-secondary)', border: '1px solid rgba(99,102,241,0.35)', borderRadius: 'var(--vio-radius-lg)', padding: '18px' }}
        >
          <h3 style={{ color: 'var(--vio-text-primary)', margin: '0 0 12px', fontSize: '15px', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Cpu size={14} color="#818cf8" /> Claude Desktop — Estensioni MCP rilevate
            <span style={{ marginLeft: 'auto', fontSize: '11px', color: 'var(--vio-text-dim)', fontWeight: 400 }}>
              {claudeExts.count} installat{claudeExts.count === 1 ? 'a' : 'e'}
            </span>
          </h3>

          {claudeActivity?.sessions && (
            <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginBottom: '10px' }}>
              <span style={{ fontSize: '10px', color: 'var(--vio-text-dim)', border: '1px solid var(--vio-border)', borderRadius: '999px', padding: '3px 8px' }}>
                workspace: {claudeActivity.sessions.workspace_count}
              </span>
              <span style={{ fontSize: '10px', color: 'var(--vio-text-dim)', border: '1px solid var(--vio-border)', borderRadius: '999px', padding: '3px 8px' }}>
                sessioni: {claudeActivity.sessions.session_count}
              </span>
              <span style={{ fontSize: '10px', color: 'var(--vio-text-dim)', border: '1px solid var(--vio-border)', borderRadius: '999px', padding: '3px 8px' }}>
                audit.jsonl: {claudeActivity.sessions.audit_files}
              </span>
            </div>
          )}

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '10px' }}>
            {claudeExts.extensions.map((ext) => (
              <div
                key={ext.id}
                style={{
                  border: '1px solid rgba(99,102,241,0.2)',
                  borderRadius: '10px',
                  padding: '12px',
                  background: 'rgba(99,102,241,0.04)',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '6px' }}>
                  <span style={{ color: 'var(--vio-text-primary)', fontWeight: 700, fontSize: '12px' }}>{ext.name}</span>
                  <span style={{ color: '#818cf8', fontSize: '10px', border: '1px solid rgba(99,102,241,0.3)', padding: '1px 6px', borderRadius: '999px', flexShrink: 0, marginLeft: '8px' }}>v{ext.version}</span>
                </div>
                <div style={{ color: 'var(--vio-text-dim)', fontSize: '10px', marginBottom: '8px', lineHeight: 1.4 }}>{ext.description.slice(0, 100)}{ext.description.length > 100 ? '…' : ''}</div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                  {ext.tools.slice(0, 8).map((tool) => (
                    <span
                      key={tool}
                      style={{ fontSize: '9px', padding: '2px 6px', borderRadius: '999px', border: '1px solid var(--vio-border)', color: 'var(--vio-text-dim)', background: 'var(--vio-bg-tertiary)' }}
                    >
                      {tool}
                    </span>
                  ))}
                  {ext.tool_count > 8 && (
                    <span style={{ fontSize: '9px', padding: '2px 6px', borderRadius: '999px', border: '1px solid var(--vio-border)', color: '#818cf8' }}>
                      +{ext.tool_count - 8} altri
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </motion.div>
      )}
    </div>
  );
}
