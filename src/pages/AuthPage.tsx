// VIO 83 AI ORCHESTRA — Auth Page (Impronta Digitale)
import { useState } from 'react';
import { useI18n } from '../hooks/useI18n';
import { useAppStore } from '../stores/appStore';

const API_BASE = 'http://localhost:4000';

export default function AuthPage() {
  const { t } = useI18n();
  const { setAuth } = useAppStore();

  const [tab, setTab] = useState<'login' | 'register'>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [purchaseCode, setPurchaseCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handleLogin = async () => {
    if (!email || !password) {
      setError(t('auth.emailRequired'));
      return;
    }
    setLoading(true);
    setError('');
    try {
      const res = await fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.detail || t('auth.invalidCredentials'));
        return;
      }
      setAuth(data.token, data.user);
      setSuccess(t('auth.loginSuccess'));
    } catch {
      setError('Errore di connessione al server');
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async () => {
    if (!email) { setError(t('auth.emailRequired')); return; }
    if (password.length < 8) { setError(t('auth.passwordMin')); return; }
    setLoading(true);
    setError('');
    try {
      const res = await fetch(`${API_BASE}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email,
          password,
          purchase_code: purchaseCode,
          plan_id: 'free_local',
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.detail || 'Errore registrazione');
        return;
      }
      setAuth(data.token, data.user);
      setSuccess(t('auth.registerSuccess'));
    } catch {
      setError('Errore di connessione al server');
    } finally {
      setLoading(false);
    }
  };

  const handleSkip = () => {
    // Accesso locale senza account — impostazioni solo Ollama
    setAuth('local-mode', {
      user_id: 'local',
      email: 'local@vio83.local',
      email_hash: 'local',
      plan_id: 'free_local',
    });
  };

  const inputStyle: React.CSSProperties = {
    width: '100%',
    padding: '10px 14px',
    borderRadius: '8px',
    border: '1px solid var(--vio-border)',
    background: 'var(--vio-bg-primary)',
    color: 'var(--vio-text-primary)',
    fontSize: '14px',
    outline: 'none',
    boxSizing: 'border-box',
  };

  const btnStyle: React.CSSProperties = {
    width: '100%',
    padding: '12px',
    borderRadius: '8px',
    border: 'none',
    background: 'var(--vio-green)',
    color: '#000',
    fontSize: '15px',
    fontWeight: 700,
    cursor: loading ? 'wait' : 'pointer',
    opacity: loading ? 0.6 : 1,
  };

  return (
    <div style={{
      height: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'var(--vio-bg-primary)',
      padding: '20px',
    }}>
      <div style={{
        width: '100%',
        maxWidth: '420px',
        background: 'var(--vio-bg-secondary)',
        borderRadius: '16px',
        border: '1px solid var(--vio-border)',
        padding: '32px',
        display: 'flex',
        flexDirection: 'column',
        gap: '20px',
      }}>
        {/* Header */}
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '32px', marginBottom: '8px' }}>🎵</div>
          <h1 style={{ fontSize: '20px', fontWeight: 700, color: 'var(--vio-green)', margin: 0 }}>
            {t('auth.title')}
          </h1>
          <p style={{ fontSize: '13px', color: 'var(--vio-text-dim)', margin: '6px 0 0' }}>
            {t('auth.subtitle')}
          </p>
        </div>

        {/* Tab switcher */}
        <div style={{ display: 'flex', gap: '4px', background: 'var(--vio-bg-primary)', borderRadius: '8px', padding: '3px' }}>
          {(['login', 'register'] as const).map(t_ => (
            <button
              key={t_}
              onClick={() => { setTab(t_); setError(''); setSuccess(''); }}
              style={{
                flex: 1,
                padding: '8px',
                borderRadius: '6px',
                border: 'none',
                background: tab === t_ ? 'var(--vio-bg-secondary)' : 'transparent',
                color: tab === t_ ? 'var(--vio-green)' : 'var(--vio-text-dim)',
                fontSize: '13px',
                fontWeight: tab === t_ ? 600 : 400,
                cursor: 'pointer',
              }}
            >
              {t_ === 'login' ? t('auth.loginTab') : t('auth.registerTab')}
            </button>
          ))}
        </div>

        {/* Form */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <input
            type="email"
            placeholder={t('auth.emailPlaceholder')}
            value={email}
            onChange={e => setEmail(e.target.value)}
            style={inputStyle}
            autoComplete="email"
          />
          <input
            type="password"
            placeholder={t('auth.passwordPlaceholder')}
            value={password}
            onChange={e => setPassword(e.target.value)}
            style={inputStyle}
            autoComplete={tab === 'login' ? 'current-password' : 'new-password'}
          />

          {tab === 'register' && (
            <>
              <input
                type="text"
                placeholder={t('auth.purchaseCodePlaceholder')}
                value={purchaseCode}
                onChange={e => setPurchaseCode(e.target.value)}
                style={inputStyle}
              />
              <p style={{ fontSize: '11px', color: 'var(--vio-text-dim)', margin: '-4px 0 0 2px' }}>
                {t('auth.purchaseCodeHint')}
              </p>
            </>
          )}
        </div>

        {/* Error / Success */}
        {error && (
          <div style={{ padding: '8px 12px', borderRadius: '6px', background: 'rgba(255,60,60,0.1)', color: '#ff5555', fontSize: '13px' }}>
            {error}
          </div>
        )}
        {success && (
          <div style={{ padding: '8px 12px', borderRadius: '6px', background: 'rgba(80,250,123,0.1)', color: 'var(--vio-green)', fontSize: '13px' }}>
            {success}
          </div>
        )}

        {/* Submit */}
        <button
          onClick={tab === 'login' ? handleLogin : handleRegister}
          disabled={loading}
          style={btnStyle}
        >
          {loading
            ? (tab === 'login' ? t('auth.loggingIn') : t('auth.registering'))
            : (tab === 'login' ? t('auth.login') : t('auth.register'))
          }
        </button>

        {/* Impronta digitale hint */}
        <p style={{ fontSize: '11px', color: 'var(--vio-text-dim)', textAlign: 'center', margin: 0 }}>
          🔐 {t('auth.improntaDigitale')}
        </p>

        {/* Skip */}
        <div style={{ textAlign: 'center', borderTop: '1px solid var(--vio-border)', paddingTop: '16px' }}>
          <button
            onClick={handleSkip}
            style={{
              background: 'none',
              border: 'none',
              color: 'var(--vio-text-dim)',
              cursor: 'pointer',
              fontSize: '13px',
              textDecoration: 'underline',
            }}
          >
            {t('auth.skipAuth')}
          </button>
          <p style={{ fontSize: '11px', color: 'var(--vio-text-dim)', margin: '4px 0 0' }}>
            {t('auth.skipAuthHint')}
          </p>
        </div>
      </div>
    </div>
  );
}
