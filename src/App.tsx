// VIO 83 AI ORCHESTRA - App Principale con Navigazione Multi-Pagina
import { Menu } from 'lucide-react';
import { useAppStore } from './stores/appStore';
import Sidebar from './components/sidebar/Sidebar';
import ChatView from './components/chat/ChatView';
import { SettingsPanel } from './components/settings/SettingsPanel';
import DashboardPage from './pages/DashboardPage';
import ModelsPage from './pages/ModelsPage';
import AnalyticsPage from './pages/AnalyticsPage';
import WorkflowPage from './pages/WorkflowPage';
import RagPage from './pages/RagPage';
import CrossCheckPage from './pages/CrossCheckPage';
import './styles/vio-dark.css';

export default function App() {
  const { sidebarOpen, toggleSidebar, settings, settingsOpen, currentPage } = useAppStore();

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
      case 'settings': return <SettingsPanel />;
      default: return <ChatView />;
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
    }}>
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
          {renderPage()}
        </div>
      </div>

      {/* Settings modal — only as overlay when triggered from non-settings pages */}
      {settingsOpen && currentPage !== 'settings' && <SettingsPanel />}
    </div>
  );
}
