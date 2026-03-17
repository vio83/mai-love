// VIO 83 AI ORCHESTRA - AI Orchestrator Service
// Il cuore dell'app: gestisce routing, fallback, cross-check e streaming

import type { AIMode, AIProvider, AIResponse, Message } from '../../types';

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

function classifyRequest(message: string): RequestType {
  const lower = message.toLowerCase();
  if (/\b(codice|code|funzione|function|bug|debug|api|database|sql|python|javascript|typescript|react|css|html|script|algoritmo|classe|metodo|array|json)\b/.test(lower)) return 'code';
  if (/\b(legge|norma|contratto|gdpr|privacy|compliance|tribunale|sentenza|clausola|licenza|diritto)\b/.test(lower)) return 'legal';
  if (/\b(medicina|clinico|diagnosi|terapia|farmaco|sintomo|linea guida|paziente|pubmed|epidemiologia|oncologia|cardiologia)\b/.test(lower)) return 'medical';
  if (/\b(linkedin|headline|about|copy|newsletter|ghostwrite|landing page|seo|scrittura|profilo)\b/.test(lower)) return 'writing';
  if (/\b(ricerca|paper|citazioni|fonti|survey|letteratura|benchmark|deep research|stato dell'arte|state of the art)\b/.test(lower)) return 'research';
  if (/\b(workflow|automazione|automation|agent|agente|tool|mcp|n8n|pipeline|browser automation|orchestrazione)\b/.test(lower)) return 'automation';
  if (/\b(scrivi|write|storia|story|poesia|poem|creativo|creative|articolo|article|blog|racconto|romanzo|canzone)\b/.test(lower)) return 'creative';
  if (/\b(analiz|analy|dati|data|grafico|chart|statistic|csv|excel|tabella|confronta|compare)\b/.test(lower)) return 'analysis';
  if (/\b(oggi|today|attual|current|news|notizie|ultimo|latest|2026|2025|tempo reale)\b/.test(lower)) return 'realtime';
  if (/\b(spiega|explain|perch[eé]|why|come funziona|how does|ragion|reason|logic|matematica|math|teoria|filosofia)\b/.test(lower)) return 'reasoning';
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

function pickLocalVerifierModel(primaryModel: string): string {
  const candidates = ['qwen2.5-coder:3b', 'llama3.2:3b', 'mistral:latest', 'deepseek-r1:latest'];
  return candidates.find((candidate) => candidate !== primaryModel) || 'llama3.2:3b';
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

async function resolveWorkingLocalModel(host: string, preferredModel: string): Promise<string> {
  const preferred = normalizeLocalModel(preferredModel);
  const installed = await fetchInstalledOllamaModels(host);

  if (installed.length === 0) {
    return preferred;
  }

  if (installed.includes(preferred)) {
    return preferred;
  }

  const aliasTarget = LOCAL_MODEL_ALIASES[preferredModel];
  if (aliasTarget && installed.includes(aliasTarget)) {
    return aliasTarget;
  }

  const fallback = LOCAL_FALLBACK_MODELS.find((candidate) => installed.includes(candidate));
  return fallback || installed[0] || preferred;
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

async function fetchLocalRagContext(question: string): Promise<{ contextText: string; sourceCount: number }> {
  const cleanQuestion = question.trim();
  if (!cleanQuestion) return { contextText: '', sourceCount: 0 };

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 800); // 800ms max, was 1800

  try {
    const query = new URLSearchParams({
      question: cleanQuestion,
      max_context_tokens: '600', // ridotto da 1200 per velocità
      n_results: '3', // ridotto da 5
    }).toString();

    const response = await fetch(`http://localhost:4000/kb/context?${query}`, {
      method: 'POST',
      signal: controller.signal,
    });

    if (!response.ok) {
      return { contextText: '', sourceCount: 0 };
    }

    const data = await response.json();
    const contextText = typeof data?.context_text === 'string' ? data.context_text.trim() : '';
    const sourceCount = Array.isArray(data?.sources) ? data.sources.length : 0;

    if (!contextText) {
      return { contextText: '', sourceCount };
    }

    return { contextText, sourceCount };
  } catch {
    return { contextText: '', sourceCount: 0 };
  } finally {
    clearTimeout(timeoutId);
  }
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
  let resolvedModel = await resolveWorkingLocalModel(host, model);
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
  const model = CLOUD_MODELS[provider];
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
  return {
    content: data.choices?.[0]?.message?.content || '',
    provider,
    model: extractProviderModelId(model),
    tokensUsed: data.usage?.total_tokens || 0,
    latencyMs: Date.now() - start,
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
    apiKeys: Record<string, string>;
    ollamaHost: string;
    ollamaModel?: string;
  },
  onToken?: (token: string) => void,
  signal?: AbortSignal,
): Promise<AIResponse> {
  const lastMessage = messages[messages.length - 1];
  if (!lastMessage) throw new Error('Nessun messaggio da inviare');

  // Dual-mode: rispetta la scelta dell'utente (local o cloud)
  const effectiveMode: AIMode = config.mode || 'local';
  const effectiveProvider: AIProvider =
    effectiveMode === 'cloud' ? (config.primaryProvider || 'claude') : 'ollama';

  if (effectiveMode === 'cloud') {
    console.log(`[Orchestra] Cloud mode: provider=${effectiveProvider}`);
  }

  const messageLength = (lastMessage.content || '').trim().length;
  const deepMode = Boolean(config.crossCheckEnabled || config.ragEnabled || config.strictEvidenceMode);
  const generationBudget = resolveGenerationBudget(messageLength, deepMode);

  // Routing intelligente — classifica PRIMA di costruire il prompt
  const provider = effectiveProvider;
  let requestType: RequestType = 'conversation';
  let activeOllamaModel = config.ollamaModel || 'llama3.2:3b';

  if (config.autoRouting) {
    requestType = classifyRequest(lastMessage.content);
    activeOllamaModel = routeToLocalModel(requestType, activeOllamaModel);
  }
  console.log(`[Orchestra] Tipo: ${requestType} | Mode: ${effectiveMode} | Provider: ${provider}`);

  // Prepara messaggi con system prompt SPECIALIZZATO per tipo di richiesta
  // Per modelli locali < 7B usa prompt compatto (~400 token vs ~4000)
  const isLocal = effectiveMode === 'local' || provider === 'ollama';
  let systemPrompt = isLocal ? buildLocalSystemPrompt(requestType) : buildSystemPrompt(requestType);
  const strictEvidenceMode = Boolean(config.strictEvidenceMode);
  let strictEvidenceDegraded = false;
  let strictEvidenceBanner = '';
  let ragContext: { contextText: string; sourceCount: number } = { contextText: '', sourceCount: 0 };

  if (config.ragEnabled) {
    ragContext = await fetchLocalRagContext(lastMessage.content);
  }

  if (strictEvidenceMode) {
    if (!config.ragEnabled) {
      strictEvidenceDegraded = true;
      strictEvidenceBanner =
        '⚠️ **Strict Evidence degradato (continuità operativa attiva)**\n\n' +
        'RAG è disattivato: procedo comunque con risposta best-effort per evitare blocchi. ' +
        'I dettagli non verificabili verranno segnalati esplicitamente.';

      systemPrompt +=
        '\n\n=== STRICT EVIDENCE DEGRADATO (RAG OFF) ===\n' +
        '- Mantieni massima accuratezza possibile con conoscenza generale consolidata.\n' +
        '- Etichetta chiaramente ciò che NON può essere verificato in questa sessione.\n' +
        '- Non inventare fonti, date o citazioni.\n' +
        '- Produci comunque una risposta completa e utile (mai bloccare output).\n' +
        '=== FINE POLICY ===';
    }

    if (!strictEvidenceDegraded && (!ragContext.contextText || ragContext.sourceCount === 0)) {
      strictEvidenceDegraded = true;
      strictEvidenceBanner =
        '⚠️ **Strict Evidence degradato (nessuna fonte locale sufficiente)**\n\n' +
        'Non ho trovato evidenze certificate sufficienti nella KB locale: procedo comunque per continuità operativa, ' +
        'segnalando esplicitamente i limiti di verificabilità.';

      systemPrompt +=
        '\n\n=== STRICT EVIDENCE DEGRADATO (KB INSUFFICIENTE) ===\n' +
        '- Fornisci risposta completa, strutturata e prudente.\n' +
        '- Distingui chiaramente: fatti consolidati vs dettagli non verificati localmente.\n' +
        '- Evidenzia limiti e aree dove servirebbero fonti aggiuntive.\n' +
        '- Non interrompere mai la risposta con messaggi di blocco.\n' +
        '=== FINE POLICY ===';
    }

    if (!strictEvidenceDegraded) {
      systemPrompt +=
        '\n\n=== STRICT EVIDENCE POLICY ATTIVA ===\n' +
        '- Rispondi SOLO con elementi supportati dal contesto certificato fornito.\n' +
        '- Se il contesto non copre un punto, dichiaralo esplicitamente come non verificato.\n' +
        '- Evita inferenze non supportate e segnala sempre i limiti delle fonti disponibili.\n' +
        '=== FINE POLICY ===';
    }
  }

  if (config.ragEnabled && ragContext.contextText) {
    systemPrompt +=
      `\n\n=== CONTESTO RAG LOCALE CERTIFICATO ===\n` +
      `Fonti recuperate: ${ragContext.sourceCount}\n` +
      `Usa le fonti seguenti per migliorare accuratezza e verificabilità della risposta:\n\n` +
      `${ragContext.contextText}\n` +
      `=== FINE CONTESTO ===`;
  }

  const apiMessages: Array<{ role: string; content: string }> = [
    { role: 'system', content: systemPrompt },
    ...messages.map(m => ({ role: m.role, content: m.content })),
  ];

  // Tenta provider principale
  try {
    let response: AIResponse;

    if (effectiveMode === 'local' || provider === 'ollama') {
      response = await callOllama(
        apiMessages,
        activeOllamaModel,
        config.ollamaHost,
        onToken,
        signal,
        generationBudget,
      );
    } else {
      response = await callCloud(apiMessages, provider, config.apiKeys, onToken, signal, generationBudget);
    }

    if (strictEvidenceDegraded && strictEvidenceBanner) {
      response.content = `${strictEvidenceBanner}\n\n${response.content}`;
    }

    // Track metrics per category
    recordMetric({
      category: requestType,
      provider: response.provider,
      model: response.model,
      tokensUsed: response.tokensUsed || 0,
      latencyMs: response.latencyMs || 0,
      success: true,
    });

    // Cross-check opzionale
    if (config.crossCheckEnabled) {
      // Fire-and-forget: cross-check locale NON blocca la risposta all'utente
      // Il risultato verrà aggiunto in background (M1 8GB troppo lento per doppia inference sincrona)
      const verifierModel = pickLocalVerifierModel(activeOllamaModel);
      const crossCheckMessages = [
        ...apiMessages,
        { role: 'assistant', content: response.content },
        {
          role: 'user',
          content: 'Verifica la risposta precedente. Rispondi con "CONFERMATO" se è accurata. Altrimenti rispondi con "CORREZIONE:" seguito da una nota breve.',
        },
      ];
      callOllama(crossCheckMessages, verifierModel, config.ollamaHost, undefined, undefined, 160)
        .then(checkResponse => {
          const normalized = checkResponse.content.trim().toUpperCase();
          const concordance = normalized.startsWith('CONFERMATO') || normalized.startsWith('CONFIRMED');
          response.crossCheckResult = {
            concordance,
            secondProvider: 'ollama',
            secondResponse: `[${verifierModel}] ${checkResponse.content}`,
          };
        })
        .catch(e => {
          console.warn('[Orchestra] Cross-check locale fallito:', e);
        });
    }

    return response;
  } catch (error) {
    // Fallback — prova sempre Ollama come ultimo tentativo
    console.warn(`[Orchestra] ${provider} fallito, tentativo fallback...`);

    // Prima prova i fallback configurati
    for (const fallback of config.fallbackProviders) {
      try {
        if (fallback !== 'ollama') continue;

        const fallbackResponse = await callOllama(apiMessages, activeOllamaModel, config.ollamaHost, onToken, signal, generationBudget);
        if (strictEvidenceDegraded && strictEvidenceBanner) {
          fallbackResponse.content = `${strictEvidenceBanner}\n\n${fallbackResponse.content}`;
        }
        return fallbackResponse;
      } catch (e) {
        console.warn(`[Orchestra] Fallback ${fallback} fallito:`, e);
      }
    }

    // Ultimo tentativo: Ollama sempre (se non già provato)
    if (provider !== 'ollama') {
      try {
        console.log('[Orchestra] Ultimo tentativo: Ollama locale');
        const fallbackResponse = await callOllama(apiMessages, activeOllamaModel, config.ollamaHost, onToken, signal, generationBudget);
        if (strictEvidenceDegraded && strictEvidenceBanner) {
          fallbackResponse.content = `${strictEvidenceBanner}\n\n${fallbackResponse.content}`;
        }
        return fallbackResponse;
      } catch (e) {
        console.warn('[Orchestra] Anche Ollama fallito:', e);
      }
    }

    throw new Error(`Tutti i modelli locali Ollama hanno fallito. Errore originale: ${error}`);
  }
}

export { classifyRequest, CLOUD_MODELS, LOCAL_MODELS, resolveGenerationBudget, routeToProvider };
