import { AlertCircle, Bot, Cpu, Download, PlayCircle, RefreshCw, Save, Square, Wrench } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { useAppStore } from '../../stores/appStore';

interface RuntimeDependencyInfo {
  available: boolean;
  version?: string | null;
}

interface RuntimeAppSupervisorState {
  pid?: number | null;
  enabled?: boolean;
  disabled_reason?: string | null;
  last_health_ok?: boolean | null;
}

interface RuntimeAppAnalysis {
  id: string;
  name: string;
  configured: boolean;
  command: string;
  health_urls: string[];
  port: number;
  stack: string[];
  required_dependencies: string[];
  notes: string[];
  recommended_actions: Array<string | null>;
  health: {
    reachable: boolean;
    url?: string | null;
    status_code?: number | null;
    latency_ms?: number | null;
    error?: string | null;
  };
  command_status: {
    configured: boolean;
    binary_ok: boolean;
    command_type: string;
    entry?: string | null;
  };
  supervisor?: RuntimeAppSupervisorState;
}

interface RuntimeAppsSnapshot {
  status: string;
  detected_at: string;
  preferences: {
    update_policy: string;
    offline_mode: string;
    last_user_approved_at?: string | null;
  };
  controls: {
    runtime_launch_agent_installed: boolean;
    runtime_launch_agent_loaded: boolean;
    orchestra_launch_agent_installed: boolean;
    orchestra_launch_agent_loaded: boolean;
    supervisor_pid?: number | null;
    env_path: string;
    project_root: string;
  };
  dependencies: Record<string, RuntimeDependencyInfo>;
  claude_desktop: {
    installed: boolean;
    base_path: string;
    extensions_count: number;
    preferences: Record<string, unknown>;
  };
  apps: RuntimeAppAnalysis[];
  honesty_notes: string[];
}

type RuntimeConfigForm = {
  openclaw_start_cmd: string;
  legalroom_start_cmd: string;
  n8n_start_cmd: string;
  openclaw_health_urls: string;
  legalroom_health_urls: string;
  n8n_health_urls: string;
  update_policy: string;
  offline_mode: string;
};

const defaultForm: RuntimeConfigForm = {
  openclaw_start_cmd: '',
  legalroom_start_cmd: '',
  n8n_start_cmd: '',
  openclaw_health_urls: 'http://127.0.0.1:4111/health,http://127.0.0.1:4111/',
  legalroom_health_urls: 'http://127.0.0.1:4222/health,http://127.0.0.1:4222/',
  n8n_health_urls: 'http://127.0.0.1:5678/healthz,http://127.0.0.1:5678/rest/healthz,http://127.0.0.1:5678/',
  update_policy: 'user-approved',
  offline_mode: 'keep-last-approved',
};

const UPDATE_POLICY_OPTIONS = [
  { value: 'user-approved', label: 'User approved', hint: 'Usa solo la configurazione approvata esplicitamente dall’utente.' },
  { value: 'manual-locked', label: 'Manual locked', hint: 'Blocca la configurazione corrente finché l’utente non la cambia.' },
  { value: 'auto-safe', label: 'Auto safe', hint: 'Accetta update/config note come sicure, ma senza aggiornare binari magicamente.' },
];

const OFFLINE_MODE_OPTIONS = [
  { value: 'keep-last-approved', label: 'Keep last approved', hint: 'Offline usa ultima configurazione approvata disponibile.' },
  { value: 'local-only', label: 'Local only', hint: 'Forza solo componenti locali/proxy quando il cloud non è disponibile.' },
  { value: 'disable-if-stale', label: 'Disable if stale', hint: 'Disattiva app non verificate o non aggiornate dall’utente.' },
];

function badgeColor(ok: boolean) {
  return ok
    ? { color: '#00ff88', border: 'rgba(0,255,136,0.3)', bg: 'rgba(0,255,136,0.12)' }
    : { color: '#f87171', border: 'rgba(248,113,113,0.3)', bg: 'rgba(248,113,113,0.12)' };
}

