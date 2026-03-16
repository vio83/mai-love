import { AlertCircle, Bot, Check, Eye, EyeOff, Globe, HardDrive, X, Zap } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { useAppStore } from '../../stores/appStore';
import type { AIProvider } from '../../types';
import { RuntimeAppsSettings } from './RuntimeAppsSettings';

const PROVIDER_INFO: Record<string, { name: string; color: string; placeholder: string; url: string }> = {
  claude: { name: 'Anthropic Claude', color: '#D97706', placeholder: 'sk-ant-...', url: 'https://console.anthropic.com/settings/keys' },
  gpt4: { name: 'OpenAI GPT-4', color: '#10B981', placeholder: 'sk-...', url: 'https://platform.openai.com/api-keys' },
  grok: { name: 'xAI Grok', color: '#3B82F6', placeholder: 'xai-...', url: 'https://console.x.ai/' },
  mistral: { name: 'Mistral AI', color: '#8B5CF6', placeholder: 'your-mistral-key', url: 'https://console.mistral.ai/api-keys/' },
  deepseek: { name: 'DeepSeek', color: '#EC4899', placeholder: 'sk-...', url: 'https://platform.deepseek.com/api_keys' },
  gemini: { name: 'Google Gemini', color: '#06B6D4', placeholder: 'AIza...', url: 'https://aistudio.google.com/apikey' },
  groq: { name: 'Groq', color: '#F97316', placeholder: 'gsk_...', url: 'https://console.groq.com/keys' },
  openrouter: { name: 'OpenRouter', color: '#A855F7', placeholder: 'sk-or-v1-...', url: 'https://openrouter.ai/keys' },
  together: { name: 'Together AI', color: '#14B8A6', placeholder: 'your-together-key', url: 'https://api.together.xyz/settings/api-keys' },
  perplexity: { name: 'Perplexity Agent API', color: '#60A5FA', placeholder: 'pplx_...', url: 'https://console.perplexity.ai/' },
};

const LOCAL_MODELS = [
  { id: 'qwen2.5-coder:3b', name: 'Qwen 2.5 Coder 3B', ram: '2.5 GB', best: 'Codice' },
  { id: 'llama3.2:3b', name: 'Llama 3.2 3B', ram: '2.5 GB', best: 'Generale' },
  { id: 'mistral:7b', name: 'Mistral 7B', ram: '5 GB', best: 'Ragionamento' },
  { id: 'phi3:3.8b', name: 'Phi-3 3.8B', ram: '3 GB', best: 'Efficienza' },
  { id: 'deepseek-coder-v2:lite', name: 'DeepSeek Coder V2', ram: '3.5 GB', best: 'Codice' },
  { id: 'gemma2:2b', name: 'Gemma 2 2B', ram: '2 GB', best: 'Velocità' },
];

type SettingsPanelProps = {
  variant?: 'modal' | 'page';
};

