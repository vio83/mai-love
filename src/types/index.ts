// VIO 83 AI ORCHESTRA - Type Definitions

export type AIProvider = 'claude' | 'gpt4' | 'grok' | 'mistral' | 'deepseek' | 'gemini' | 'groq' | 'openrouter' | 'together' | 'perplexity' | 'ollama';

// Pagine disponibili nell'app
export type AppPage = 'chat' | 'dashboard' | 'analytics' | 'workflow' | 'models' | 'rag' | 'crosscheck' | 'runtime' | 'settings';

export type AIMode = 'cloud' | 'local';

export interface AIModel {
  id: string;
  name: string;
  provider: AIProvider;
  mode: AIMode;
  description: string;
  maxTokens: number;
  costPer1kTokens?: number; // undefined for local models
}

export interface Attachment {
  id: string;
  name: string;
  type: string;        // MIME type
  size: number;
  dataUrl?: string;    // base64 data URL for images/small files
  path?: string;       // local file path (desktop only)
}

export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  provider?: AIProvider;
  model?: string;
  timestamp: number;
  latencyMs?: number;    // Response latency in ms
  tokensUsed?: number;   // Tokens consumed
  qualityScore?: number; // Cross-check quality badge
  verified?: boolean;    // RAG verification status
  attachments?: Attachment[];
}

export interface Conversation {
  id: string;
  title: string;
  messages: Message[];
  model: string;
  provider: AIProvider;
  mode: AIMode;
  createdAt: number;
  updatedAt: number;
}

export interface APIKeyConfig {
  provider: AIProvider;
  key: string;
  isValid: boolean;
  lastChecked?: number;
}

export interface OrchestratorConfig {
  mode: AIMode;
  primaryProvider: AIProvider;
  fallbackProviders: AIProvider[];
  crossCheckEnabled: boolean;
  ragEnabled: boolean;
  strictEvidenceMode: boolean;
  autoRouting: boolean; // Smart routing based on request type
}

export interface AppSettings {
  theme: 'vio-dark' | 'light';
  language: 'it' | 'en';
  orchestrator: OrchestratorConfig;
  apiKeys: APIKeyConfig[];
  ollamaHost: string;
  ollamaModel: string;
  fontSize: number;
}

// AI Response with metadata
export interface AIResponse {
  content: string;
  provider: AIProvider;
  model: string;
  tokensUsed: number;
  latencyMs: number;
  crossCheckResult?: {
    concordance: boolean;
    concordanceScore?: number;
    secondProvider: AIProvider;
    secondResponse?: string;
  };
}

// Model info per la pagina Models
export interface AIModelInfo {
  id: string;
  name: string;
  provider: AIProvider;
  mode: AIMode;
  description: string;
  maxTokens: number;
  contextWindow: number;
  costPer1kInput?: number;
  costPer1kOutput?: number;
  speedScore: number;     // 0-100
  qualityScore: number;   // 0-100
  specialties: string[];
  supportsVision: boolean;
  supportsTools: boolean;
  status: 'online' | 'offline' | 'standby';
}

// Analytics data
export interface MetricEvent {
  id: string;
  provider: AIProvider;
  model: string;
  category: string;
  tokensUsed: number;
  latencyMs: number;
  costUsd: number;
  success: boolean;
  timestamp: number;
}

// Workflow node
export interface WorkflowNode {
  id: string;
  type: 'trigger' | 'router' | 'model' | 'crosscheck' | 'rag' | 'output' | 'condition';
  label: string;
  x: number;
  y: number;
  config?: Record<string, unknown>;
}

// Workflow
export interface Workflow {
  id: string;
  name: string;
  description: string;
  nodes: WorkflowNode[];
  connections: [string, string][];
  active: boolean;
  runs: number;
  createdAt: number;
}

// RAG Source
export interface RAGSource {
  id: string;
  name: string;
  documentsCount: number;
  status: 'indexed' | 'indexing' | 'queued' | 'error';
  quality: 'gold' | 'silver' | 'bronze' | 'unverified';
  category: string;
  lastUpdated: number;
}

// Cross-check result
export interface CrossCheckResult {
  id: string;
  query: string;
  models: string[];
  concordanceScore: number;
  level: 'full_agree' | 'partial' | 'disagree';
  verdict: string;
  timestamp: number;
}
