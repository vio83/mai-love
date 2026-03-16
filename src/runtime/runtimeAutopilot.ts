export type RuntimeTargetId = 'ollama-local' | 'openclaw-local' | 'legalroom-360' | 'n8n-automation';

export type RuntimeTargetStatus = 'online' | 'degraded' | 'offline';

export interface ProbeError {
  ts: string;
  msg: string;
}

export interface LatencySample {
  ts: string;
  latencyMs: number;
  reachable: boolean;
}

export interface RuntimeTarget {
  id: RuntimeTargetId;
  name: string;
  mode: 'local' | 'local-proxy';
  endpoint: string;
  status: RuntimeTargetStatus;
  autoOptimize: boolean;
  optimizationScore: number;
  latencyMs: number;
  lastHeartbeat: string;
  capabilities: string[];
  errorHistory: ProbeError[];
  latencyTrend: LatencySample[];
}

export interface RuntimeAutopilotState {
  version: string;
  tickIntervalMs: number;
  lastOptimizationAt: string;
  targets: RuntimeTarget[];
}

const STORAGE_KEY = 'vio83-runtime-autopilot-v1';
const DEFAULT_TICK_MS = 15 * 60 * 1000;
const MAX_TREND_POINTS = 20;
const MAX_ERROR_HISTORY = 200;

export const ERROR_RATE_WINDOW_MINUTES = 30;

const DEFAULT_TARGETS: RuntimeTarget[] = [
  {
    id: 'ollama-local',
    name: 'Ollama Local Inference',
    mode: 'local',
    endpoint: 'http://localhost:11434',
    status: 'online',
    autoOptimize: true,
    optimizationScore: 92,
    latencyMs: 0,
    lastHeartbeat: new Date().toISOString(),
    capabilities: ['LLM inference', 'privacy mode', 'offline fallback'],
    errorHistory: [],
    latencyTrend: [],
  },
  {
    id: 'openclaw-local',
    name: 'OpenClaw Runtime Bridge',
    mode: 'local-proxy',
    endpoint: 'http://localhost:4111',
    status: 'degraded',
    autoOptimize: true,
    optimizationScore: 78,
    latencyMs: 0,
    lastHeartbeat: new Date().toISOString(),
    capabilities: ['agent tools', 'task automation', 'local execution'],
    errorHistory: [],
    latencyTrend: [],
  },
  {
    id: 'legalroom-360',
    name: 'LegalRoom 360 Engine',
    mode: 'local-proxy',
    endpoint: 'http://localhost:4222',
    status: 'degraded',
    autoOptimize: true,
    optimizationScore: 74,
    latencyMs: 0,
    lastHeartbeat: new Date().toISOString(),
    capabilities: ['document workflows', 'legal checks', 'case context memory'],
    errorHistory: [],
    latencyTrend: [],
  },
  {
    id: 'n8n-automation',
    name: 'n8n Automation Hub',
    mode: 'local-proxy',
    endpoint: 'http://localhost:5678',
    status: 'online',
    autoOptimize: true,
    optimizationScore: 88,
    latencyMs: 0,
    lastHeartbeat: new Date().toISOString(),
    capabilities: ['cron workflows', 'webhooks', 'tool chaining'],
    errorHistory: [],
    latencyTrend: [],
  },
];

const defaultState = (): RuntimeAutopilotState => ({
  version: '2026.03-runtime-1',
  tickIntervalMs: DEFAULT_TICK_MS,
  lastOptimizationAt: new Date().toISOString(),
  targets: DEFAULT_TARGETS,
});

function isBrowser() {
  return typeof window !== 'undefined' && typeof localStorage !== 'undefined';
}

function safeParseState(raw: string | null): RuntimeAutopilotState | null {
  if (!raw) return null;

  try {
    const parsed = JSON.parse(raw) as RuntimeAutopilotState;
    if (!parsed?.targets || !Array.isArray(parsed.targets)) return null;

    const defaultsById = new Map(DEFAULT_TARGETS.map((target) => [target.id, target]));
    const normalizedTargets = parsed.targets
      .map((target) => {
        const fallback = defaultsById.get(target.id);
        if (!fallback) return null;

        const incomingErrors = Array.isArray((target as Partial<RuntimeTarget>).errorHistory)
          ? (target as Partial<RuntimeTarget>).errorHistory ?? []
          : [];
        const incomingTrend = Array.isArray((target as Partial<RuntimeTarget>).latencyTrend)
          ? (target as Partial<RuntimeTarget>).latencyTrend ?? []
          : [];

        return {
          ...fallback,
          ...target,
          capabilities: Array.isArray(target.capabilities) ? target.capabilities : fallback.capabilities,
          latencyMs: Number.isFinite(target.latencyMs) ? target.latencyMs : 0,
          errorHistory: incomingErrors.slice(-MAX_ERROR_HISTORY),
          latencyTrend: incomingTrend.slice(-MAX_TREND_POINTS),
        } as RuntimeTarget;
      })
      .filter((target): target is RuntimeTarget => Boolean(target));

    if (normalizedTargets.length === 0) return null;

    return {
      ...parsed,
      targets: normalizedTargets,
    };
  } catch {
    return null;
  }
}

export function getRuntimeAutopilotState(): RuntimeAutopilotState {
  if (!isBrowser()) return defaultState();

  const parsed = safeParseState(localStorage.getItem(STORAGE_KEY));
  if (parsed) return parsed;

  const fallback = defaultState();
  localStorage.setItem(STORAGE_KEY, JSON.stringify(fallback));
  return fallback;
}

