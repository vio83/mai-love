// VIO 83 AI ORCHESTRA — Mobile Configuration Service
// Gestisce la connessione al backend per piattaforme mobile
// Su desktop: localhost:4000 (backend locale)
// Su mobile: URL configurabile (backend remoto o tunnel)

interface MobileConfig {
  backendUrl: string;
  isRemote: boolean;
  connectionStatus: 'connected' | 'disconnected' | 'connecting';
}

const STORAGE_KEY = 'vio83_mobile_backend_url';
const DEFAULT_LOCAL_URL = 'http://localhost:4000';

// Tunnel services che possono esporre il backend locale
const KNOWN_TUNNEL_PATTERNS = [
  /\.ngrok-free\.app$/,
  /\.loca\.lt$/,
  /\.cloudflare\.com$/,
  /\.tailscale\.net$/,
];

function detectPlatformType(): 'desktop' | 'mobile' | 'web' {
  if (typeof window === 'undefined') return 'web';
  const hasTauri = '__TAURI_INTERNALS__' in window;
  if (!hasTauri) return 'web';

  const ua = navigator.userAgent.toLowerCase();
  if (/iphone|ipad|android/.test(ua)) return 'mobile';
  return 'desktop';
}

/**
 * Ottieni l'URL base del backend.
 * Desktop → localhost:4000
 * Mobile → URL salvato o discovery
 */
export function getBackendBaseUrl(): string {
  const platform = detectPlatformType();

  if (platform === 'desktop') {
    return DEFAULT_LOCAL_URL;
  }

  // Mobile: usa URL configurato o default
  if (platform === 'mobile') {
    try {
      const saved = globalThis.localStorage?.getItem(STORAGE_KEY);
      if (saved && saved.startsWith('http')) return saved;
    } catch {
      // localStorage non disponibile
    }
  }

  // Web: usa proxy relativo (Vite proxy in dev, nginx/caddy in prod)
  return '';
}

/**
 * Salva l'URL del backend remoto (per mobile).
 */
export function setBackendUrl(url: string): void {
  try {
    globalThis.localStorage?.setItem(STORAGE_KEY, url);
  } catch {
    // ignore
  }
}

/**
 * Verifica la connessione al backend.
 */
export async function checkBackendConnection(url?: string): Promise<{
  ok: boolean;
  latencyMs: number;
  version?: string;
}> {
  const baseUrl = url || getBackendBaseUrl();
  const healthUrl = baseUrl ? `${baseUrl}/health` : '/api/health';
  const start = performance.now();

  try {
    const response = await fetch(healthUrl, {
      signal: AbortSignal.timeout(5000),
    });
    const latencyMs = Math.round(performance.now() - start);

    if (response.ok) {
      const data = await response.json();
      return { ok: true, latencyMs, version: data.version };
    }
    return { ok: false, latencyMs };
  } catch {
    return { ok: false, latencyMs: Math.round(performance.now() - start) };
  }
}

/**
 * Genera QR code data per connessione mobile.
 * Il desktop genera un URL con il suo IP locale o tunnel.
 */
export function generateConnectionPayload(tunnelUrl?: string): string {
  const payload = {
    type: 'vio83-connect',
    version: '1.0',
    url: tunnelUrl || DEFAULT_LOCAL_URL,
    timestamp: Date.now(),
  };
  return JSON.stringify(payload);
}

/**
 * Parsa il payload di connessione da QR code.
 */
export function parseConnectionPayload(data: string): { url: string } | null {
  try {
    const parsed = JSON.parse(data);
    if (parsed.type === 'vio83-connect' && parsed.url) {
      return { url: parsed.url };
    }
  } catch {
    // Se è un URL diretto
    if (data.startsWith('http')) {
      return { url: data };
    }
  }
  return null;
}

/**
 * Controlla se un URL è un tunnel conosciuto.
 */
export function isTunnelUrl(url: string): boolean {
  try {
    const hostname = new URL(url).hostname;
    return KNOWN_TUNNEL_PATTERNS.some((p) => p.test(hostname));
  } catch {
    return false;
  }
}

export type { MobileConfig };
