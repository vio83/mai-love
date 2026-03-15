// VIO 83 AI ORCHESTRA — Workflow Builder: Pipeline Visuale
import { useState } from 'react';
import { motion } from 'framer-motion';
import { Plus, Play, Pause, RotateCcw, GitBranch } from 'lucide-react';

interface WFNode {
  id: string;
  type: 'trigger' | 'router' | 'model' | 'crosscheck' | 'rag' | 'output';
  label: string;
  x: number;
  y: number;
  color: string;
  icon: string;
}

const INITIAL_NODES: WFNode[] = [
  { id: 'n1', type: 'trigger', label: 'Input Utente', x: 60, y: 100, color: '#3B82F6', icon: '📥' },
  { id: 'n2', type: 'router', label: 'AI Router', x: 260, y: 100, color: '#8B5CF6', icon: '🎛️' },
  { id: 'n3', type: 'model', label: 'Claude Opus', x: 460, y: 40, color: '#D97706', icon: '🧠' },
  { id: 'n4', type: 'model', label: 'GPT-4o', x: 460, y: 160, color: '#10B981', icon: '🌀' },
  { id: 'n5', type: 'crosscheck', label: 'Cross-Check', x: 660, y: 100, color: '#F59E0B', icon: '✅' },
  { id: 'n6', type: 'output', label: 'Risposta', x: 860, y: 100, color: '#22C55E', icon: '📤' },
];

const CONNECTIONS: [string, string][] = [
  ['n1', 'n2'], ['n2', 'n3'], ['n2', 'n4'], ['n3', 'n5'], ['n4', 'n5'], ['n5', 'n6'],
];

const savedWorkflows = [
  { id: 1, name: 'Smart Auto-Route', desc: 'Routing intelligente basato su analisi task', active: true, runs: 2341, lastRun: '2 min fa' },
  { id: 2, name: 'Code Review Pipeline', desc: 'Claude + DeepSeek validazione duale codice', active: true, runs: 892, lastRun: '15 min fa' },
  { id: 3, name: 'Research Deep Dive', desc: 'Grok real-time + Claude analisi + RAG verifica', active: false, runs: 456, lastRun: '2 ore fa' },
  { id: 4, name: 'Translation Pro', desc: 'Mistral primario + GPT-4o validazione pipeline', active: true, runs: 1023, lastRun: '8 min fa' },
  { id: 5, name: 'Privacy Local', desc: 'Solo Ollama — zero dati trasmessi', active: true, runs: 567, lastRun: '1 min fa' },
  { id: 6, name: 'Math & Reasoning', desc: 'DeepSeek R1 + Claude cross-check per matematica', active: false, runs: 234, lastRun: '1 giorno fa' },
];

