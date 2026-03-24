// VIO 83 AI ORCHESTRA — Workflow Builder: Pipeline Visuale
import { motion } from 'framer-motion';
import { GitBranch, Play, Plus, RotateCcw, Trash2, GripVertical } from 'lucide-react';
import { useCallback, useRef, useState } from 'react';
import { useI18n } from '../hooks/useI18n';

interface WFNode {
  id: string;
  type: 'trigger' | 'router' | 'model' | 'crosscheck' | 'rag' | 'output';
  label: string;
  x: number;
  y: number;
  color: string;
  icon: string;
}

const DEFAULT_NODES: WFNode[] = [
  { id: 'n1', type: 'trigger', label: 'Input Utente', x: 60, y: 100, color: '#3B82F6', icon: '📥' },
  { id: 'n2', type: 'router', label: 'AI Router', x: 260, y: 100, color: '#8B5CF6', icon: '🎛️' },
  { id: 'n3', type: 'model', label: 'Claude Opus', x: 460, y: 40, color: '#D97706', icon: '🧠' },
  { id: 'n4', type: 'model', label: 'GPT-4o', x: 460, y: 160, color: '#10B981', icon: '🌀' },
  { id: 'n5', type: 'crosscheck', label: 'Cross-Check', x: 660, y: 100, color: '#F59E0B', icon: '✅' },
  { id: 'n6', type: 'output', label: 'Risposta', x: 860, y: 100, color: '#22C55E', icon: '📤' },
];

const DEFAULT_CONNECTIONS: [string, string][] = [
  ['n1', 'n2'], ['n2', 'n3'], ['n2', 'n4'], ['n3', 'n5'], ['n4', 'n5'], ['n5', 'n6'],
];

interface SavedWorkflow {
  id: string;
  name: string;
  desc: string;
  active: boolean;
  runs: number;
  lastRun: string;
  nodes: WFNode[];
  connections: [string, string][];
}

const STORAGE_KEY = 'vio83-workflows';

function loadWorkflows(): SavedWorkflow[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) return JSON.parse(raw) as SavedWorkflow[];
  } catch { /* ignore */ }
  return [
    { id: 'wf-1', name: 'Smart Auto-Route', desc: 'Routing intelligente basato su analisi task', active: true, runs: 0, lastRun: '—', nodes: DEFAULT_NODES, connections: DEFAULT_CONNECTIONS },
    { id: 'wf-2', name: 'Code Review Pipeline', desc: 'Claude + DeepSeek validazione duale codice', active: true, runs: 0, lastRun: '—', nodes: DEFAULT_NODES, connections: DEFAULT_CONNECTIONS },
  ];
}

const NODE_TYPES: { type: WFNode['type']; label: string; icon: string; color: string }[] = [
  { type: 'model', label: 'Modello AI', icon: '🧠', color: '#D97706' },
  { type: 'crosscheck', label: 'Cross-Check', icon: '✅', color: '#F59E0B' },
  { type: 'rag', label: 'RAG', icon: '📚', color: '#06B6D4' },
  { type: 'router', label: 'Router', icon: '🎛️', color: '#8B5CF6' },
  { type: 'output', label: 'Output', icon: '📤', color: '#22C55E' },
];

