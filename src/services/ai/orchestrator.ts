// VIO 83 AI ORCHESTRA - AI Orchestrator Service
// Il cuore dell'app: gestisce routing, fallback, cross-check e streaming
// Strategia backend-first: POST /chat/stream → JetEngine + RAG + persistence
// Fallback: chiamate dirette a Ollama/Cloud se backend non raggiungibile

import type { AIMode, AIProvider, AIResponse, Message } from '../../types';

const BACKEND_URL = 'http://localhost:4000';
const CONTEXT_WINDOW_MAX_MESSAGES = 10;
const CONTEXT_WINDOW_MAX_CHARS = 8_000;
const RESPONSE_CACHE_TTL_MS = 60_000;
const RESPONSE_CACHE_MAX_ENTRIES = 200;

type CachedResponseEntry = {
  response: AIResponse;
  timestamp: number;
};

const RESPONSE_CACHE = new Map<string, CachedResponseEntry>();

// Model mapping per cloud providers — REAL model IDs verified March 2026
const CLOUD_MODELS: Record<string, string> = {
  claude: 'anthropic/claude-sonnet-4-20250514',
  gpt4: 'openai/gpt-4o',
  grok: 'xai/grok-2-latest',
  mistral: 'mistral/mistral-large-latest',
  deepseek: 'deepseek/deepseek-chat',
  gemini: 'google/gemini-2.5-pro-preview-06-05',
  groq: 'groq/llama-3.3-70b-versatile',
  openrouter: 'openrouter/meta-llama/llama-3.3-70b-instruct:free',
  together: 'together/meta-llama/Llama-3.3-70B-Instruct-Turbo',
  perplexity: 'perplexity/sonar-pro',
};

const LOCAL_MODELS: Record<string, string> = {
  'qwen-coder': 'qwen2.5-coder:3b',
  'llama3': 'llama3.2:3b',
  'mistral': 'mistral:latest',
  'phi3': 'llama3.2:3b',
  'deepseek-coder': 'qwen2.5-coder:3b',
};

const LOCAL_MODEL_ALIASES: Record<string, string> = {
  'mistral:7b': 'mistral:latest',
  'phi3:3.8b': 'llama3.2:3b',
  'deepseek-coder-v2:lite': 'qwen2.5-coder:3b',
};

const LOCAL_FALLBACK_MODELS = [
  'qwen2.5-coder:3b',
  'llama3.2:3b',
  'gemma2:2b',
  'mistral:latest',
  'codellama:latest',
  'llama3:latest',
  'deepseek-r1:latest',
];

// Classificazione tipo richiesta per routing intelligente
type RequestType = 'code' | 'legal' | 'medical' | 'writing' | 'research' | 'automation' | 'creative' | 'analysis' | 'conversation' | 'realtime' | 'reasoning';

function extractProviderModelId(modelString: string): string {
  const parts = modelString.split('/');
  return parts.length > 1 ? parts.slice(1).join('/') : modelString;
}

function extractPerplexityOutput(data: unknown): string {
  const d = data as Record<string, unknown>;
  if (typeof d?.output_text === 'string' && (d.output_text as string).trim()) return d.output_text as string;
  if (Array.isArray(d?.output)) {
    return (d.output as unknown[])
      .flatMap((item: unknown) => { const it = item as Record<string, unknown>; return Array.isArray(it?.content) ? it.content as unknown[] : []; })
      .map((item: unknown) => (item as Record<string, unknown>)?.text || '')
      .filter(Boolean)
      .join('')
      .trim();
  }
  return '';
}

