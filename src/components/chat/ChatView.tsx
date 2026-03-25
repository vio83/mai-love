// VIO 83 AI ORCHESTRA - Vista Chat Principale con Streaming
import { Music } from 'lucide-react';
import { useCallback, useEffect, useRef, useState } from 'react';
import { useI18n } from '../../hooks/useI18n';
import { sendToOrchestra } from '../../services/ai/orchestrator';
import { useAppStore } from '../../stores/appStore';
import type { AIProvider, Attachment, Message } from '../../types';
import ChatInput from './ChatInput';
import ChatMessage from './ChatMessage';
import ModelBar from './ModelBar';

export default function ChatView() {
  const { t } = useI18n();
  const conversations = useAppStore((s) => s.conversations);
  const activeConversationId = useAppStore((s) => s.activeConversationId);
  const settings = useAppStore((s) => s.settings);
  const isStreaming = useAppStore((s) => s.isStreaming);
  const createConversation = useAppStore((s) => s.createConversation);
  const addMessage = useAppStore((s) => s.addMessage);
  const setStreaming = useAppStore((s) => s.setStreaming);
  const setAbortController = useAppStore((s) => s.setAbortController);
  const syncConversationId = useAppStore((s) => s.syncConversationId);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const streamBufferRef = useRef('');
  const flushRafRef = useRef<number | null>(null);
  const lastAutoScrollAtRef = useRef(0);
  const [streamingContent, setStreamingContent] = useState('');
  const [streamingProvider, setStreamingProvider] = useState('');
  const [streamingStartedAt, setStreamingStartedAt] = useState<number | null>(null);
  const [elapsedMs, setElapsedMs] = useState(0);
  const activeConversation = conversations.find((c) => c.id === activeConversationId);

  // Auto-scroll
  useEffect(() => {
    if (!messagesEndRef.current) return;

    const now = performance.now();
    if (isStreaming && now - lastAutoScrollAtRef.current < 140) {
      return;
    }

    lastAutoScrollAtRef.current = now;
    messagesEndRef.current.scrollIntoView({ behavior: isStreaming ? 'auto' : 'smooth' });
  }, [activeConversation?.messages, streamingContent, isStreaming]);

  useEffect(() => () => resetStreamBuffer(), []);

  useEffect(() => {
    if (!isStreaming || !streamingStartedAt) {
      setElapsedMs(0);
      return;
    }

    const timer = window.setInterval(() => {
      setElapsedMs(Date.now() - streamingStartedAt);
    }, 500);

    return () => window.clearInterval(timer);
  }, [isStreaming, streamingStartedAt]);

  const formatElapsed = (ms: number) => {
    const totalSeconds = Math.floor(ms / 1000);
    const hours = Math.floor(totalSeconds / 3600);
    const minutes = Math.floor((totalSeconds % 3600) / 60);
    const seconds = totalSeconds % 60;

    if (hours > 0) return `${hours}h ${minutes}m ${seconds}s`;
    if (minutes > 0) return `${minutes}m ${seconds}s`;
    return `${seconds}s`;
  };

  const flushBufferedStream = useCallback(() => {
    if (!streamBufferRef.current) return;
    const chunk = streamBufferRef.current;
    streamBufferRef.current = '';
    setStreamingContent((prev) => prev + chunk);
  }, []);

  const scheduleStreamFlush = useCallback(() => {
    if (flushRafRef.current !== null) return;
    flushRafRef.current = window.requestAnimationFrame(() => {
      flushRafRef.current = null;
      flushBufferedStream();
    });
  }, [flushBufferedStream]);

  const resetStreamBuffer = () => {
    if (flushRafRef.current !== null) {
      window.cancelAnimationFrame(flushRafRef.current);
      flushRafRef.current = null;
    }
    streamBufferRef.current = '';
  };

  const handleSend = useCallback(
    async (content: string, attachments?: Attachment[]) => {
      let convId = activeConversationId;
      if (!convId) {
        convId = createConversation();
      }

      // Aggiungi messaggio utente
      const userMessage: Message = {
        id: crypto.randomUUID(),
        role: 'user',
        content,
        timestamp: Date.now(),
        attachments,
      };
      addMessage(convId, userMessage);

      // Crea AbortController per permettere lo stop
      const controller = new AbortController();
      setAbortController(controller);
      setStreaming(true);
      setStreamingStartedAt(Date.now());
      setStreamingContent('');
      resetStreamBuffer();
      setStreamingProvider('ollama');

      try {
        const apiKeys: Record<string, string> = {};
        settings.apiKeys.forEach((k) => {
          const keyName = {
            claude: 'ANTHROPIC_API_KEY',
            gpt4: 'OPENAI_API_KEY',
            grok: 'XAI_API_KEY',
            mistral: 'MISTRAL_API_KEY',
            deepseek: 'DEEPSEEK_API_KEY',
            gemini: 'GEMINI_API_KEY',
            groq: 'GROQ_API_KEY',
            openrouter: 'OPENROUTER_API_KEY',
            together: 'TOGETHER_API_KEY',
            perplexity: 'PERPLEXITY_API_KEY',
            ollama: '',
          }[k.provider];
          if (keyName) apiKeys[keyName] = k.key;
        });

        const conv = useAppStore.getState().conversations.find((c) => c.id === convId);
        const allMessages = conv?.messages || [userMessage];

        // Streaming callback — aggiorna il testo in tempo reale
        const onToken = (token: string) => {
          if (!token) return;
          streamBufferRef.current += token;
          scheduleStreamFlush();
        };

        const response = await sendToOrchestra(
          allMessages,
          {
            mode: settings.orchestrator.mode,
            primaryProvider: settings.orchestrator.primaryProvider,
            fallbackProviders: settings.orchestrator.fallbackProviders,
            autoRouting: settings.orchestrator.autoRouting,
            crossCheckEnabled: settings.orchestrator.crossCheckEnabled,
            ragEnabled: settings.orchestrator.ragEnabled,
            strictEvidenceMode: settings.orchestrator.strictEvidenceMode,
            protocollo100x: settings.orchestrator.protocollo100x,
            apiKeys,
            ollamaHost: settings.ollamaHost,
            ollamaModel: settings.ollamaModel || 'qwen2.5-coder:3b',
            conversationId: convId,
          },
          onToken,
          controller.signal,
        );

        flushBufferedStream();

        // Sincronizza l'ID conversazione backend → frontend
        if (response.conversationId && convId) {
          syncConversationId(convId, response.conversationId);
          convId = response.conversationId;
        }

        // Aggiungi risposta finale
        const aiMessage: Message = {
          id: crypto.randomUUID(),
          role: 'assistant',
          content: response.content,
          provider: response.provider,
          model: response.model,
          timestamp: Date.now(),
          latencyMs: response.latencyMs,
          tokensUsed: response.tokensUsed,
          thinking: response.thinking,
          verified: response.crossCheckResult?.concordance,
          qualityScore: response.crossCheckResult
            ? response.crossCheckResult.concordance
              ? 1
              : 0.5
            : undefined,
        };
        addMessage(convId, aiMessage);
      } catch (error: unknown) {
        const err = error as { name?: string; message?: string };
        if (err?.name === 'AbortError') {
          const abortedMessage: Message = {
            id: crypto.randomUUID(),
            role: 'assistant',
            content: t('chat.aborted'),
            timestamp: Date.now(),
          };
          addMessage(convId, abortedMessage);
          return;
        }

        const fallbackMessage = err.message || t('chat.errorFallback');

        const errorMessage: Message = {
          id: crypto.randomUUID(),
          role: 'assistant',
          content: `${t('chat.errorTitle', { message: fallbackMessage })}\n\n${t('chat.errorSolutions')}`,
          timestamp: Date.now(),
        };
        addMessage(convId, errorMessage);
      } finally {
        setStreaming(false);
        setAbortController(null);
        setStreamingStartedAt(null);
        setElapsedMs(0);
        setStreamingContent('');
        resetStreamBuffer();
      }
    },
    [
      activeConversationId,
      addMessage,
      createConversation,
      flushBufferedStream,
      scheduleStreamFlush,
      setAbortController,
      setStreaming,
      settings,
      syncConversationId,
      t,
    ],
  );

  // === Welcome Screen ===
  if (!activeConversation || activeConversation.messages.length === 0) {
    return (
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          height: '100%',
          backgroundColor: 'var(--vio-bg-primary)',
        }}
      >
        <ModelBar />
        <div
          style={{
            flex: 1,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '40px',
            gap: '20px',
          }}
        >
          <div
            style={{
              width: '80px',
              height: '80px',
              borderRadius: '50%',
              background: 'linear-gradient(135deg, rgba(0,255,0,0.2), rgba(255,0,255,0.2))',
              border: '2px solid var(--vio-green)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <Music size={36} color="var(--vio-green)" />
          </div>

          <h1
            style={{
              fontSize: '28px',
              fontWeight: 700,
              background: 'linear-gradient(90deg, var(--vio-green), var(--vio-cyan))',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              textAlign: 'center',
            }}
          >
            VIO 83 AI Orchestra
          </h1>

          <p
            style={{
              color: 'var(--vio-text-secondary)',
              fontSize: '14px',
              textAlign: 'center',
              maxWidth: '500px',
              lineHeight: '1.6',
            }}
          >
            {settings.orchestrator.mode === 'cloud'
              ? t('chat.cloudActive', { provider: settings.orchestrator.primaryProvider })
              : t('chat.localActive')}
          </p>

          <div
            style={{
              display: 'flex',
              gap: '12px',
              marginTop: '16px',
              flexWrap: 'wrap',
              justifyContent: 'center',
            }}
          >
            {[
              t('chat.suggestionCode'),
              t('chat.suggestionData'),
              t('chat.suggestionExplain'),
              t('chat.suggestionApi'),
            ].map((suggestion, i) => (
              <button
                key={i}
                onClick={() => handleSend(suggestion)}
                style={{
                  padding: '8px 16px',
                  borderRadius: '20px',
                  border: '1px solid var(--vio-border)',
                  backgroundColor: 'transparent',
                  color: 'var(--vio-text-secondary)',
                  fontSize: '13px',
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor = 'var(--vio-green)';
                  e.currentTarget.style.color = 'var(--vio-green)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderColor = 'var(--vio-border)';
                  e.currentTarget.style.color = 'var(--vio-text-secondary)';
                }}
              >
                {suggestion}
              </button>
            ))}
          </div>
        </div>
        <ChatInput onSend={handleSend} />
      </div>
    );
  }

  // === Chat con messaggi ===
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        backgroundColor: 'var(--vio-bg-primary)',
      }}
    >
      <ModelBar />
      <div style={{ flex: 1, overflowY: 'auto', paddingBottom: '20px' }}>
        {activeConversation.messages.map((msg) => (
          <ChatMessage key={msg.id} message={msg} />
        ))}

        {/* Streaming in tempo reale */}
        {isStreaming && streamingContent && (
          <ChatMessage
            message={{
              id: 'streaming',
              role: 'assistant',
              content: streamingContent,
              provider: streamingProvider as AIProvider,
              timestamp: Date.now(),
            }}
          />
        )}

        {/* Indicatore "sta scrivendo" */}
        {isStreaming && !streamingContent && (
          <div
            style={{
              display: 'flex',
              gap: '12px',
              padding: '16px 20px',
              backgroundColor: 'var(--vio-bg-secondary)',
            }}
          >
            <div
              style={{
                width: '32px',
                height: '32px',
                borderRadius: '50%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                backgroundColor: 'rgba(0,255,0,0.1)',
                border: '1px solid var(--vio-green-dim)',
              }}
            >
              <Music size={16} color="var(--vio-green)" />
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ color: 'var(--vio-green)', fontSize: '13px' }}>
                {t('chat.processing')}
              </span>
              <span style={{ color: 'var(--vio-green)', animation: 'pulse 1.5s infinite' }}>
                ...
              </span>
              <span style={{ color: 'var(--vio-cyan)', fontSize: '12px' }}>
                ⏱ {formatElapsed(elapsedMs)}
              </span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>
      <ChatInput onSend={handleSend} />
    </div>
  );
}
