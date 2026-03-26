// VIO 83 AI ORCHESTRA - Sidebar con Navigazione Multi-Pagina
import { useEffect, useState } from 'react';
import {
  Archive,
  BarChart3,
  BookOpen,
  Check,
  CheckCircle2,
  ChevronLeft,
  CircleAlert,
  Cpu,
  GitBranch,
  LayoutDashboard, MessageSquare,
  MessageSquarePlus,
  Music,
  Orbit,
  Pencil,
  Puzzle,
  Scale,
  Settings,
  Shield,
  Smartphone,
  Trash2,
  X,
  Zap
} from 'lucide-react';
import { useI18n } from '../../hooks/useI18n';
import { useAppStore } from '../../stores/appStore';
import type { AppPage } from '../../types';

const NAV_ITEMS: { id: AppPage; labelKey: string; icon: typeof LayoutDashboard }[] = [
  { id: 'dashboard', labelKey: 'nav.dashboard', icon: LayoutDashboard },
  { id: 'chat', labelKey: 'nav.chat', icon: MessageSquare },
  { id: 'workflow', labelKey: 'nav.workflow', icon: GitBranch },
  { id: 'crosscheck', labelKey: 'nav.crosscheck', icon: Shield },
  { id: 'analytics', labelKey: 'nav.analytics', icon: BarChart3 },
  { id: 'rag', labelKey: 'nav.rag', icon: BookOpen },
  { id: 'models', labelKey: 'nav.models', icon: Cpu },
  { id: 'runtime', labelKey: 'nav.runtime', icon: Orbit },
  { id: 'privacy', labelKey: 'nav.privacy', icon: Scale },
  { id: 'plugins', labelKey: 'nav.plugins', icon: Puzzle },
  { id: 'openclaw', labelKey: 'nav.openclaw', icon: Zap },
  { id: 'mobile', labelKey: 'nav.mobile', icon: Smartphone },
];