export function SettingsPanel({ variant = 'modal' }: SettingsPanelProps) {
  const { settings, toggleSettings, updateSettings, setCurrentPage, activateFullOrchestration } = useAppStore();
  const [apiKeys, setApiKeys] = useState<Record<string, string>>({});
  const [showKeys, setShowKeys] = useState<Record<string, boolean>>({});
  const [saved, setSaved] = useState<Record<string, boolean>>({});
  const [activeTab, setActiveTab] = useState<'cloud' | 'local' | 'apps' | 'general'>('cloud');
  const [ollamaHost, setOllamaHost] = useState(settings.ollamaHost || 'http://localhost:11434');
  const [hostSaved, setHostSaved] = useState(false);
  const [strictPolicySyncState, setStrictPolicySyncState] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle');

  const savedKeysByProvider = useMemo(
    () => Object.fromEntries(settings.apiKeys.map((entry) => [entry.provider, entry.key])),
    [settings.apiKeys]
  );

  useEffect(() => {
    setApiKeys(savedKeysByProvider);
  }, [savedKeysByProvider]);

  useEffect(() => {
    setOllamaHost(settings.ollamaHost || 'http://localhost:11434');
  }, [settings.ollamaHost]);

  useEffect(() => {
    let cancelled = false;

    const syncPolicyFromBackend = async () => {
      try {
        const response = await fetch('http://localhost:4000/knowledge/scheduler');
        if (!response.ok) return;

        const data = await response.json();
        if (cancelled || data?.status !== 'ok') return;

        const strictFromBackend = Boolean(data.policy?.strict_evidence_mode);
        const current = useAppStore.getState().settings.orchestrator;

        if ((current.strictEvidenceMode ?? true) !== strictFromBackend) {
          updateSettings({
            orchestrator: {
              ...current,
              strictEvidenceMode: strictFromBackend,
            },
          });
        }
      } catch {
        // backend non disponibile: mantieni stato locale
      }
    };

    void syncPolicyFromBackend();
    return () => { cancelled = true; };
  }, [updateSettings]);

  const handleClose = () => {
    if (variant === 'page') {
      setCurrentPage('dashboard');
      return;
    }

    toggleSettings();
  };

  const handleSaveKey = (provider: string) => {
    const key = apiKeys[provider];
    if (!key || key.length < 5) return;

    const nextApiKeys = [
      ...settings.apiKeys.filter(entry => entry.provider !== provider),
      {
        provider: provider as AIProvider,
        key,
        isValid: true,
        lastChecked: Date.now(),
      },
    ];

    updateSettings({ apiKeys: nextApiKeys });
    setSaved(prev => ({ ...prev, [provider]: true }));
    setTimeout(() => setSaved(prev => ({ ...prev, [provider]: false })), 2000);
  };

  const handleSaveOllamaHost = () => {
    const normalizedHost = ollamaHost.trim();
    if (!/^https?:\/\//.test(normalizedHost)) return;

    updateSettings({ ollamaHost: normalizedHost });
    setHostSaved(true);
    setTimeout(() => setHostSaved(false), 2000);
  };

  const toggleShowKey = (provider: string) => {
    setShowKeys(prev => ({ ...prev, [provider]: !prev[provider] }));
  };

  const strictEvidenceMode = settings.orchestrator.strictEvidenceMode ?? true;

  const handleToggleStrictEvidence = async () => {
    const current = useAppStore.getState().settings.orchestrator;
    updateSettings({
      orchestrator: {
        ...current,
        strictEvidenceMode: !strictEvidenceMode,
      },
    });

    setStrictPolicySyncState('saving');

    try {
      const scheduler = await fetch('http://localhost:4000/knowledge/scheduler')
        .then((r) => r.ok ? r.json() : null)
        .catch(() => null);

      const minimumDomainScore = Number(scheduler?.policy?.minimum_domain_score ?? 70);
      const response = await fetch(
        `http://localhost:4000/knowledge/policy?strict_evidence_mode=${!strictEvidenceMode}&minimum_domain_score=${minimumDomainScore}`,
        { method: 'PUT' },
      );

      if (response.ok) {
        setStrictPolicySyncState('saved');
        window.setTimeout(() => setStrictPolicySyncState('idle'), 1800);
      } else {
        setStrictPolicySyncState('error');
      }
    } catch {
      setStrictPolicySyncState('error');
    }
  };

  return (
    <div
      className={variant === 'modal' ? 'fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm' : 'h-full'}
      style={variant === 'page' ? { position: 'relative', zIndex: 1, padding: '28px 32px', overflowY: 'auto', height: '100%' } : undefined}
    >
      <div
        className={variant === 'modal' ? 'w-full max-w-2xl max-h-[85vh] rounded-2xl overflow-hidden' : 'w-full rounded-2xl overflow-hidden'}
        style={{ backgroundColor: '#0a0a0a', border: '1px solid #1a1a1a' }}
      >

        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4" style={{ borderBottom: '1px solid #1a1a1a' }}>
          <div className="flex items-center gap-3">
            <Zap size={20} style={{ color: '#00ff00' }} />
            <h2 className="text-lg font-semibold text-white">
              {variant === 'page' ? 'Settings Command Center' : 'Impostazioni Orchestra'}
            </h2>
          </div>
          <button onClick={handleClose} className="p-2 rounded-lg hover:bg-white/10 transition-colors">
            <X size={18} className="text-gray-400" />
          </button>
        </div>

        {/* Tabs */}
        <div className="flex px-6 pt-4 gap-1">
          {[
            { id: 'cloud' as const, label: 'Cloud API', icon: Globe },
            { id: 'local' as const, label: 'Locale', icon: HardDrive },
            { id: 'apps' as const, label: 'App AI', icon: Bot },
            { id: 'general' as const, label: 'Generale', icon: Zap },
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className="flex items-center gap-2 px-4 py-2 rounded-t-lg text-sm font-medium transition-colors"
              style={{
                backgroundColor: activeTab === tab.id ? '#1a1a1a' : 'transparent',
                color: activeTab === tab.id ? '#00ff00' : '#888',
              }}
            >
              <tab.icon size={14} />
              {tab.label}
            </button>
          ))}
        </div>

        {/* Content */}
        <div
          className="px-6 py-4 overflow-y-auto"
          style={{ maxHeight: variant === 'modal' ? 'calc(85vh - 140px)' : 'none', backgroundColor: '#0d0d0d' }}
        >

          {/* TAB: Cloud API Keys */}
          {activeTab === 'cloud' && (
            <div className="space-y-4">
              <p className="text-sm text-gray-500 mb-4">
                Inserisci le API key dei provider cloud. In questa build vengono salvate nello storage locale dell'app; l'integrazione Keychain richiede il layer Tauri nativo.
              </p>
              {Object.entries(PROVIDER_INFO).map(([key, info]) => (
                <div key={key} className="rounded-xl p-4" style={{ backgroundColor: '#111', border: '1px solid #222' }}>
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 rounded-full" style={{ backgroundColor: info.color }} />
                      <span className="text-white font-medium text-sm">{info.name}</span>
                    </div>
                    <a href={info.url} target="_blank" rel="noopener noreferrer"
                       className="text-xs hover:underline" style={{ color: info.color }}>
                      Ottieni API Key →
                    </a>
                  </div>
                  <div className="flex gap-2">
                    <div className="flex-1 relative">
                      <input
                        type={showKeys[key] ? 'text' : 'password'}
                        placeholder={info.placeholder}
                        value={apiKeys[key] || ''}
                        onChange={e => setApiKeys(prev => ({ ...prev, [key]: e.target.value }))}
                        className="w-full px-3 py-2 pr-10 rounded-lg text-sm text-white placeholder-gray-600 outline-none focus:ring-1"
                        style={{ backgroundColor: '#0a0a0a', border: '1px solid #333' }}
                      />
                      <button
                        onClick={() => toggleShowKey(key)}
                        className="absolute right-2 top-1/2 -translate-y-1/2 p-1 text-gray-500 hover:text-gray-300"
                      >
                        {showKeys[key] ? <EyeOff size={14} /> : <Eye size={14} />}
                      </button>
                    </div>
                    <button
                      onClick={() => handleSaveKey(key)}
                      className="px-4 py-2 rounded-lg text-sm font-medium transition-all"
                      style={{
                        backgroundColor: saved[key] ? '#00ff0020' : `${info.color}20`,
                        color: saved[key] ? '#00ff00' : info.color,
                        border: `1px solid ${saved[key] ? '#00ff0040' : info.color + '40'}`,
                      }}
                    >
                      {saved[key] ? <Check size={14} /> : 'Salva'}
                    </button>
                  </div>
                  {savedKeysByProvider[key] && (
                    <p className="mt-2 text-xs" style={{ color: '#6b7280' }}>
                      Chiave presente in configurazione locale.
                    </p>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* TAB: Local Models */}
          {activeTab === 'local' && (
            <div className="space-y-4">
              <div className="rounded-xl p-4" style={{ backgroundColor: '#111', border: '1px solid #222' }}>
                <label className="text-sm text-gray-400 mb-2 block">Ollama Host</label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={ollamaHost}
                    onChange={e => setOllamaHost(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg text-sm text-white outline-none"
                    style={{ backgroundColor: '#0a0a0a', border: '1px solid #333' }}
                  />
                  <button
                    onClick={handleSaveOllamaHost}
                    className="px-4 py-2 rounded-lg text-sm font-medium transition-all"
                    style={{
                      backgroundColor: hostSaved ? '#00ff0020' : '#00ff0010',
                      color: '#00ff00',
                      border: '1px solid #00ff0030',
                    }}
                  >
                    {hostSaved ? <Check size={14} /> : 'Salva'}
                  </button>
                </div>
              </div>

              <p className="text-sm text-gray-500">
                Modelli disponibili per 8GB RAM. Scarica con: <code className="text-green-400">ollama pull nome-modello</code>
              </p>

              {LOCAL_MODELS.map(model => (
                <div key={model.id} className="flex items-center justify-between rounded-xl p-4"
                     style={{ backgroundColor: '#111', border: '1px solid #222' }}>
                  <div>
                    <p className="text-white text-sm font-medium">{model.name}</p>
                    <p className="text-gray-500 text-xs mt-1">RAM: {model.ram} · Ottimale per: {model.best}</p>
                  </div>
                  <code className="text-xs px-2 py-1 rounded" style={{ backgroundColor: '#00ff0010', color: '#00ff00' }}>
                    {model.id}
                  </code>
                </div>
              ))}

              <div className="rounded-xl p-4" style={{ backgroundColor: '#0a1a0a', border: '1px solid #00ff0020' }}>
                <div className="flex items-start gap-2">
                  <AlertCircle size={16} style={{ color: '#00ff00', marginTop: 2 }} />
                  <div>
                    <p className="text-sm text-green-400 font-medium">Nota: 8GB RAM</p>
                    <p className="text-xs text-gray-500 mt-1">
                      Con 8GB di RAM, usa un solo modello alla volta. I modelli 3B sono i più performanti.
                      Per modelli 7B+, chiudi le altre applicazioni prima dell'uso.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB: App AI & Runtime */}
          {activeTab === 'apps' && <RuntimeAppsSettings />}

          {/* TAB: General */}
          {activeTab === 'general' && (
            <div className="space-y-4">
              <div className="rounded-xl p-4" style={{ backgroundColor: '#111', border: '1px solid #222' }}>
                <p className="text-white text-sm font-medium mb-2">Routing Intelligente</p>
                <p className="text-gray-500 text-xs mb-3">
                  L'orchestra seleziona automaticamente il modello migliore per ogni tipo di richiesta.
                </p>
                <button
                  onClick={activateFullOrchestration}
                  className="mb-3 px-3 py-2 rounded-lg text-xs font-semibold"
                  style={{
                    backgroundColor: '#00ff0015',
                    border: '1px solid #00ff0040',
                    color: '#00ff00',
                  }}
                >
                  ATTIVA STACK COMPLETO (LOCAL/PROXY)
                </button>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  {[
                    { type: 'Codice', provider: 'Claude / Groq / Qwen' },
                    { type: 'Legale', provider: 'Claude / Perplexity / Mistral' },
                    { type: 'Medicina', provider: 'Claude / Gemini / Perplexity' },
                    { type: 'Scrittura', provider: 'Claude / GPT-5 / Mistral' },
                    { type: 'Ricerca', provider: 'Perplexity / Claude / Grok' },
                    { type: 'Realtime', provider: 'Grok / Perplexity / Gemini' },
                    { type: 'Ragionamento', provider: 'Claude / DeepSeek / Phi-3' },
                    { type: 'Automazione', provider: 'Claude / Groq / Ollama' },
                  ].map(r => (
                    <div key={r.type} className="flex justify-between px-3 py-2 rounded-lg" style={{ backgroundColor: '#0a0a0a' }}>
                      <span className="text-gray-400">{r.type}</span>
                      <span style={{ color: '#00ff00' }}>{r.provider}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="rounded-xl p-4" style={{ backgroundColor: '#111', border: '1px solid #222' }}>
                <p className="text-white text-sm font-medium mb-2">Cross-Check</p>
                <p className="text-gray-500 text-xs">
                  Quando attivato, una seconda AI verifica la risposta della prima.
                  Utile per risposte critiche ma aumenta latenza e costi.
                </p>
              </div>

              <div className="rounded-xl p-4" style={{ backgroundColor: '#111', border: '1px solid #222' }}>
                <p className="text-white text-sm font-medium mb-2">RAG — Verifica Fonti Certificate</p>
                <p className="text-gray-500 text-xs">
                  Il sistema RAG confronta le risposte AI con un database di fonti certificate
                  (accademiche, bibliotecarie, ufficiali). Badge qualità: 🥇 Gold, 🥈 Silver, 🥉 Bronze.
                </p>
              </div>

              <div className="rounded-xl p-4" style={{ backgroundColor: '#111', border: '1px solid #222' }}>
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <p className="text-white text-sm font-medium mb-2">Strict Evidence Policy</p>
                    <p className="text-gray-500 text-xs">
                      Se attiva, l'orchestratore risponde solo con evidenze certificate via RAG; in assenza di fonti,
                      restituisce fallback esplicito invece di inventare contenuti.
                    </p>
                  </div>
                  <button
                    onClick={handleToggleStrictEvidence}
                    className="px-3 py-2 rounded-lg text-xs font-semibold"
                    style={{
                      backgroundColor: strictEvidenceMode ? '#00ff0018' : '#ffffff12',
                      border: strictEvidenceMode ? '1px solid #00ff0045' : '1px solid #ffffff25',
                      color: strictEvidenceMode ? '#00ff00' : '#9ca3af',
                      minWidth: '80px',
                    }}
                  >
                    {strictEvidenceMode ? 'ON' : 'OFF'}
                  </button>
                </div>
                {strictPolicySyncState !== 'idle' && (
                  <p className="mt-2 text-[11px]"
                    style={{ color: strictPolicySyncState === 'saved' ? '#00ff00' : strictPolicySyncState === 'saving' ? '#67e8f9' : '#f87171' }}
                  >
                    {strictPolicySyncState === 'saving' && 'Sincronizzazione policy con backend…'}
                    {strictPolicySyncState === 'saved' && 'Policy strict sincronizzata con successo.'}
                    {strictPolicySyncState === 'error' && 'Sync backend non riuscita: resta attivo lo stato locale.'}
                  </p>
                )}
              </div>

              <div className="rounded-xl p-4" style={{ backgroundColor: '#111', border: '1px solid #222' }}>
                <p className="text-white text-sm font-medium mb-3">Info Sistema</p>
                <div className="space-y-1 text-xs">
                  <div className="flex justify-between"><span className="text-gray-500">Versione</span><span className="text-white">0.1.0-alpha</span></div>
                  <div className="flex justify-between"><span className="text-gray-500">Framework</span><span className="text-white">Tauri 2.0 + React 18</span></div>
                  <div className="flex justify-between"><span className="text-gray-500">Orchestratore</span><span className="text-white">Direct Router + FastAPI</span></div>
                  <div className="flex justify-between"><span className="text-gray-500">Vector DB</span><span className="text-white">ChromaDB</span></div>
                  <div className="flex justify-between"><span className="text-gray-500">Ollama Host</span><span className="text-white">{settings.ollamaHost}</span></div>
                  <div className="flex justify-between"><span className="text-gray-500">Autore</span><span style={{ color: '#00ff00' }}>PadronaVio</span></div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
