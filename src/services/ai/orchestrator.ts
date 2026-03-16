// VIO 83 AI ORCHESTRA - AI Orchestrator Service
// Il cuore dell'app: gestisce routing, fallback, cross-check e streaming

import type { AIMode, AIProvider, AIResponse, Message } from '../../types';

// Model mapping per cloud providers
const CLOUD_MODELS: Record<string, string> = {
  claude: 'anthropic/claude-sonnet-4-6',
  gpt4: 'openai/gpt-5.4',
  grok: 'xai/grok-4',
  mistral: 'mistral/mistral-large-latest',
  deepseek: 'deepseek/deepseek-chat',
  gemini: 'google/gemini-2.5-pro',
  groq: 'groq/openai/gpt-oss-120b',
  openrouter: 'openrouter/meta-llama/llama-3.3-70b-instruct:free',
  together: 'together/meta-llama/Llama-3.3-70B-Instruct-Turbo',
};

const LOCAL_MODELS: Record<string, string> = {
  'qwen-coder': 'qwen2.5-coder:3b',
  'llama3': 'llama3.2:3b',
  'mistral': 'mistral:7b',
  'phi3': 'phi3:3.8b',
  'deepseek-coder': 'deepseek-coder-v2:lite',
};

// Classificazione tipo richiesta per routing intelligente
type RequestType = 'code' | 'legal' | 'medical' | 'writing' | 'research' | 'automation' | 'creative' | 'analysis' | 'conversation' | 'realtime' | 'reasoning';

function extractProviderModelId(modelString: string): string {
  const parts = modelString.split('/');
  return parts.length > 1 ? parts.slice(1).join('/') : modelString;
}

function extractPerplexityOutput(data: any): string {
  if (typeof data?.output_text === 'string' && data.output_text.trim()) return data.output_text;
  if (Array.isArray(data?.output)) {
    return data.output
      .flatMap((item: any) => Array.isArray(item?.content) ? item.content : [])
      .map((item: any) => item?.text || '')
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
    legal: 'mistral:7b',
    medical: 'mistral:7b',
    writing: 'llama3.2:3b',
    research: 'llama3.2:3b',
    automation: 'qwen2.5-coder:3b',
    creative: 'llama3.2:3b',
    analysis: 'mistral:7b',
    conversation: preferredModel || 'llama3.2:3b',
    realtime: 'llama3.2:3b',
    reasoning: 'phi3:3.8b',
  };

  return localByRequestType[requestType] || preferredModel || 'llama3.2:3b';
}

function pickLocalVerifierModel(primaryModel: string): string {
  const candidates = ['qwen2.5-coder:3b', 'llama3.2:3b', 'mistral:7b', 'phi3:3.8b'];
  return candidates.find((candidate) => candidate !== primaryModel) || 'llama3.2:3b';
}

