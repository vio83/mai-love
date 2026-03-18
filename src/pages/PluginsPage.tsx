// VIO 83 AI ORCHESTRA — Plugins / MCP Page
// Copyright (c) 2026 Viorica Porcu. AGPL-3.0 / Proprietaria
import { CheckCircle2, Cpu, Play, RefreshCw, Search, Terminal, XCircle, Zap } from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';
import { useI18n } from '../hooks/useI18n';

interface PluginTool {
  name: string;
  description: string;
  parameters: Record<string, unknown>;
  examples: string[];
}

interface Plugin {
  id: string;
  name: string;
  version: string;
  description: string;
  author: string;
  icon: string;
  status: 'active' | 'disabled' | 'error';
  tools: PluginTool[];
  built_in: boolean;
}

interface ExecuteResult {
  pluginId: string;
  toolName: string;
  result: unknown;
  elapsed: number;
}

const API = 'http://localhost:8000';

export default function PluginsPage() {
  const { t } = useI18n();
  const [plugins, setPlugins] = useState<Plugin[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<Plugin | null>(null);
  const [selectedTool, setSelectedTool] = useState<string>('');
  const [toolParams, setToolParams] = useState<Record<string, string>>({});
  const [executing, setExecuting] = useState(false);
  const [lastResult, setLastResult] = useState<ExecuteResult | null>(null);

  const fetchPlugins = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const resp = await fetch(`${API}/plugins`);
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const data = await resp.json();
      setPlugins(data.plugins || []);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Errore caricamento plugin');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchPlugins(); }, [fetchPlugins]);

  const handleSelectPlugin = (plugin: Plugin) => {
    setSelected(plugin);
    setSelectedTool(plugin.tools[0]?.name || '');
    setToolParams({});
    setLastResult(null);
  };

  const handleExecute = async () => {
    if (!selected || !selectedTool) return;
    setExecuting(true);
    const start = Date.now();
    try {
      const resp = await fetch(`${API}/plugins/${selected.id}/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tool: selectedTool, params: toolParams }),
      });
      const data = await resp.json();
      setLastResult({
        pluginId: selected.id,
        toolName: selectedTool,
        result: data,
        elapsed: Date.now() - start,
      });
    } catch (e: unknown) {
      setLastResult({
        pluginId: selected.id,
        toolName: selectedTool,
        result: { error: e instanceof Error ? e.message : 'Errore' },
        elapsed: Date.now() - start,
      });
    } finally {
      setExecuting(false);
    }
  };

  const currentTool = selected?.tools.find(t => t.name === selectedTool);

  return (
    <div style={{
      height: '100%',
      display: 'flex',
      flexDirection: 'column',
      backgroundColor: 'var(--vio-bg-primary)',
      color: 'var(--vio-text-primary)',
      overflow: 'hidden',
    }}>
      {/* Header */}
      <div style={{
        padding: '20px 24px 16px',
        borderBottom: '1px solid var(--vio-border)',
        flexShrink: 0,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
      }}>
        <div>
          <h1 style={{ margin: 0, fontSize: '18px', fontWeight: 700, display: 'flex', alignItems: 'center', gap: 8 }}>
            <Cpu size={20} color="var(--vio-green)" />
            Plugin & Integrazioni
          </h1>
          <p style={{ margin: '4px 0 0', fontSize: '12px', color: 'var(--vio-text-dim)' }}>
            Sistema MCP-compatibile — {plugins.length} plugin installati
          </p>
        </div>
        <button
          onClick={fetchPlugins}
          title="Ricarica plugin"
          style={{
            background: 'none',
            border: '1px solid var(--vio-border)',
            borderRadius: '8px',
            color: 'var(--vio-text-secondary)',
            cursor: 'pointer',
            padding: '6px 12px',
            display: 'flex',
            alignItems: 'center',
            gap: 6,
            fontSize: '12px',
          }}
        >
          <RefreshCw size={14} />
          Ricarica
        </button>
      </div>

      <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
        {/* Plugin list */}
        <div style={{
          width: '260px',
          borderRight: '1px solid var(--vio-border)',
          overflowY: 'auto',
          padding: '12px',
          flexShrink: 0,
        }}>
          {loading ? (
            <div style={{ color: 'var(--vio-text-dim)', fontSize: '13px', padding: 12 }}>
              Caricamento plugin...
            </div>
          ) : error ? (
            <div style={{ color: '#ef4444', fontSize: '12px', padding: 12 }}>
              ⚠ {error}
              <br />
              <small>Assicurati che il backend sia in esecuzione</small>
            </div>
          ) : (
            plugins.map(plugin => (
              <button
                key={plugin.id}
                onClick={() => handleSelectPlugin(plugin)}
                style={{
                  width: '100%',
                  textAlign: 'left',
                  padding: '10px 12px',
                  borderRadius: '8px',
                  border: `1px solid ${selected?.id === plugin.id ? 'var(--vio-green)' : 'var(--vio-border)'}`,
                  backgroundColor: selected?.id === plugin.id ? 'rgba(0,255,0,0.06)' : 'var(--vio-bg-secondary)',
                  cursor: 'pointer',
                  marginBottom: '6px',
                  color: 'var(--vio-text-primary)',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                  <span style={{ fontSize: '16px' }}>{plugin.icon}</span>
                  <span style={{ fontWeight: 600, fontSize: '13px' }}>{plugin.name}</span>
                  {plugin.status === 'active' ? (
                    <CheckCircle2 size={12} color="var(--vio-green)" style={{ marginLeft: 'auto' }} />
                  ) : (
                    <XCircle size={12} color="#ef4444" style={{ marginLeft: 'auto' }} />
                  )}
                </div>
                <div style={{ fontSize: '11px', color: 'var(--vio-text-dim)' }}>
                  {plugin.tools.length} tools • v{plugin.version}
                </div>
              </button>
            ))
          )}
        </div>

        {/* Plugin detail + execute */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '20px' }}>
          {!selected ? (
            <div style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              height: '100%',
              gap: 12,
              color: 'var(--vio-text-dim)',
            }}>
              <Cpu size={40} />
              <div>Seleziona un plugin per esplorarlo ed eseguire i suoi tool</div>
            </div>
          ) : (
            <>
              {/* Plugin header */}
              <div style={{ marginBottom: '20px' }}>
                <h2 style={{ margin: 0, display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span style={{ fontSize: '20px' }}>{selected.icon}</span>
                  {selected.name}
                  <span style={{
                    fontSize: '11px',
                    padding: '2px 8px',
                    borderRadius: '12px',
                    backgroundColor: selected.status === 'active' ? 'rgba(0,255,0,0.1)' : 'rgba(239,68,68,0.1)',
                    color: selected.status === 'active' ? 'var(--vio-green)' : '#ef4444',
                    fontWeight: 500,
                  }}>
                    {selected.status}
                  </span>
                </h2>
                <p style={{ margin: '6px 0 0', color: 'var(--vio-text-secondary)', fontSize: '13px' }}>
                  {selected.description}
                </p>
                <div style={{ marginTop: 6, fontSize: '11px', color: 'var(--vio-text-dim)' }}>
                  ID: <code style={{ color: 'var(--vio-green)' }}>{selected.id}</code>
                  {' · '} Autore: {selected.author}
                  {' · '} v{selected.version}
                  {selected.built_in && ' · 🔒 Built-in'}
                </div>
              </div>

              {/* Tool selector */}
              <div style={{ marginBottom: '16px' }}>
                <label style={{ fontSize: '12px', color: 'var(--vio-text-dim)', marginBottom: 6, display: 'block' }}>
                  Tool da eseguire
                </label>
                <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                  {selected.tools.map(tool => (
                    <button
                      key={tool.name}
                      onClick={() => { setSelectedTool(tool.name); setToolParams({}); setLastResult(null); }}
                      style={{
                        padding: '6px 14px',
                        borderRadius: '16px',
                        border: `1px solid ${selectedTool === tool.name ? 'var(--vio-green)' : 'var(--vio-border)'}`,
                        backgroundColor: selectedTool === tool.name ? 'rgba(0,255,0,0.1)' : 'transparent',
                        color: selectedTool === tool.name ? 'var(--vio-green)' : 'var(--vio-text-secondary)',
                        cursor: 'pointer',
                        fontSize: '12px',
                        fontWeight: selectedTool === tool.name ? 600 : 400,
                      }}
                    >
                      {tool.name}
                    </button>
                  ))}
                </div>
              </div>

              {/* Tool description + params */}
              {currentTool && (
                <div style={{
                  backgroundColor: 'var(--vio-bg-secondary)',
                  border: '1px solid var(--vio-border)',
                  borderRadius: '10px',
                  padding: '14px',
                  marginBottom: '16px',
                }}>
                  <div style={{ fontSize: '12px', color: 'var(--vio-text-secondary)', marginBottom: 10 }}>
                    <Zap size={12} style={{ verticalAlign: 'middle', marginRight: 4 }} />
                    {currentTool.description}
                  </div>

                  {/* Dynamic parameter inputs */}
                  {Object.entries(currentTool.parameters).map(([paramName, paramDef]) => {
                    const def = paramDef as Record<string, unknown>;
                    return (
                      <div key={paramName} style={{ marginBottom: 10 }}>
                        <label style={{ fontSize: '11px', color: 'var(--vio-text-dim)', display: 'block', marginBottom: 4 }}>
                          {paramName}
                          {def.type && <span style={{ color: 'var(--vio-magenta)', marginLeft: 4 }}>({def.type as string})</span>}
                          {def.description && <span> — {def.description as string}</span>}
                        </label>
                        <input
                          type="text"
                          value={toolParams[paramName] || ''}
                          onChange={e => setToolParams(prev => ({ ...prev, [paramName]: e.target.value }))}
                          placeholder={def.default != null ? `default: ${def.default}` : `Inserisci ${paramName}...`}
                          style={{
                            width: '100%',
                            padding: '8px 12px',
                            borderRadius: '6px',
                            border: '1px solid var(--vio-border)',
                            backgroundColor: 'var(--vio-bg-primary)',
                            color: 'var(--vio-text-primary)',
                            fontSize: '13px',
                            outline: 'none',
                            boxSizing: 'border-box',
                          }}
                        />
                      </div>
                    );
                  })}

                  {/* Execute button */}
                  <button
                    onClick={handleExecute}
                    disabled={executing}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 8,
                      padding: '8px 20px',
                      borderRadius: '8px',
                      border: 'none',
                      backgroundColor: executing ? 'var(--vio-bg-tertiary)' : 'var(--vio-green)',
                      color: executing ? 'var(--vio-text-dim)' : '#000',
                      cursor: executing ? 'default' : 'pointer',
                      fontWeight: 600,
                      fontSize: '13px',
                      marginTop: 4,
                    }}
                  >
                    <Play size={14} />
                    {executing ? 'Esecuzione...' : `Esegui ${selectedTool}`}
                  </button>
                </div>
              )}

              {/* Result */}
              {lastResult && (
                <div>
                  <div style={{ fontSize: '12px', color: 'var(--vio-text-dim)', marginBottom: 6, display: 'flex', alignItems: 'center', gap: 8 }}>
                    <Terminal size={12} />
                    Risultato — {lastResult.elapsed}ms
                  </div>
                  <pre style={{
                    backgroundColor: 'var(--vio-bg-secondary)',
                    border: '1px solid var(--vio-border)',
                    borderRadius: '8px',
                    padding: '12px',
                    fontSize: '12px',
                    color: 'var(--vio-green)',
                    overflow: 'auto',
                    maxHeight: '300px',
                    margin: 0,
                    fontFamily: 'var(--vio-font-mono)',
                  }}>
                    {JSON.stringify(lastResult.result, null, 2)}
                  </pre>
                </div>
              )}

              {/* Examples */}
              {currentTool?.examples?.length ? (
                <div style={{ marginTop: 16 }}>
                  <div style={{ fontSize: '11px', color: 'var(--vio-text-dim)', marginBottom: 6 }}>
                    <Search size={11} style={{ verticalAlign: 'middle', marginRight: 4 }} />
                    Esempi:
                  </div>
                  {currentTool.examples.map((ex, i) => (
                    <code key={i} style={{
                      display: 'block',
                      fontSize: '11px',
                      color: 'var(--vio-text-secondary)',
                      backgroundColor: 'var(--vio-bg-tertiary)',
                      padding: '4px 8px',
                      borderRadius: '4px',
                      marginBottom: 4,
                    }}>
                      {ex}
                    </code>
                  ))}
                </div>
              ) : null}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
