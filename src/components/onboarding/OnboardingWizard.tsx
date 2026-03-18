import { CheckCircle2, Globe, KeyRound, ShieldCheck, Sparkles } from 'lucide-react';
import { useMemo, useState } from 'react';
import { translateForLocale } from '../../hooks/useI18n';
import { useAppStore } from '../../stores/appStore';
import type { AIProvider } from '../../types';

type Props = {
  onComplete: () => void;
};

const CLOUD_PROVIDER_OPTIONS: Array<{ id: AIProvider; label: string; placeholder: string }> = [
  { id: 'groq', label: 'Groq (free tier)', placeholder: 'gsk_...' },
  { id: 'claude', label: 'Anthropic Claude', placeholder: 'sk-ant-...' },
  { id: 'openrouter', label: 'OpenRouter', placeholder: 'sk-or-v1-...' },
  { id: 'gemini', label: 'Google Gemini', placeholder: 'AIza...' },
];

const LOCAL_MODELS = ['qwen2.5-coder:3b', 'llama3.2:3b', 'mistral:latest', 'deepseek-r1:latest'];

function detectLanguage(): 'it' | 'en' {
  const raw = (navigator.language || 'it').toLowerCase();
  return raw.startsWith('en') ? 'en' : 'it';
}

export default function OnboardingWizard({ onComplete }: Props) {
  const { settings, updateSettings, setCurrentPage } = useAppStore();

  const [step, setStep] = useState(1);
  const [mode, setMode] = useState<'local' | 'cloud'>(settings.orchestrator.mode || 'local');
  const [provider, setProvider] = useState<AIProvider>('groq');
  const [apiKey, setApiKey] = useState('');
  const [localModel, setLocalModel] = useState(settings.ollamaModel || 'qwen2.5-coder:3b');
  const [language, setLanguage] = useState<'it' | 'en'>(settings.language === 'en' ? 'en' : detectLanguage());

  const t = (key: string, options?: Record<string, string | number | boolean | null | undefined>) =>
    translateForLocale(language, key, options);

  const selectedProvider = useMemo(
    () => CLOUD_PROVIDER_OPTIONS.find((option) => option.id === provider) || CLOUD_PROVIDER_OPTIONS[0],
    [provider],
  );

  const canGoNext =
    (step === 1)
    || (step === 2 && (mode === 'local' || apiKey.trim().length >= 6))
    || step === 3;

  const completeSetup = () => {
    const existing = settings.apiKeys.filter((item) => item.provider !== provider);
    const updatedKeys =
      mode === 'cloud' && apiKey.trim().length >= 6
        ? [
            ...existing,
            {
              provider,
              key: apiKey.trim(),
              isValid: true,
              lastChecked: Date.now(),
            },
          ]
        : existing;

    localStorage.setItem('vio83-locale', language);

    updateSettings({
      language,
      ollamaModel: localModel,
      apiKeys: updatedKeys,
      onboardingCompleted: true,
      orchestrator: {
        ...settings.orchestrator,
        mode,
        primaryProvider: mode === 'cloud' ? provider : 'ollama',
        fallbackProviders: mode === 'cloud' ? [provider, 'ollama'] : ['ollama'],
        autoRouting: true,
      },
    });

    setCurrentPage('chat');
    onComplete();
  };

  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      zIndex: 60,
      background: 'rgba(0,0,0,0.82)',
      backdropFilter: 'blur(6px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '16px',
    }}>
      <div style={{
        width: 'min(720px, 100%)',
        borderRadius: '16px',
        border: '1px solid #1f2937',
        background: '#0a0a0a',
        color: '#e5e7eb',
        overflow: 'hidden',
      }}>
        <div style={{ padding: '18px 22px', borderBottom: '1px solid #1f2937', display: 'flex', justifyContent: 'space-between' }}>
          <div>
            <div style={{ fontSize: 17, fontWeight: 700 }}>{t('onboarding.title')}</div>
            <div style={{ fontSize: 12, color: '#9ca3af' }}>{t('onboarding.subtitle')}</div>
          </div>
          <div style={{ fontSize: 12, color: '#86efac' }}>{t('onboarding.step', { step, total: 3 })}</div>
        </div>

        <div style={{ padding: 22, display: 'grid', gap: 18 }}>
          {step === 1 && (
            <>
              <div style={{ fontSize: 14, fontWeight: 600, display: 'flex', gap: 8, alignItems: 'center' }}>
                <Sparkles size={16} color="#86efac" /> {t('onboarding.modeLanguage')}
              </div>

              <div style={{ display: 'grid', gap: 10 }}>
                <button onClick={() => setMode('local')} style={{
                  textAlign: 'left',
                  padding: 12,
                  borderRadius: 10,
                  border: mode === 'local' ? '1px solid #22c55e' : '1px solid #374151',
                  background: mode === 'local' ? '#052e16' : '#111827',
                  color: '#e5e7eb',
                  cursor: 'pointer',
                }}>
                  {t('onboarding.localMode')}
                </button>

                <button onClick={() => setMode('cloud')} style={{
                  textAlign: 'left',
                  padding: 12,
                  borderRadius: 10,
                  border: mode === 'cloud' ? '1px solid #22c55e' : '1px solid #374151',
                  background: mode === 'cloud' ? '#052e16' : '#111827',
                  color: '#e5e7eb',
                  cursor: 'pointer',
                }}>
                  {t('onboarding.cloudMode')}
                </button>
              </div>

              <label style={{ fontSize: 13, color: '#cbd5e1', display: 'flex', alignItems: 'center', gap: 8 }}>
                <Globe size={14} /> {t('onboarding.language')}
                <select
                  value={language}
                  onChange={(e) => setLanguage(e.target.value as 'it' | 'en')}
                  style={{ marginLeft: 'auto', background: '#111827', color: '#e5e7eb', border: '1px solid #374151', borderRadius: 8, padding: '6px 10px' }}
                >
                  <option value="it">Italiano</option>
                  <option value="en">English</option>
                </select>
              </label>
            </>
          )}

          {step === 2 && mode === 'cloud' && (
            <>
              <div style={{ fontSize: 14, fontWeight: 600, display: 'flex', gap: 8, alignItems: 'center' }}>
                <KeyRound size={16} color="#86efac" /> {t('onboarding.configureCloud')}
              </div>

              <select
                value={provider}
                onChange={(e) => setProvider(e.target.value as AIProvider)}
                style={{ background: '#111827', color: '#e5e7eb', border: '1px solid #374151', borderRadius: 8, padding: '10px 12px' }}
              >
                {CLOUD_PROVIDER_OPTIONS.map((item) => (
                  <option key={item.id} value={item.id}>{item.label}</option>
                ))}
              </select>

              <input
                type="password"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder={selectedProvider.placeholder}
                style={{ background: '#111827', color: '#e5e7eb', border: '1px solid #374151', borderRadius: 8, padding: '10px 12px' }}
              />

              <div style={{ fontSize: 12, color: '#93c5fd' }}>
                {t('onboarding.keyHint')}
              </div>
            </>
          )}

          {step === 2 && mode === 'local' && (
            <>
              <div style={{ fontSize: 14, fontWeight: 600, display: 'flex', gap: 8, alignItems: 'center' }}>
                <ShieldCheck size={16} color="#86efac" /> {t('onboarding.configureLocal')}
              </div>

              <select
                value={localModel}
                onChange={(e) => setLocalModel(e.target.value)}
                style={{ background: '#111827', color: '#e5e7eb', border: '1px solid #374151', borderRadius: 8, padding: '10px 12px' }}
              >
                {LOCAL_MODELS.map((model) => (
                  <option key={model} value={model}>{model}</option>
                ))}
              </select>

              <div style={{ fontSize: 12, color: '#93c5fd' }}>
                {t('onboarding.modelHint', { command: `ollama pull ${localModel}` })}
              </div>
            </>
          )}

          {step === 3 && (
            <div style={{ display: 'grid', gap: 10 }}>
              <div style={{ fontSize: 14, fontWeight: 600, display: 'flex', gap: 8, alignItems: 'center' }}>
                <CheckCircle2 size={16} color="#86efac" /> {t('onboarding.summary')}
              </div>

              <div style={{ background: '#111827', border: '1px solid #374151', borderRadius: 10, padding: 12, fontSize: 13 }}>
                <div>{t('onboarding.summaryMode')}: <strong>{mode === 'local' ? t('mode.local') : t('mode.cloud')}</strong></div>
                <div>{t('onboarding.summaryLanguage')}: <strong>{language.toUpperCase()}</strong></div>
                <div>{t('onboarding.summaryProvider')}: <strong>{mode === 'cloud' ? provider : 'ollama'}</strong></div>
                <div>{t('onboarding.summaryLocalModel')}: <strong>{localModel}</strong></div>
                <div>{t('onboarding.summaryApiKey')}: <strong>{mode === 'cloud' ? (apiKey ? t('onboarding.summaryConfigured') : t('onboarding.summaryMissing')) : t('onboarding.summaryNa')}</strong></div>
              </div>

              <div style={{ fontSize: 12, color: '#9ca3af' }}>
                {t('onboarding.afterHint')}
              </div>
            </div>
          )}
        </div>

        <div style={{ borderTop: '1px solid #1f2937', padding: '14px 22px', display: 'flex', justifyContent: 'space-between' }}>
          <button
            onClick={() => step === 1 ? completeSetup() : setStep(step - 1)}
            style={{
              padding: '8px 12px',
              borderRadius: 8,
              border: '1px solid #374151',
              background: 'transparent',
              color: '#d1d5db',
              cursor: 'pointer',
            }}
          >
            {step === 1 ? t('onboarding.skipForNow') : t('onboarding.back')}
          </button>

          <button
            onClick={() => step < 3 ? setStep(step + 1) : completeSetup()}
            disabled={!canGoNext}
            style={{
              padding: '8px 14px',
              borderRadius: 8,
              border: '1px solid #16a34a',
              background: canGoNext ? '#16a34a' : '#14532d',
              color: '#052e16',
              fontWeight: 700,
              cursor: canGoNext ? 'pointer' : 'not-allowed',
            }}
          >
            {step < 3 ? t('onboarding.next') : t('onboarding.complete')}
          </button>
        </div>
      </div>
    </div>
  );
}