export default function WorkflowPage() {
  const { t } = useI18n();
  const [workflows, setWorkflows] = useState<SavedWorkflow[]>(loadWorkflows);
  const [activeWfId, setActiveWfId] = useState<string>(() => workflows[0]?.id ?? '');
  const activeWf = workflows.find(w => w.id === activeWfId) ?? workflows[0];
  // Sync nodes when switching workflow — derive from activeWf directly
  const currentNodes = activeWf?.nodes ?? DEFAULT_NODES;
  const [nodes, setNodes] = useState<WFNode[]>(currentNodes);
  const [connections] = useState<[string, string][]>(activeWf?.connections ?? DEFAULT_CONNECTIONS);
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  const [dragging, setDragging] = useState<string | null>(null);
  const dragOffset = useRef({ x: 0, y: 0 });
  const containerRef = useRef<HTMLDivElement>(null);

  const getNode = (id: string) => nodes.find(n => n.id === id);

  const handleMouseDown = (nodeId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    const node = nodes.find(n => n.id === nodeId);
    if (!node || !containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    dragOffset.current = { x: e.clientX - rect.left - node.x, y: e.clientY - rect.top - node.y + 20 };
    setDragging(nodeId);
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!dragging || !containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const newX = Math.max(0, e.clientX - rect.left - dragOffset.current.x);
    const newY = Math.max(0, e.clientY - rect.top - dragOffset.current.y);
    setNodes(prev => prev.map(n => n.id === dragging ? { ...n, x: newX, y: newY } : n));
  };

  const handleMouseUp = () => {
    if (dragging && activeWf) {
      setWorkflows(prev => prev.map(w =>
        w.id === activeWf.id ? { ...w, nodes: nodes.map(n => n.id === dragging ? { ...n } : n) } : w
      ));
    }
    setDragging(null);
  };

  const addNode = useCallback((type: WFNode['type'], label: string, icon: string, color: string) => {
    const newNode: WFNode = {
      id: `n-${Date.now()}`,
      type, label, icon, color,
      x: 200 + Math.random() * 300,
      y: 50 + Math.random() * 120,
    };
    setNodes(prev => [...prev, newNode]);
    if (activeWf) {
      setWorkflows(prev => prev.map(w =>
        w.id === activeWf.id ? { ...w, nodes: [...w.nodes, newNode] } : w
      ));
    }
  }, [activeWf]);

  const removeNode = useCallback((nodeId: string) => {
    setNodes(prev => prev.filter(n => n.id !== nodeId));
    if (activeWf) {
      setWorkflows(prev => prev.map(w =>
        w.id === activeWf.id ? { ...w, nodes: w.nodes.filter(n => n.id !== nodeId) } : w
      ));
    }
    setSelectedNode(null);
  }, [activeWf]);

  const createWorkflow = useCallback(() => {
    const newWf: SavedWorkflow = {
      id: `wf-${Date.now()}`,
      name: `Workflow ${workflows.length + 1}`,
      desc: 'Nuovo workflow personalizzato',
      active: true, runs: 0, lastRun: '—',
      nodes: [
        { id: 'n1', type: 'trigger', label: 'Input', x: 60, y: 100, color: '#3B82F6', icon: '📥' },
        { id: 'n6', type: 'output', label: 'Output', x: 460, y: 100, color: '#22C55E', icon: '📤' },
      ],
      connections: [['n1', 'n6']],
    };
    setWorkflows(prev => [...prev, newWf]);
    setActiveWfId(newWf.id);
    setNodes(newWf.nodes);
  }, [workflows.length]);

  return (
    <div style={{ padding: '28px 32px', overflowY: 'auto', height: '100%' }}>
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
          <div>
            <h1 style={{ fontSize: '26px', fontWeight: 700, color: 'var(--vio-text-primary)', margin: '0 0 4px', letterSpacing: '-0.5px' }}>
              {t('workflowPage.title')}
            </h1>
            <p style={{ color: 'var(--vio-text-dim)', fontSize: '13px', margin: 0 }}>
              {t('workflowPage.subtitle')}
            </p>
          </div>
          <button onClick={createWorkflow} style={{
            background: 'var(--vio-green)', border: 'none', borderRadius: '10px',
            padding: '10px 18px', color: '#000', fontSize: '13px', fontWeight: 600,
            cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px',
          }}>
            <Plus size={16} /> {t('workflowPage.newWorkflow')}
          </button>
        </div>
      </motion.div>

      {/* Add Node Toolbar */}
      <div style={{ display: 'flex', gap: '8px', marginBottom: '16px', flexWrap: 'wrap' }}>
        {NODE_TYPES.map(nt => (
          <button key={nt.type} onClick={() => addNode(nt.type, nt.label, nt.icon, nt.color)}
            title={`Aggiungi ${nt.label}`}
            style={{
              background: 'var(--vio-bg-secondary)', border: '1px solid var(--vio-border)',
              borderRadius: '8px', padding: '6px 12px', cursor: 'pointer',
              color: 'var(--vio-text-secondary)', fontSize: '11px', display: 'flex', alignItems: 'center', gap: '4px',
            }}>
            <span>{nt.icon}</span> + {nt.label}
          </button>
        ))}
        {selectedNode && (
          <button onClick={() => removeNode(selectedNode)}
            title="Rimuovi nodo selezionato"
            style={{
              background: 'rgba(255,50,50,0.1)', border: '1px solid var(--vio-red)',
              borderRadius: '8px', padding: '6px 12px', cursor: 'pointer',
              color: 'var(--vio-red)', fontSize: '11px', display: 'flex', alignItems: 'center', gap: '4px',
            }}>
            <Trash2 size={12} /> Rimuovi nodo
          </button>
        )}
      </div>

      {/* Visual Pipeline — draggable */}
      <motion.div
        ref={containerRef}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        style={{
          background: 'var(--vio-bg-secondary)',
          borderRadius: 'var(--vio-radius-lg)',
          padding: '24px',
          border: '1px solid var(--vio-border)',
          marginBottom: '24px',
          position: 'relative',
          minHeight: '260px',
          overflow: 'hidden',
          cursor: dragging ? 'grabbing' : 'default',
        }}
      >
        {/* Pipeline label */}
        <div style={{
          position: 'absolute', top: '12px', left: '16px', zIndex: 5,
          background: 'var(--vio-bg-tertiary)', padding: '4px 12px', borderRadius: '6px',
        }}>
          <span style={{ color: 'var(--vio-text-dim)', fontSize: '11px' }}>
            <GitBranch size={11} style={{ verticalAlign: 'middle', marginRight: '4px' }} />
            {activeWf?.name ?? 'Pipeline'}
          </span>
        </div>

        {/* Connection lines */}
        <svg width="100%" height="240" style={{ position: 'absolute', top: 0, left: 0, pointerEvents: 'none' }}>
          {connections.map(([fromId, toId], i) => {
            const from = getNode(fromId);
            const to = getNode(toId);
            if (!from || !to) return null;
            return (
              <line key={i}
                x1={from.x + 55} y1={from.y + 28}
                x2={to.x} y2={to.y + 28}
                stroke="var(--vio-green)" strokeWidth={1.5} strokeDasharray="6 3" opacity={0.4}
              />
            );
          })}
        </svg>

        {/* Nodes — draggable */}
        {nodes.map(node => (
          <motion.div
            key={node.id}
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.2 }}
            onClick={() => setSelectedNode(selectedNode === node.id ? null : node.id)}
            onMouseDown={(e) => handleMouseDown(node.id, e)}
            style={{
              position: 'absolute',
              left: node.x,
              top: node.y + 20,
              width: '110px',
              padding: '12px',
              background: selectedNode === node.id ? 'rgba(0,255,0,0.1)' : 'var(--vio-bg-tertiary)',
              border: `2px solid ${selectedNode === node.id ? node.color : 'var(--vio-border)'}`,
              borderRadius: '12px',
              cursor: dragging === node.id ? 'grabbing' : 'grab',
              textAlign: 'center',
              zIndex: dragging === node.id ? 10 : 2,
              transition: dragging === node.id ? 'none' : 'all 0.2s',
              userSelect: 'none',
            }}
          >
            <GripVertical size={10} style={{ position: 'absolute', top: 4, right: 4, color: 'var(--vio-text-dim)', opacity: 0.5 }} />
            <div style={{ fontSize: '22px', marginBottom: '4px' }}>{node.icon}</div>
            <div style={{ color: 'var(--vio-text-primary)', fontSize: '11px', fontWeight: 600 }}>{node.label}</div>
            <div style={{ color: 'var(--vio-text-dim)', fontSize: '9px', marginTop: '2px', textTransform: 'uppercase' }}>{node.type}</div>
          </motion.div>
        ))}
      </motion.div>

      {/* Saved Workflows */}
      <h3 style={{ color: 'var(--vio-text-primary)', fontSize: '16px', fontWeight: 600, marginBottom: '14px' }}>
        {t('workflowPage.savedWorkflows')}
      </h3>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
        {workflows.map((wf, i) => (
          <motion.div
            key={wf.id}
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 + i * 0.05 }}
            onClick={() => {
              setActiveWfId(wf.id);
              setNodes(wf.nodes);
            }}
            style={{
              background: 'var(--vio-bg-secondary)',
              borderRadius: 'var(--vio-radius-lg)',
              padding: '16px 20px',
              border: `1px solid ${wf.id === activeWfId ? 'rgba(0,255,0,0.4)' : wf.active ? 'rgba(0,255,0,0.2)' : 'var(--vio-border)'}`,
              cursor: 'pointer',
              transition: 'all 0.2s',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
              <span style={{ color: 'var(--vio-text-primary)', fontSize: '14px', fontWeight: 600 }}>{wf.name}</span>
              <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
                <span style={{
                  padding: '3px 10px', borderRadius: '6px', fontSize: '10px', fontWeight: 600,
                  background: wf.id === activeWfId ? 'rgba(0,255,0,0.2)' : 'rgba(0,255,0,0.1)',
                  color: 'var(--vio-green)',
                  border: '1px solid var(--vio-green-dim)40',
                }}>
                  {wf.id === activeWfId ? '● Attivo' : t('workflowPage.active')}
                </span>
                <button title="Esegui workflow" style={{
                  background: 'none', border: 'none', cursor: 'pointer', padding: '2px',
                  color: 'var(--vio-green)',
                }}>
                  <Play size={14} />
                </button>
              </div>
            </div>
            <p style={{ color: 'var(--vio-text-dim)', fontSize: '12px', margin: '0 0 8px' }}>{wf.desc}</p>
            <div style={{ display: 'flex', gap: '16px', fontSize: '11px', color: 'var(--vio-text-dim)' }}>
              <span><RotateCcw size={11} style={{ verticalAlign: 'middle', marginRight: '3px' }} />{wf.runs.toLocaleString()} {t('workflowPage.runs')}</span>
              <span>{t('workflowPage.lastRun')} {wf.lastRun}</span>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
