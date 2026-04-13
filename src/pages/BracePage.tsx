import { useEffect, useMemo, useState } from 'react';
import { ShieldCheck, RefreshCw, PlayCircle, GaugeCircle } from 'lucide-react';

interface BraceStatePayload {
  status: string;
  state: {
    active: boolean;
    active_scenario: string;
    profile: {
      mode: string;
      intensity: number;
      safeguard: string;
      notes: string;
    };
    processed: number;
    updated_at: string;
  };
  available_scenarios: string[];
}

interface BraceScenariosPayload {
  status: string;
  scenarios: Record<string, { mode: string; intensity: number; safeguard: string; notes: string }>;
}

interface BraceProcessPayload {
  status: string;
  result: {
    signature: string;
    confidence: number;
    mode: string;
    recommendation: string;
    input_len: number;
    processed_total: number;
    updated_at: string;
  };
}

const API = 'http://localhost:4000';

export default function BracePage() {
  const [loading, setLoading] = useState(true);
  const [state, setState] = useState<BraceStatePayload | null>(null);
  const [scenarios, setScenarios] = useState<BraceScenariosPayload | null>(null);
  const [stimulus, setStimulus] = useState('Verifica robustezza locale con policy bunker.');
  const [result, setResult] = useState<BraceProcessPayload | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeScenario, setActiveScenario] = useState('baseline');

  const confidenceColor = useMemo(() => {
    const confidence = result?.result.confidence ?? 0;
    if (confidence >= 0.85) return 'var(--vio-green)';
    if (confidence >= 0.7) return 'var(--vio-yellow)';
    return 'var(--vio-red)';
  }, [result]);

  const refresh = async () => {
    setLoading(true);
    setError(null);
    try {
      const [stateResp, scenariosResp] = await Promise.all([
        fetch(`${API}/brace/state`),
        fetch(`${API}/brace/scenarios`),
      ]);
      if (!stateResp.ok || !scenariosResp.ok) {
        throw new Error('Endpoint BRACE non disponibili.');
      }

      const stateData = (await stateResp.json()) as BraceStatePayload;
      const scenarioData = (await scenariosResp.json()) as BraceScenariosPayload;
      setState(stateData);
      setScenarios(scenarioData);
      setActiveScenario(stateData.state.active_scenario);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Errore BRACE sconosciuto');
    } finally {
      setLoading(false);
    }
  };

  const loadScenario = async () => {
    setError(null);
    try {
      const resp = await fetch(`${API}/brace/load-scenario`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scenario: activeScenario }),
      });
      if (!resp.ok) {
        throw new Error('Caricamento scenario fallito.');
      }
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Errore load scenario');
    }
  };

  const processStimulus = async () => {
    setError(null);
    setResult(null);
    try {
      const resp = await fetch(`${API}/brace/process`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ stimulus }),
      });
      if (!resp.ok) {
        throw new Error('Process BRACE fallito.');
      }
      const data = (await resp.json()) as BraceProcessPayload;
      setResult(data);
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Errore process BRACE');
    }
  };

  useEffect(() => {
    void refresh();
  }, []);

  return (
    <div
      style={{
        height: '100%',
        overflow: 'auto',
        padding: '22px',
        background: 'var(--vio-bg-primary)',
        color: 'var(--vio-text-primary)',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '14px' }}>
        <ShieldCheck size={20} color="var(--vio-cyan)" />
        <h2 style={{ margin: 0, fontSize: '20px' }}>BRACE v3.0 Local Prototype</h2>
      </div>

      <p style={{ marginTop: 0, color: 'var(--vio-text-secondary)', fontSize: '13px' }}>
        Demo locale: processi su loopback, nessun invio cloud, controllo scenario e stress test operativo.
      </p>

      <div style={{ display: 'flex', gap: '10px', marginBottom: '14px', flexWrap: 'wrap' }}>
        <button
          onClick={refresh}
          disabled={loading}
          style={{
            border: '1px solid var(--vio-border)',
            background: 'var(--vio-bg-secondary)',
            color: 'var(--vio-text-primary)',
            borderRadius: '8px',
            padding: '8px 12px',
            display: 'flex',
            gap: '8px',
            alignItems: 'center',
            cursor: 'pointer',
          }}
        >
          <RefreshCw size={15} /> Refresh
        </button>

        <select
          value={activeScenario}
          onChange={(e) => setActiveScenario(e.target.value)}
          style={{
            border: '1px solid var(--vio-border)',
            background: 'var(--vio-bg-secondary)',
            color: 'var(--vio-text-primary)',
            borderRadius: '8px',
            padding: '8px 10px',
          }}
        >
          {(state?.available_scenarios ?? []).map((scenario) => (
            <option key={scenario} value={scenario}>
              {scenario}
            </option>
          ))}
        </select>

        <button
          onClick={loadScenario}
          style={{
            border: '1px solid var(--vio-cyan)',
            background: 'rgba(0,170,255,0.12)',
            color: 'var(--vio-cyan)',
            borderRadius: '8px',
            padding: '8px 12px',
            cursor: 'pointer',
          }}
        >
          Carica scenario
        </button>
      </div>

      {error && (
        <div
          style={{
            border: '1px solid rgba(255,60,60,0.45)',
            background: 'rgba(255,60,60,0.12)',
            color: 'var(--vio-red)',
            borderRadius: '10px',
            padding: '10px 12px',
            marginBottom: '12px',
            fontSize: '13px',
          }}
        >
          {error}
        </div>
      )}

      <div
        style={{
          border: '1px solid var(--vio-border)',
          borderRadius: '12px',
          padding: '14px',
          marginBottom: '14px',
          background: 'var(--vio-bg-secondary)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
          <GaugeCircle size={15} color="var(--vio-green)" />
          <strong>Stato BRACE</strong>
        </div>
        {loading ? (
          <div style={{ fontSize: '13px', color: 'var(--vio-text-dim)' }}>Caricamento stato...</div>
        ) : (
          <div style={{ fontSize: '13px', lineHeight: 1.5 }}>
            <div>Scenario attivo: {state?.state.active_scenario ?? 'n/a'}</div>
            <div>Mode: {state?.state.profile.mode ?? 'n/a'}</div>
            <div>Safeguard: {state?.state.profile.safeguard ?? 'n/a'}</div>
            <div>Processati: {state?.state.processed ?? 0}</div>
            <div>Aggiornato: {state?.state.updated_at ?? 'n/a'}</div>
          </div>
        )}
      </div>

      <div
        style={{
          border: '1px solid var(--vio-border)',
          borderRadius: '12px',
          padding: '14px',
          background: 'var(--vio-bg-secondary)',
        }}
      >
        <div style={{ marginBottom: '8px', fontWeight: 700 }}>Processo Stimulus</div>
        <textarea
          value={stimulus}
          onChange={(e) => setStimulus(e.target.value)}
          rows={4}
          style={{
            width: '100%',
            background: 'var(--vio-bg-primary)',
            color: 'var(--vio-text-primary)',
            border: '1px solid var(--vio-border)',
            borderRadius: '10px',
            padding: '10px',
            resize: 'vertical',
            marginBottom: '10px',
          }}
        />

        <button
          onClick={processStimulus}
          style={{
            border: '1px solid var(--vio-green)',
            background: 'rgba(0,255,0,0.12)',
            color: 'var(--vio-green)',
            borderRadius: '8px',
            padding: '8px 12px',
            display: 'inline-flex',
            alignItems: 'center',
            gap: '8px',
            cursor: 'pointer',
          }}
        >
          <PlayCircle size={15} /> Esegui process
        </button>

        {result && (
          <div style={{ marginTop: '12px', fontSize: '13px', lineHeight: 1.6 }}>
            <div>Signature: {result.result.signature}</div>
            <div style={{ color: confidenceColor }}>
              Confidence: {(result.result.confidence * 100).toFixed(1)}%
            </div>
            <div>Mode: {result.result.mode}</div>
            <div>Recommendation: {result.result.recommendation}</div>
            <div>Input len: {result.result.input_len}</div>
          </div>
        )}
      </div>

      {scenarios && (
        <div style={{ marginTop: '14px', fontSize: '12px', color: 'var(--vio-text-dim)' }}>
          Preset disponibili: {Object.keys(scenarios.scenarios).join(', ')}
        </div>
      )}
    </div>
  );
}
