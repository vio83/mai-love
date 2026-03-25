import { AlertCircle, Bot, Check, Eye, EyeOff, Globe, HardDrive, X, Zap } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { useI18n } from '../../hooks/useI18n';
import { saveApiKey, saveSetting } from '../../services/settingsService';
import { useAppStore } from '../../stores/appStore';
import type { AIProvider } from '../../types';
import { RuntimeAppsSettings } from './RuntimeAppsSettings';

const PROVIDER_INFO: Record<
  string,
  { name: string; color: string; placeholder: string; url: string }
> = {
  claude: {
    name: 'Anthropic Claude',
    color: '#D97706',
    placeholder: 'sk-ant-...',
    url: 'https://console.anthropic.com/settings/keys',
  },
  gpt4: {
    name: 'OpenAI GPT-4',
    color: '#10B981',
    placeholder: 'sk-...',
    url: 'https://platform.openai.com/api-keys',
  },
  grok: {
    name: 'xAI Grok',
    color: '#3B82F6',
    placeholder: 'xai-...',
    url: 'https://console.x.ai/',
  },
  mistral: {
    name: 'Mistral AI',
    color: '#8B5CF6',
    placeholder: 'your-mistral-key',
    url: 'https://console.mistral.ai/api-keys/',
  },
  deepseek: {
    name: 'DeepSeek',
    color: '#EC4899',
    placeholder: 'sk-...',
    url: 'https://platform.deepseek.com/api_keys',
  },
  gemini: {
    name: 'Google Gemini',
    color: '#06B6D4',
    placeholder: 'AIza...',
    url: 'https://aistudio.google.com/apikey',
  },
  groq: {
    name: 'Groq',
    color: '#F97316',
    placeholder: 'gsk_...',
    url: 'https://console.groq.com/keys',
  },
  openrouter: {
    name: 'OpenRouter',
    color: '#A855F7',
    placeholder: 'sk-or-v1-...',
    url: 'https://openrouter.ai/keys',
  },
  together: {
    name: 'Together AI',
    color: '#14B8A6',
    placeholder: 'your-together-key',
    url: 'https://api.together.xyz/settings/api-keys',
  },
  perplexity: {
    name: 'Perplexity Agent API',
    color: '#60A5FA',
    placeholder: 'pplx_...',
    url: 'https://console.perplexity.ai/',
  },
};

const LOCAL_MODELS = [
  {
    id: 'qwen2.5-coder:3b',
    name: 'Qwen 2.5 Coder 3B',
    ram: '2.5 GB',
    bestKey: 'settingsPanel.modelBestCode',
  },
  {
    id: 'llama3.2:3b',
    name: 'Llama 3.2 3B',
    ram: '2.5 GB',
    bestKey: 'settingsPanel.modelBestGeneral',
  },
  {
    id: 'mistral:latest',
    name: 'Mistral (latest)',
    ram: '5 GB',
    bestKey: 'settingsPanel.modelBestReasoning',
  },
  {
    id: 'deepseek-r1:latest',
    name: 'DeepSeek R1 (latest)',
    ram: '5+ GB',
    bestKey: 'settingsPanel.modelBestAdvancedReasoning',
  },
  {
    id: 'codellama:latest',
    name: 'CodeLlama (latest)',
    ram: '4+ GB',
    bestKey: 'settingsPanel.modelBestCodeSpecialist',
  },
  { id: 'gemma2:2b', name: 'Gemma 2 2B', ram: '2 GB', bestKey: 'settingsPanel.modelBestSpeed' },
];

const ROUTING_MATRIX = [
  { typeKey: 'settingsPanel.routeCode', provider: 'Claude / Groq / Qwen' },
  { typeKey: 'settingsPanel.routeLegal', provider: 'Claude / Perplexity / Mistral' },
  { typeKey: 'settingsPanel.routeMedical', provider: 'Claude / Gemini / Perplexity' },
  { typeKey: 'settingsPanel.routeWriting', provider: 'Claude / GPT-5 / Mistral' },
  { typeKey: 'settingsPanel.routeResearch', provider: 'Perplexity / Claude / Grok' },
  { typeKey: 'settingsPanel.routeRealtime', provider: 'Grok / Perplexity / Gemini' },
  { typeKey: 'settingsPanel.routeReasoning', provider: 'Claude / DeepSeek / Phi-3' },
  { typeKey: 'settingsPanel.routeAutomation', provider: 'Claude / Groq / Ollama' },
];

