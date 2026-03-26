// VIO 83 AI ORCHESTRA - Conversation Service
// Sincronizza conversazioni tra frontend e backend

const BACKEND_BASE = '/api';
const DEFAULT_LIST_LIMIT = 50;
const MAX_LIST_LIMIT = 200;
const RETRYABLE_STATUS = new Set([408, 429, 502, 503, 504]);

export class ConversationServiceError extends Error {
  status?: number;
  isTimeout: boolean;
  isRetryable: boolean;

  constructor(message: string, options?: { status?: number; isTimeout?: boolean; isRetryable?: boolean }) {
    super(message);
    this.name = 'ConversationServiceError';
    this.status = options?.status;
    this.isTimeout = Boolean(options?.isTimeout);
    this.isRetryable = Boolean(options?.isRetryable);
  }
}

export function isConversationServiceError(error: unknown): error is ConversationServiceError {
  return error instanceof ConversationServiceError;
}

export interface FetchConversationsOptions {
  limit?: number;
  offset?: number;
  includeArchived?: boolean;
  retry?: boolean;
}

export interface CreateConversationPayload {
  title?: string;
  mode?: string;
}

function sanitizeOffset(offset: number): number {
  if (!Number.isFinite(offset)) return 0;
  return Math.max(0, Math.trunc(offset));
}

function sanitizeTitle(title: string): string {
  const normalized = title.trim();
  if (!normalized) throw new ConversationServiceError('Title is required');
  return normalized.slice(0, 160);
}

function clampListLimit(limit: number): number {
  if (!Number.isFinite(limit)) return DEFAULT_LIST_LIMIT;
  return Math.min(MAX_LIST_LIMIT, Math.max(1, Math.trunc(limit)));
}

function buildConversationPath(convId: string): string {
  const normalized = convId.trim();
  if (!normalized) {
    throw new ConversationServiceError('Conversation id is required');
  }
  return `${BACKEND_BASE}/conversations/${encodeURIComponent(normalized)}`;
}

function withJsonAcceptHeader(init?: RequestInit): RequestInit {
  return {
    ...init,
    headers: {
      Accept: 'application/json',
      ...(init?.headers ?? {}),
    },
  };
}

function isAbortError(error: unknown): boolean {
  return error instanceof DOMException && error.name === 'AbortError';
}

async function readErrorMessage(response: Response): Promise<string> {
  try {
    const contentType = response.headers.get('content-type') ?? '';
    if (contentType.includes('application/json')) {
      const payload = await response.json() as { detail?: unknown; error?: unknown; message?: unknown };
      const detail = payload.detail ?? payload.error ?? payload.message;
      if (typeof detail === 'string' && detail.trim()) {
        return detail.trim();
      }
    } else {
      const text = (await response.text()).trim();
      if (text) return text;
    }
  } catch {
    // Ignore body parsing issues and fallback to status text.
  }

  return response.statusText || `HTTP ${response.status}`;
}

async function requestJson<T>(url: string, timeoutMs: number, init?: RequestInit): Promise<T> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(url, {
      ...withJsonAcceptHeader(init),
      signal: controller.signal,
    });

    if (!response.ok) {
      const reason = await readErrorMessage(response);
      throw new ConversationServiceError(`Backend ${response.status}: ${reason}`, {
        status: response.status,
        isRetryable: RETRYABLE_STATUS.has(response.status),
      });
    }

    try {
      return await response.json() as T;
    } catch {
      throw new ConversationServiceError('Backend returned invalid JSON response');
    }
  } catch (error) {
    if (isAbortError(error)) {
      throw new ConversationServiceError(`Backend timeout after ${timeoutMs}ms`, {
        isTimeout: true,
        isRetryable: true,
      });
    }
    if (error instanceof ConversationServiceError) {
      throw error;
    }
    throw new ConversationServiceError(error instanceof Error ? error.message : 'Unknown backend error');
  } finally {
    clearTimeout(timeoutId);
  }
}