export function RuntimeAppsSettings() {
  const { settings } = useAppStore();
  const [snapshot, setSnapshot] = useState<RuntimeAppsSnapshot | null>(null);
  const [form, setForm] = useState<RuntimeConfigForm>(defaultForm);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [actionBusy, setActionBusy] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<{ kind: 'success' | 'error' | 'info'; message: string } | null>(null);

  const claudeApiConfigured = useMemo(
    () => settings.apiKeys.some((entry) => entry.provider === 'claude' && entry.key.trim().length > 0),
    [settings.apiKeys],
  );

  const loadAnalysis = async (quiet = false) => {
    if (!quiet) setLoading(true);
    try {
      const response = await fetch('http://localhost:4000/runtime/apps/analysis');
      if (!response.ok) throw new Error('analysis_failed');
      const data = await response.json() as RuntimeAppsSnapshot;
      setSnapshot(data);

      const openclaw = data.apps.find((app) => app.id === 'openclaw');
      const legalroom = data.apps.find((app) => app.id === 'legalroom');
      const n8n = data.apps.find((app) => app.id === 'n8n');

      setForm({
        openclaw_start_cmd: openclaw?.command ?? '',
        legalroom_start_cmd: legalroom?.command ?? '',
        n8n_start_cmd: n8n?.command ?? '',
        openclaw_health_urls: (openclaw?.health_urls ?? defaultForm.openclaw_health_urls.split(',')).join(','),
        legalroom_health_urls: (legalroom?.health_urls ?? defaultForm.legalroom_health_urls.split(',')).join(','),
        n8n_health_urls: (n8n?.health_urls ?? defaultForm.n8n_health_urls.split(',')).join(','),
        update_policy: data.preferences.update_policy || defaultForm.update_policy,
        offline_mode: data.preferences.offline_mode || defaultForm.offline_mode,
      });
    } catch {
      setFeedback({ kind: 'error', message: 'Analisi runtime apps non disponibile: backend non raggiungibile.' });
    } finally {
      if (!quiet) setLoading(false);
    }
  };

  useEffect(() => {
    void loadAnalysis();
    const id = window.setInterval(() => void loadAnalysis(true), 15000);
    return () => window.clearInterval(id);
  }, []);

  useEffect(() => {
    if (!feedback) return;
    const id = window.setTimeout(() => setFeedback(null), 3200);
    return () => window.clearTimeout(id);
  }, [feedback]);

  const handleSave = async () => {
    setSaving(true);
    try {
      const response = await fetch('http://localhost:4000/runtime/apps/config', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      });

      if (!response.ok) throw new Error('save_failed');
      const data = await response.json();
      setSnapshot(data.snapshot as RuntimeAppsSnapshot);
      setFeedback({ kind: 'success', message: 'Configurazione runtime salvata in .env con successo.' });
    } catch {
      setFeedback({ kind: 'error', message: 'Salvataggio runtime apps fallito.' });
    } finally {
      setSaving(false);
    }
  };

  const runAction = async (action: 'start-supervisor' | 'stop-supervisor' | 'install-autostart') => {
    setActionBusy(action);
    try {
      const response = await fetch('http://localhost:4000/runtime/apps/action', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action }),
      });
      if (!response.ok) {
        throw new Error('action_failed');
      }
      const data = await response.json();
      setSnapshot(data.snapshot as RuntimeAppsSnapshot);
      setFeedback({ kind: 'success', message: `Azione completata: ${action}` });
    } catch {
      setFeedback({ kind: 'error', message: `Azione non riuscita: ${action}` });
    } finally {
      setActionBusy(null);
    }
  };

  return (
    <div className="space-y-4">
      {feedback && (
        <div
          className="rounded-xl px-4 py-3 text-xs font-semibold"
          style={{
            backgroundColor: feedback.kind === 'success' ? 'rgba(0,255,136,0.12)' : feedback.kind === 'error' ? 'rgba(248,113,113,0.12)' : 'rgba(103,232,249,0.12)',
            border: `1px solid ${feedback.kind === 'success' ? 'rgba(0,255,136,0.3)' : feedback.kind === 'error' ? 'rgba(248,113,113,0.3)' : 'rgba(103,232,249,0.3)'}`,
            color: feedback.kind === 'success' ? '#00ff88' : feedback.kind === 'error' ? '#f87171' : '#67e8f9',
          }}
        >
          {feedback.message}
        </div>
      )}

      <div className="rounded-xl p-4" style={{ backgroundColor: '#111', border: '1px solid #222' }}>
        <div className="flex items-start justify-between gap-4 flex-wrap">
          <div>
            <p className="text-white text-sm font-medium mb-1">Sessione dedicata App AI & Runtime</p>
            <p className="text-xs text-gray-500 max-w-3xl">
              Analisi reale di stack, dipendenze, comandi di avvio, health endpoint, LaunchAgent, modalità offline e policy di aggiornamento approvata dall’utente.
              Questa sezione non inventa servizi: mostra ciò che esiste davvero e ti permette di salvarlo in modo gestibile.
            </p>
          </div>
          <button
            onClick={() => void loadAnalysis()}
            className="px-3 py-2 rounded-lg text-xs font-semibold flex items-center gap-2"
            style={{ backgroundColor: '#00ffff14', border: '1px solid #00ffff33', color: '#67e8f9' }}
          >
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
            {loading ? 'Analisi…' : 'Riesegui analisi'}
          </button>
        </div>
      </div>

      {snapshot && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
            {[
              { label: 'Supervisor PID', value: snapshot.controls.supervisor_pid ? String(snapshot.controls.supervisor_pid) : 'non attivo', ok: Boolean(snapshot.controls.supervisor_pid) },
              { label: 'LaunchAgent runtime', value: snapshot.controls.runtime_launch_agent_loaded ? 'LOADED' : snapshot.controls.runtime_launch_agent_installed ? 'INSTALLED' : 'MISSING', ok: snapshot.controls.runtime_launch_agent_loaded },
              { label: 'Policy update', value: snapshot.preferences.update_policy, ok: true },
              { label: 'Offline mode', value: snapshot.preferences.offline_mode, ok: true },
            ].map((item) => {
              const color = badgeColor(item.ok);
              return (
                <div key={item.label} className="rounded-xl p-4" style={{ backgroundColor: '#111', border: '1px solid #222' }}>
                  <div className="text-[11px] text-gray-500 mb-1">{item.label}</div>
                  <div className="text-sm font-semibold" style={{ color: color.color }}>{item.value}</div>
                </div>
              );
            })}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="rounded-xl p-4" style={{ backgroundColor: '#111', border: '1px solid #222' }}>
              <div className="flex items-center gap-2 mb-3">
                <Bot size={16} style={{ color: '#D97706' }} />
                <p className="text-white text-sm font-medium">Claude API / Modello top</p>
              </div>
              <div className="space-y-2 text-xs">
                <div className="flex justify-between"><span className="text-gray-500">API key Claude</span><span style={{ color: claudeApiConfigured ? '#00ff88' : '#f87171' }}>{claudeApiConfigured ? 'CONFIGURATA' : 'ASSENTE'}</span></div>
                <div className="flex justify-between"><span className="text-gray-500">Mode app</span><span className="text-white">{settings.orchestrator.mode}</span></div>
                <div className="flex justify-between"><span className="text-gray-500">Primary provider</span><span className="text-white">{settings.orchestrator.primaryProvider}</span></div>
                <p className="text-gray-500 pt-2">
                  Nota onesta: il modello cloud “più nuovo” dipende da chiave API, routing e disponibilità del provider. Qui non dichiariamo versioni non verificate automaticamente.
                </p>
              </div>
            </div>

            <div className="rounded-xl p-4" style={{ backgroundColor: '#111', border: '1px solid #222' }}>
              <div className="flex items-center gap-2 mb-3">
                <Cpu size={16} style={{ color: '#a78bfa' }} />
                <p className="text-white text-sm font-medium">Claude Desktop locale</p>
              </div>
              <div className="space-y-2 text-xs">
                <div className="flex justify-between"><span className="text-gray-500">Installato</span><span style={{ color: snapshot.claude_desktop.installed ? '#00ff88' : '#f87171' }}>{snapshot.claude_desktop.installed ? 'SI' : 'NO'}</span></div>
                <div className="flex justify-between"><span className="text-gray-500">Estensioni MCP</span><span className="text-white">{snapshot.claude_desktop.extensions_count}</span></div>
                <div className="flex justify-between"><span className="text-gray-500">keepAwake</span><span className="text-white">{String(snapshot.claude_desktop.preferences.keepAwakeEnabled ?? false)}</span></div>
                <div className="text-gray-500 break-all">{snapshot.claude_desktop.base_path}</div>
              </div>
            </div>

            <div className="rounded-xl p-4" style={{ backgroundColor: '#111', border: '1px solid #222' }}>
              <div className="flex items-center gap-2 mb-3">
                <Wrench size={16} style={{ color: '#67e8f9' }} />
                <p className="text-white text-sm font-medium">Dipendenze host</p>
              </div>
              <div className="space-y-2 text-xs">
                {Object.entries(snapshot.dependencies).map(([name, info]) => (
                  <div key={name} className="flex justify-between gap-3">
                    <span className="text-gray-500">{name}</span>
                    <span style={{ color: info.available ? '#00ff88' : '#f87171' }}>
                      {info.available ? (info.version || 'OK') : 'MISSING'}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="rounded-xl p-4" style={{ backgroundColor: '#111', border: '1px solid #222' }}>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="text-sm text-gray-400 mb-2 block">Policy update approvata utente</label>
                <select
                  value={form.update_policy}
                  onChange={(e) => setForm((prev) => ({ ...prev, update_policy: e.target.value }))}
                  className="w-full px-3 py-2 rounded-lg text-sm text-white outline-none"
                  style={{ backgroundColor: '#0a0a0a', border: '1px solid #333' }}
                >
                  {UPDATE_POLICY_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>{option.label}</option>
                  ))}
                </select>
                <p className="text-[11px] text-gray-500 mt-2">
                  {UPDATE_POLICY_OPTIONS.find((option) => option.value === form.update_policy)?.hint}
                </p>
              </div>
              <div>
                <label className="text-sm text-gray-400 mb-2 block">Modalità offline</label>
                <select
                  value={form.offline_mode}
                  onChange={(e) => setForm((prev) => ({ ...prev, offline_mode: e.target.value }))}
                  className="w-full px-3 py-2 rounded-lg text-sm text-white outline-none"
                  style={{ backgroundColor: '#0a0a0a', border: '1px solid #333' }}
                >
                  {OFFLINE_MODE_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>{option.label}</option>
                  ))}
                </select>
                <p className="text-[11px] text-gray-500 mt-2">
                  {OFFLINE_MODE_OPTIONS.find((option) => option.value === form.offline_mode)?.hint}
                </p>
              </div>
            </div>

            <div className="flex gap-2 flex-wrap mt-4">
              <button
                onClick={handleSave}
                disabled={saving}
                className="px-4 py-2 rounded-lg text-xs font-semibold flex items-center gap-2"
                style={{ backgroundColor: '#00ff0015', border: '1px solid #00ff0040', color: '#00ff88', opacity: saving ? 0.6 : 1 }}
              >
                <Save size={14} /> {saving ? 'Salvataggio…' : 'Salva configurazione runtime'}
              </button>
              <button
                onClick={() => void runAction('start-supervisor')}
                disabled={actionBusy !== null}
                className="px-4 py-2 rounded-lg text-xs font-semibold flex items-center gap-2"
                style={{ backgroundColor: '#00ffff14', border: '1px solid #00ffff33', color: '#67e8f9', opacity: actionBusy ? 0.6 : 1 }}
              >
                <PlayCircle size={14} /> {actionBusy === 'start-supervisor' ? 'Avvio…' : 'Avvia supervisor'}
              </button>
              <button
                onClick={() => void runAction('stop-supervisor')}
                disabled={actionBusy !== null}
                className="px-4 py-2 rounded-lg text-xs font-semibold flex items-center gap-2"
                style={{ backgroundColor: '#ffffff10', border: '1px solid #ffffff25', color: '#d1d5db', opacity: actionBusy ? 0.6 : 1 }}
              >
                <Square size={14} /> {actionBusy === 'stop-supervisor' ? 'Stop…' : 'Ferma supervisor'}
              </button>
              <button
                onClick={() => void runAction('install-autostart')}
                disabled={actionBusy !== null}
                className="px-4 py-2 rounded-lg text-xs font-semibold flex items-center gap-2"
                style={{ backgroundColor: '#a78bfa14', border: '1px solid #a78bfa33', color: '#c4b5fd', opacity: actionBusy ? 0.6 : 1 }}
              >
                <Download size={14} /> {actionBusy === 'install-autostart' ? 'Installazione…' : 'Installa autostart'}
              </button>
            </div>
          </div>

          <div className="space-y-4">
            {snapshot.apps.map((app) => {
              const healthColor = badgeColor(app.health.reachable);
              const configOperational = app.id === 'n8n'
                ? app.configured
                : app.configured && app.command_status.binary_ok;
              const configuredColor = badgeColor(configOperational);
              const commandField = `${app.id}_start_cmd` as keyof RuntimeConfigForm;
              const healthField = `${app.id}_health_urls` as keyof RuntimeConfigForm;

              return (
                <div key={app.id} className="rounded-xl p-4" style={{ backgroundColor: '#111', border: '1px solid #222' }}>
                  <div className="flex items-start justify-between gap-4 flex-wrap mb-3">
                    <div>
                      <p className="text-white text-sm font-medium">{app.name}</p>
                      <p className="text-xs text-gray-500">Porta {app.port} · stack verificata: {app.stack.join(' · ')}</p>
                    </div>
                    <div className="flex gap-2 flex-wrap">
                      <span className="px-2 py-1 rounded-full text-[10px] font-semibold" style={{ color: configuredColor.color, border: `1px solid ${configuredColor.border}`, backgroundColor: configuredColor.bg }}>
                        {app.id === 'n8n'
                          ? (app.configured ? 'FALLBACK/CONFIG OK' : 'NON CONFIG')
                          : app.configured
                            ? (app.command_status.binary_ok ? 'CONFIG OK' : 'CMD DA VERIFICARE')
                            : 'NON CONFIG'}
                      </span>
                      <span className="px-2 py-1 rounded-full text-[10px] font-semibold" style={{ color: healthColor.color, border: `1px solid ${healthColor.border}`, backgroundColor: healthColor.bg }}>
                        {app.health.reachable ? `HEALTH OK${app.health.latency_ms ? ` · ${app.health.latency_ms}ms` : ''}` : 'HEALTH KO'}
                      </span>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="text-sm text-gray-400 mb-2 block">Comando reale di avvio</label>
                      <textarea
                        rows={3}
                        value={String(form[commandField] ?? '')}
                        onChange={(e) => setForm((prev) => ({ ...prev, [commandField]: e.target.value }))}
                        className="w-full px-3 py-2 rounded-lg text-sm text-white outline-none resize-y"
                        style={{ backgroundColor: '#0a0a0a', border: '1px solid #333' }}
                        placeholder={app.id === 'openclaw'
                          ? 'python3 /percorso/reale/openclaw/main.py --port 4111'
                          : app.id === 'legalroom'
                            ? 'python3 /percorso/reale/legalroom/server.py --port 4222'
                            : 'lascia vuoto per usare fallback n8n'}
                      />
                      <p className="text-[11px] text-gray-500 mt-2">
                        {app.command_status.entry ? `Entry rilevata: ${app.command_status.entry}` : 'Nessuna entry binaria rilevata ancora.'}
                      </p>
                    </div>
                    <div>
                      <label className="text-sm text-gray-400 mb-2 block">Health URLs</label>
                      <textarea
                        rows={3}
                        value={String(form[healthField] ?? '')}
                        onChange={(e) => setForm((prev) => ({ ...prev, [healthField]: e.target.value }))}
                        className="w-full px-3 py-2 rounded-lg text-sm text-white outline-none resize-y"
                        style={{ backgroundColor: '#0a0a0a', border: '1px solid #333' }}
                      />
                      <p className="text-[11px] mt-2" style={{ color: app.health.reachable ? '#00ff88' : '#f87171' }}>
                        {app.health.reachable
                          ? `Endpoint valido: ${app.health.url} (${app.health.status_code ?? 'ok'})`
                          : `Ultimo errore: ${app.health.error || 'endpoint non raggiungibile'}`}
                      </p>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4 text-xs">
                    <div>
                      <p className="text-gray-400 mb-2">Dipendenze richieste</p>
                      <div className="flex flex-wrap gap-2">
                        {app.required_dependencies.map((dep) => (
                          <span key={dep} className="px-2 py-1 rounded-full" style={{ backgroundColor: '#0a0a0a', border: '1px solid #333', color: '#9ca3af' }}>
                            {dep}
                          </span>
                        ))}
                      </div>
                    </div>
                    <div>
                      <p className="text-gray-400 mb-2">Supervisor</p>
                      <div className="space-y-1 text-gray-500">
                        <div>enabled: {String(app.supervisor?.enabled ?? false)}</div>
                        <div>pid: {app.supervisor?.pid ?? '—'}</div>
                        <div>last health: {app.supervisor?.last_health_ok == null ? 'n/d' : app.supervisor?.last_health_ok ? 'ok' : 'ko'}</div>
                        {app.supervisor?.disabled_reason && <div style={{ color: '#fbbf24' }}>{app.supervisor.disabled_reason}</div>}
                      </div>
                    </div>
                    <div>
                      <p className="text-gray-400 mb-2">Azioni consigliate</p>
                      <ul className="space-y-1 text-gray-500 list-disc pl-4">
                        {app.recommended_actions.filter(Boolean).map((action) => (
                          <li key={action}>{action}</li>
                        ))}
                        {app.notes.map((note) => (
                          <li key={note}>{note}</li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          <div className="rounded-xl p-4" style={{ backgroundColor: '#101010', border: '1px solid rgba(248,113,113,0.2)' }}>
            <div className="flex items-center gap-2 mb-3">
              <AlertCircle size={16} style={{ color: '#fbbf24' }} />
              <p className="text-white text-sm font-medium">Onestà operativa brutale</p>
            </div>
            <ul className="text-xs text-gray-400 space-y-1 list-disc pl-4">
              {snapshot.honesty_notes.map((note) => (
                <li key={note}>{note}</li>
              ))}
            </ul>
            <div className="mt-3 text-[11px] text-gray-500">
              Ultima analisi: {new Date(snapshot.detected_at).toLocaleString('it-IT')}
              {snapshot.preferences.last_user_approved_at && (
                <span> · ultima approvazione utente: {new Date(snapshot.preferences.last_user_approved_at).toLocaleString('it-IT')}</span>
              )}
            </div>
          </div>
        </>
      )}

      {!snapshot && !loading && (
        <div className="rounded-xl p-4 text-sm text-gray-500" style={{ backgroundColor: '#111', border: '1px solid #222' }}>
          Nessuna snapshot disponibile al momento.
        </div>
      )}

      {loading && !snapshot && (
        <div className="rounded-xl p-4 text-sm text-cyan-300" style={{ backgroundColor: '#111', border: '1px solid #222' }}>
          Analisi runtime apps in corso…
        </div>
      )}
    </div>
  );
}