export function setRuntimeAutopilotState(next: RuntimeAutopilotState): RuntimeAutopilotState {
  if (isBrowser()) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
  }

  return next;
}

export function setRuntimeTickInterval(ms: number) {
  const state = getRuntimeAutopilotState();
  const boundedMs = Math.min(Math.max(ms, 60_000), 24 * 60 * 60 * 1000);

  return setRuntimeAutopilotState({
    ...state,
    tickIntervalMs: boundedMs,
  });
}

export function setRuntimeTargetAutoOptimize(id: RuntimeTargetId, autoOptimize: boolean) {
  const state = getRuntimeAutopilotState();

  return setRuntimeAutopilotState({
    ...state,
    targets: state.targets.map((target) =>
      target.id === id
        ? { ...target, autoOptimize }
        : target
    ),
  });
}

const TARGET_PROBE_URLS: Record<RuntimeTargetId, string[]> = {
  'ollama-local': ['http://localhost:11434/api/tags', 'http://localhost:11434/'],
  'openclaw-local': ['http://localhost:4111/health', 'http://localhost:4111/'],
  'legalroom-360': ['http://localhost:4222/health', 'http://localhost:4222/'],
  'n8n-automation': ['http://localhost:5678/healthz', 'http://localhost:5678/rest/healthz', 'http://localhost:5678/'],
};

async function probeUrl(url: string, timeoutMs: number = 2200): Promise<{ ok: boolean; latencyMs: number }> {
  const startedAt = performance.now();
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), timeoutMs);

  try {
    await fetch(url, {
      method: 'GET',
      mode: 'no-cors',
      cache: 'no-store',
      signal: controller.signal,
    });

    return {
      ok: true,
      latencyMs: Math.max(1, Math.round(performance.now() - startedAt)),
    };
  } catch {
    return {
      ok: false,
      latencyMs: Math.max(1, Math.round(performance.now() - startedAt)),
    };
  } finally {
    clearTimeout(timeout);
  }
}

async function probeTarget(target: RuntimeTarget): Promise<{ reachable: boolean; latencyMs: number }> {
  const urls = TARGET_PROBE_URLS[target.id] || [target.endpoint];
  let lastLatencyMs = 0;

  for (const url of urls) {
    const probe = await probeUrl(url);
    lastLatencyMs = probe.latencyMs;
    if (probe.ok) {
      return { reachable: true, latencyMs: probe.latencyMs };
    }
  }

  return { reachable: false, latencyMs: lastLatencyMs };
}

function computeOptimizationScore(current: number, reachable: boolean, latencyMs: number, autoOptimize: boolean) {
  const baseScore = reachable ? 74 : 25;
  const latencyBonus = reachable ? Math.max(0, 18 - Math.floor(Math.min(latencyMs, 4500) / 250)) : 0;
  const autoBonus = autoOptimize ? 8 : -6;
  const blended = Math.round((current * 0.2 + (baseScore + latencyBonus + autoBonus) * 0.8) * 10) / 10;
  return Math.max(0, Math.min(100, blended));
}

function computeStatus(score: number): RuntimeTargetStatus {
  if (score >= 85) return 'online';
  if (score >= 65) return 'degraded';
  return 'offline';
}

export async function runRuntimeOptimizationTick() {
  const state = getRuntimeAutopilotState();
  const nowIso = new Date().toISOString();
  const nowTs = Date.now();

  const nextTargets = await Promise.all(
    state.targets.map(async (target) => {
      const { reachable, latencyMs } = await probeTarget(target);
      const score = computeOptimizationScore(target.optimizationScore, reachable, latencyMs, target.autoOptimize);

      const prevErrors: ProbeError[] = target.errorHistory ?? [];
      const prevTrend: LatencySample[] = target.latencyTrend ?? [];
      const probeMsg = `unreachable (${Math.max(1, latencyMs)}ms probe)`;
      const lastError = prevErrors[prevErrors.length - 1];
      const lastErrorTs = lastError ? new Date(lastError.ts).getTime() : 0;
      const shouldAppendError = !reachable
        && (!lastError || lastError.msg !== probeMsg || nowTs - lastErrorTs > 20_000);

      const newErrors: ProbeError[] = reachable
        ? prevErrors
        : shouldAppendError
          ? [...prevErrors, { ts: nowIso, msg: probeMsg }].slice(-MAX_ERROR_HISTORY)
          : prevErrors;
      const newTrend: LatencySample[] = [
        ...prevTrend,
        {
          ts: nowIso,
          latencyMs,
          reachable,
        },
      ].slice(-MAX_TREND_POINTS);

      return {
        ...target,
        optimizationScore: score,
        status: computeStatus(score),
        latencyMs: reachable ? latencyMs : 0,
        lastHeartbeat: nowIso,
        errorHistory: newErrors,
        latencyTrend: newTrend,
      };
    })
  );

  return setRuntimeAutopilotState({
    ...state,
    lastOptimizationAt: nowIso,
    targets: nextTargets,
  });
}

export function bootstrapRuntimeAutopilot() {
  if (!isBrowser()) return () => undefined;

  const bootState = getRuntimeAutopilotState();
  const intervalMs = bootState.tickIntervalMs || DEFAULT_TICK_MS;
  void runRuntimeOptimizationTick();

  const intervalId = window.setInterval(() => {
    void runRuntimeOptimizationTick();
  }, intervalMs);

  const visibilityHandler = () => {
    if (document.visibilityState === 'visible') {
      void runRuntimeOptimizationTick();
    }
  };

  window.addEventListener('visibilitychange', visibilityHandler);

  return () => {
    window.clearInterval(intervalId);
    window.removeEventListener('visibilitychange', visibilityHandler);
  };
}