export default function Sidebar() {
  const { t } = useI18n();
  const conversations = useAppStore(s => s.conversations);
  const activeConversationId = useAppStore(s => s.activeConversationId);
  const currentPage = useAppStore(s => s.currentPage);
  const sidebarOpen = useAppStore(s => s.sidebarOpen);
  const createConversation = useAppStore(s => s.createConversation);
  const setActiveConversation = useAppStore(s => s.setActiveConversation);
  const deleteConversation = useAppStore(s => s.deleteConversation);
  const archiveConversation = useAppStore(s => s.archiveConversation);
  const renameConversation = useAppStore(s => s.renameConversation);
  const toggleSidebar = useAppStore(s => s.toggleSidebar);
  const setCurrentPage = useAppStore(s => s.setCurrentPage);
  const [editingConversationId, setEditingConversationId] = useState<string | null>(null);
  const [draftTitle, setDraftTitle] = useState('');
  const [busyConversationId, setBusyConversationId] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<{ kind: 'success' | 'error'; message: string } | null>(null);

  useEffect(() => {
    if (!feedback) return;
    const id = window.setTimeout(() => setFeedback(null), 2600);
    return () => window.clearTimeout(id);
  }, [feedback]);

  const startRenaming = (conversationId: string, title: string) => {
    setEditingConversationId(conversationId);
    setDraftTitle(title);
  };

  const cancelRenaming = () => {
    setEditingConversationId(null);
    setDraftTitle('');
  };

  const submitRename = async (conversationId: string) => {
    const normalized = draftTitle.trim();
    if (!normalized) {
      setFeedback({ kind: 'error', message: 'Titolo conversazione obbligatorio.' });
      return;
    }

    setBusyConversationId(conversationId);
    try {
      await renameConversation(conversationId, normalized);
      setEditingConversationId(null);
      setDraftTitle('');
      setFeedback({ kind: 'success', message: 'Titolo conversazione aggiornato.' });
    } catch (error) {
      setFeedback({
        kind: 'error',
        message: error instanceof Error ? error.message : 'Rinomina conversazione fallita.',
      });
    } finally {
      setBusyConversationId(null);
    }
  };

  const handleArchive = async (conversationId: string) => {
    setBusyConversationId(conversationId);
    try {
      await archiveConversation(conversationId);
      setFeedback({ kind: 'success', message: 'Conversazione archiviata.' });
    } catch (error) {
      setFeedback({
        kind: 'error',
        message: error instanceof Error ? error.message : 'Archiviazione conversazione fallita.',
      });
    } finally {
      setBusyConversationId(null);
    }
  };

  const handleDelete = async (conversationId: string) => {
    setBusyConversationId(conversationId);
    try {
      await deleteConversation(conversationId);
      setFeedback({ kind: 'success', message: 'Conversazione eliminata.' });
    } catch (error) {
      setFeedback({
        kind: 'error',
        message: error instanceof Error ? error.message : 'Eliminazione conversazione fallita.',
      });
    } finally {
      setBusyConversationId(null);
    }
  };

  if (!sidebarOpen) return null;

  return (
    <div style={{
      width: '260px',
      height: '100%',
      backgroundColor: 'var(--vio-bg-secondary)',
      borderRight: '1px solid var(--vio-border)',
      display: 'flex',
      flexDirection: 'column',
      flexShrink: 0,
    }}>
      {/* Header */}
      <div style={{
        padding: '16px',
        borderBottom: '1px solid var(--vio-border)',
        display: 'flex',
        alignItems: 'center',
        gap: '10px',
      }}>
        <Music size={20} color="var(--vio-green)" />
        <span style={{
          fontSize: '15px',
          fontWeight: 700,
          color: 'var(--vio-green)',
          flex: 1,
        }}>
          VIO 83
        </span>
        <button
          onClick={toggleSidebar}
          style={{
            background: 'none', border: 'none', cursor: 'pointer',
            color: 'var(--vio-text-dim)', padding: '4px',
          }}
        >
          <ChevronLeft size={16} />
        </button>
      </div>

      {feedback && (
        <div
          role="alert"
          style={{
            margin: '8px',
            padding: '10px 12px',
            borderRadius: '10px',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            fontSize: '12px',
            fontWeight: 600,
            border: feedback.kind === 'success'
              ? '1px solid rgba(0,255,0,0.35)'
              : '1px solid rgba(255,60,60,0.35)',
            background: feedback.kind === 'success'
              ? 'rgba(0,255,0,0.10)'
              : 'rgba(255,60,60,0.10)',
            color: feedback.kind === 'success' ? 'var(--vio-green)' : 'var(--vio-red)',
          }}
        >
          {feedback.kind === 'success' ? <CheckCircle2 size={14} /> : <CircleAlert size={14} />}
          <span>{feedback.message}</span>
        </div>
      )}

      {/* Navigation */}
      <nav style={{ padding: '10px 8px', borderBottom: '1px solid var(--vio-border)' }}>
        {NAV_ITEMS.map(item => {
          const isActive = currentPage === item.id;
          const Icon = item.icon;
          return (
            <button
              key={item.id}
              onClick={() => setCurrentPage(item.id)}
              style={{
                width: '100%',
                display: 'flex',
                alignItems: 'center',
                gap: '10px',
                padding: '8px 12px',
                borderRadius: '6px',
                border: 'none',
                cursor: 'pointer',
                marginBottom: '1px',
                background: isActive ? 'rgba(0,255,0,0.08)' : 'transparent',
                color: isActive ? 'var(--vio-green)' : 'var(--vio-text-secondary)',
                fontSize: '13px',
                fontWeight: isActive ? 600 : 400,
                transition: 'all 0.15s',
                textAlign: 'left',
              }}
              onMouseEnter={e => {
                if (!isActive) e.currentTarget.style.background = 'var(--vio-bg-hover)';
              }}
              onMouseLeave={e => {
                if (!isActive) e.currentTarget.style.background = 'transparent';
              }}
            >
              <Icon size={16} />
              {t(item.labelKey)}
            </button>
          );
        })}
      </nav>

      {/* Conversations (only visible on chat page) */}
      {currentPage === 'chat' && (
        <>
          {/* New chat button */}
          <div style={{ padding: '10px 8px' }}>
            <button
              onClick={() => createConversation()}
              style={{
                width: '100%',
                padding: '8px',
                borderRadius: 'var(--vio-radius)',
                border: '1px dashed var(--vio-green-dim)',
                backgroundColor: 'transparent',
                color: 'var(--vio-green)',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '6px',
                fontSize: '12px',
                fontWeight: 500,
                transition: 'all 0.2s',
              }}
              onMouseEnter={(e) => e.currentTarget.style.backgroundColor = 'rgba(0,255,0,0.05)'}
              onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
            >
              <MessageSquarePlus size={14} />
              {t('sidebar.newConversation')}
            </button>
          </div>

          {/* Conversation list */}
          <div style={{
            flex: 1,
            overflowY: 'auto',
            padding: '0 8px',
          }}>
            {conversations.length === 0 ? (
              <p style={{
                color: 'var(--vio-text-dim)',
                fontSize: '12px',
                textAlign: 'center',
                padding: '16px',
              }}>
                {t('sidebar.noConversations')}
              </p>
            ) : (
              conversations.map(conv => (
                <div
                  key={conv.id}
                  onClick={() => setActiveConversation(conv.id)}
                  style={{
                    padding: '8px 10px',
                    borderRadius: '6px',
                    marginBottom: '2px',
                    cursor: 'pointer',
                    backgroundColor: conv.id === activeConversationId ? 'rgba(0,255,0,0.08)' : 'transparent',
                    border: conv.id === activeConversationId ? '1px solid rgba(0,255,0,0.2)' : '1px solid transparent',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    transition: 'all 0.15s',
                  }}
                  onMouseEnter={(e) => {
                    if (conv.id !== activeConversationId)
                      e.currentTarget.style.backgroundColor = 'var(--vio-bg-hover)';
                  }}
                  onMouseLeave={(e) => {
                    if (conv.id !== activeConversationId)
                      e.currentTarget.style.backgroundColor = 'transparent';
                  }}
                >
                  {editingConversationId === conv.id ? (
                    <div
                      onClick={(e) => e.stopPropagation()}
                      style={{ display: 'flex', alignItems: 'center', gap: '6px', flex: 1 }}
                    >
                      <input
                        autoFocus
                        value={draftTitle}
                        onChange={(e) => setDraftTitle(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') void submitRename(conv.id);
                          if (e.key === 'Escape') cancelRenaming();
                        }}
                        style={{
                          flex: 1,
                          minWidth: 0,
                          fontSize: '12px',
                          borderRadius: '6px',
                          border: '1px solid rgba(0,255,0,0.25)',
                          background: 'var(--vio-bg-tertiary)',
                          color: 'var(--vio-text-primary)',
                          padding: '5px 6px',
                        }}
                      />
                      <button
                        onClick={() => void submitRename(conv.id)}
                        disabled={busyConversationId === conv.id}
                        style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--vio-green)', padding: '2px' }}
                      >
                        <Check size={12} />
                      </button>
                      <button
                        onClick={cancelRenaming}
                        disabled={busyConversationId === conv.id}
                        style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--vio-text-dim)', padding: '2px' }}
                      >
                        <X size={12} />
                      </button>
                    </div>
                  ) : (
                    <>
                      <span style={{
                        flex: 1,
                        fontSize: '12px',
                        color: conv.id === activeConversationId ? 'var(--vio-green)' : 'var(--vio-text-secondary)',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap',
                      }}>
                        {conv.title}
                      </span>
                      <button
                        onClick={(e) => { e.stopPropagation(); startRenaming(conv.id, conv.title); }}
                        disabled={busyConversationId === conv.id}
                        style={{
                          background: 'none', border: 'none', cursor: 'pointer',
                          color: 'var(--vio-text-dim)', padding: '2px', opacity: 0.45, transition: 'opacity 0.2s',
                        }}
                        onMouseEnter={(e) => e.currentTarget.style.opacity = '1'}
                        onMouseLeave={(e) => e.currentTarget.style.opacity = '0.45'}
                      >
                        <Pencil size={12} />
                      </button>
                      <button
                        onClick={(e) => { e.stopPropagation(); void handleArchive(conv.id); }}
                        disabled={busyConversationId === conv.id}
                        style={{
                          background: 'none', border: 'none', cursor: 'pointer',
                          color: 'var(--vio-text-dim)', padding: '2px', opacity: 0.45, transition: 'opacity 0.2s',
                        }}
                        onMouseEnter={(e) => e.currentTarget.style.opacity = '1'}
                        onMouseLeave={(e) => e.currentTarget.style.opacity = '0.45'}
                      >
                        <Archive size={12} />
                      </button>
                      <button
                        onClick={(e) => { e.stopPropagation(); void handleDelete(conv.id); }}
                        disabled={busyConversationId === conv.id}
                        style={{
                          background: 'none', border: 'none', cursor: 'pointer',
                          color: 'var(--vio-text-dim)', padding: '2px', opacity: 0.45, transition: 'opacity 0.2s',
                        }}
                        onMouseEnter={(e) => e.currentTarget.style.opacity = '1'}
                        onMouseLeave={(e) => e.currentTarget.style.opacity = '0.45'}
                      >
                        <Trash2 size={12} />
                      </button>
                    </>
                  )}
                </div>
              ))
            )}
          </div>
        </>
      )}

      {/* Spacer if not chat page */}
      {currentPage !== 'chat' && <div style={{ flex: 1 }} />}

      {/* Footer: Settings */}
      <div style={{
        padding: '10px 8px',
        borderTop: '1px solid var(--vio-border)',
      }}>
        <button
          onClick={() => setCurrentPage('settings')}
          style={{
            width: '100%',
            padding: '8px',
            borderRadius: '6px',
            border: 'none',
            backgroundColor: currentPage === 'settings' ? 'rgba(0,255,0,0.08)' : 'var(--vio-bg-tertiary)',
            color: currentPage === 'settings' ? 'var(--vio-green)' : 'var(--vio-text-secondary)',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '8px',
            fontSize: '13px',
            transition: 'all 0.2s',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.backgroundColor = 'var(--vio-bg-hover)';
            e.currentTarget.style.color = 'var(--vio-green)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.backgroundColor = currentPage === 'settings' ? 'rgba(0,255,0,0.08)' : 'var(--vio-bg-tertiary)';
            e.currentTarget.style.color = currentPage === 'settings' ? 'var(--vio-green)' : 'var(--vio-text-secondary)';
          }}
        >
          <Settings size={16} />
          {t('nav.settings')}
        </button>
      </div>
    </div>
  );
}
