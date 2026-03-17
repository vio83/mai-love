// VIO 83 AI ORCHESTRA - App Principale con Navigazione Multi-Pagina
import { Menu } from 'lucide-react';
import { lazy, Suspense, useEffect } from 'react';
import ParticleBackground from './components/layout/ParticleBackground';
import OnboardingWizard from './components/onboarding/OnboardingWizard';
import { SettingsPanel } from './components/settings/SettingsPanel';
import Sidebar from './components/sidebar/Sidebar';
import { detectLocale } from './i18n';
import { useAppStore } from './stores/appStore';
import './styles/vio-dark.css';

const DashboardPage = lazy(() => import('./pages/DashboardPage'));
const ChatView = lazy(() => import('./components/chat/ChatView'));
const WorkflowPage = lazy(() => import('./pages/WorkflowPage'));
const CrossCheckPage = lazy(() => import('./pages/CrossCheckPage'));
const AnalyticsPage = lazy(() => import('./pages/AnalyticsPage'));
const RagPage = lazy(() => import('./pages/RagPage'));
const ModelsPage = lazy(() => import('./pages/ModelsPage'));
const OrchestraRuntimePage = lazy(() => import('./pages/OrchestraRuntimePage'));

export default function App() {
  const { sidebarOpen, toggleSidebar, settings, settingsOpen, currentPage, updateSettings } = useAppStore();

  useEffect(() => {
    if (!settings.onboardingCompleted) {
      const autoLocale = detectLocale();
      if (settings.language !== autoLocale) {
        updateSettings({ language: autoLocale });
      }
    }
  }, [settings.onboardingCompleted, settings.language, updateSettings]);

  const showOnboarding = !settings.onboardingCompleted;

  const loadingFallback = (
    <div style={{
      height: '100%',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      color: 'var(--vio-text-dim)',
      fontSize: '13px',
      background: 'var(--vio-bg-primary)',
    }}>
      Caricamento runtime…
    </div>
  );

  const notFoundFallback = (
    <div style={{
      height: '100%',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      gap: '10px',
      color: 'var(--vio-text-secondary)',
      background: 'var(--vio-bg-primary)',
      padding: '24px',
      textAlign: 'center',
    }}>
      <div style={{ fontSize: '28px' }}>🧭</div>
      <div style={{ fontWeight: 700, color: 'var(--vio-text-primary)' }}>Pagina non trovata</div>
      <div style={{ fontSize: '13px' }}>La sezione richiesta non esiste o è stata rinominata.</div>
    </div>
  );

  // Render the active page
  const renderPage = () => {
    switch (currentPage) {
      case 'dashboard': return <DashboardPage />;
      case 'chat': return <ChatView />;
      case 'workflow': return <WorkflowPage />;
      case 'crosscheck': return <CrossCheckPage />;
      case 'analytics': return <AnalyticsPage />;
      case 'rag': return <RagPage />;
      case 'models': return <ModelsPage />;
      case 'runtime': return <OrchestraRuntimePage />;
      case 'settings': return <SettingsPanel variant="page" />;
      default: return notFoundFallback;
    }
  };

  const pageTitle: Record<string, string> = {
    dashboard: 'Dashboard',
    chat: 'AI Chat',
    workflow: 'Workflow Builder',
    crosscheck: 'Cross-Check',
    analytics: 'Analytics',
    rag: 'RAG Knowledge',
    models: 'AI Models',
    runtime: 'Runtime 360',
    settings: 'Impostazioni',
  };

  return (
    <div style={{
      display: 'flex',
      height: '100vh',
      width: '100vw',
      overflow: 'hidden',
      backgroundColor: 'var(--vio-bg-primary)',
      color: 'var(--vio-text-primary)',
      position: 'relative',
    }}>
      <ParticleBackground />

      {/* Sidebar */}
      <Sidebar />

      {/* Main content */}
      <div style={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        minWidth: 0,
      }}>
        {/* Top bar */}
        {!sidebarOpen && (
          <div style={{
            padding: '8px 16px',
            borderBottom: '1px solid var(--vio-border)',
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            backgroundColor: 'var(--vio-bg-secondary)',
          }}>
            <button
              onClick={toggleSidebar}
              style={{
                background: 'none', border: 'none', cursor: 'pointer',
                color: 'var(--vio-text-secondary)', padding: '4px',
              }}
            >
              <Menu size={20} />
            </button>
            <span style={{ fontSize: '14px', color: 'var(--vio-green)', fontWeight: 600 }}>
              VIO 83 AI Orchestra
            </span>
            <span style={{ fontSize: '12px', color: 'var(--vio-text-dim)' }}>
              — {pageTitle[currentPage] || 'Chat'}
            </span>
            <span style={{
              fontSize: '11px',
              marginLeft: 'auto',
              padding: '2px 8px',
              borderRadius: '10px',
              border: `1px solid ${settings.orchestrator.mode === 'cloud' ? 'var(--vio-cyan)' : 'var(--vio-green)'}`,
              color: settings.orchestrator.mode === 'cloud' ? 'var(--vio-cyan)' : 'var(--vio-green)',
            }}>
              {settings.orchestrator.mode === 'cloud' ? '☁️ Cloud' : '💻 Locale'}
            </span>
          </div>
        )}

        {/* Page content */}
        <div style={{ flex: 1, overflow: 'hidden' }}>
          <Suspense fallback={loadingFallback}>
            {renderPage()}
          </Suspense>
        </div>
      </div>

      {/* Settings modal — only as overlay when triggered from non-settings pages */}
      {settingsOpen && currentPage !== 'settings' && <SettingsPanel />}

      {/* First-run onboarding */}
      {showOnboarding && (
        <OnboardingWizard onComplete={() => updateSettings({ onboardingCompleted: true })} />
      )}
    </div>
  );
}
