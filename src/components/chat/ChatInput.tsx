// VIO 83 AI ORCHESTRA - Input Chat con selettore modello, allegati, stop
import { Cloud, Cpu, FileText, HardDrive, Image, Plus, Send, Square, X, Zap } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import { useAppStore } from '../../stores/appStore';
import type { AIProvider, Attachment } from '../../types';

// Modelli Ollama disponibili localmente (su MacBook Air M1 8GB)
const OLLAMA_MODELS = [
  { id: 'llama3.2:3b', name: 'Llama 3.2 3B', desc: 'Più potente — generale', ram: '~2GB' },
  { id: 'qwen2.5-coder:3b', name: 'Qwen Coder 3B', desc: 'Migliore per codice', ram: '~2GB' },
  { id: 'gemma2:2b', name: 'Gemma 2 2B', desc: 'Leggero — rapido', ram: '~1.5GB' },
];

const cloudProviders: { id: AIProvider; name: string; icon: string }[] = [
  { id: 'claude', name: 'Claude', icon: '🟠' },
  { id: 'gpt4', name: 'GPT-4o', icon: '🟢' },
  { id: 'grok', name: 'Grok 3', icon: '🔵' },
  { id: 'gemini', name: 'Gemini', icon: '💎' },
  { id: 'mistral', name: 'Mistral', icon: '🟣' },
  { id: 'deepseek', name: 'DeepSeek', icon: '🩷' },
];

const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10 MB

interface ChatInputProps {
  onSend: (message: string, attachments?: Attachment[]) => void;
  disabled?: boolean;
}

