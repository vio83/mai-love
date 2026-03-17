import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import ErrorBoundary from './components/ErrorBoundary';
import { initI18n } from './i18n';

// Initialize i18n (graceful — app works even if react-i18next not installed)
initI18n().then((ok) => {
  if (!ok) {
    console.info('[VIO] i18n skipped — run: npm install react-i18next i18next i18next-browser-languagedetector');
  }
});

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  </React.StrictMode>,
);