async function requestVoid(url: string, timeoutMs: number, init?: RequestInit): Promise<void> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(url, {
      ...withJsonAcceptHeader(init),
      signal: controller.signal,
    });

    if (!response.ok) {
      const reason = await readErrorMessage(response);
      throw new ConversationServiceError(`Backend ${response.status}: ${reason}`, {
        status: response.status,
        isRetryable: RETRYABLE_STATUS.has(response.status),
      });
    }
  } catch (error) {
    if (isAbortError(error)) {
      throw new ConversationServiceError(`Backend timeout after ${timeoutMs}ms`, {
        isTimeout: true,
        isRetryable: true,
      });
    }
    if (error instanceof ConversationServiceError) {
      throw error;
    }
    throw new ConversationServiceError(error instanceof Error ? error.message : 'Unknown backend error');
  } finally {
    clearTimeout(timeoutId);
  }
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => {
    setTimeout(resolve, ms);
  });
}

async function requestJsonWithRetry<T>(url: string, timeoutMs: number, init?: RequestInit): Promise<T> {
  try {
    return await requestJson<T>(url, timeoutMs, init);
  } catch (error) {
    const serviceError = isConversationServiceError(error) ? error : null;
    if (!serviceError?.isRetryable) throw error;

    await sleep(250);
    return requestJson<T>(url, timeoutMs + 1500, init);
  }
}

async function requestVoidWithRetry(url: string, timeoutMs: number, init?: RequestInit): Promise<void> {
  try {
    await requestVoid(url, timeoutMs, init);
  } catch (error) {
    const serviceError = isConversationServiceError(error) ? error : null;
    if (!serviceError?.isRetryable) throw error;

    await sleep(250);
    await requestVoid(url, timeoutMs + 1500, init);
  }
}

export interface BackendConversation {
  id: string;
  title: string;
  created_at: number;
  updated_at: number;
  mode: string;
  primary_provider: string;
  message_count: number;
  total_tokens: number;
  archived: number;
  messages?: BackendMessage[];
}

export interface BackendMessage {
  id: string;
  conversation_id: string;
  role: 'user' | 'assistant';
  content: string;
  provider: string | null;
  model: string | null;
  tokens_used: number;
  latency_ms: number;
  verified: number | null;
  quality_score: number | null;
  timestamp: number;
}

export async function fetchConversations(
  options: number | FetchConversationsOptions = DEFAULT_LIST_LIMIT,
): Promise<BackendConversation[]> {
  const normalized = typeof options === 'number'
    ? { limit: options }
    : options;

  const safeLimit = clampListLimit(normalized.limit ?? DEFAULT_LIST_LIMIT);
  const safeOffset = sanitizeOffset(normalized.offset ?? 0);
  const includeArchived = normalized.includeArchived ? '1' : '0';
  const url = `${BACKEND_BASE}/conversations?limit=${safeLimit}&offset=${safeOffset}&include_archived=${includeArchived}`;

  if (normalized.retry === false) {
    return requestJson<BackendConversation[]>(url, 3000);
  }

  return requestJsonWithRetry<BackendConversation[]>(url, 3000);
}

export async function createBackendConversation(
  payload: CreateConversationPayload = {},
): Promise<BackendConversation> {
  const params = new URLSearchParams();
  params.set('title', sanitizeTitle(payload.title ?? 'Nuova conversazione'));
  params.set('mode', (payload.mode?.trim() || 'local').slice(0, 64));

  return requestJson<BackendConversation>(`${BACKEND_BASE}/conversations?${params.toString()}`, 4000, {
    method: 'POST',
  });
}

export async function fetchConversation(
  convId: string,
): Promise<BackendConversation> {
  return requestJson<BackendConversation>(buildConversationPath(convId), 5000);
}

export async function deleteBackendConversation(
  convId: string,
): Promise<void> {
  await requestVoidWithRetry(buildConversationPath(convId), 3000, { method: 'DELETE' });
}

export async function archiveBackendConversation(convId: string): Promise<void> {
  await requestVoidWithRetry(`${buildConversationPath(convId)}/archive`, 3500, { method: 'POST' });
}

export async function updateBackendConversationTitle(convId: string, title: string): Promise<void> {
  const safeTitle = sanitizeTitle(title);
  const params = new URLSearchParams();
  params.set('title', safeTitle);

  await requestVoidWithRetry(`${buildConversationPath(convId)}/title?${params.toString()}`, 3500, {
    method: 'PUT',
  });
}