type SettingsPanelProps = {
  variant?: 'modal' | 'page';
};

export function SettingsPanel({ variant = 'modal' }: SettingsPanelProps) {
  const { t } = useI18n();
  const settings = useAppStore((s) => s.settings);
  const toggleSettings = useAppStore((s) => s.toggleSettings);
  const updateSettings = useAppStore((s) => s.updateSettings);
  const setCurrentPage = useAppStore((s) => s.setCurrentPage);
  const activateFullOrchestration = useAppStore((s) => s.activateFullOrchestration);
  const [apiKeys, setApiKeys] = useState<Record<string, string>>({});
  const [showKeys, setShowKeys] = useState<Record<string, boolean>>({});
  const [saved, setSaved] = useState<Record<string, boolean>>({});
  const [activeTab, setActiveTab] = useState<'cloud' | 'local' | 'apps' | 'general'>('cloud');
  const [ollamaHost, setOllamaHost] = useState(settings.ollamaHost || 'http://localhost:11434');
  const [hostSaved, setHostSaved] = useState(false);
  const [strictPolicySyncState, setStrictPolicySyncState] = useState<
    'idle' | 'saving' | 'saved' | 'error'
  >('idle');

  const savedKeysByProvider = useMemo(
    () => Object.fromEntries(settings.apiKeys.map((entry) => [entry.provider, entry.key])),
    [settings.apiKeys],
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
    return () => {
      cancelled = true;
    };
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
      ...settings.apiKeys.filter((entry) => entry.provider !== provider),
      {
        provider: provider as AIProvider,
        key,
        isValid: true,
        lastChecked: Date.now(),
      },
    ];

    updateSettings({ apiKeys: nextApiKeys });
    // Sync al backend (best-effort — non blocca UI)
    fetch(`/api/settings/api_key_${provider}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ value: key }),
    }).catch(() => {});
    setSaved((prev) => ({ ...prev, [provider]: true }));
    setTimeout(() => setSaved((prev) => ({ ...prev, [provider]: false })), 2000);
  };

  const handleSaveOllamaHost = () => {
    const normalizedHost = ollamaHost.trim();
    if (!/^https?:\/\//.test(normalizedHost)) return;

    updateSettings({ ollamaHost: normalizedHost });
    fetch(`/api/settings/ollama_host`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ value: normalizedHost }),
    }).catch(() => {});
    setHostSaved(true);
    setTimeout(() => setHostSaved(false), 2000);
  };

  const toggleShowKey = (provider: string) => {
    setShowKeys((prev) => ({ ...prev, [provider]: !prev[provider] }));
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
        .then((r) => (r.ok ? r.json() : null))
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
      className={
        variant === 'modal'
          ? 'fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm'
          : 'h-full'
      }
      style={
        variant === 'page'
          ? {
              position: 'relative',
              zIndex: 1,
              padding: '28px 32px',
              overflowY: 'auto',
              height: '100%',
            }
          : undefined
      }
    >
      <div
        className={
          variant === 'modal'
            ? 'w-full max-w-2xl max-h-[85vh] rounded-2xl overflow-hidden'
            : 'w-full rounded-2xl overflow-hidden'
        }
        style={{ backgroundColor: '#0a0a0a', border: '1px solid #1a1a1a' }}
      >
        {/* Header */}
        <div
          className="flex items-center justify-between px-6 py-4"
          style={{ borderBottom: '1px solid #1a1a1a' }}
        >
          <div className="flex items-center gap-3">
            <Zap size={20} style={{ color: '#00ff00' }} />
            <h2 className="text-lg font-semibold text-white">
              {variant === 'page'
                ? t('settingsPanel.commandCenterPage')
                : t('settingsPanel.commandCenter')}
            </h2>
          </div>
          <button
            onClick={handleClose}
            className="p-2 rounded-lg hover:bg-white/10 transition-colors"
          >
            <X size={18} className="text-gray-400" />
          </button>
        </div>

        {/* Tabs */}
        <div className="flex px-6 pt-4 gap-1">
          {[
            { id: 'cloud' as const, label: t('settingsPanel.tabCloud'), icon: Globe },
            { id: 'local' as const, label: t('settingsPanel.tabLocal'), icon: HardDrive },
            { id: 'apps' as const, label: t('settingsPanel.tabApps'), icon: Bot },
            { id: 'general' as const, label: t('settingsPanel.tabGeneral'), icon: Zap },
          ].map((tab) => (
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
          style={{
            maxHeight: variant === 'modal' ? 'calc(85vh - 140px)' : 'none',
            backgroundColor: '#0d0d0d',
          }}
        >
          {/* TAB: Cloud API Keys */}
          {activeTab === 'cloud' && (
            <div className="space-y-4">
              <p className="text-sm text-gray-500 mb-4">{t('settingsPanel.cloudDescription')}</p>
              {Object.entries(PROVIDER_INFO).map(([key, info]) => (
                <div
                  key={key}
                  className="rounded-xl p-4"
                  style={{ backgroundColor: '#111', border: '1px solid #222' }}
                >
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <div
                        className="w-3 h-3 rounded-full"
                        style={{ backgroundColor: info.color }}
                      />
                      <span className="text-white font-medium text-sm">{info.name}</span>
                    </div>
                    <a
                      href={info.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-xs hover:underline"
                      style={{ color: info.color }}
                    >
                      {t('settingsPanel.getApiKey')}
                    </a>
                  </div>
                  <div className="flex gap-2">
                    <div className="flex-1 relative">
                      <input
                        type={showKeys[key] ? 'text' : 'password'}
                        placeholder={info.placeholder}
                        value={apiKeys[key] || ''}
                        onChange={(e) => setApiKeys((prev) => ({ ...prev, [key]: e.target.value }))}
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
                      {saved[key] ? <Check size={14} /> : t('settings.save')}
                    </button>
                  </div>
                  {savedKeysByProvider[key] && (
                    <p className="mt-2 text-xs" style={{ color: '#6b7280' }}>
                      {t('settingsPanel.keyPresent')}
                    </p>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* TAB: Local Models */}
          {activeTab === 'local' && (
            <div className="space-y-4">
              <div
                className="rounded-xl p-4"
                style={{ backgroundColor: '#111', border: '1px solid #222' }}
              >
                <label className="text-sm text-gray-400 mb-2 block">
                  {t('settingsPanel.ollamaHost')}
                </label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={ollamaHost}
                    onChange={(e) => setOllamaHost(e.target.value)}
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
                    {hostSaved ? <Check size={14} /> : t('settings.save')}
                  </button>
                </div>
              </div>

              <p className="text-sm text-gray-500">
                {t('settingsPanel.localModelsHint', { command: 'ollama pull nome-modello' })}
              </p>

              {LOCAL_MODELS.map((model) => (
                <div
                  key={model.id}
                  className="flex items-center justify-between rounded-xl p-4"
                  style={{ backgroundColor: '#111', border: '1px solid #222' }}
                >
                  <div>
                    <p className="text-white text-sm font-medium">{model.name}</p>
                    <p className="text-gray-500 text-xs mt-1">
                      RAM: {model.ram} · {t('settingsPanel.bestFor')}: {t(model.bestKey)}
                    </p>
                  </div>
                  <code
                    className="text-xs px-2 py-1 rounded"
                    style={{ backgroundColor: '#00ff0010', color: '#00ff00' }}
                  >
                    {model.id}
                  </code>
                </div>
              ))}

              <div
                className="rounded-xl p-4"
                style={{ backgroundColor: '#0a1a0a', border: '1px solid #00ff0020' }}
              >
                <div className="flex items-start gap-2">
                  <AlertCircle size={16} style={{ color: '#00ff00', marginTop: 2 }} />
                  <div>
                    <p className="text-sm text-green-400 font-medium">
                      {t('settingsPanel.ramNoteTitle')}
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                      {t('settingsPanel.ramNoteDescription')}
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
              <div
                className="rounded-xl p-4"
                style={{ backgroundColor: '#111', border: '1px solid #222' }}
              >
                <p className="text-white text-sm font-medium mb-2">
                  {t('settingsPanel.routingTitle')}
                </p>
                <p className="text-gray-500 text-xs mb-3">
                  {t('settingsPanel.routingDescription')}
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
                  {t('settingsPanel.activateStack')}
                </button>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  {ROUTING_MATRIX.map((route) => (
                    <div
                      key={route.typeKey}
                      className="flex justify-between px-3 py-2 rounded-lg"
                      style={{ backgroundColor: '#0a0a0a' }}
                    >
                      <span className="text-gray-400">{t(route.typeKey)}</span>
                      <span style={{ color: '#00ff00' }}>{route.provider}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div
                className="rounded-xl p-4"
                style={{ backgroundColor: '#111', border: '1px solid #222' }}
              >
                <p className="text-white text-sm font-medium mb-2">
                  {t('settingsPanel.crosscheckTitle')}
                </p>
                <p className="text-gray-500 text-xs">{t('settingsPanel.crosscheckDescription')}</p>
              </div>

              <div
                className="rounded-xl p-4"
                style={{ backgroundColor: '#111', border: '1px solid #222' }}
              >
                <p className="text-white text-sm font-medium mb-2">{t('settingsPanel.ragTitle')}</p>
                <p className="text-gray-500 text-xs">{t('settingsPanel.ragDescription')}</p>
              </div>

              <div
                className="rounded-xl p-4"
                style={{ backgroundColor: '#111', border: '1px solid #222' }}
              >
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <p className="text-white text-sm font-medium mb-2">
                      {t('settingsPanel.strictEvidenceTitle')}
                    </p>
                    <p className="text-gray-500 text-xs">
                      {t('settingsPanel.strictEvidenceDescription')}
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
                  <p
                    className="mt-2 text-[11px]"
                    style={{
                      color:
                        strictPolicySyncState === 'saved'
                          ? '#00ff00'
                          : strictPolicySyncState === 'saving'
                            ? '#67e8f9'
                            : '#f87171',
                    }}
                  >
                    {strictPolicySyncState === 'saving' && t('settingsPanel.syncSaving')}
                    {strictPolicySyncState === 'saved' && t('settingsPanel.syncSaved')}
                    {strictPolicySyncState === 'error' && t('settingsPanel.syncError')}
                  </p>
                )}
              </div>

              <div
                className="rounded-xl p-4"
                style={{ backgroundColor: '#111', border: '1px solid #222' }}
              >
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <p className="text-white text-sm font-medium mb-2">
                      Protocollo di Aderenza Totale 100x
                    </p>
                    <p className="text-gray-500 text-xs">
                      Output gemello al 100% dell&apos;obiettivo. Reale, verificabile, eseguibile.
                      Zero scarto, zero fluff.
                    </p>
                  </div>
                  <button
                    onClick={() => {
                      const current = useAppStore.getState().settings.orchestrator;
                      updateSettings({
                        orchestrator: {
                          ...current,
                          protocollo100x: !(current.protocollo100x ?? true),
                        },
                      });
                    }}
                    className="px-3 py-2 rounded-lg text-xs font-semibold"
                    style={{
                      backgroundColor:
                        (settings.orchestrator.protocollo100x ?? true) ? '#00ff0018' : '#ffffff12',
                      border:
                        (settings.orchestrator.protocollo100x ?? true)
                          ? '1px solid #00ff0045'
                          : '1px solid #ffffff25',
                      color: (settings.orchestrator.protocollo100x ?? true) ? '#00ff00' : '#9ca3af',
                      minWidth: '80px',
                    }}
                  >
                    {(settings.orchestrator.protocollo100x ?? true) ? '100x ON' : 'OFF'}
                  </button>
                </div>
              </div>

              <div
                className="rounded-xl p-4"
                style={{ backgroundColor: '#111', border: '1px solid #222' }}
              >
                <p className="text-white text-sm font-medium mb-3">
                  {t('settingsPanel.systemInfo')}
                </p>
                <div className="space-y-1 text-xs">
                  <div className="flex justify-between">
                    <span className="text-gray-500">{t('settingsPanel.version')}</span>
                    <span className="text-white">0.9.0-beta</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">{t('settingsPanel.framework')}</span>
                    <span className="text-white">Tauri 2.0 + React 18</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">{t('settingsPanel.orchestrator')}</span>
                    <span className="text-white">Direct Router + FastAPI</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">{t('settingsPanel.vectorDb')}</span>
                    <span className="text-white">ChromaDB</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">{t('settingsPanel.ollamaHost')}</span>
                    <span className="text-white">{settings.ollamaHost}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">{t('settingsPanel.author')}</span>
                    <span style={{ color: '#00ff00' }}>PadronaVio</span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