async function fetchLocalRagContext(question: string): Promise<{ contextText: string; sourceCount: number }> {
  const cleanQuestion = question.trim();
  if (!cleanQuestion) return { contextText: '', sourceCount: 0 };

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 1800);

  try {
    const query = new URLSearchParams({
      question: cleanQuestion,
      max_context_tokens: '1200',
      n_results: '5',
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
import { buildSystemPrompt } from './systemPrompt';

// ============================================================
// OLLAMA — Chiamata locale con streaming
// ============================================================

async function callOllama(
  messages: Array<{ role: string; content: string }>,
  model: string = 'qwen2.5-coder:3b',
  host: string = 'http://localhost:11434',
  onToken?: (token: string) => void,
): Promise<AIResponse> {
  const start = Date.now();

  // Se abbiamo callback streaming, usiamo stream: true
  if (onToken) {
    const response = await fetch(`${host}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ model, messages, stream: true }),
    });

    if (!response.ok) throw new Error(`Ollama error: ${response.status}`);
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
        } catch { /* skip malformed JSON */ }
      }
    }

    return {
      content: fullContent,
      provider: 'ollama',
      model,
      tokensUsed: totalTokens,
      latencyMs: Date.now() - start,
    };
  }

  // Senza streaming
  const response = await fetch(`${host}/api/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ model, messages, stream: false }),
  });

  if (!response.ok) throw new Error(`Ollama error: ${response.status} ${response.statusText}`);
  const data = await response.json();

  return {
    content: data.message?.content || '',
    provider: 'ollama',
    model,
    tokensUsed: (data.prompt_eval_count || 0) + (data.eval_count || 0),
    latencyMs: Date.now() - start,
  };
}

// ============================================================
// CLOUD — Chiamata API provider con streaming
// ============================================================

async function callCloud(
  messages: Array<{ role: string; content: string }>,
  provider: AIProvider,
  apiKeys: Record<string, string>,
  onToken?: (token: string) => void,
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
      max_tokens: 4096,
      stream: useStream,
    }),
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
): Promise<AIResponse> {
  const lastMessage = messages[messages.length - 1];
  if (!lastMessage) throw new Error('Nessun messaggio da inviare');

  // Controlla se ci sono API keys configurate
  const hasAnyApiKey = Object.values(config.apiKeys).some(k => k && k.trim().length > 0);

  // Se siamo in cloud mode ma non ci sono API keys, forza Ollama
  const effectiveMode: AIMode = (config.mode === 'cloud' && !hasAnyApiKey) ? 'local' : config.mode;
  const effectiveProvider: AIProvider = effectiveMode === 'local' ? 'ollama' : config.primaryProvider;

  if (effectiveMode !== config.mode) {
    console.log(`[Orchestra] Nessuna API key trovata — fallback automatico a Ollama locale`);
  }

  // Routing intelligente — classifica PRIMA di costruire il prompt
  let provider = effectiveProvider;
  let requestType: RequestType = 'conversation';
  let activeOllamaModel = config.ollamaModel || 'llama3.2:3b';

  if (config.autoRouting) {
    requestType = classifyRequest(lastMessage.content);
    if (effectiveMode === 'cloud') {
      provider = routeToProvider(requestType, effectiveMode);
    } else {
      activeOllamaModel = routeToLocalModel(requestType, activeOllamaModel);
    }
  }
  console.log(`[Orchestra] Tipo: ${requestType} | Mode: ${effectiveMode} | Provider: ${provider}`);

  // Prepara messaggi con system prompt SPECIALIZZATO per tipo di richiesta
  let systemPrompt = buildSystemPrompt(requestType);
  const strictEvidenceMode = Boolean(config.strictEvidenceMode);
  let ragContext: { contextText: string; sourceCount: number } = { contextText: '', sourceCount: 0 };

  if (config.ragEnabled) {
    ragContext = await fetchLocalRagContext(lastMessage.content);
  }

  if (strictEvidenceMode) {
    if (!config.ragEnabled) {
      return {
        content:
          '⚠️ **Fallback esplicito (Strict Evidence Mode)**\n\n' +
          'La modalità evidenza rigorosa è attiva, ma RAG è disattivato. ' +
          'Per policy non posso fornire una risposta non supportata da fonti certificate.\n\n' +
          'Abilita RAG e riprova, oppure disattiva la modalità "strict evidence" se vuoi una risposta generativa standard.',
        provider: effectiveMode === 'local' ? 'ollama' : provider,
        model: effectiveMode === 'local' ? activeOllamaModel : (CLOUD_MODELS[provider] ? extractProviderModelId(CLOUD_MODELS[provider]) : provider),
        tokensUsed: 0,
        latencyMs: 0,
      };
    }

    if (!ragContext.contextText || ragContext.sourceCount === 0) {
      return {
        content:
          '⚠️ **Fallback esplicito (Strict Evidence Mode)**\n\n' +
          'Non ho trovato evidenze certificate sufficienti nelle fonti RAG locali per rispondere in modo verificabile.\n\n' +
          'Per rispettare la policy di affidabilità, interrompo la generazione libera e ti invito a:\n' +
          '1) aggiungere fonti certificate nella Knowledge Base;\n' +
          '2) rifare la domanda con maggiore specificità (paese, data, norma, disciplina).',
        provider: effectiveMode === 'local' ? 'ollama' : provider,
        model: effectiveMode === 'local' ? activeOllamaModel : (CLOUD_MODELS[provider] ? extractProviderModelId(CLOUD_MODELS[provider]) : provider),
        tokensUsed: 0,
        latencyMs: 0,
      };
    }

    systemPrompt +=
      '\n\n=== STRICT EVIDENCE POLICY ATTIVA ===\n' +
      '- Rispondi SOLO con elementi supportati dal contesto certificato fornito.\n' +
      '- Se il contesto non copre un punto, dichiaralo esplicitamente come non verificato.\n' +
      '- Evita inferenze non supportate e segnala sempre i limiti delle fonti disponibili.\n' +
      '=== FINE POLICY ===';
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
      );
    } else {
      response = await callCloud(apiMessages, provider, config.apiKeys, onToken);
    }

    // Cross-check opzionale
    if (config.crossCheckEnabled) {
      if (effectiveMode === 'cloud' && config.fallbackProviders.length > 0) {
        try {
          const checkProvider = config.fallbackProviders[0];
          const checkResponse = await callCloud(
            [
              ...apiMessages,
              { role: 'assistant', content: response.content },
              { role: 'user', content: 'Verifica se la risposta precedente è accurata. Rispondi solo con "CONFERMATO" se corretta, o spiega brevemente gli errori.' },
            ],
            checkProvider,
            config.apiKeys,
          );
          response.crossCheckResult = {
            concordance: checkResponse.content.includes('CONFERMATO'),
            secondProvider: checkProvider,
            secondResponse: checkResponse.content,
          };
        } catch (e) {
          console.warn('[Orchestra] Cross-check cloud fallito:', e);
        }
      }

      if (effectiveMode === 'local') {
        try {
          const verifierModel = pickLocalVerifierModel(activeOllamaModel);
          const checkResponse = await callOllama(
            [
              ...apiMessages,
              { role: 'assistant', content: response.content },
              {
                role: 'user',
                content: 'Verifica la risposta precedente. Rispondi con "CONFERMATO" se è accurata. Altrimenti rispondi con "CORREZIONE:" seguito da una nota breve.',
              },
            ],
            verifierModel,
            config.ollamaHost,
          );

          const normalized = checkResponse.content.trim().toUpperCase();
          const concordance = normalized.startsWith('CONFERMATO') || normalized.startsWith('CONFIRMED');

          response.crossCheckResult = {
            concordance,
            secondProvider: 'ollama',
            secondResponse: `[${verifierModel}] ${checkResponse.content}`,
          };
        } catch (e) {
          console.warn('[Orchestra] Cross-check locale fallito:', e);
        }
      }
    }

    return response;
  } catch (error) {
    // Fallback — prova sempre Ollama come ultimo tentativo
    console.warn(`[Orchestra] ${provider} fallito, tentativo fallback...`);

    // Prima prova i fallback configurati
    for (const fallback of config.fallbackProviders) {
      try {
        if (fallback === 'ollama') {
          return await callOllama(apiMessages, activeOllamaModel, config.ollamaHost, onToken);
        }
        // Solo se abbiamo API keys per questo provider
        if (hasAnyApiKey) {
          return await callCloud(apiMessages, fallback, config.apiKeys, onToken);
        }
      } catch (e) {
        console.warn(`[Orchestra] Fallback ${fallback} fallito:`, e);
      }
    }

    // Ultimo tentativo: Ollama sempre (se non già provato)
    if (provider !== 'ollama') {
      try {
        console.log('[Orchestra] Ultimo tentativo: Ollama locale');
        return await callOllama(apiMessages, activeOllamaModel, config.ollamaHost, onToken);
      } catch (e) {
        console.warn('[Orchestra] Anche Ollama fallito:', e);
      }
    }

    throw new Error(`Tutti i provider hanno fallito. Errore originale: ${error}`);
  }
}

export { classifyRequest, CLOUD_MODELS, LOCAL_MODELS, routeToProvider };