export default function WorkflowPage() {
  const [nodes] = useState(INITIAL_NODES);
  const [selectedNode, setSelectedNode] = useState<string | null>(null);

  const getNode = (id: string) => nodes.find(n => n.id === id);

  return (
    <div style={{ padding: '28px 32px', overflowY: 'auto', height: '100%' }}>
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
          <div>
            <h1 style={{ fontSize: '26px', fontWeight: 700, color: 'var(--vio-text-primary)', margin: '0 0 4px', letterSpacing: '-0.5px' }}>
              Workflow Builder
            </h1>
            <p style={{ color: 'var(--vio-text-dim)', fontSize: '13px', margin: 0 }}>
              Progetta pipeline di orchestrazione multi-AI visualmente
            </p>
          </div>
          <button style={{
            background: 'var(--vio-green)', border: 'none', borderRadius: '10px',
            padding: '10px 18px', color: '#000', fontSize: '13px', fontWeight: 600,
            cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px',
          }}>
            <Plus size={16} /> Nuovo Workflow
          </button>
        </div>
      </motion.div>

      {/* Visual Pipeline */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        style={{
          background: 'var(--vio-bg-secondary)',
          borderRadius: 'var(--vio-radius-lg)',
          padding: '24px',
          border: '1px solid var(--vio-border)',
          marginBottom: '24px',
          position: 'relative',
          minHeight: '260px',
          overflow: 'hidden',
        }}
      >
        {/* Pipeline label */}
        <div style={{
          position: 'absolute', top: '12px', left: '16px', zIndex: 5,
          background: 'var(--vio-bg-tertiary)', padding: '4px 12px', borderRadius: '6px',
        }}>
          <span style={{ color: 'var(--vio-text-dim)', fontSize: '11px' }}>
            <GitBranch size={11} style={{ verticalAlign: 'middle', marginRight: '4px' }} />
            Smart Auto-Route Pipeline
          </span>
        </div>

        {/* Connection lines */}
        <svg width="100%" height="240" style={{ position: 'absolute', top: 0, left: 0, pointerEvents: 'none' }}>
          {CONNECTIONS.map(([fromId, toId], i) => {
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

        {/* Nodes */}
        {nodes.map(node => (
          <motion.div
            key={node.id}
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.2 }}
            onClick={() => setSelectedNode(selectedNode === node.id ? null : node.id)}
            style={{
              position: 'absolute',
              left: node.x,
              top: node.y + 20,
              width: '110px',
              padding: '12px',
              background: selectedNode === node.id ? 'rgba(0,255,0,0.1)' : 'var(--vio-bg-tertiary)',
              border: `2px solid ${selectedNode === node.id ? node.color : 'var(--vio-border)'}`,
              borderRadius: '12px',
              cursor: 'pointer',
              textAlign: 'center',
              zIndex: 2,
              transition: 'all 0.2s',
            }}
          >
            <div style={{ fontSize: '22px', marginBottom: '4px' }}>{node.icon}</div>
            <div style={{ color: 'var(--vio-text-primary)', fontSize: '11px', fontWeight: 600 }}>{node.label}</div>
            <div style={{ color: 'var(--vio-text-dim)', fontSize: '9px', marginTop: '2px', textTransform: 'uppercase' }}>{node.type}</div>
          </motion.div>
        ))}
      </motion.div>

      {/* Saved Workflows */}
      <h3 style={{ color: 'var(--vio-text-primary)', fontSize: '16px', fontWeight: 600, marginBottom: '14px' }}>
        Workflow Salvati
      </h3>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
        {savedWorkflows.map((wf, i) => (
          <motion.div
            key={wf.id}
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 + i * 0.05 }}
            style={{
              background: 'var(--vio-bg-secondary)',
              borderRadius: 'var(--vio-radius-lg)',
              padding: '16px 20px',
              border: `1px solid ${wf.active ? 'rgba(0,255,0,0.2)' : 'var(--vio-border)'}`,
              cursor: 'pointer',
              transition: 'all 0.2s',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
              <span style={{ color: 'var(--vio-text-primary)', fontSize: '14px', fontWeight: 600 }}>{wf.name}</span>
              <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
                <span style={{
                  padding: '3px 10px', borderRadius: '6px', fontSize: '10px', fontWeight: 600,
                  background: wf.active ? 'rgba(0,255,0,0.1)' : 'rgba(255,50,50,0.1)',
                  color: wf.active ? 'var(--vio-green)' : 'var(--vio-red)',
                  border: `1px solid ${wf.active ? 'var(--vio-green-dim)' : 'var(--vio-red)'}40`,
                }}>
                  {wf.active ? 'Attivo' : 'In Pausa'}
                </span>
                <button style={{
                  background: 'none', border: 'none', cursor: 'pointer', padding: '2px',
                  color: wf.active ? 'var(--vio-yellow)' : 'var(--vio-green)',
                }}>
                  {wf.active ? <Pause size={14} /> : <Play size={14} />}
                </button>
              </div>
            </div>
            <p style={{ color: 'var(--vio-text-dim)', fontSize: '12px', margin: '0 0 8px' }}>{wf.desc}</p>
            <div style={{ display: 'flex', gap: '16px', fontSize: '11px', color: 'var(--vio-text-dim)' }}>
              <span><RotateCcw size={11} style={{ verticalAlign: 'middle', marginRight: '3px' }} />{wf.runs.toLocaleString()} esecuzioni</span>
              <span>Ultimo: {wf.lastRun}</span>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
