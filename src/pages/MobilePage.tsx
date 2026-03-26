// VIO 83 AI ORCHESTRA — Mobile Pairing Page
// Pagina desktop per generare QR code di connessione mobile
import { Loader2, MonitorSmartphone, QrCode, RefreshCw, Wifi } from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';
import { useI18n } from '../hooks/useI18n';

interface PairInfo {
  local_ip: string;
  port: number;
  url: string;
  version: string;
  capabilities: Record<string, boolean>;
}

export default function MobilePage() {
  useI18n();
  const [pairInfo, setPairInfo] = useState<PairInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchPairInfo = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const res = await fetch('/api/mobile/pair', { signal: AbortSignal.timeout(5000) });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setPairInfo(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Errore sconosciuto');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchPairInfo();
  }, [fetchPairInfo]);

  // Genera SVG QR code semplice (placeholder — in prod usa qrcode library)
  const qrDataUrl = pairInfo
    ? `https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=${encodeURIComponent(
        JSON.stringify({ type: 'vio83-connect', url: pairInfo.url }),
      )}`
    : '';

  return (
    <div style={{ padding: '32px', maxWidth: '700px', margin: '0 auto' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '24px' }}>
        <MonitorSmartphone size={28} color="var(--vio-green)" />
        <h1 style={{ fontSize: '22px', fontWeight: 700, color: 'var(--vio-text-primary)' }}>
          Mobile App
        </h1>
      </div>

      <p style={{ color: 'var(--vio-text-secondary)', marginBottom: '24px', lineHeight: 1.6 }}>
        Connetti il tuo iPhone o Android a VIO 83 AI Orchestra. Il tuo Mac fa da server, il mobile
        si connette via rete locale.
      </p>

      {loading && (
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            color: 'var(--vio-text-dim)',
          }}
        >
          <Loader2 size={16} style={{ animation: 'spin 1s linear infinite' }} />
          Rilevamento rete...
        </div>
      )}

      {error && (
        <div
          style={{
            padding: '12px 16px',
            background: 'rgba(255,51,51,0.1)',
            border: '1px solid var(--vio-red)',
            borderRadius: 'var(--vio-radius)',
            color: 'var(--vio-red)',
            fontSize: '14px',
          }}
        >
          {error}
          <button
            onClick={fetchPairInfo}
            style={{
              marginLeft: '12px',
              background: 'none',
              border: 'none',
              color: 'var(--vio-red)',
              cursor: 'pointer',
              textDecoration: 'underline',
            }}
          >
            Riprova
          </button>
        </div>
      )}

      {pairInfo && !loading && (
        <div style={{ display: 'flex', gap: '32px', flexWrap: 'wrap' }}>
          {/* QR Code */}
          <div
            style={{
              background: '#fff',
              borderRadius: '16px',
              padding: '16px',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: '12px',
            }}
          >
            <img
              src={qrDataUrl}
              alt="QR Code connessione mobile"
              width={200}
              height={200}
              style={{ borderRadius: '8px' }}
            />
            <span style={{ fontSize: '12px', color: '#666' }}>
              <QrCode size={12} style={{ display: 'inline', verticalAlign: 'middle' }} /> Scansiona
              con l&apos;app VIO 83
            </span>
          </div>

          {/* Connection Info */}
          <div style={{ flex: 1, minWidth: '240px' }}>
            <h3
              style={{
                fontSize: '16px',
                fontWeight: 600,
                color: 'var(--vio-text-primary)',
                marginBottom: '16px',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
              }}
            >
              <Wifi size={18} color="var(--vio-green)" />
              Dettagli Connessione
            </h3>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {[
                ['IP Locale', pairInfo.local_ip],
                ['Porta', String(pairInfo.port)],
                ['URL', pairInfo.url],
                ['Versione', pairInfo.version],
              ].map(([label, value]) => (
                <div key={label} style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--vio-text-dim)', fontSize: '13px' }}>{label}</span>
                  <code
                    style={{
                      fontSize: '13px',
                      color: 'var(--vio-green)',
                      background: 'var(--vio-bg-tertiary)',
                      padding: '2px 8px',
                      borderRadius: '4px',
                      fontFamily: 'var(--vio-font-mono)',
                    }}
                  >
                    {value}
                  </code>
                </div>
              ))}
            </div>

            {/* Capabilities */}
            <h4
              style={{
                fontSize: '14px',
                color: 'var(--vio-text-secondary)',
                marginTop: '20px',
                marginBottom: '8px',
              }}
            >
              Capabilities
            </h4>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
              {Object.entries(pairInfo.capabilities).map(([cap, enabled]) => (
                <span
                  key={cap}
                  style={{
                    fontSize: '11px',
                    padding: '3px 8px',
                    borderRadius: '12px',
                    background: enabled ? 'rgba(0,255,0,0.1)' : 'rgba(255,51,51,0.1)',
                    color: enabled ? 'var(--vio-green)' : 'var(--vio-red)',
                    border: `1px solid ${enabled ? 'var(--vio-green-dim)' : 'var(--vio-red)'}`,
                  }}
                >
                  {cap}
                </span>
              ))}
            </div>

            <button
              onClick={fetchPairInfo}
              style={{
                marginTop: '20px',
                padding: '10px 16px',
                background: 'var(--vio-bg-tertiary)',
                border: '1px solid var(--vio-border)',
                borderRadius: 'var(--vio-radius)',
                color: 'var(--vio-text-secondary)',
                cursor: 'pointer',
                fontSize: '13px',
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
              }}
            >
              <RefreshCw size={14} />
              Aggiorna Info
            </button>
          </div>
        </div>
      )}

      {/* Istruzioni */}
      <div
        style={{
          marginTop: '32px',
          padding: '16px 20px',
          background: 'var(--vio-bg-secondary)',
          borderRadius: 'var(--vio-radius-lg)',
          border: '1px solid var(--vio-border)',
        }}
      >
        <h3 style={{ fontSize: '15px', color: 'var(--vio-text-primary)', marginBottom: '12px' }}>
          Setup Mobile
        </h3>
        <ol
          style={{
            fontSize: '13px',
            color: 'var(--vio-text-secondary)',
            lineHeight: 1.8,
            paddingLeft: '20px',
          }}
        >
          <li>
            Assicurati che Mac e telefono siano sulla <strong>stessa rete WiFi</strong>
          </li>
          <li>
            Sul Mac: avvia il backend (<code>./orchestra.sh</code>)
          </li>
          <li>
            Sul telefono: apri l&apos;app VIO 83 e inserisci l&apos;URL sopra (oppure scansiona il
            QR)
          </li>
          <li>
            Per accesso da fuori casa: usa <code>ngrok http 4000</code> o Tailscale
          </li>
        </ol>
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