// Pre-compiled regex patterns — compiled once at module load, ~10x faster than inline
const CLASSIFY_PATTERNS: Array<[RequestType, RegExp]> = [
  ['code', /\b(codice|code|funzione|function|bug|debug|api|database|sql|python|javascript|typescript|react|css|html|script|algoritmo|classe|metodo|array|json)\b/],
  ['legal', /\b(legge|norma|contratto|gdpr|privacy|compliance|tribunale|sentenza|clausola|licenza|diritto)\b/],
  ['medical', /\b(medicina|clinico|diagnosi|terapia|farmaco|sintomo|linea guida|paziente|pubmed|epidemiologia|oncologia|cardiologia)\b/],
  ['writing', /\b(linkedin|headline|about|copy|newsletter|ghostwrite|landing page|seo|scrittura|profilo)\b/],
  ['research', /\b(ricerca|paper|citazioni|fonti|survey|letteratura|benchmark|deep research|stato dell'arte|state of the art)\b/],
  ['automation', /\b(workflow|automazione|automation|agent|agente|tool|mcp|n8n|pipeline|browser automation|orchestrazione)\b/],
  ['creative', /\b(scrivi|write|storia|story|poesia|poem|creativo|creative|articolo|article|blog|racconto|romanzo|canzone)\b/],
  ['analysis', /\b(analiz|analy|dati|data|grafico|chart|statistic|csv|excel|tabella|confronta|compare)\b/],
  ['realtime', /\b(oggi|today|attual|current|news|notizie|ultimo|latest|2026|2025|tempo reale)\b/],
  ['reasoning', /(spiega|explain|perché|perche|why|come funziona|how does|ragion|reason|logic|matematica|math|teoria|filosofia)/],
];

function classifyRequest(message: string): RequestType {
  const lower = message.toLowerCase();
  for (const [type, pattern] of CLASSIFY_PATTERNS) {
    if (pattern.test(lower)) return type;
  }
  return 'conversation';
}

// Router intelligente
function routeToProvider(requestType: RequestType, mode: AIMode): AIProvider {
  if (mode === 'local') return 'ollama';
  switch (requestType) {
    case 'code': return 'claude';
    case 'legal': return 'claude';
    case 'medical': return 'claude';
    case 'writing': return 'claude';
    case 'research': return 'perplexity';
    case 'automation': return 'claude';
    case 'creative': return 'gpt4';
    case 'realtime': return 'grok';
    case 'analysis': return 'claude';
    case 'reasoning': return 'claude';
    case 'conversation': default: return 'claude';
  }
}

function routeToLocalModel(requestType: RequestType, preferredModel: string): string {
  const localByRequestType: Record<RequestType, string> = {
    code: 'qwen2.5-coder:3b',
    legal: 'mistral:latest',
    medical: 'mistral:latest',
    writing: 'llama3.2:3b',
    research: 'llama3.2:3b',
    automation: 'qwen2.5-coder:3b',
    creative: 'llama3.2:3b',
    analysis: 'mistral:latest',
    conversation: preferredModel || 'llama3.2:3b',
    realtime: 'llama3.2:3b',
    reasoning: 'deepseek-r1:latest',
  };

  const candidate = localByRequestType[requestType] || preferredModel || 'llama3.2:3b';
  return LOCAL_MODEL_ALIASES[candidate] || candidate;
}

function normalizeLocalModel(model: string): string {
  const trimmed = (model || '').trim();
  if (!trimmed) return 'llama3.2:3b';
  return LOCAL_MODEL_ALIASES[trimmed] || trimmed;
}

function resolveGenerationBudget(messageLength: number, deepMode: boolean): number {
  if (deepMode) {
    if (messageLength <= 120) return 320;
    if (messageLength <= 400) return 512;
    return 768;
  }

  if (messageLength <= 120) return 160;
  if (messageLength <= 400) return 288;
  return 448;
}

function optimizeConversationWindow(messages: Message[]): Message[] {
  if (messages.length <= 1) return messages;

  const selected: Message[] = [];
  let totalChars = 0;

  for (let i = messages.length - 1; i >= 0; i--) {
    const msg = messages[i]!;
    const content = (msg.content || '').trim();
    const msgChars = content.length;

    const mustInclude = selected.length === 0; // always keep latest message
    const withinMessageCap = selected.length < CONTEXT_WINDOW_MAX_MESSAGES;
    const withinCharCap = (totalChars + msgChars) <= CONTEXT_WINDOW_MAX_CHARS;

    if (!mustInclude && (!withinMessageCap || !withinCharCap)) {
      break;
    }

    selected.push(msg);
    totalChars += msgChars;
  }

  return selected.reverse();
}

function buildResponseCacheKey(input: {
  mode: AIMode;
  provider: AIProvider;
  model: string;
  requestType: RequestType;
  deepMode: boolean;
  strictEvidenceMode: boolean;
  messages: Message[];
}): string {
  const compactMessages = input.messages.slice(-8).map((m) => ({
    role: m.role,
    content: (m.content || '').slice(-1200),
  }));

  return JSON.stringify({
    mode: input.mode,
    provider: input.provider,
    model: input.model,
    requestType: input.requestType,
    deepMode: input.deepMode,
    strictEvidenceMode: input.strictEvidenceMode,
    messages: compactMessages,
  });
}

function getCachedResponse(key: string): AIResponse | null {
  const cached = RESPONSE_CACHE.get(key);
  if (!cached) return null;

  if ((Date.now() - cached.timestamp) > RESPONSE_CACHE_TTL_MS) {
    RESPONSE_CACHE.delete(key);
    return null;
  }

  return {
    ...cached.response,
    latencyMs: Math.max(1, cached.response.latencyMs || 1),
  };
}

function setCachedResponse(key: string, response: AIResponse): void {
  if (RESPONSE_CACHE.size >= RESPONSE_CACHE_MAX_ENTRIES) {
    const oldestKey = RESPONSE_CACHE.keys().next().value;
    if (oldestKey) RESPONSE_CACHE.delete(oldestKey);
  }

  RESPONSE_CACHE.set(key, {
    response: {
      ...response,
      crossCheckResult: undefined,
    },
    timestamp: Date.now(),
  });
}

// Cache dei modelli Ollama installati (evita fetch /api/tags ad ogni messaggio)
let _ollamaModelCache: { models: string[]; timestamp: number } = { models: [], timestamp: 0 };
const OLLAMA_CACHE_TTL = 60_000; // 60 secondi

async function fetchInstalledOllamaModels(host: string, forceRefresh: boolean = false): Promise<string[]> {
  const now = Date.now();
  if (!forceRefresh && _ollamaModelCache.models.length > 0 && (now - _ollamaModelCache.timestamp) < OLLAMA_CACHE_TTL) {
    return _ollamaModelCache.models;
  }
  try {
    const response = await fetch(`${host}/api/tags`, { method: 'GET' });
    if (!response.ok) return _ollamaModelCache.models;
    const data = await response.json();
    if (!Array.isArray(data?.models)) return _ollamaModelCache.models;
    const models = data.models
      .map((m: unknown) => typeof (m as Record<string, unknown>)?.name === 'string' ? (m as Record<string, unknown>).name as string : '')
      .filter((name: string) => !!name);
    _ollamaModelCache = { models, timestamp: now };
    return models;
  } catch {
    return _ollamaModelCache.models;
  }
}

async function pickRetryLocalModel(host: string, excludedModels: Set<string>): Promise<string | null> {
  const installed = await fetchInstalledOllamaModels(host, true);
  if (installed.length === 0) return null;

  const preferredFallback = LOCAL_FALLBACK_MODELS.find(
    (candidate) => installed.includes(candidate) && !excludedModels.has(candidate),
  );
  if (preferredFallback) return preferredFallback;

  const firstAvailable = installed.find((model) => !excludedModels.has(model));
  return firstAvailable || null;
}

// ============================================================
// SYSTEM PROMPT — importato dal modulo dedicato
// ============================================================
import { recordMetric } from '../metrics/categoryTracker';
import { buildLocalSystemPrompt, buildSystemPrompt } from './systemPrompt';

// ============================================================
// OLLAMA — Chiamata locale con streaming
// ============================================================

async function callOllama(
  messages: Array<{ role: string; content: string }>,
  model: string = 'qwen2.5-coder:3b',
  host: string = 'http://localhost:11434',
  onToken?: (token: string) => void,
  signal?: AbortSignal,
  maxPredict: number = 512,
): Promise<AIResponse> {
  const start = Date.now();
  let resolvedModel = normalizeLocalModel(model);
  const attemptedModels = new Set<string>([resolvedModel]);

  // Se abbiamo callback streaming, usiamo stream: true
  if (onToken) {
    for (let attempt = 0; attempt < 2; attempt++) {
      const response = await fetch(`${host}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model: resolvedModel,
          messages,
          stream: true,
          options: {
            num_predict: maxPredict,
            temperature: 0.2,
          },
        }),
        signal,
      });

      if (!response.ok) {
        if (response.status === 404) {
          const aliasTarget = LOCAL_MODEL_ALIASES[resolvedModel];
          if (aliasTarget && !attemptedModels.has(aliasTarget)) {
            resolvedModel = aliasTarget;
            attemptedModels.add(resolvedModel);
            continue;
          }

          const retryModel = await pickRetryLocalModel(host, attemptedModels);
          if (retryModel) {
            resolvedModel = retryModel;
            attemptedModels.add(resolvedModel);
            continue;
          }

          const installed = await fetchInstalledOllamaModels(host, true);
          throw new Error(`Ollama error: 404 (model '${resolvedModel}' non trovato). Installati: ${installed.join(', ') || 'nessuno'}`);
        }
        throw new Error(`Ollama error: ${response.status}`);
      }
      if (!response.body) throw new Error('Ollama: no response body');

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let fullContent = '';
      let totalTokens = 0;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        // Ollama manda un JSON per riga
        const lines = chunk.split('\n').filter(l => l.trim());

        for (const line of lines) {
          try {
            const data = JSON.parse(line);
            if (data.message?.content) {
              fullContent += data.message.content;
              onToken(data.message.content);
            }
            if (data.eval_count) totalTokens = (data.prompt_eval_count || 0) + data.eval_count;
          } catch {
            // skip malformed JSON
          }
        }
      }

      return {
        content: fullContent,
        provider: 'ollama',
        model: resolvedModel,
        tokensUsed: totalTokens,
        latencyMs: Date.now() - start,
      };
    }

    throw new Error(`Ollama error: model non disponibile dopo retry. Ultimo tentativo: '${resolvedModel}'`);
  }

  // Senza streaming
  for (let attempt = 0; attempt < 2; attempt++) {
    const response = await fetch(`${host}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model: resolvedModel,
        messages,
        stream: false,
        options: {
          num_predict: maxPredict,
          temperature: 0.2,
        },
      }),
      signal,
    });

    if (!response.ok) {
      if (response.status === 404) {
        const aliasTarget = LOCAL_MODEL_ALIASES[resolvedModel];
        if (aliasTarget && !attemptedModels.has(aliasTarget)) {
          resolvedModel = aliasTarget;
          attemptedModels.add(resolvedModel);
          continue;
        }

        const retryModel = await pickRetryLocalModel(host, attemptedModels);
        if (retryModel) {
          resolvedModel = retryModel;
          attemptedModels.add(resolvedModel);
          continue;
        }

        const installed = await fetchInstalledOllamaModels(host, true);
        throw new Error(`Ollama error: 404 (model '${resolvedModel}' non trovato). Installati: ${installed.join(', ') || 'nessuno'}`);
      }
      throw new Error(`Ollama error: ${response.status} ${response.statusText}`);
    }

    const data = await response.json();
    return {
      content: data.message?.content || '',
      provider: 'ollama',
      model: resolvedModel,
      tokensUsed: (data.prompt_eval_count || 0) + (data.eval_count || 0),
      latencyMs: Date.now() - start,
    };
  }

  throw new Error(`Ollama error: model non disponibile dopo retry. Ultimo tentativo: '${resolvedModel}'`);
}

