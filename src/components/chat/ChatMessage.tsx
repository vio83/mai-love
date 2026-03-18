// VIO 83 AI ORCHESTRA - Componente Messaggio Chat
import { AlertCircle, Bot, CheckCircle, Clock, User, Zap } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { PrismLight as SyntaxHighlighter } from 'react-syntax-highlighter';
import bash from 'react-syntax-highlighter/dist/esm/languages/prism/bash';
import javascript from 'react-syntax-highlighter/dist/esm/languages/prism/javascript';
import json from 'react-syntax-highlighter/dist/esm/languages/prism/json';
import python from 'react-syntax-highlighter/dist/esm/languages/prism/python';
import typescript from 'react-syntax-highlighter/dist/esm/languages/prism/typescript';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import remarkGfm from 'remark-gfm';
import { useI18n } from '../../hooks/useI18n';
import type { AIProvider, Message } from '../../types';

SyntaxHighlighter.registerLanguage('ts', typescript);
SyntaxHighlighter.registerLanguage('tsx', typescript);
SyntaxHighlighter.registerLanguage('typescript', typescript);
SyntaxHighlighter.registerLanguage('js', javascript);
SyntaxHighlighter.registerLanguage('javascript', javascript);
SyntaxHighlighter.registerLanguage('json', json);
SyntaxHighlighter.registerLanguage('py', python);
SyntaxHighlighter.registerLanguage('python', python);
SyntaxHighlighter.registerLanguage('bash', bash);
SyntaxHighlighter.registerLanguage('sh', bash);

const providerColors: Record<AIProvider, string> = {
  claude: '#D97706',
  gpt4: '#10B981',
  grok: '#3B82F6',
  mistral: '#8B5CF6',
  deepseek: '#EC4899',
  gemini: '#06B6D4',
  groq: '#F97316',
  openrouter: '#A855F7',
  together: '#14B8A6',
  perplexity: '#60A5FA',
  ollama: '#00FF00',
};

const providerNames: Record<AIProvider, string> = {
  claude: 'Claude',
  gpt4: 'OpenAI',
  grok: 'Grok 4',
  mistral: 'Mistral',
  deepseek: 'DeepSeek',
  gemini: 'Gemini 2.5',
  groq: 'Groq',
  openrouter: 'OpenRouter',
  together: 'Together',
  perplexity: 'Perplexity',
  ollama: 'Ollama (Locale)',
};

interface ChatMessageProps {
  message: Message;
}

export default function ChatMessage({ message }: ChatMessageProps) {
  const { t, lang } = useI18n();
  const isUser = message.role === 'user';

  return (
    <div style={{
      display: 'flex',
      gap: '12px',
      padding: '16px 20px',
      backgroundColor: isUser ? 'transparent' : 'var(--vio-bg-secondary)',
      borderBottom: '1px solid var(--vio-bg-tertiary)',
    }}>
      {/* Avatar */}
      <div style={{
        width: '32px',
        height: '32px',
        borderRadius: '50%',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: isUser ? 'var(--vio-bg-tertiary)' : 'rgba(0, 255, 0, 0.1)',
        border: `1px solid ${isUser ? 'var(--vio-border)' : 'var(--vio-green-dim)'}`,
        flexShrink: 0,
      }}>
        {isUser
          ? <User size={16} color="var(--vio-text-secondary)" />
          : <Bot size={16} color="var(--vio-green)" />
        }
      </div>

      {/* Content */}
      <div style={{ flex: 1, minWidth: 0 }}>
        {/* Header: provider badge */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          marginBottom: '6px',
        }}>
          <span style={{
            fontSize: '13px',
            fontWeight: 600,
            color: isUser ? 'var(--vio-text-secondary)' : 'var(--vio-green)',
          }}>
            {isUser ? t('chat.you') : t('chat.orchestra')}
          </span>

          {message.provider && (
            <span style={{
              fontSize: '11px',
              padding: '2px 8px',
              borderRadius: '10px',
              backgroundColor: `${providerColors[message.provider]}20`,
              color: providerColors[message.provider],
              border: `1px solid ${providerColors[message.provider]}40`,
            }}>
              {providerNames[message.provider]}
            </span>
          )}

          {message.verified && (
            <CheckCircle size={14} color="var(--vio-green)" />
          )}

          {message.qualityScore !== undefined && message.qualityScore < 0.7 && (
            <AlertCircle size={14} color="var(--vio-orange)" />
          )}
        </div>

        {/* Message body with Markdown */}
        <div style={{
          fontSize: '14px',
          lineHeight: '1.7',
          color: 'var(--vio-text-primary)',
        }}>
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              code(props) {
                const { children, className, ...rest } = props;
                const match = /language-(\w+)/.exec(className || '');
                const inline = !match;
                return inline ? (
                  <code style={{
                    backgroundColor: 'var(--vio-bg-tertiary)',
                    padding: '2px 6px',
                    borderRadius: '4px',
                    fontSize: '13px',
                    fontFamily: 'var(--vio-font-mono)',
                    color: 'var(--vio-cyan)',
                  }} {...rest}>
                    {children}
                  </code>
                ) : (
                  <SyntaxHighlighter
                    style={vscDarkPlus}
                    language={match[1]}
                    PreTag="div"
                    customStyle={{
                      borderRadius: '8px',
                      margin: '8px 0',
                      fontSize: '13px',
                    }}
                  >
                    {String(children).replace(/\n$/, '')}
                  </SyntaxHighlighter>
                );
              },
            }}
          >
            {message.content}
          </ReactMarkdown>
        </div>

        {message.attachments && message.attachments.length > 0 && (
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginTop: '10px' }}>
            {message.attachments.map((att) => (
              <div
                key={att.id}
                style={{
                  border: '1px solid var(--vio-border)',
                  borderRadius: '8px',
                  padding: '8px 10px',
                  backgroundColor: 'var(--vio-bg-tertiary)',
                  minWidth: '180px',
                  maxWidth: '320px',
                }}
              >
                {att.type.startsWith('image/') && att.dataUrl ? (
                  <img
                    src={att.dataUrl}
                    alt={att.name}
                    style={{ width: '100%', maxHeight: '180px', objectFit: 'cover', borderRadius: '6px', marginBottom: '6px' }}
                  />
                ) : null}
                <div style={{ fontSize: '12px', color: 'var(--vio-text-secondary)', wordBreak: 'break-word' }}>
                  📎 {t('chat.attachment')}: {att.name}
                </div>
                <div style={{ fontSize: '11px', color: 'var(--vio-text-dim)' }}>
                  {att.type || 'file'} • {(att.size / 1024).toFixed(1)} KB
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Footer: timestamp + model info */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          marginTop: '8px',
          fontSize: '11px',
          color: 'var(--vio-text-dim)',
        }}>
          <Clock size={11} />
          {new Date(message.timestamp).toLocaleTimeString(lang === 'en' ? 'en-US' : 'it-IT', { hour: '2-digit', minute: '2-digit' })}

          {message.model && (
            <>
              <span style={{ color: 'var(--vio-border)' }}>•</span>
              <span>{message.model}</span>
            </>
          )}

          {message.latencyMs && message.latencyMs > 0 && (
            <>
              <span style={{ color: 'var(--vio-border)' }}>•</span>
              <Zap size={11} />
              <span>{message.latencyMs < 1000 ? `${message.latencyMs}ms` : `${(message.latencyMs / 1000).toFixed(1)}s`}</span>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
