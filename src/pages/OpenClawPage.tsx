// VIO 83 AI ORCHESTRA — OpenClaw Agent Page
// Copyright (c) 2026 Viorica Porcu. AGPL-3.0 / Proprietaria
import { AlertTriangle, CheckCircle2, Clock, Play, RefreshCw, Terminal, Zap } from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';
import { useI18n } from '../hooks/useI18n';

interface AgentStep {
  step: number;
  action: string;
  content: string;
  latency_ms: number;
}

interface AgentResult {
  task: string;
  answer: string;
  status: string;
  total_steps: number;
  total_latency_ms: number;
  tools_used: string[];
  steps: AgentStep[];
}

interface AgentCapabilities {
  name: string;
  version: string;
  status: string;
  max_iterations: number;
  plugins_loaded: number;
  total_tools: number;
  supported_providers: string[];
  capabilities: string[];
}

const API = 'http://localhost:4000';

export default function OpenClawPage() {
  const { t } = useI18n();
  const [task, setTask] = useState('');
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<AgentResult | null>(null);
  const [capabilities, setCapabilities] = useState<AgentCapabilities | null>(null);
  const [provider, setProvider] = useState('ollama');
  const [model, setModel] = useState('qwen2.5-coder:3b');
  const [error, setError] = useState<string | null>(null);

  const fetchCapabilities = useCallback(async () => {
    try {
      const resp = await fetch(`${API}/openclaw/capabilities`);
      if (resp.ok) setCapabilities(await resp.json());
    } catch {
      // ignore — will show degraded state
    }
  }, []);

  useEffect(() => { fetchCapabilities(); }, [fetchCapabilities]);

  const runTask = async () => {
    if (!task.trim() || running) return;
    setRunning(true);
    setError(null);
    setResult(null);
    try {
      const resp = await fetch(`${API}/openclaw/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          task: task.trim(),
          provider,
          model,
          max_iterations: 8,
        }),
      });
      if (!resp.ok) {
        const data = await resp.json().catch(() => null);
        throw new Error(data?.error || `HTTP ${resp.status}`);
      }
      setResult(await resp.json());
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setRunning(false);
    }
  };

  const stepColor: Record<string, string> = {
    think: 'var(--vio-cyan)',
    tool_call: 'var(--vio-green)',
    tool_result: 'var(--vio-yellow, #f0c040)',
    answer: 'var(--vio-green)',
    error: '#ef4444',
  };

  const stepIcon: Record<string, string> = {
    think: '🧠',
    tool_call: '🔧',
    tool_result: '📋',
    answer: '✅',
    error: '❌',
  };

  return (
    <div style={{
      height: '100%',
      display: 'flex',
      flexDirection: 'column',
      background: 'var(--vio-bg-primary)',
      color: 'var(--vio-text-primary)',
    }}>
      {/* Header */}
      <div style={{
        padding: '16px 20px',
        borderBottom: '1px solid var(--vio-border)',
        background: 'var(--vio-bg-secondary)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Zap size={22} color="var(--vio-green)" />
          <div>
            <h2 style={{ margin: 0, fontSize: '16px', fontWeight: 700 }}>
              {t('openclaw.title')}
            </h2>
            <p style={{ margin: 0, fontSize: '12px', color: 'var(--vio-text-dim)' }}>
              {t('openclaw.subtitle')}
            </p>
          </div>
          {capabilities && (
            <div style={{
              marginLeft: 'auto',
              display: 'flex',
              gap: '12px',
              fontSize: '11px',
              color: 'var(--vio-text-secondary)',
            }}>
              <span style={{ color: 'var(--vio-green)' }}>
                <CheckCircle2 size={12} style={{ verticalAlign: 'middle', marginRight: 3 }} />
                {capabilities.plugins_loaded} {t('openclaw.plugins')}
              </span>
              <span>
                <Terminal size={12} style={{ verticalAlign: 'middle', marginRight: 3 }} />
                {capabilities.total_tools} {t('openclaw.tools')}
              </span>
              <span>v{capabilities.version}</span>
              <button
                onClick={fetchCapabilities}
                style={{
                  background: 'none', border: 'none', cursor: 'pointer',
                  color: 'var(--vio-text-dim)', padding: '2px',
                }}
              >
                <RefreshCw size={12} />
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Main content */}
      <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
        {/* Left panel: Input */}
        <div style={{
          width: '40%',
          display: 'flex',
          flexDirection: 'column',
          borderRight: '1px solid var(--vio-border)',
          padding: '16px',
          gap: '12px',
        }}>
          {/* Task input */}
          <label style={{ fontSize: '12px', fontWeight: 600, color: 'var(--vio-text-secondary)' }}>
            {t('openclaw.taskLabel')}
          </label>
          <textarea
            value={task}
            onChange={(e) => setTask(e.target.value)}
            placeholder={t('openclaw.taskPlaceholder')}
            onKeyDown={(e) => { if (e.key === 'Enter' && e.metaKey) runTask(); }}
            style={{
              flex: 1,
              minHeight: '120px',
              background: 'var(--vio-bg-tertiary, #1a1a2e)',
              color: 'var(--vio-text-primary)',
              border: '1px solid var(--vio-border)',
              borderRadius: '8px',
              padding: '12px',
              fontSize: '13px',
              resize: 'none',
              fontFamily: 'inherit',
            }}
          />

          {/* Provider & Model */}
          <div style={{ display: 'flex', gap: '8px' }}>
            <select
              value={provider}
              onChange={(e) => setProvider(e.target.value)}
              style={{
                flex: 1,
                background: 'var(--vio-bg-tertiary, #1a1a2e)',
                color: 'var(--vio-text-primary)',
                border: '1px solid var(--vio-border)',
                borderRadius: '6px',
                padding: '6px 10px',
                fontSize: '12px',
              }}
            >
              <option value="ollama">Ollama (Local)</option>
              <option value="claude">Claude</option>
              <option value="gpt4">GPT-4</option>
              <option value="groq">Groq</option>
              <option value="deepseek">DeepSeek</option>
              <option value="mistral">Mistral</option>
            </select>
            <input
              value={model}
              onChange={(e) => setModel(e.target.value)}
              placeholder="model"
              style={{
                flex: 1,
                background: 'var(--vio-bg-tertiary, #1a1a2e)',
                color: 'var(--vio-text-primary)',
                border: '1px solid var(--vio-border)',
                borderRadius: '6px',
                padding: '6px 10px',
                fontSize: '12px',
              }}
            />
          </div>

          {/* Run button */}
          <button
            onClick={runTask}
            disabled={running || !task.trim()}
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
              padding: '10px 16px',
              background: running ? 'var(--vio-bg-tertiary, #1a1a2e)' : 'var(--vio-green)',
              color: running ? 'var(--vio-text-dim)' : '#000',
              border: 'none',
              borderRadius: '8px',
              fontWeight: 700,
              fontSize: '13px',
              cursor: running ? 'not-allowed' : 'pointer',
            }}
          >
            <Play size={14} />
            {running ? t('openclaw.running') : t('openclaw.run')}
          </button>

          {/* Capabilities list */}
          {capabilities && (
            <div style={{
              marginTop: '8px',
              padding: '10px',
              background: 'var(--vio-bg-tertiary, #1a1a2e)',
              borderRadius: '8px',
              fontSize: '11px',
              color: 'var(--vio-text-dim)',
            }}>
              <div style={{ fontWeight: 600, marginBottom: '6px', color: 'var(--vio-text-secondary)' }}>
                {t('openclaw.capabilities')}
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                {capabilities.capabilities.map((cap) => (
                  <span key={cap} style={{
                    padding: '2px 6px',
                    borderRadius: '4px',
                    background: 'var(--vio-bg-secondary)',
                    border: '1px solid var(--vio-border)',
                  }}>
                    {cap}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Right panel: Results */}
        <div style={{
          flex: 1,
          padding: '16px',
          overflow: 'auto',
        }}>
          {error && (
            <div style={{
              padding: '12px',
              background: 'rgba(239, 68, 68, 0.1)',
              border: '1px solid rgba(239, 68, 68, 0.3)',
              borderRadius: '8px',
              color: '#ef4444',
              fontSize: '13px',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              marginBottom: '12px',
            }}>
              <AlertTriangle size={16} />
              {error}
            </div>
          )}

          {running && (
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
              padding: '20px',
              color: 'var(--vio-text-dim)',
              fontSize: '13px',
            }}>
              <RefreshCw size={16} className="animate-spin" style={{ animation: 'spin 1s linear infinite' }} />
              {t('openclaw.thinking')}
            </div>
          )}

          {result && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {/* Summary */}
              <div style={{
                padding: '12px',
                background: 'var(--vio-bg-secondary)',
                borderRadius: '8px',
                border: '1px solid var(--vio-border)',
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                  <CheckCircle2 size={16} color={result.status === 'completed' ? 'var(--vio-green)' : 'var(--vio-yellow, #f0c040)'} />
                  <span style={{ fontWeight: 700, fontSize: '14px' }}>
                    {result.status === 'completed' ? t('openclaw.completed') : t('openclaw.partial')}
                  </span>
                  <span style={{ marginLeft: 'auto', fontSize: '11px', color: 'var(--vio-text-dim)' }}>
                    <Clock size={11} style={{ verticalAlign: 'middle', marginRight: 3 }} />
                    {result.total_latency_ms}ms · {result.total_steps} {t('openclaw.stepsLabel')}
                  </span>
                </div>
                {result.tools_used.length > 0 && (
                  <div style={{ fontSize: '11px', color: 'var(--vio-text-dim)', marginBottom: '8px' }}>
                    {t('openclaw.toolsUsed')}: {result.tools_used.join(', ')}
                  </div>
                )}
              </div>

              {/* Answer */}
              <div style={{
                padding: '14px',
                background: 'var(--vio-bg-tertiary, #1a1a2e)',
                borderRadius: '8px',
                border: '1px solid var(--vio-green)',
                fontSize: '13px',
                lineHeight: '1.6',
                whiteSpace: 'pre-wrap',
              }}>
                {result.answer}
              </div>

              {/* Steps */}
              {result.steps.length > 0 && (
                <details style={{ marginTop: '4px' }}>
                  <summary style={{
                    cursor: 'pointer',
                    fontSize: '12px',
                    fontWeight: 600,
                    color: 'var(--vio-text-secondary)',
                    padding: '6px 0',
                  }}>
                    {t('openclaw.showSteps')} ({result.steps.length})
                  </summary>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', marginTop: '8px' }}>
                    {result.steps.map((step, i) => (
                      <div key={i} style={{
                        padding: '8px 10px',
                        background: 'var(--vio-bg-secondary)',
                        borderRadius: '6px',
                        borderLeft: `3px solid ${stepColor[step.action] || 'var(--vio-border)'}`,
                        fontSize: '12px',
                      }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '4px' }}>
                          <span>{stepIcon[step.action] || '•'}</span>
                          <span style={{ fontWeight: 600, color: stepColor[step.action] }}>
                            {step.action}
                          </span>
                          <span style={{ marginLeft: 'auto', fontSize: '10px', color: 'var(--vio-text-dim)' }}>
                            {step.latency_ms}ms
                          </span>
                        </div>
                        <div style={{
                          color: 'var(--vio-text-dim)',
                          whiteSpace: 'pre-wrap',
                          maxHeight: '200px',
                          overflow: 'auto',
                          fontSize: '11px',
                        }}>
                          {step.content}
                        </div>
                      </div>
                    ))}
                  </div>
                </details>
              )}
            </div>
          )}

          {/* Empty state */}
          {!result && !running && !error && (
            <div style={{
              height: '100%',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '12px',
              color: 'var(--vio-text-dim)',
              textAlign: 'center',
            }}>
              <Zap size={40} strokeWidth={1} />
              <div style={{ fontSize: '14px', fontWeight: 600, color: 'var(--vio-text-secondary)' }}>
                {t('openclaw.emptyTitle')}
              </div>
              <div style={{ fontSize: '12px', maxWidth: '300px' }}>
                {t('openclaw.emptyDescription')}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
