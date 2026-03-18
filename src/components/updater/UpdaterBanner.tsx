/**
 * UpdaterBanner — Auto-update notification per VIO 83 AI Orchestra
 *
 * Usa il plugin Tauri v2 `@tauri-apps/plugin-updater` per:
 * - Controllare aggiornamenti all'avvio (e ogni 4 ore)
 * - Mostrare un banner discreto quando disponibile
 * - Scaricare e installare con feedback progress
 *
 * Graceful: se il plugin non è disponibile (dev mode), non mostra nulla.
 */
import { useEffect, useState } from 'react';
import { useI18n } from '../../hooks/useI18n';

type UpdateStatus =
  | 'idle'
  | 'checking'
  | 'available'
  | 'downloading'
  | 'ready'
  | 'error';

interface UpdateInfo {
  version: string;
  date?: string;
  body?: string;
}

const CHECK_INTERVAL_MS = 4 * 60 * 60 * 1000; // 4 ore

export default function UpdaterBanner() {
  const { t } = useI18n();
  const [status, setStatus] = useState<UpdateStatus>('idle');
  const [updateInfo, setUpdateInfo] = useState<UpdateInfo | null>(null);
  const [progress, setProgress] = useState(0);
  const [dismissed, setDismissed] = useState(false);

  const checkForUpdates = async () => {
    try {
      // Importazione dinamica — evita errori in dev mode senza il plugin
      const { check } = await import('@tauri-apps/plugin-updater');
      setStatus('checking');
      const update = await check();

      if (update?.available) {
        setUpdateInfo({
          version: update.version,
          date: update.date,
          body: update.body,
        });
        setStatus('available');
      } else {
        setStatus('idle');
      }
    } catch {
      // Plugin non disponibile o rete assente — fail silenzioso
      setStatus('idle');
    }
  };

  useEffect(() => {
    // Controlla all'avvio dopo 10s (non bloccare il boot)
    const initial = setTimeout(checkForUpdates, 10_000);
    // Controlla ogni 4 ore
    const interval = setInterval(checkForUpdates, CHECK_INTERVAL_MS);
    return () => {
      clearTimeout(initial);
      clearInterval(interval);
    };
  }, []);

  const handleInstall = async () => {
    if (!updateInfo) return;
    setStatus('downloading');
    setProgress(0);

    try {
      const { check } = await import('@tauri-apps/plugin-updater');
      const update = await check();
      if (!update?.available) return;

      await update.downloadAndInstall((event) => {
        if (event.event === 'Progress' && event.data.chunkLength && event.data.contentLength) {
          setProgress(Math.round((event.data.chunkLength / event.data.contentLength) * 100));
        }
      });

      setStatus('ready');
    } catch (e) {
      console.error('[Updater] Install failed:', e);
      setStatus('error');
    }
  };

  const handleRestart = async () => {
    try {
      const { relaunch } = await import('@tauri-apps/plugin-process');
      await relaunch();
    } catch {
      window.location.reload();
    }
  };

  if (dismissed || status === 'idle' || status === 'checking') return null;

  const bannerStyle: React.CSSProperties = {
    position: 'fixed',
    bottom: '16px',
    right: '16px',
    zIndex: 100,
    width: '320px',
    background: 'var(--vio-bg-secondary)',
    border: '1px solid var(--vio-green)',
    borderRadius: '10px',
    padding: '14px 16px',
    boxShadow: '0 4px 20px rgba(0,0,0,0.4)',
    fontSize: '13px',
    color: 'var(--vio-text-primary)',
  };

  return (
    <div style={bannerStyle} role="alert" aria-live="polite">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '10px' }}>
        <div style={{ fontWeight: 700, color: 'var(--vio-green)' }}>
          {status === 'available' && `🆕 ${t('updater.available')}`}
          {status === 'downloading' && `⬇️ ${t('updater.downloading')}`}
          {status === 'ready' && `✅ ${t('updater.restart_required')}`}
          {status === 'error' && `⚠️ ${t('common.error')}`}
        </div>
        {status === 'available' && (
          <button
            onClick={() => setDismissed(true)}
            style={{
              background: 'none', border: 'none', cursor: 'pointer',
              color: 'var(--vio-text-dim)', fontSize: '16px', lineHeight: 1, padding: '0 2px',
            }}
            aria-label="Chiudi"
          >
            ×
          </button>
        )}
      </div>

      {status === 'available' && updateInfo && (
        <>
          <div style={{ color: 'var(--vio-text-secondary)', marginBottom: '12px' }}>
            {t('updater.version', { version: updateInfo.version })}
          </div>
          <div style={{ display: 'flex', gap: '8px' }}>
            <button
              onClick={handleInstall}
              style={{
                flex: 1, padding: '7px 12px', borderRadius: '7px',
                background: 'var(--vio-green)', border: 'none',
                color: '#052e16', fontWeight: 700, cursor: 'pointer', fontSize: '12px',
              }}
            >
              {t('updater.download')}
            </button>
            <button
              onClick={() => setDismissed(true)}
              style={{
                padding: '7px 12px', borderRadius: '7px',
                background: 'transparent', border: '1px solid var(--vio-border)',
                color: 'var(--vio-text-secondary)', cursor: 'pointer', fontSize: '12px',
              }}
            >
              {t('updater.later')}
            </button>
          </div>
        </>
      )}

      {status === 'downloading' && (
        <div>
          <div style={{ color: 'var(--vio-text-secondary)', marginBottom: '8px' }}>
            {progress > 0 ? `${progress}%` : t('updater.downloading')}
          </div>
          <div style={{ background: 'var(--vio-bg-primary)', borderRadius: '4px', height: '6px', overflow: 'hidden' }}>
            <div style={{
              height: '100%',
              width: `${progress}%`,
              background: 'var(--vio-green)',
              transition: 'width 0.3s ease',
              borderRadius: '4px',
            }} />
          </div>
        </div>
      )}

      {status === 'ready' && (
        <button
          onClick={handleRestart}
          style={{
            width: '100%', padding: '8px', borderRadius: '7px',
            background: 'var(--vio-green)', border: 'none',
            color: '#052e16', fontWeight: 700, cursor: 'pointer', fontSize: '12px',
          }}
        >
          {t('updater.restart')}
        </button>
      )}

      {status === 'error' && (
        <div style={{ color: 'var(--vio-text-dim)', fontSize: '12px' }}>
          {t('updater.check_failed')}
        </div>
      )}
    </div>
  );
}
