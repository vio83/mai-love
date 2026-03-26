// VIO 83 AI ORCHESTRA — Mobile Connection Screen
// Schermata iniziale mobile per connessione al backend
import { Loader2, Server, Wifi, WifiOff } from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';
import { checkBackendConnection, setBackendUrl } from '../../services/mobileConfig';

interface MobileConnectProps {
  onConnected: (url: string) => void;
}

export default function MobileConnect({ onConnected }: MobileConnectProps) {
  const [url, setUrl] = useState('');
  const [status, setStatus] = useState<'idle' | 'checking' | 'connected' | 'error'>('idle');
  const [latency, setLatency] = useState(0);
  const [errorMsg, setErrorMsg] = useState('');

  const tryConnect = useCallback(
    async (targetUrl: string) => {
      if (!targetUrl.trim()) return;
      setStatus('checking');
      setErrorMsg('');

      const result = await checkBackendConnection(targetUrl);
      if (result.ok) {
        setStatus('connected');
        setLatency(result.latencyMs);
        setBackendUrl(targetUrl);
        setTimeout(() => onConnected(targetUrl), 800);
      } else {
        setStatus('error');
        setErrorMsg(`Connessione fallita (${result.latencyMs}ms)`);
      }
    },
    [onConnected],
  );

  // Auto-connect se URL salvato
  useEffect(() => {
    const saved = globalThis.localStorage?.getItem('vio83_mobile_backend_url');
    if (saved) {
      setUrl(saved);
      tryConnect(saved);
    }
  }, [tryConnect]);

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        height: '100dvh',
        padding: '24px',
        background: 'var(--vio-bg-primary)',
        color: 'var(--vio-text-primary)',
        fontFamily: 'var(--vio-font-sans)',
      }}
    >
      {/* Logo */}
      <div
        style={{
          width: '80px',
          height: '80px',
          borderRadius: '20px',
          background: 'linear-gradient(135deg, #00ff00 0%, #00cc00 100%)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          marginBottom: '24px',
          boxShadow: '0 0 30px rgba(0,255,0,0.3)',
        }}
      >
        <Server size={40} color="#000" />
      </div>

      <h1
        style={{
          fontSize: '24px',
          fontWeight: 700,
          marginBottom: '8px',
          color: 'var(--vio-green)',
        }}
      >
        VIO 83 AI Orchestra
      </h1>

      <p
        style={{
          fontSize: '14px',
          color: 'var(--vio-text-dim)',
          marginBottom: '32px',
          textAlign: 'center',
        }}
      >
        Connettiti al tuo backend locale o remoto
      </p>

      {/* URL Input */}
      <div style={{ width: '100%', maxWidth: '400px' }}>
        <label
          style={{
            display: 'block',
            fontSize: '12px',
            color: 'var(--vio-text-secondary)',
            marginBottom: '6px',
          }}
        >
          URL Backend
        </label>
        <input
          type="url"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="http://192.168.1.x:4000"
          style={{
            width: '100%',
            padding: '14px 16px',
            fontSize: '16px',
            background: 'var(--vio-bg-tertiary)',
            border: `1px solid ${status === 'error' ? 'var(--vio-red)' : 'var(--vio-border)'}`,
            borderRadius: 'var(--vio-radius)',
            color: 'var(--vio-text-primary)',
            outline: 'none',
          }}
          onKeyDown={(e) => {
            if (e.key === 'Enter') tryConnect(url);
          }}
        />

        <button
          onClick={() => tryConnect(url)}
          disabled={status === 'checking' || !url.trim()}
          style={{
            width: '100%',
            padding: '14px',
            marginTop: '12px',
            fontSize: '16px',
            fontWeight: 600,
            background: status === 'connected' ? 'var(--vio-green)' : 'var(--vio-bg-tertiary)',
            color: status === 'connected' ? '#000' : 'var(--vio-green)',
            border: `1px solid var(--vio-green)`,
            borderRadius: 'var(--vio-radius)',
            cursor: status === 'checking' ? 'wait' : 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '8px',
          }}
        >
          {status === 'checking' && <Loader2 size={18} style={{ animation: 'spin 1s linear infinite' }} />}
          {status === 'connected' && <Wifi size={18} />}
          {status === 'error' && <WifiOff size={18} />}
          {status === 'idle' && <Wifi size={18} />}
          {status === 'checking'
            ? 'Connessione...'
            : status === 'connected'
              ? `Connesso (${latency}ms)`
              : 'Connetti'}
        </button>

        {errorMsg && (
          <p style={{ color: 'var(--vio-red)', fontSize: '13px', marginTop: '8px', textAlign: 'center' }}>
            {errorMsg}
          </p>
        )}
      </div>

      {/* Help */}
      <div
        style={{
          marginTop: '40px',
          fontSize: '12px',
          color: 'var(--vio-text-dim)',
          textAlign: 'center',
          lineHeight: 1.6,
          maxWidth: '350px',
        }}
      >
        <p style={{ marginBottom: '8px' }}>
          <strong style={{ color: 'var(--vio-text-secondary)' }}>Rete locale:</strong> Usa l&apos;IP del tuo Mac
          (Preferenze di Sistema &gt; Rete)
        </p>
        <p>
          <strong style={{ color: 'var(--vio-text-secondary)' }}>Da fuori:</strong> Usa un tunnel (ngrok, Tailscale)
          per esporre il backend
        </p>
      </div>

      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}
