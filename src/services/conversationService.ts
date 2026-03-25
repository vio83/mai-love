// VIO 83 AI ORCHESTRA - Conversation Service
// Sincronizza conversazioni tra frontend e backend

const BACKEND_URL = 'http://localhost:4000';

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
  limit = 50,
): Promise<BackendConversation[]> {
  const response = await fetch(
    `${BACKEND_URL}/conversations?limit=${limit}`,
    { signal: AbortSignal.timeout(3000) },
  );
  if (!response.ok) throw new Error(`Backend: ${response.status}`);
  return response.json();
}

export async function fetchConversation(
  convId: string,
): Promise<BackendConversation> {
  const response = await fetch(
    `${BACKEND_URL}/conversations/${encodeURIComponent(convId)}`,
    { signal: AbortSignal.timeout(5000) },
  );
  if (!response.ok) throw new Error(`Backend: ${response.status}`);
  return response.json();
}

export async function deleteBackendConversation(
  convId: string,
): Promise<void> {
  const response = await fetch(
    `${BACKEND_URL}/conversations/${encodeURIComponent(convId)}`,
    { method: 'DELETE', signal: AbortSignal.timeout(3000) },
  );
  if (!response.ok) throw new Error(`Backend: ${response.status}`);
}
