import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import ErrorBoundary from './components/ErrorBoundary';
import { initI18n } from './i18n';

// === PostHog Product Analytics (GAP-04) ===
// Attivo solo se VITE_POSTHOG_KEY è definita — zero impatto se assente
const _posthogKey = (import.meta as unknown as Record<string, Record<string, string>>).env?.VITE_POSTHOG_KEY ?? '';
if (_posthogKey) {
  // @ts-expect-error posthog-js è opzionale e può non essere installato.
  import('posthog-js').then(({ default: posthog }) => {
    posthog.init(_posthogKey, {
      api_host: (import.meta as unknown as Record<string, Record<string, string>>).env?.VITE_POSTHOG_HOST ?? 'https://app.posthog.com',
      autocapture: false,         // Solo eventi espliciti — privacy-first
      capture_pageview: true,
      persistence: 'localStorage',
    });
    console.warn('[VIO] PostHog analytics: ATTIVO');
  }).catch(() => {/* posthog-js non installato — silenzioso */});
}

// Initialize i18n (graceful — app works even if react-i18next not installed)
initI18n().then((ok) => {
  if (!ok) {
    console.warn('[VIO] i18n skipped — run: npm install react-i18next i18next i18next-browser-languagedetector');
  }
});

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  </React.StrictMode>,
);
