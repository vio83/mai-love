// VIO 83 AI ORCHESTRA - Artifacts Viewer
// Renders HTML/SVG/Mermaid/React artifacts inline (like Claude Artifacts)
import { Check, Code2, Copy, FileCode, Maximize2, Minimize2, X } from 'lucide-react';
import { memo, useCallback, useMemo, useState } from 'react';

// ─── Artifact Detection ───

export type ArtifactType = 'html' | 'svg' | 'mermaid' | 'csv' | 'json' | 'react';

interface DetectedArtifact {
  type: ArtifactType;
  content: string;
  title?: string;
  language: string;
}

/**
 * Scansiona il contenuto di un messaggio AI cercando blocchi artifact
 * (code fences con linguaggi specifici che hanno contenuto renderizzabile).
 */
export function detectArtifacts(text: string): DetectedArtifact[] {
  const artifacts: DetectedArtifact[] = [];
  // Match ```lang\n...content...\n```
  const codeBlockRegex = /```(\w+)\s*\n([\s\S]*?)```/g;
  let match: RegExpExecArray | null;
  while ((match = codeBlockRegex.exec(text)) !== null) {
    const lang = (match[1] ?? '').toLowerCase();
    const content = (match[2] ?? '').trim();
    if (lang === 'html' && content.length > 30) {
      artifacts.push({
        type: 'html',
        content,
        language: lang,
        title: extractTitle(content, 'html'),
      });
    } else if (lang === 'svg' && content.includes('<svg')) {
      artifacts.push({ type: 'svg', content, language: lang, title: 'SVG Image' });
    } else if (lang === 'mermaid') {
      artifacts.push({ type: 'mermaid', content, language: lang, title: 'Mermaid Diagram' });
    } else if (lang === 'csv' && content.includes(',')) {
      artifacts.push({ type: 'csv', content, language: lang, title: 'CSV Data' });
    } else if (lang === 'json' && content.length > 50) {
      artifacts.push({ type: 'json', content, language: lang, title: 'JSON Data' });
    } else if ((lang === 'jsx' || lang === 'tsx') && content.includes('return')) {
      artifacts.push({ type: 'react', content, language: lang, title: 'React Component' });
    }
  }
  return artifacts;
}

function extractTitle(html: string, type: string): string {
  if (type === 'html') {
    const titleMatch = /<title>(.*?)<\/title>/i.exec(html);
    if (titleMatch) return titleMatch[1] ?? 'Artifact';
    const h1Match = /<h1[^>]*>(.*?)<\/h1>/i.exec(html);
    if (h1Match) return (h1Match[1] ?? '').replace(/<[^>]*>/g, '');
  }
  return 'Artifact';
}

// ─── Artifact Renderers ───

function HtmlArtifactRenderer({ content }: { content: string }) {
  // Sanitize: wrap in sandboxed iframe with srcdoc
  const safeHtml = useMemo(() => {
    // Add base styling if missing
    if (!content.includes('<html') && !content.includes('<!DOCTYPE')) {
      return `<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
body { font-family: system-ui, sans-serif; margin: 16px; color: #e0e0e0; background: #1a1a2e; }
a { color: #64b5f6; }
table { border-collapse: collapse; width: 100%; }
th, td { border: 1px solid #444; padding: 8px; text-align: left; }
th { background: #2a2a4a; }
</style></head><body>${content}</body></html>`;
    }
    return content;
  }, [content]);

  return (
    <iframe
      srcDoc={safeHtml}
      sandbox="allow-scripts"
      style={{
        width: '100%',
        minHeight: '300px',
        border: 'none',
        borderRadius: '6px',
        background: '#1a1a2e',
      }}
      title="HTML Artifact"
    />
  );
}

function SvgArtifactRenderer({ content }: { content: string }) {
  return (
    <div
      style={{
        padding: '16px',
        background: '#1a1a2e',
        borderRadius: '6px',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        overflow: 'auto',
      }}
      dangerouslySetInnerHTML={{ __html: content }}
    />
  );
}