export default function ChatInput({ onSend, disabled }: ChatInputProps) {
  const [input, setInput] = useState('');
  const [attachments, setAttachments] = useState<Attachment[]>([]);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { settings, setMode, setProvider, setOllamaModel, isStreaming, stopStreaming } = useAppStore();
  const { mode, primaryProvider } = settings.orchestrator;
  const currentOllamaModel = settings.ollamaModel || 'llama3.2:3b';

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 200) + 'px';
    }
  }, [input]);

  // Auto-focus textarea quando non sta streamando
  useEffect(() => {
    if (!isStreaming && textareaRef.current) {
      textareaRef.current.focus();
    }
  }, [isStreaming]);

  const canSend = (input.trim() || attachments.length > 0) && !disabled && !isStreaming;

  const handleSend = () => {
    if (!canSend) return;
    const msg = input.trim();
    const atts = attachments.length > 0 ? [...attachments] : undefined;

    // Aggiungi descrizione allegati nel messaggio se non c'è testo
    let content = msg;
    if (!content && atts) {
      content = atts.map(a => `[Allegato: ${a.name}]`).join('\n');
    }

    onSend(content, atts);
    setInput('');
    setAttachments([]);
    if (textareaRef.current) textareaRef.current.style.height = 'auto';
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleStop = () => {
    stopStreaming();
  };

  // File attachment handler
  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files) return;

    Array.from(files).forEach(file => {
      if (file.size > MAX_FILE_SIZE) {
        alert(`File "${file.name}" troppo grande (max 10MB)`);
        return;
      }

      const reader = new FileReader();
      reader.onload = () => {
        const newAttachment: Attachment = {
          id: crypto.randomUUID(),
          name: file.name,
          type: file.type,
          size: file.size,
          dataUrl: reader.result as string,
        };
        setAttachments(prev => [...prev, newAttachment]);
      };
      reader.readAsDataURL(file);
    });

    // Reset input so same file can be added again
    e.target.value = '';
  };

  const removeAttachment = (id: string) => {
    setAttachments(prev => prev.filter(a => a.id !== id));
  };

  // Paste handler (images from clipboard)
  const handlePaste = (e: React.ClipboardEvent) => {
    const items = e.clipboardData?.items;
    if (!items) return;

    for (const item of items) {
      if (item.type.startsWith('image/')) {
        e.preventDefault();
        const file = item.getAsFile();
        if (!file) continue;
        const reader = new FileReader();
        reader.onload = () => {
          const newAttachment: Attachment = {
            id: crypto.randomUUID(),
            name: `clipboard-${Date.now()}.${file.type.split('/')[1] || 'png'}`,
            type: file.type,
            size: file.size,
            dataUrl: reader.result as string,
          };
          setAttachments(prev => [...prev, newAttachment]);
        };
        reader.readAsDataURL(file);
      }
    }
  };

  const getFileIcon = (type: string) => {
    if (type.startsWith('image/')) return <Image size={14} />;
    return <FileText size={14} />;
  };

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes}B`;
    if (bytes < 1048576) return `${(bytes / 1024).toFixed(0)}KB`;
    return `${(bytes / 1048576).toFixed(1)}MB`;
  };

  const currentModelInfo = OLLAMA_MODELS.find(m => m.id === currentOllamaModel);

  return (
    <div style={{
      borderTop: '1px solid var(--vio-border)',
      backgroundColor: 'var(--vio-bg-secondary)',
      padding: '12px 20px',
    }}>
      {/* Mode + Provider/Model selector */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '8px',
        marginBottom: '10px',
        flexWrap: 'wrap',
      }}>
        {/* Cloud / Local toggle */}
        <button
          onClick={() => setMode(mode === 'cloud' ? 'local' : 'cloud')}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            padding: '4px 12px',
            borderRadius: '20px',
            border: `1px solid ${mode === 'cloud' ? 'var(--vio-cyan)' : 'var(--vio-green)'}`,
            backgroundColor: `${mode === 'cloud' ? 'rgba(0,255,255,0.1)' : 'rgba(0,255,0,0.1)'}`,
            color: mode === 'cloud' ? 'var(--vio-cyan)' : 'var(--vio-green)',
            cursor: 'pointer',
            fontSize: '12px',
            fontWeight: 600,
          }}
        >
          {mode === 'cloud' ? <Cloud size={14} /> : <HardDrive size={14} />}
          {mode === 'cloud' ? 'Cloud' : 'Locale'}
        </button>

        {/* === LOCAL MODE: Ollama model selector === */}
        {mode === 'local' && OLLAMA_MODELS.map(model => (
          <button
            key={model.id}
            onClick={() => setOllamaModel(model.id)}
            title={`${model.desc} (${model.ram})`}
            style={{
              padding: '4px 10px',
              borderRadius: '16px',
              border: `1px solid ${currentOllamaModel === model.id ? 'var(--vio-green)' : 'var(--vio-border)'}`,
              backgroundColor: currentOllamaModel === model.id ? 'rgba(0,255,0,0.1)' : 'transparent',
              color: currentOllamaModel === model.id ? 'var(--vio-green)' : 'var(--vio-text-secondary)',
              cursor: 'pointer',
              fontSize: '11px',
              transition: 'all 0.2s',
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
            }}
          >
            <Cpu size={10} />
            {model.name}
          </button>
        ))}

        {mode === 'local' && (
          <span style={{
            display: 'flex',
            alignItems: 'center',
            gap: '4px',
            fontSize: '11px',
            color: 'var(--vio-green-dim)',
            marginLeft: 'auto',
          }}>
            <HardDrive size={11} />
            Ollama {currentModelInfo ? `— ${currentModelInfo.ram}` : ''}
          </span>
        )}

        {/* === CLOUD MODE: Provider buttons === */}
        {mode === 'cloud' && cloudProviders.map(p => (
          <button
            key={p.id}
            onClick={() => setProvider(p.id)}
            style={{
              padding: '4px 10px',
              borderRadius: '16px',
              border: `1px solid ${primaryProvider === p.id ? 'var(--vio-green)' : 'var(--vio-border)'}`,
              backgroundColor: primaryProvider === p.id ? 'rgba(0,255,0,0.1)' : 'transparent',
              color: primaryProvider === p.id ? 'var(--vio-green)' : 'var(--vio-text-secondary)',
              cursor: 'pointer',
              fontSize: '11px',
              transition: 'all 0.2s',
            }}
          >
            {p.icon} {p.name}
          </button>
        ))}

        {/* Auto-routing indicator */}
        {mode === 'cloud' && settings.orchestrator.autoRouting && (
          <span style={{
            display: 'flex',
            alignItems: 'center',
            gap: '4px',
            fontSize: '11px',
            color: 'var(--vio-magenta)',
            marginLeft: 'auto',
          }}>
            <Zap size={12} /> Auto-routing attivo
          </span>
        )}
      </div>

      {/* Attachments preview */}
      {attachments.length > 0 && (
        <div style={{
          display: 'flex',
          gap: '8px',
          marginBottom: '10px',
          flexWrap: 'wrap',
        }}>
          {attachments.map(att => (
            <div key={att.id} style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '4px 10px',
              borderRadius: '8px',
              border: '1px solid var(--vio-border)',
              backgroundColor: 'var(--vio-bg-tertiary)',
              fontSize: '12px',
              color: 'var(--vio-text-secondary)',
            }}>
              {att.type.startsWith('image/') && att.dataUrl ? (
                <img src={att.dataUrl} alt={att.name} style={{ width: 24, height: 24, objectFit: 'cover', borderRadius: 3 }} />
              ) : getFileIcon(att.type)}
              <span style={{ maxWidth: '120px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {att.name}
              </span>
              <span style={{ color: 'var(--vio-text-dim)', fontSize: '10px' }}>{formatSize(att.size)}</span>
              <button
                onClick={() => removeAttachment(att.id)}
                style={{
                  background: 'none', border: 'none', cursor: 'pointer', padding: 0,
                  color: 'var(--vio-text-dim)', display: 'flex',
                }}
              >
                <X size={14} />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        multiple
        style={{ display: 'none' }}
        onChange={handleFileSelect}
        accept="image/*,video/*,audio/*,.pdf,.doc,.docx,.txt,.md,.py,.js,.ts,.tsx,.jsx,.json,.csv,.html,.css,.yaml,.yml,.xml,.sql,.sh,.rs,.go,.java,.c,.cpp,.h,.swift,.kt,.rb,.php,.r,.m,.log,.env,.toml,.ini,.cfg"
      />

      {/* Input area */}
      <div style={{
        display: 'flex',
        gap: '8px',
        alignItems: 'flex-end',
      }}>
        {/* (+) Attach file button */}
        <button
          onClick={() => fileInputRef.current?.click()}
          disabled={isStreaming}
          title="Allega file (foto, video, documenti, codice...)"
          style={{
            width: '42px',
            height: '42px',
            borderRadius: 'var(--vio-radius)',
            border: '1px solid var(--vio-border)',
            backgroundColor: 'var(--vio-bg-tertiary)',
            color: isStreaming ? 'var(--vio-text-dim)' : 'var(--vio-text-secondary)',
            cursor: isStreaming ? 'default' : 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            transition: 'all 0.2s',
            flexShrink: 0,
          }}
          onMouseEnter={e => { if (!isStreaming) e.currentTarget.style.borderColor = 'var(--vio-green)'; }}
          onMouseLeave={e => { e.currentTarget.style.borderColor = 'var(--vio-border)'; }}
        >
          <Plus size={20} />
        </button>

        <textarea
          ref={textareaRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          onPaste={handlePaste}
          placeholder={mode === 'local'
            ? `Scrivi un messaggio... (${currentModelInfo?.name || 'Ollama'})`
            : `Scrivi un messaggio... (${cloudProviders.find(p => p.id === primaryProvider)?.name || 'Cloud'})`
          }
          disabled={disabled}
          rows={1}
          style={{
            flex: 1,
            resize: 'none',
            padding: '10px 16px',
            borderRadius: 'var(--vio-radius)',
            border: '1px solid var(--vio-border)',
            backgroundColor: 'var(--vio-bg-primary)',
            color: 'var(--vio-text-primary)',
            fontSize: '14px',
            fontFamily: 'var(--vio-font-sans)',
            lineHeight: '1.5',
            outline: 'none',
            transition: 'border-color 0.2s',
            maxHeight: '200px',
            opacity: isStreaming ? 0.6 : 1,
          }}
          onFocus={(e) => e.target.style.borderColor = 'var(--vio-green)'}
          onBlur={(e) => e.target.style.borderColor = 'var(--vio-border)'}
        />

        {/* Send OR Stop button */}
        {isStreaming ? (
          <button
            onClick={handleStop}
            title="Ferma generazione"
            style={{
              width: '42px',
              height: '42px',
              borderRadius: 'var(--vio-radius)',
              border: 'none',
              backgroundColor: '#ef4444',
              color: '#fff',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              transition: 'all 0.2s',
              flexShrink: 0,
              animation: 'pulse 1.5s infinite',
            }}
          >
            <Square size={16} fill="#fff" />
          </button>
        ) : (
          <button
            onClick={handleSend}
            disabled={!canSend}
            title="Invia messaggio"
            style={{
              width: '42px',
              height: '42px',
              borderRadius: 'var(--vio-radius)',
              border: 'none',
              backgroundColor: canSend ? 'var(--vio-green)' : 'var(--vio-bg-tertiary)',
              color: canSend ? '#000' : 'var(--vio-text-dim)',
              cursor: canSend ? 'pointer' : 'default',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              transition: 'all 0.2s',
              flexShrink: 0,
            }}
          >
            <Send size={18} />
          </button>
        )}
      </div>
    </div>
  );
}
