export const BACKEND_API_BASE = '/api';

export function buildBackendUrl(path: string): string {
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  return `${BACKEND_API_BASE}${normalizedPath}`;
}