function CsvArtifactRenderer({ content }: { content: string }) {
  const rows = useMemo(() => {
    return content
      .split('\n')
      .filter((l) => l.trim())
      .map((line) => line.split(',').map((c) => c.trim()));
  }, [content]);

  if (rows.length === 0) return null;
  const headers = rows[0] ?? [];
  const data = rows.slice(1);

  return (
    <div style={{ overflow: 'auto', maxHeight: '400px' }}>
      <table
        style={{
          width: '100%',
          borderCollapse: 'collapse',
          fontSize: '13px',
          color: 'var(--vio-text-primary)',
        }}
      >
        <thead>
          <tr>
            {headers.map((h, i) => (
              <th
                key={i}
                style={{
                  padding: '8px 10px',
                  background: 'var(--vio-bg-tertiary)',
                  borderBottom: '2px solid var(--vio-cyan)',
                  textAlign: 'left',
                  fontWeight: 600,
                }}
              >
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((row, ri) => (
            <tr key={ri}>
              {row.map((cell, ci) => (
                <td
                  key={ci}
                  style={{
                    padding: '6px 10px',
                    borderBottom: '1px solid var(--vio-border)',
                  }}
                >
                  {cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function JsonArtifactRenderer({ content }: { content: string }) {
  const formatted = useMemo(() => {
    try {
      return JSON.stringify(JSON.parse(content), null, 2);
    } catch {
      return content;
    }
  }, [content]);

  return (
    <pre
      style={{
        background: '#1e1e2e',
        color: '#e0e0e0',
        padding: '12px',
        borderRadius: '6px',
        fontSize: '13px',
        overflow: 'auto',
        maxHeight: '400px',
        margin: 0,
      }}
    >
      {formatted}
    </pre>
  );
}

// ─── Main ArtifactViewer Component ───

interface ArtifactViewerProps {
  artifact: DetectedArtifact;
  index: number;
}

function ArtifactViewerInner({ artifact, index }: ArtifactViewerProps) {
  const [expanded, setExpanded] = useState(false);
  const [showSource, setShowSource] = useState(false);
  const [copied, setCopied] = useState(false);

  const handleCopy = useCallback(() => {
    navigator.clipboard.writeText(artifact.content).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }, [artifact.content]);

  const typeLabels: Record<ArtifactType, string> = {
    html: 'HTML',
    svg: 'SVG',
    mermaid: 'Mermaid',
    csv: 'Tabella CSV',
    json: 'JSON',
    react: 'React Component',
  };

  const typeColors: Record<ArtifactType, string> = {
    html: '#e44d26',
    svg: '#ffb13b',
    mermaid: '#ff3670',
    csv: '#10b981',
    json: '#60a5fa',
    react: '#61dafb',
  };

  return (
    <div
      style={{
        border: '1px solid var(--vio-border)',
        borderRadius: '12px',
        marginTop: '12px',
        overflow: 'hidden',
        background: 'var(--vio-bg-secondary)',
        maxWidth: expanded ? '100%' : '100%',
        position: expanded ? 'fixed' : 'relative',
        top: expanded ? '2%' : undefined,
        left: expanded ? '2%' : undefined,
        right: expanded ? '2%' : undefined,
        bottom: expanded ? '2%' : undefined,
        zIndex: expanded ? 1000 : undefined,
        boxShadow: expanded ? '0 25px 50px -12px rgba(0, 0, 0, 0.5)' : undefined,
      }}
    >
      {/* Header */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          padding: '8px 12px',
          background: 'var(--vio-bg-tertiary)',
          borderBottom: '1px solid var(--vio-border)',
        }}
      >
        <FileCode size={14} color={typeColors[artifact.type]} />
        <span
          style={{
            fontSize: '11px',
            fontWeight: 600,
            color: typeColors[artifact.type],
            textTransform: 'uppercase',
            letterSpacing: '0.5px',
          }}
        >
          {typeLabels[artifact.type]}
        </span>
        <span style={{ fontSize: '12px', color: 'var(--vio-text-secondary)', flex: 1 }}>
          {artifact.title || `Artifact #${index + 1}`}
        </span>

        {/* Actions */}
        <button
          onClick={() => setShowSource(!showSource)}
          style={{
            background: 'none',
            border: 'none',
            cursor: 'pointer',
            padding: '4px',
            color: showSource ? 'var(--vio-cyan)' : 'var(--vio-text-dim)',
            borderRadius: '4px',
          }}
          title={showSource ? 'Mostra anteprima' : 'Mostra codice sorgente'}
        >
          <Code2 size={14} />
        </button>
        <button
          onClick={handleCopy}
          style={{
            background: 'none',
            border: 'none',
            cursor: 'pointer',
            padding: '4px',
            color: copied ? 'var(--vio-green)' : 'var(--vio-text-dim)',
            borderRadius: '4px',
          }}
          title="Copia codice"
        >
          {copied ? <Check size={14} /> : <Copy size={14} />}
        </button>
        <button
          onClick={() => setExpanded(!expanded)}
          style={{
            background: 'none',
            border: 'none',
            cursor: 'pointer',
            padding: '4px',
            color: 'var(--vio-text-dim)',
            borderRadius: '4px',
          }}
          title={expanded ? 'Riduci' : 'Espandi'}
        >
          {expanded ? <Minimize2 size={14} /> : <Maximize2 size={14} />}
        </button>
        {expanded && (
          <button
            onClick={() => setExpanded(false)}
            style={{
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              padding: '4px',
              color: 'var(--vio-text-dim)',
              borderRadius: '4px',
            }}
            title="Chiudi"
          >
            <X size={14} />
          </button>
        )}
      </div>

      {/* Content */}
      <div
        style={{
          padding: showSource ? '0' : '0',
          overflow: 'auto',
          maxHeight: expanded ? 'calc(100vh - 120px)' : '500px',
        }}
      >
        {showSource ? (
          <pre
            style={{
              background: '#1e1e2e',
              color: '#e0e0e0',
              padding: '12px',
              fontSize: '13px',
              margin: 0,
              overflow: 'auto',
            }}
          >
            {artifact.content}
          </pre>
        ) : (
          <div style={{ padding: artifact.type === 'html' ? '0' : '0' }}>
            {artifact.type === 'html' && <HtmlArtifactRenderer content={artifact.content} />}
            {artifact.type === 'svg' && <SvgArtifactRenderer content={artifact.content} />}
            {artifact.type === 'csv' && <CsvArtifactRenderer content={artifact.content} />}
            {artifact.type === 'json' && <JsonArtifactRenderer content={artifact.content} />}
            {artifact.type === 'mermaid' && (
              <div
                style={{ padding: '16px', color: 'var(--vio-text-secondary)', fontSize: '13px' }}
              >
                <Code2 size={16} style={{ marginRight: '6px' }} />
                Mermaid diagram detected — rendering richiede libreria mermaid.js
                <pre style={{ marginTop: '8px', fontSize: '12px', opacity: 0.8 }}>
                  {artifact.content}
                </pre>
              </div>
            )}
            {artifact.type === 'react' && (
              <div
                style={{ padding: '16px', color: 'var(--vio-text-secondary)', fontSize: '13px' }}
              >
                <Code2 size={16} style={{ marginRight: '6px' }} />
                React component detected — anteprima live in sviluppo
                <pre style={{ marginTop: '8px', fontSize: '12px', opacity: 0.8 }}>
                  {artifact.content}
                </pre>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export const ArtifactViewer = memo(ArtifactViewerInner);
export default ArtifactViewer;
