// VIO 83 AI ORCHESTRA — Mobile Layout Wrapper
// Gestisce safe areas iOS, gesture navigation, responsive sidebar
import { ArrowLeft, Menu, Settings } from 'lucide-react';
import type { ReactNode } from 'react';
import { usePlatform } from '../../hooks/usePlatform';
import { useAppStore } from '../../stores/appStore';

interface MobileLayoutProps {
  children: ReactNode;
  title?: string;
  showBackButton?: boolean;
  onBack?: () => void;
}

export default function MobileLayout({ children, title, showBackButton, onBack }: MobileLayoutProps) {
  const { isMobile, isSmallScreen, safeAreaTop, safeAreaBottom, platform } = usePlatform();
  const toggleSidebar = useAppStore((s) => s.toggleSidebar);
  const toggleSettings = useAppStore((s) => s.toggleSettings);
  const sidebarOpen = useAppStore((s) => s.sidebarOpen);

  // Solo su mobile/small screen attiva il layout mobile
  if (!isMobile && !isSmallScreen) return <>{children}</>;

  return (
    <div
      className="mobile-layout"
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100dvh', // dynamic viewport height (gestisce tastiera mobile)
        width: '100vw',
        overflow: 'hidden',
        paddingTop: safeAreaTop > 0 ? `${safeAreaTop}px` : platform === 'ios' ? '47px' : '0',
        paddingBottom: safeAreaBottom > 0 ? `${safeAreaBottom}px` : platform === 'ios' ? '34px' : '0',
        background: 'var(--vio-bg-primary)',
      }}
    >
      {/* Mobile Header */}
      <header
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '8px 12px',
          borderBottom: '1px solid var(--vio-border)',
          background: 'var(--vio-bg-secondary)',
          minHeight: '48px',
          flexShrink: 0,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {showBackButton ? (
            <button
              onClick={onBack}
              style={{
                background: 'none',
                border: 'none',
                color: 'var(--vio-accent)',
                cursor: 'pointer',
                padding: '8px',
                display: 'flex',
              }}
            >
              <ArrowLeft size={20} />
            </button>
          ) : (
            <button
              onClick={toggleSidebar}
              style={{
                background: 'none',
                border: 'none',
                color: 'var(--vio-text)',
                cursor: 'pointer',
                padding: '8px',
                display: 'flex',
              }}
            >
              <Menu size={20} />
            </button>
          )}
          <span
            style={{
              fontSize: '16px',
              fontWeight: 600,
              color: 'var(--vio-text)',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
              maxWidth: '200px',
            }}
          >
            {title || 'VIO 83'}
          </span>
        </div>

        <button
          onClick={toggleSettings}
          style={{
            background: 'none',
            border: 'none',
            color: 'var(--vio-text-dim)',
            cursor: 'pointer',
            padding: '8px',
            display: 'flex',
          }}
        >
          <Settings size={20} />
        </button>
      </header>

      {/* Mobile Sidebar Overlay */}
      {sidebarOpen && (
        <div
          onClick={toggleSidebar}
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0,0,0,0.5)',
            zIndex: 90,
          }}
        />
      )}

      {/* Content */}
      <main
        style={{
          flex: 1,
          overflow: 'auto',
          WebkitOverflowScrolling: 'touch', // smooth scroll iOS
          position: 'relative',
        }}
      >
        {children}
      </main>
    </div>
  );
}
