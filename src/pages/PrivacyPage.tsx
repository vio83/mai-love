// VIO 83 AI ORCHESTRA — Privacy & Legal Page
import { ExternalLink, Lock, Server, ShieldCheck, Trash2 } from 'lucide-react';

const PROVIDERS = [
  { name: 'Anthropic (Claude)', url: 'https://www.anthropic.com/privacy' },
  { name: 'OpenAI (GPT-4)', url: 'https://openai.com/policies/privacy-policy' },
  { name: 'Google (Gemini)', url: 'https://policies.google.com/privacy' },
  { name: 'Groq', url: 'https://groq.com/privacy-policy/' },
  { name: 'Mistral AI', url: 'https://mistral.ai/privacy-policy/' },
  { name: 'DeepSeek', url: 'https://www.deepseek.com/privacy' },
  { name: 'xAI (Grok)', url: 'https://x.ai/legal/privacy-policy' },
];

const LOCAL_DATA = [
  { item: 'Messaggi chat', file: 'data/vio83_orchestra.db', retention: 'Fino a cancellazione' },
  { item: 'Preferenze app', file: 'data/vio83_orchestra.db', retention: 'Permanente' },
  { item: 'Metriche aggregate', file: 'data/vio83_orchestra.db', retention: '90 giorni (auto)' },
  { item: 'Log di processo', file: 'data/process_log.db', retention: '7 giorni (rotazione)' },
  { item: 'Cache risposte AI', file: 'data/cache.db', retention: 'TTL configurabile' },
  { item: 'Knowledge base', file: 'data/knowledge_distilled.db', retention: 'Fino a cancellazione' },
];

const cardStyle: React.CSSProperties = {
  background: 'var(--vio-bg-secondary)',
  border: '1px solid var(--vio-border)',
  borderRadius: '10px',
  padding: '18px 20px',
  marginBottom: '16px',
};

const headerStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  gap: '10px',
  fontSize: '15px',
  fontWeight: 700,
  color: 'var(--vio-text-primary)',
  marginBottom: '12px',
};

const labelStyle: React.CSSProperties = {
  fontSize: '11px',
  fontWeight: 700,
  textTransform: 'uppercase',
  letterSpacing: '0.06em',
  color: 'var(--vio-text-dim)',
};

