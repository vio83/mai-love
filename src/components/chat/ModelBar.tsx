// VIO 83 AI ORCHESTRA — ModelBar: tutti i modelli pronti al click nella barra superiore
import { Cloud, Cpu, Globe, HardDrive, Zap } from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';
import { useAppStore } from '../../stores/appStore';
import type { AIProvider } from '../../types';

// ─── Registry modelli: ogni entry = un modello cliccabile ───
interface ModelEntry {
  id: string;           // ID univoco (usato come ollamaModel o cloudModelId)
  name: string;         // Nome display compatto
  provider: AIProvider; // Provider backend
  mode: 'local' | 'cloud';
  emoji: string;        // Icona rapida
  color: string;        // Colore pill
  tag?: string;         // Tag breve (opzionale)
}

const ALL_CHAT_MODELS: ModelEntry[] = [
  // ── Ollama (locali) ──
  { id: 'qwen2.5-coder:3b', name: 'Qwen Coder 3B', provider: 'ollama', mode: 'local', emoji: '🏠', color: '#00FF00', tag: 'Code' },
  { id: 'llama3.2:3b', name: 'Llama 3.2 3B', provider: 'ollama', mode: 'local', emoji: '🏠', color: '#00FF00', tag: 'General' },
  { id: 'gemma2:2b', name: 'Gemma 2 2B', provider: 'ollama', mode: 'local', emoji: '🏠', color: '#00FF00', tag: 'Fast' },
  { id: 'mistral:latest', name: 'Mistral 7B', provider: 'ollama', mode: 'local', emoji: '🏠', color: '#00FF00', tag: 'Quality' },
  { id: 'deepseek-r1:1.5b', name: 'DeepSeek R1 1.5B', provider: 'ollama', mode: 'local', emoji: '🏠', color: '#00FF00', tag: 'Reason' },
  // ── Cloud ──
  { id: 'claude-sonnet-4-6', name: 'Claude Sonnet 4.6', provider: 'claude', mode: 'cloud', emoji: '🧠', color: '#D97706', tag: 'Top' },
  { id: 'claude-opus-4-6', name: 'Claude Opus 4.6', provider: 'claude', mode: 'cloud', emoji: '🧠', color: '#D97706', tag: 'Agent' },
  { id: 'gpt-5.4', name: 'GPT-5.4', provider: 'gpt4', mode: 'cloud', emoji: '🌀', color: '#10B981', tag: 'Reason' },
  { id: 'gpt-5-mini', name: 'GPT-5 mini', provider: 'gpt4', mode: 'cloud', emoji: '🌀', color: '#10B981', tag: 'Fast' },
  { id: 'grok-4', name: 'Grok 4', provider: 'grok', mode: 'cloud', emoji: '🔮', color: '#3B82F6', tag: 'Realtime' },
  { id: 'gemini-2-5-pro', name: 'Gemini 2.5 Pro', provider: 'gemini', mode: 'cloud', emoji: '💎', color: '#06B6D4', tag: 'Long' },
  { id: 'gemini-2-5-flash', name: 'Gemini 2.5 Flash', provider: 'gemini', mode: 'cloud', emoji: '💎', color: '#06B6D4', tag: 'Speed' },
  { id: 'mistral-large', name: 'Mistral Large', provider: 'mistral', mode: 'cloud', emoji: '🌊', color: '#8B5CF6', tag: 'EU' },
  { id: 'deepseek-reasoner', name: 'DeepSeek R1', provider: 'deepseek', mode: 'cloud', emoji: '🔬', color: '#EC4899', tag: 'Math' },
  { id: 'groq-fast', name: 'Groq 120B', provider: 'groq', mode: 'cloud', emoji: '⚡', color: '#F97316', tag: 'Ultra' },
  { id: 'perplexity-pro', name: 'Perplexity Pro', provider: 'perplexity', mode: 'cloud', emoji: '🧭', color: '#60A5FA', tag: 'Search' },
  { id: 'openrouter-free', name: 'OpenRouter Free', provider: 'openrouter', mode: 'cloud', emoji: '🛣️', color: '#A855F7', tag: 'Free' },
  { id: 'together-llama', name: 'Together Llama', provider: 'together', mode: 'cloud', emoji: '🤝', color: '#14B8A6', tag: 'Budget' },
];

// Ollama status check
async function checkOllamaModels(host: string): Promise<string[]> {
  try {
    const resp = await fetch(`${host}/api/tags`, { signal: AbortSignal.timeout(3000) });
    if (!resp.ok) return [];
    const data = await resp.json();
    return (data.models || []).map((m: { name: string }) => m.name);
  } catch {
    return [];
  }
}

