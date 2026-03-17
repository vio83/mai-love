// ============================================================
// VIO 83 AI ORCHESTRA — Global Error Boundary
// Copyright (c) 2026 Viorica Porcu (vio83) — AGPL-3.0
// Catches unhandled React render errors and shows a recovery UI
// ============================================================
import { Component, type ErrorInfo, type ReactNode } from 'react';

interface Props {
  children: ReactNode;
  /** Optional custom fallback UI */
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
  errorId: string;
}

function generateErrorId(): string {
  return `ERR-${Date.now().toString(36).toUpperCase()}-${Math.random().toString(36).slice(2, 6).toUpperCase()}`;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      errorId: '',
    };
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    return {
      hasError: true,
      error,
      errorId: generateErrorId(),
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    this.setState({ errorInfo });

    // Log strutturato per debugging e telemetry futura
    console.error('[VIO ErrorBoundary]', {
      errorId: this.state.errorId,
      message: error.message,
      name: error.name,
      stack: error.stack,
      componentStack: errorInfo.componentStack,
      timestamp: new Date().toISOString(),
    });
  }

  handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
      errorId: '',
    });
  };

  handleReload = () => {
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      const { error, errorInfo, errorId } = this.state;
      const isDev = import.meta.env.DEV;

      return (
        <div
          role="alert"
          aria-live="assertive"
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            height: '100vh',
            width: '100vw',
            background: 'var(--vio-bg-primary, #0d1117)',
            color: 'var(--vio-text-primary, #e6edf3)',
            fontFamily: "'Inter', 'SF Pro Text', system-ui, sans-serif",
            padding: '32px',
            boxSizing: 'border-box',
            gap: '24px',
          }}
        >
          {/* Icon */}
          <div style={{ fontSize: '48px', lineHeight: 1 }}>⚠️</div>

          {/* Title */}
          <div style={{ textAlign: 'center', maxWidth: '560px' }}>
            <h1 style={{
              fontSize: '22px',
              fontWeight: 700,
              color: 'var(--vio-red, #ff4444)',
              margin: '0 0 8px',
            }}>
              Errore critico dell'applicazione
            </h1>
            <p style={{
              fontSize: '14px',
              color: 'var(--vio-text-secondary, #8b949e)',
              margin: 0,
              lineHeight: 1.6,
            }}>
              VIO 83 AI Orchestra ha incontrato un errore inatteso.
              Premi <strong style={{ color: 'var(--vio-text-primary, #e6edf3)' }}>Ripristina</strong> per riprendere
              oppure <strong style={{ color: 'var(--vio-text-primary, #e6edf3)' }}>Ricarica</strong> per riavviare.
            </p>
          </div>

          {/* Error ID badge */}
          <div style={{
            padding: '4px 12px',
            borderRadius: '6px',
            background: 'var(--vio-bg-secondary, #161b22)',
            border: '1px solid var(--vio-border, #30363d)',
            fontSize: '11px',
            fontFamily: 'monospace',
            color: 'var(--vio-text-dim, #6e7681)',
            letterSpacing: '0.05em',
          }}>
            Error ID: {errorId}
          </div>

          {/* Buttons */}
          <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', justifyContent: 'center' }}>
            <button
              onClick={this.handleReset}
              style={{
                padding: '10px 24px',
                borderRadius: '8px',
                border: 'none',
                background: 'var(--vio-green, #39d353)',
                color: '#0d1117',
                fontWeight: 700,
                fontSize: '14px',
                cursor: 'pointer',
                transition: 'opacity 0.15s',
              }}
              onMouseEnter={e => (e.currentTarget.style.opacity = '0.85')}
              onMouseLeave={e => (e.currentTarget.style.opacity = '1')}
            >
              🔄 Ripristina componente
            </button>
            <button
              onClick={this.handleReload}
              style={{
                padding: '10px 24px',
                borderRadius: '8px',
                border: '1px solid var(--vio-border, #30363d)',
                background: 'transparent',
                color: 'var(--vio-text-primary, #e6edf3)',
                fontWeight: 600,
                fontSize: '14px',
                cursor: 'pointer',
                transition: 'background 0.15s',
              }}
              onMouseEnter={e => (e.currentTarget.style.background = 'var(--vio-bg-secondary, #161b22)')}
              onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
            >
              ↺ Ricarica applicazione
            </button>
          </div>

          {/* Dev-only stack trace */}
          {isDev && error && (
            <details style={{
              maxWidth: '760px',
              width: '100%',
              background: 'var(--vio-bg-secondary, #161b22)',
              border: '1px solid var(--vio-border, #30363d)',
              borderRadius: '8px',
              overflow: 'hidden',
            }}>
              <summary style={{
                padding: '10px 16px',
                cursor: 'pointer',
                fontSize: '12px',
                fontWeight: 600,
                color: 'var(--vio-text-secondary, #8b949e)',
                userSelect: 'none',
              }}>
                🔍 Stack trace (solo in modalità sviluppo)
              </summary>
              <pre style={{
                padding: '16px',
                margin: 0,
                fontSize: '11px',
                color: 'var(--vio-red, #ff4444)',
                overflowX: 'auto',
                whiteSpace: 'pre-wrap',
                wordBreak: 'break-word',
                lineHeight: 1.5,
              }}>
                {error.name}: {error.message}
                {'\n\n'}
                {error.stack}
                {errorInfo?.componentStack && (
                  '\n\nComponent Stack:' + errorInfo.componentStack
                )}
              </pre>
            </details>
          )}
        </div>
      );
    }

    return this.props.children;
  }
}

/**
 * Lightweight functional wrapper — use for page-level isolation
 * so one broken page doesn't crash the entire layout.
 *
 * Usage:
 *   <PageErrorBoundary name="ChatView">
 *     <ChatView />
 *   </PageErrorBoundary>
 */
export function PageErrorBoundary({
  children,
  name = 'Pagina',
}: {
  children: ReactNode;
  name?: string;
}) {
  const fallback = (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      height: '100%',
      gap: '12px',
      color: 'var(--vio-text-secondary, #8b949e)',
      padding: '32px',
    }}>
      <span style={{ fontSize: '32px' }}>⚠️</span>
      <p style={{ margin: 0, fontSize: '14px', textAlign: 'center' }}>
        <strong style={{ color: 'var(--vio-text-primary, #e6edf3)' }}>{name}</strong>
        {' '}non è riuscito a caricarsi.
      </p>
      <button
        onClick={() => window.location.reload()}
        style={{
          padding: '6px 16px',
          borderRadius: '6px',
          border: '1px solid var(--vio-border, #30363d)',
          background: 'transparent',
          color: 'var(--vio-text-primary, #e6edf3)',
          cursor: 'pointer',
          fontSize: '13px',
        }}
      >
        Ricarica
      </button>
    </div>
  );

  return <ErrorBoundary fallback={fallback}>{children}</ErrorBoundary>;
}

export default ErrorBoundary;