export default function PrivacyPage() {
  return (
    <div style={{
      height: '100%',
      overflow: 'auto',
      padding: '28px 32px',
      background: 'var(--vio-bg-primary)',
      color: 'var(--vio-text-primary)',
    }}>
      <div style={{ maxWidth: '760px', margin: '0 auto' }}>

        {/* Header */}
        <div style={{ marginBottom: '28px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '6px' }}>
            <ShieldCheck size={24} color="var(--vio-green)" />
            <h1 style={{ fontSize: '22px', fontWeight: 800, margin: 0 }}>Privacy & Legal</h1>
          </div>
          <p style={{ fontSize: '13px', color: 'var(--vio-text-secondary)', margin: 0 }}>
            VIO 83 AI Orchestra v0.9.0-beta — Viorica Porcu — AGPL-3.0 / Licenza Commerciale
          </p>
        </div>

        {/* Local-First badge */}
        <div style={{
          ...cardStyle,
          borderColor: 'var(--vio-green)',
          background: 'rgba(34,197,94,0.05)',
          display: 'flex',
          alignItems: 'flex-start',
          gap: '14px',
        }}>
          <Lock size={20} color="var(--vio-green)" style={{ flexShrink: 0, marginTop: '2px' }} />
          <div>
            <div style={{ fontWeight: 700, marginBottom: '4px', color: 'var(--vio-green)' }}>
              Local-First by Design
            </div>
            <div style={{ fontSize: '13px', color: 'var(--vio-text-secondary)', lineHeight: '1.6' }}>
              Tutti i dati vengono salvati <strong>esclusivamente sul tuo Mac</strong>, in database SQLite locali
              in <code style={{ color: 'var(--vio-cyan)' }}>~/Projects/vio83-ai-orchestra/data/</code>.
              Nessun dato viene inviato a server del progetto. Nessuna telemetria, nessun tracking, nessuna pubblicità.
            </div>
          </div>
        </div>

        {/* Dati locali */}
        <div style={cardStyle}>
          <div style={headerStyle}>
            <Server size={16} color="var(--vio-cyan)" />
            Dati salvati localmente
          </div>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px' }}>
            <thead>
              <tr>
                {['Dato', 'File', 'Durata'].map((h) => (
                  <th key={h} style={{ ...labelStyle, textAlign: 'left', padding: '6px 10px 6px 0', borderBottom: '1px solid var(--vio-border)' }}>
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {LOCAL_DATA.map((row) => (
                <tr key={row.item}>
                  <td style={{ padding: '7px 10px 7px 0', color: 'var(--vio-text-primary)', borderBottom: '1px solid var(--vio-border)' }}>
                    {row.item}
                  </td>
                  <td style={{ padding: '7px 10px 7px 0', color: 'var(--vio-cyan)', fontFamily: 'monospace', fontSize: '11px', borderBottom: '1px solid var(--vio-border)' }}>
                    {row.file}
                  </td>
                  <td style={{ padding: '7px 0', color: 'var(--vio-text-dim)', borderBottom: '1px solid var(--vio-border)' }}>
                    {row.retention}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Diritti GDPR */}
        <div style={cardStyle}>
          <div style={headerStyle}>
            <ShieldCheck size={16} color="var(--vio-green)" />
            I tuoi diritti (GDPR Art. 15–22)
          </div>
          <div style={{ display: 'grid', gap: '8px', fontSize: '13px' }}>
            {[
              { right: 'Accesso', how: 'Apri i file .db in data/ con DB Browser for SQLite' },
              { right: 'Cancellazione', how: 'Elimina i file in data/ o usa "Cancella tutto" in Impostazioni' },
              { right: 'Portabilità', how: 'Esporta conversazioni dalla sezione Analytics' },
              { right: 'Opposizione', how: 'Disattiva cache: VIO_CACHE_ENABLED=false nel .env' },
              { right: 'Rettifica', how: 'Modifica direttamente il database locale' },
            ].map(({ right, how }) => (
              <div key={right} style={{ display: 'flex', gap: '10px', padding: '8px', background: 'var(--vio-bg-primary)', borderRadius: '6px' }}>
                <span style={{ color: 'var(--vio-green)', fontWeight: 700, minWidth: '90px' }}>{right}</span>
                <span style={{ color: 'var(--vio-text-secondary)' }}>{how}</span>
              </div>
            ))}
          </div>
          <div style={{ marginTop: '12px', fontSize: '12px', color: 'var(--vio-text-dim)' }}>
            Contatto GDPR: <a href="mailto:porcu.v.83@gmail.com" style={{ color: 'var(--vio-cyan)' }}>porcu.v.83@gmail.com</a>
          </div>
        </div>

        {/* Provider cloud */}
        <div style={cardStyle}>
          <div style={headerStyle}>
            <ExternalLink size={16} color="var(--vio-cyan)" />
            Provider Cloud (opzionali)
          </div>
          <p style={{ fontSize: '13px', color: 'var(--vio-text-secondary)', marginBottom: '12px' }}>
            Quando configuri una API key e invii un messaggio, il testo viene trasmesso
            direttamente al provider via HTTPS. Si applicano le loro policy:
          </p>
          <div style={{ display: 'grid', gap: '6px' }}>
            {PROVIDERS.map(({ name, url }) => (
              <a
                key={name}
                href={url}
                target="_blank"
                rel="noopener noreferrer"
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '8px 12px',
                  background: 'var(--vio-bg-primary)',
                  borderRadius: '6px',
                  textDecoration: 'none',
                  color: 'var(--vio-text-primary)',
                  fontSize: '13px',
                  border: '1px solid transparent',
                  transition: 'border-color 0.15s',
                }}
                onMouseEnter={(e) => (e.currentTarget.style.borderColor = 'var(--vio-border)')}
                onMouseLeave={(e) => (e.currentTarget.style.borderColor = 'transparent')}
              >
                <span>{name}</span>
                <ExternalLink size={12} color="var(--vio-text-dim)" />
              </a>
            ))}
          </div>
          <div style={{ marginTop: '12px', padding: '10px', background: 'rgba(34,197,94,0.05)', borderRadius: '6px', fontSize: '12px', color: 'var(--vio-green)' }}>
            💻 La modalità <strong>Ollama locale</strong> non trasmette nulla fuori dal dispositivo.
          </div>
        </div>

        {/* Sicurezza */}
        <div style={cardStyle}>
          <div style={headerStyle}>
            <Lock size={16} color="var(--vio-text-dim)" />
            Sicurezza
          </div>
          <div style={{ display: 'grid', gap: '6px', fontSize: '13px', color: 'var(--vio-text-secondary)' }}>
            <div>• Database accessibili solo dall'utente macOS loggato (permessi <code style={{ color: 'var(--vio-cyan)' }}>rw-------</code>)</div>
            <div>• API keys salvate nel <code style={{ color: 'var(--vio-cyan)' }}>.env</code> locale — <strong style={{ color: 'var(--vio-text-primary)' }}>non condividere mai questo file</strong></div>
            <div>• Backend API accessibile solo da <code style={{ color: 'var(--vio-cyan)' }}>localhost:4000</code></div>
            <div>• Comunicazioni cloud via HTTPS con TLS 1.2+</div>
            <div>• Rate limiting: 30 richieste/minuto per endpoint chat</div>
          </div>
          <div style={{ marginTop: '12px', fontSize: '12px', color: 'var(--vio-text-dim)' }}>
            Segnalazione vulnerabilità: <a href="mailto:porcu.v.83@gmail.com" style={{ color: 'var(--vio-cyan)' }}>porcu.v.83@gmail.com</a>
          </div>
        </div>

        {/* Cancella dati */}
        <div style={{ ...cardStyle, borderColor: 'rgba(239,68,68,0.3)' }}>
          <div style={{ ...headerStyle }}>
            <Trash2 size={16} color="#ef4444" />
            Cancella tutti i dati locali
          </div>
          <p style={{ fontSize: '13px', color: 'var(--vio-text-secondary)', marginBottom: '12px' }}>
            Per eliminare completamente tutti i dati locali:
          </p>
          <pre style={{
            background: 'var(--vio-bg-primary)',
            border: '1px solid var(--vio-border)',
            borderRadius: '6px',
            padding: '12px',
            fontSize: '12px',
            color: 'var(--vio-cyan)',
            overflowX: 'auto',
            margin: 0,
          }}>
{`# Ferma il backend
pm2 stop vio83-backend

# Elimina tutti i database
rm ~/Projects/vio83-ai-orchestra/data/*.db

# Riavvia
pm2 start ecosystem.config.cjs`}
          </pre>
        </div>

        {/* Footer legale */}
        <div style={{ fontSize: '12px', color: 'var(--vio-text-dim)', textAlign: 'center', paddingTop: '8px', lineHeight: '1.8' }}>
          <div>VIO 83 AI Orchestra è distribuita con doppia licenza: <strong>AGPL-3.0</strong> (open source) e licenza commerciale proprietaria.</div>
          <div>Le risposte AI non costituiscono consulenza medica, legale o finanziaria.</div>
          <div>
            <a href="https://github.com/vio83/vio83-ai-orchestra" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--vio-cyan)', marginRight: '16px' }}>GitHub</a>
            <a href="mailto:porcu.v.83@gmail.com" style={{ color: 'var(--vio-cyan)' }}>porcu.v.83@gmail.com</a>
          </div>
          <div style={{ marginTop: '4px' }}>© 2026 Viorica Porcu — Giurisdizione: Tribunale di Cagliari, Italia</div>
        </div>

      </div>
    </div>
  );
}