export default function ModelBar() {
  const settings = useAppStore(s => s.settings);
  const setOllamaModel = useAppStore(s => s.setOllamaModel);
  const setMode = useAppStore(s => s.setMode);
  const setProvider = useAppStore(s => s.setProvider);
  const [ollamaModels, setOllamaModels] = useState<string[]>([]);
  const [filter, setFilter] = useState<'all' | 'local' | 'cloud'>('all');

  // ID del modello attualmente selezionato
  const currentMode = settings.orchestrator.mode;
  const currentProvider = settings.orchestrator.primaryProvider;
  const currentOllamaModel = settings.ollamaModel || 'qwen2.5-coder:3b';

  // Controlla modelli Ollama disponibili
  useEffect(() => {
    checkOllamaModels(settings.ollamaHost).then(setOllamaModels);
  }, [settings.ollamaHost]);

  const isSelected = useCallback((entry: ModelEntry) => {
    if (entry.mode === 'local') {
      return currentMode === 'local' && currentOllamaModel === entry.id;
    }
    return currentMode === 'cloud' && currentProvider === entry.provider;
  }, [currentMode, currentOllamaModel, currentProvider]);

  const handleSelect = useCallback((entry: ModelEntry) => {
    if (entry.mode === 'local') {
      setMode('local');
      setOllamaModel(entry.id);
    } else {
      setMode('cloud');
      setProvider(entry.provider);
    }
  }, [setMode, setOllamaModel, setProvider]);

  const isOllamaAvailable = (modelId: string): boolean => {
    // Match anche modelli parziali (es. "qwen2.5-coder:3b" matcha "qwen2.5-coder:3b")
    return ollamaModels.some(m => m === modelId || m.startsWith(modelId.split(':')[0] ?? modelId));
  };

  const filteredModels = ALL_CHAT_MODELS.filter(m => {
    if (filter === 'local') return m.mode === 'local';
    if (filter === 'cloud') return m.mode === 'cloud';
    return true;
  });

  return (
    <div style={{
      borderBottom: '1px solid var(--vio-border)',
      backgroundColor: 'var(--vio-bg-secondary)',
      padding: '6px 12px',
      display: 'flex',
      flexDirection: 'column',
      gap: '4px',
    }}>
      {/* Filtri + stato */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '6px',
        fontSize: '11px',
      }}>
        <Zap size={12} style={{ color: 'var(--vio-green)' }} />
        <span style={{ color: 'var(--vio-text-dim)', fontWeight: 600 }}>Modelli</span>

        {(['all', 'local', 'cloud'] as const).map(f => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            style={{
              padding: '1px 8px',
              borderRadius: '10px',
              border: `1px solid ${filter === f ? 'var(--vio-green)' : 'var(--vio-border)'}`,
              backgroundColor: filter === f ? 'rgba(0,255,0,0.1)' : 'transparent',
              color: filter === f ? 'var(--vio-green)' : 'var(--vio-text-dim)',
              cursor: 'pointer',
              fontSize: '10px',
              fontWeight: 500,
            }}
          >
            {f === 'all' ? 'Tutti' : f === 'local' ? (
              <><HardDrive size={9} style={{ display: 'inline', verticalAlign: 'middle', marginRight: 2 }} />Locali</>
            ) : (
              <><Cloud size={9} style={{ display: 'inline', verticalAlign: 'middle', marginRight: 2 }} />Cloud</>
            )}
          </button>
        ))}

        <span style={{ marginLeft: 'auto', color: 'var(--vio-text-dim)', fontSize: '10px' }}>
          {currentMode === 'local' ? (
            <><Cpu size={10} style={{ display: 'inline', verticalAlign: 'middle' }} /> {currentOllamaModel}</>
          ) : (
            <><Globe size={10} style={{ display: 'inline', verticalAlign: 'middle' }} /> {currentProvider}</>
          )}
        </span>
      </div>

      {/* Modelli pill scrollabili */}
      <div style={{
        display: 'flex',
        gap: '4px',
        overflowX: 'auto',
        paddingBottom: '2px',
        scrollbarWidth: 'thin',
        scrollbarColor: 'var(--vio-border) transparent',
      }}>
        {filteredModels.map(entry => {
          const selected = isSelected(entry);
          const available = entry.mode === 'local' ? isOllamaAvailable(entry.id) : true;

          return (
            <button
              key={`${entry.provider}-${entry.id}`}
              onClick={() => handleSelect(entry)}
              title={`${entry.name} (${entry.provider}) — ${entry.mode === 'local' ? (available ? 'Disponibile' : 'Non scaricato') : 'Cloud'}`}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '3px',
                padding: '3px 8px',
                borderRadius: '12px',
                border: `1px solid ${selected ? entry.color : 'var(--vio-border)'}`,
                backgroundColor: selected ? `${entry.color}20` : 'transparent',
                color: selected ? entry.color : 'var(--vio-text-secondary)',
                cursor: 'pointer',
                fontSize: '10px',
                fontWeight: selected ? 600 : 400,
                whiteSpace: 'nowrap',
                flexShrink: 0,
                transition: 'all 0.15s',
                opacity: available ? 1 : 0.5,
              }}
            >
              <span style={{ fontSize: '11px' }}>{entry.emoji}</span>
              <span>{entry.name}</span>
              {entry.tag && (
                <span style={{
                  fontSize: '8px',
                  padding: '0 3px',
                  borderRadius: '4px',
                  backgroundColor: selected ? `${entry.color}30` : 'var(--vio-bg-tertiary)',
                  color: selected ? entry.color : 'var(--vio-text-dim)',
                  fontWeight: 500,
                }}>
                  {entry.tag}
                </span>
              )}
              {!available && entry.mode === 'local' && (
                <span style={{ fontSize: '8px', color: 'var(--vio-text-dim)' }}>⬇</span>
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
}

export { ALL_CHAT_MODELS };
export type { ModelEntry };
