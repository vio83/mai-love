import React, { useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import ErrorBoundary from './components/ErrorBoundary';
import { initI18n } from './i18n';
import './index.css';

// Lazy-load App to catch import errors gracefully
const App = React.lazy(() => import('./App'));

// Initialize i18n (graceful — app works even if react-i18next not installed)
initI18n().then((ok) => {
  if (!ok) {
    console.info('[VIO] i18n skipped — using built-in translations');
  }
}).catch(() => {
  console.info('[VIO] i18n init failed gracefully');
});

// Runtime autopilot — lazy import to avoid blocking render
function RuntimeBootstrap() {
  useEffect(() => {
    let dispose;
    import('./runtime/runtimeAutopilot')
      .then((mod) => {
        dispose = mod.bootstrapRuntimeAutopilot();
      })
      .catch((err) => {
        console.warn('[VIO] Runtime autopilot skipped:', err);
      });
    return () => dispose?.();
  }, []);

  return (
    <React.Suspense
      fallback={
        <div
          style={{
            height: '100vh',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            background: '#000',
            color: '#00ff00',
            fontFamily: "'Inter', system-ui, sans-serif",
            gap: '16px',
          }}
        >
          <div style={{ fontSize: '48px' }}>🎵</div>
          <div style={{ fontSize: '18px', fontWeight: 700 }}>
            VIO 83 AI Orchestra
          </div>
          <div style={{ fontSize: '13px', color: '#666' }}>
            Caricamento in corso...
          </div>
        </div>
      }
    >
      <App />
    </React.Suspense>
  );
}

const rootEl = document.getElementById('root');
if (rootEl) {
  ReactDOM.createRoot(rootEl).render(
    <React.StrictMode>
      <ErrorBoundary>
        <RuntimeBootstrap />
      </ErrorBoundary>
    </React.StrictMode>,
  );
} else {
  console.error('[VIO] #root element not found in DOM!');
}
