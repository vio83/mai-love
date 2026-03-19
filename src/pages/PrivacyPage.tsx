// VIO 83 AI ORCHESTRA — Privacy & Legal Page
import { ExternalLink, Lock, Server, ShieldCheck, Trash2 } from 'lucide-react';
import { useI18n } from '../hooks/useI18n';

const PROVIDERS = [
  { name: 'Anthropic (Claude)', url: 'https://www.anthropic.com/privacy' },
  { name: 'OpenAI (GPT-4)', url: 'https://openai.com/policies/privacy-policy' },
  { name: 'Google (Gemini)', url: 'https://policies.google.com/privacy' },
  { name: 'Groq', url: 'https://groq.com/privacy-policy/' },
  { name: 'Mistral AI', url: 'https://mistral.ai/privacy-policy/' },
  { name: 'DeepSeek', url: 'https://www.deepseek.com/privacy' },
  { name: 'xAI (Grok)', url: 'https://x.ai/legal/privacy-policy' },
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
  const { t } = useI18n();

  const LOCAL_DATA = [
    { item: t('privacyPage.chatMessages'), file: 'data/vio83_orchestra.db', retention: t('privacyPage.untilDeletion') },
    { item: t('privacyPage.appPreferences'), file: 'data/vio83_orchestra.db', retention: t('privacyPage.permanent') },
    { item: t('privacyPage.aggregateMetrics'), file: 'data/vio83_orchestra.db', retention: t('privacyPage.ninetyDays') },
    { item: t('privacyPage.processLogs'), file: 'data/process_log.db', retention: t('privacyPage.sevenDays') },
    { item: t('privacyPage.aiCache'), file: 'data/cache.db', retention: t('privacyPage.configurableTtl') },
    { item: t('privacyPage.knowledgeBase'), file: 'data/knowledge_distilled.db', retention: t('privacyPage.untilDeletion') },
  ];

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
            <h1 style={{ fontSize: '22px', fontWeight: 800, margin: 0 }}>{t('privacyPage.title')}</h1>
          </div>
          <p style={{ fontSize: '13px', color: 'var(--vio-text-secondary)', margin: 0 }}>
            {t('privacyPage.versionLine')}
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
              {t('privacyPage.localFirst')}
            </div>
            <div style={{ fontSize: '13px', color: 'var(--vio-text-secondary)', lineHeight: '1.6' }}>
              {t('privacyPage.localFirstDesc')}
            </div>
          </div>
        </div>

        {/* Dati locali */}
        <div style={cardStyle}>
          <div style={headerStyle}>
            <Server size={16} color="var(--vio-cyan)" />
            {t('privacyPage.localData')}
          </div>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px' }}>
            <thead>
              <tr>
                {[t('privacyPage.thData'), t('privacyPage.thFile'), t('privacyPage.thRetention')].map((h) => (
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
            {t('privacyPage.gdprTitle')}
          </div>
          <div style={{ display: 'grid', gap: '8px', fontSize: '13px' }}>
            {[
              { right: t('privacyPage.gdprAccess'), how: t('privacyPage.gdprAccessHow') },
              { right: t('privacyPage.gdprDeletion'), how: t('privacyPage.gdprDeletionHow') },
              { right: t('privacyPage.gdprPortability'), how: t('privacyPage.gdprPortabilityHow') },
              { right: t('privacyPage.gdprObjection'), how: t('privacyPage.gdprObjectionHow') },
              { right: t('privacyPage.gdprRectification'), how: t('privacyPage.gdprRectificationHow') },
            ].map(({ right, how }) => (
              <div key={right} style={{ display: 'flex', gap: '10px', padding: '8px', background: 'var(--vio-bg-primary)', borderRadius: '6px' }}>
                <span style={{ color: 'var(--vio-green)', fontWeight: 700, minWidth: '90px' }}>{right}</span>
                <span style={{ color: 'var(--vio-text-secondary)' }}>{how}</span>
              </div>
            ))}
          </div>
          <div style={{ marginTop: '12px', fontSize: '12px', color: 'var(--vio-text-dim)' }}>
            {t('privacyPage.gdprContact')} <a href="mailto:porcu.v.83@gmail.com" style={{ color: 'var(--vio-cyan)' }}>porcu.v.83@gmail.com</a>
          </div>
        </div>

        {/* Provider cloud */}
        <div style={cardStyle}>
          <div style={headerStyle}>
            <ExternalLink size={16} color="var(--vio-cyan)" />
            {t('privacyPage.cloudProviders')}
          </div>
          <p style={{ fontSize: '13px', color: 'var(--vio-text-secondary)', marginBottom: '12px' }}>
            {t('privacyPage.cloudProvidersDesc')}
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
            💻 {t('privacyPage.localModeNote')}
          </div>
        </div>

        {/* Sicurezza */}
        <div style={cardStyle}>
          <div style={headerStyle}>
            <Lock size={16} color="var(--vio-text-dim)" />
            {t('privacyPage.security')}
          </div>
          <div style={{ display: 'grid', gap: '6px', fontSize: '13px', color: 'var(--vio-text-secondary)' }}>
            {(t('privacyPage.securityItems') as unknown as string[]).map((item: string, idx: number) => (
              <div key={idx}>• {item}</div>
            ))}
          </div>
          <div style={{ marginTop: '12px', fontSize: '12px', color: 'var(--vio-text-dim)' }}>
            {t('privacyPage.vulnReport')} <a href="mailto:porcu.v.83@gmail.com" style={{ color: 'var(--vio-cyan)' }}>porcu.v.83@gmail.com</a>
          </div>
        </div>

        {/* Cancella dati */}
        <div style={{ ...cardStyle, borderColor: 'rgba(239,68,68,0.3)' }}>
          <div style={{ ...headerStyle }}>
            <Trash2 size={16} color="#ef4444" />
            {t('privacyPage.deleteAll')}
          </div>
          <p style={{ fontSize: '13px', color: 'var(--vio-text-secondary)', marginBottom: '12px' }}>
            {t('privacyPage.deleteDesc')}
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
          <div>{t('privacyPage.footerLicense')}</div>
          <div>{t('privacyPage.footerDisclaimer')}</div>
          <div>
            <a href="https://github.com/vio83/vio83-ai-orchestra" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--vio-cyan)', marginRight: '16px' }}>GitHub</a>
            <a href="mailto:porcu.v.83@gmail.com" style={{ color: 'var(--vio-cyan)' }}>porcu.v.83@gmail.com</a>
          </div>
          <div style={{ marginTop: '4px' }}>{t('privacyPage.footerJurisdiction')}</div>
        </div>

      </div>
    </div>
  );
}