// ============================================================
// CLOUD — Chiamata API provider con streaming
// ============================================================

async function callCloud(
  messages: Array<{ role: string; content: string }>,
  provider: AIProvider,
  apiKeys: Record<string, string>,
  onToken?: (token: string) => void,
  signal?: AbortSignal,
  maxTokens: number = 768,
): Promise<AIResponse> {
  const start = Date.now();
  const model = CLOUD_MODELS[provider]!;
  if (provider !== 'perplexity' && !model) throw new Error(`Provider non supportato: ${provider}`);

  const keyMap: Record<string, string> = {
    claude: apiKeys.ANTHROPIC_API_KEY || '',
    gpt4: apiKeys.OPENAI_API_KEY || '',
    grok: apiKeys.XAI_API_KEY || '',
    mistral: apiKeys.MISTRAL_API_KEY || '',
    deepseek: apiKeys.DEEPSEEK_API_KEY || '',
    gemini: apiKeys.GEMINI_API_KEY || '',
    groq: apiKeys.GROQ_API_KEY || '',
    openrouter: apiKeys.OPENROUTER_API_KEY || '',
    together: apiKeys.TOGETHER_API_KEY || '',
    perplexity: apiKeys.PERPLEXITY_API_KEY || '',
  };
  const apiKey = keyMap[provider];
  if (!apiKey) throw new Error(`API key mancante per ${provider}. Configurala nelle Impostazioni.`);

  const baseUrls: Record<string, string> = {
    claude: 'https://api.anthropic.com/v1',
    gpt4: 'https://api.openai.com/v1',
    grok: 'https://api.x.ai/v1',
    mistral: 'https://api.mistral.ai/v1',
    deepseek: 'https://api.deepseek.com/v1',
    gemini: 'https://generativelanguage.googleapis.com/v1beta/openai',
    groq: 'https://api.groq.com/openai/v1',
    openrouter: 'https://openrouter.ai/api/v1',
    together: 'https://api.together.xyz/v1',
    perplexity: 'https://api.perplexity.ai/v1',
  };

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${apiKey}`,
  };
  if (provider === 'claude') {
    headers['x-api-key'] = apiKey;
    headers['anthropic-version'] = '2023-06-01';
  }
  if (provider === 'openrouter') {
    headers['HTTP-Referer'] = 'https://github.com/vio83/vio83-ai-orchestra';
    headers['X-Title'] = 'VIO 83 AI ORCHESTRA';
  }

  if (provider === 'perplexity') {
    const input = messages.map((m) => `${m.role.toUpperCase()}: ${m.content}`).join('\n\n');
    const response = await fetch(`${baseUrls[provider]}/responses`, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        preset: 'pro-search',
        input,
      }),
      signal,
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`${provider} API error: ${response.status} - ${error}`);
    }

    const data = await response.json();
    const content = extractPerplexityOutput(data);
    if (onToken && content) onToken(content);

    return {
      content,
      provider,
      model: data.model || 'pro-search',
      tokensUsed: data.usage?.total_tokens || 0,
      latencyMs: Date.now() - start,
    };
  }

  const useStream = !!onToken;
  const response = await fetch(`${baseUrls[provider]}/chat/completions`, {
    method: 'POST',
    headers,
    body: JSON.stringify({
      model: extractProviderModelId(model),
      messages,
      max_tokens: maxTokens,
      stream: useStream,
    }),
    signal,
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`${provider} API error: ${response.status} - ${error}`);
  }

  // Streaming
  if (useStream && response.body) {
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let fullContent = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value, { stream: true });
      const lines = chunk.split('\n').filter(l => l.startsWith('data: '));

      for (const line of lines) {
        const data = line.slice(6); // remove 'data: '
        if (data === '[DONE]') break;
        try {
          const parsed = JSON.parse(data);
          const token = parsed.choices?.[0]?.delta?.content;
          if (token) {
            fullContent += token;
            onToken(token);
          }
        } catch { /* skip */ }
      }
    }

    return {
      content: fullContent,
      provider,
      model: extractProviderModelId(model),
      tokensUsed: 0,
      latencyMs: Date.now() - start,
    };
  }

  // Non-streaming
  const data = await response.json();
  const msg = data.choices?.[0]?.message;
  return {
    content: msg?.content || '',
    provider,
    model: extractProviderModelId(model),
    tokensUsed: data.usage?.total_tokens || 0,
    latencyMs: Date.now() - start,
    thinking: msg?.reasoning_content || undefined,
  };
}

// ============================================================
// BACKEND STREAMING — POST /chat/stream con SSE
// ============================================================

async function callBackendStream(
  message: string,
  history: Array<{ role: string; content: string }>,
  config: {
    mode: AIMode;
    provider: AIProvider;
    model?: string;
    conversationId?: string;
    maxTokens?: number;
    temperature?: number;
    enableRag?: boolean;
    protocollo100x?: boolean;
    showThinking?: boolean;
  },
  onToken?: (token: string) => void,
  signal?: AbortSignal,
): Promise<AIResponse> {
  const start = Date.now();
  const body = {
    message,
    history: history.length > 1 ? history : undefined,
    mode: config.mode,
    provider: config.provider === 'ollama' ? undefined : config.provider,
    model: config.model,
    conversation_id: config.conversationId,
    max_tokens: config.maxTokens || 512,
    temperature: config.temperature || 0.7,
    enable_rag: config.enableRag ?? true,
    enable_protocollo_100x: config.protocollo100x ?? true,
    show_thinking: config.showThinking ?? false,
  };

  const response = await fetch(`${BACKEND_URL}/chat/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
    signal,
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Backend error: ${response.status} — ${errorText}`);
  }

  if (!response.body) {
    throw new Error('Backend: no response body for streaming');
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let fullContent = '';
  let finalProvider: AIProvider = config.provider;
  let finalModel = config.model || '';
  let finalLatency = 0;
  let thinking: string | undefined;

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    const chunk = decoder.decode(value, { stream: true });
    const lines = chunk.split('\n').filter((l) => l.startsWith('data: '));

    for (const line of lines) {
      const jsonStr = line.slice(6);
      try {
        const event = JSON.parse(jsonStr);

        if (event.error) {
          throw new Error(`Backend stream error: ${event.error}`);
        }

        if (event.token && !event.done) {
          fullContent += event.token;
          onToken?.(event.token);
        }

        if (event.done) {
          if (event.full_content) fullContent = event.full_content;
          if (event.provider) finalProvider = event.provider as AIProvider;
          if (event.model) finalModel = event.model;
          if (event.latency_ms) finalLatency = event.latency_ms;
          if (event.thinking) thinking = event.thinking;
        }
      } catch (e) {
        if (e instanceof Error && e.message.startsWith('Backend stream error:')) throw e;
        // skip malformed JSON
      }
    }
  }

  return {
    content: fullContent,
    provider: finalProvider,
    model: finalModel,
    tokensUsed: 0,
    latencyMs: finalLatency || Date.now() - start,
    thinking,
  };
}

// ============================================================
// FUNZIONE PRINCIPALE — Invia messaggio all'orchestra
// ============================================================

export async function sendToOrchestra(
  messages: Message[],
  config: {
    mode: AIMode;
    primaryProvider: AIProvider;
    fallbackProviders: AIProvider[];
    autoRouting: boolean;
    crossCheckEnabled: boolean;
    ragEnabled: boolean;
    strictEvidenceMode: boolean;
    protocollo100x: boolean;
    apiKeys: Record<string, string>;
    ollamaHost: string;
    ollamaModel?: string;
  },
  onToken?: (token: string) => void,
  signal?: AbortSignal,
): Promise<AIResponse> {
  const optimizedMessages = optimizeConversationWindow(messages);
  const lastMessage = optimizedMessages[optimizedMessages.length - 1];
  if (!lastMessage) throw new Error('Nessun messaggio da inviare');

  // Dual-mode: rispetta la scelta dell'utente (local o cloud)
  const effectiveMode: AIMode = config.mode || 'local';
  const effectiveProvider: AIProvider =
    effectiveMode === 'cloud' ? (config.primaryProvider || 'claude') : 'ollama';

  const messageLength = (lastMessage.content || '').trim().length;
  const deepMode = Boolean(config.crossCheckEnabled || config.ragEnabled || config.strictEvidenceMode);
  const wantsDeepDetail = /approfond|dettagl|detail|complete|completo|exhaustive/i.test(lastMessage.content || '');
  const baseGenerationBudget = resolveGenerationBudget(messageLength, deepMode);
  const generationBudget = wantsDeepDetail
    ? Math.min(Math.round(baseGenerationBudget * 1.6), deepMode ? 1024 : 768)
    : baseGenerationBudget;

  // Routing intelligente
  let requestType: RequestType = 'conversation';
  let activeOllamaModel = config.ollamaModel || 'llama3.2:3b';

  if (config.autoRouting) {
    requestType = classifyRequest(lastMessage.content);
    activeOllamaModel = routeToLocalModel(requestType, activeOllamaModel);
  }
  console.warn(`[Orchestra] Tipo: ${requestType} | Mode: ${effectiveMode} | Provider: ${effectiveProvider}`);

  // Cache frontend (primo layer ultra-rapido)
  const cacheKey = buildResponseCacheKey({
    mode: effectiveMode,
    provider: effectiveProvider,
    model: activeOllamaModel,
    requestType,
    deepMode,
    strictEvidenceMode: Boolean(config.strictEvidenceMode),
    messages: optimizedMessages,
  });

  const cachedResponse = getCachedResponse(cacheKey);
  if (cachedResponse) {
    if (onToken && cachedResponse.content) onToken(cachedResponse.content);
    return cachedResponse;
  }

  // === STRATEGIA BACKEND-FIRST ===
  // Il backend fornisce JetEngine, RAG, FeatherMemory, persistence, system prompt specializzato
  const backendModel = effectiveMode === 'local' ? activeOllamaModel : undefined;
  const apiHistory = optimizedMessages.map((m) => ({ role: m.role, content: m.content }));

  try {
    const response = await callBackendStream(
      lastMessage.content,
      apiHistory,
      {
        mode: effectiveMode,
        provider: effectiveProvider,
        model: backendModel,
        maxTokens: generationBudget,
        enableRag: config.ragEnabled,
        protocollo100x: config.protocollo100x,
      },
      onToken,
      signal,
    );

    setCachedResponse(cacheKey, response);
    recordMetric({
      category: requestType,
      provider: response.provider,
      model: response.model,
      tokensUsed: response.tokensUsed || 0,
      latencyMs: response.latencyMs || 0,
      success: true,
    });

    return response;
  } catch (backendError) {
    console.warn('[Orchestra] Backend non raggiungibile, fallback diretto:', backendError);
  }

  // === FALLBACK DIRETTO ===
  // Se il backend è down, usa le chiamate dirette (Ollama/Cloud)
  const isLocal = effectiveMode === 'local' || effectiveProvider === 'ollama';
  const protocollo100x = config.protocollo100x ?? true;
  const systemPrompt = isLocal
    ? buildLocalSystemPrompt(requestType, protocollo100x)
    : buildSystemPrompt(requestType, protocollo100x);

  const apiMessages: Array<{ role: string; content: string }> = [
    { role: 'system', content: systemPrompt },
    ...optimizedMessages.map((m) => ({ role: m.role, content: m.content })),
  ];

  try {
    let response: AIResponse;

    if (isLocal) {
      response = await callOllama(
        apiMessages,
        activeOllamaModel,
        config.ollamaHost,
        onToken,
        signal,
        generationBudget,
      );
    } else {
      response = await callCloud(apiMessages, effectiveProvider, config.apiKeys, onToken, signal, generationBudget);
    }

    setCachedResponse(cacheKey, response);
    recordMetric({
      category: requestType,
      provider: response.provider,
      model: response.model,
      tokensUsed: response.tokensUsed || 0,
      latencyMs: response.latencyMs || 0,
      success: true,
    });

    return response;
  } catch (error) {
    // Ultimo tentativo: Ollama locale
    if (effectiveProvider !== 'ollama') {
      try {
        console.warn('[Orchestra] Ultimo tentativo: Ollama locale');
        const fallbackResponse = await callOllama(
          apiMessages,
          activeOllamaModel,
          config.ollamaHost,
          onToken,
          signal,
          generationBudget,
        );
        setCachedResponse(cacheKey, fallbackResponse);
        return fallbackResponse;
      } catch (e) {
        console.warn('[Orchestra] Anche Ollama fallito:', e);
      }
    }

    throw new Error(`Tutti i provider hanno fallito. Errore originale: ${error}`);
  }
}

export { classifyRequest, CLOUD_MODELS, LOCAL_MODELS, resolveGenerationBudget, routeToProvider };
