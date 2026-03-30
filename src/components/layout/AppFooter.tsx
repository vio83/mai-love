// VIO 83 AI ORCHESTRA — Global Legal Footer
// Copyright (c) 2026 Viorica Porcu (vio83) — AGPL-3.0
import { useI18n } from '../../hooks/useI18n';

export default function AppFooter() {
  const { t } = useI18n();

  return (
    <footer
      style={{
        padding: '4px 16px',
        borderTop: '1px solid var(--vio-border)',
        backgroundColor: 'var(--vio-bg-secondary)',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        gap: '16px',
        flexWrap: 'wrap',
        fontSize: '10px',
        color: 'var(--vio-text-dim)',
        lineHeight: '1.6',
        flexShrink: 0,
      }}
    >
      <span>{t('app.footerDisclaimer')}</span>
      <span style={{ opacity: 0.4 }}>|</span>
      <span>{t('app.footerJurisdiction')}</span>
    </footer>
  );
}
