// VIO 83 AI ORCHESTRA - Global State Management (Zustand)
import { create } from 'zustand';
import { persist, subscribeWithSelector } from 'zustand/middleware';
import type { BackendConversation } from '../services/conversationService';
import { deleteBackendConversation, fetchConversations } from '../services/conversationService';
import type { AIMode, AIProvider, AppPage, AppSettings, AuthUser, Conversation, Message } from '../types';

interface AppState {
  // Current conversation
  conversations: Conversation[];
  activeConversationId: string | null;

  // AI Settings
  settings: AppSettings;

  // Auth State (impronta digitale)
  authToken: string | null;
  authUser: AuthUser | null;

  // UI State
  sidebarOpen: boolean;
  settingsOpen: boolean;
  isStreaming: boolean;
  abortController: AbortController | null;
  currentPage: AppPage;

  // Actions
  createConversation: () => string;
  setActiveConversation: (id: string) => void;
  addMessage: (conversationId: string, message: Message) => void;
  updateSettings: (settings: Partial<AppSettings>) => void;
  setMode: (mode: AIMode) => void;
  setProvider: (provider: AIProvider) => void;
  setOllamaModel: (model: string) => void;
  toggleSidebar: () => void;
  toggleSettings: () => void;
  setStreaming: (streaming: boolean) => void;
  stopStreaming: () => void;
  setAbortController: (controller: AbortController | null) => void;
  deleteConversation: (id: string) => void;
  syncConversationId: (localId: string, backendId: string) => void;
  loadConversationsFromBackend: () => Promise<void>;
  resetToLocal: () => void;
  setCurrentPage: (page: AppPage) => void;
  activateFullOrchestration: () => void;
  setAuth: (token: string, user: AuthUser) => void;
  clearAuth: () => void;
}

const defaultSettings: AppSettings = {
  theme: 'vio-dark',
  language: 'it',
  orchestrator: {
    mode: 'local',
    primaryProvider: 'ollama',
    fallbackProviders: ['ollama'],
    crossCheckEnabled: false,
    ragEnabled: false,
    strictEvidenceMode: false,
    autoRouting: true,
    protocollo100x: true,
  },
  apiKeys: [],
  ollamaHost: 'http://localhost:11434',
  ollamaModel: 'llama3.2:3b',
  fontSize: 14,
  onboardingCompleted: false,
  analyticsOptIn: false,
};

// Versione dello schema — incrementa per forzare reset dei settings corrotti
const STORE_VERSION = 8;

function normalizeOrchestrator(
  orchestrator: AppSettings['orchestrator'],
): AppSettings['orchestrator'] {
  const mode = orchestrator.mode || 'local';
  const primaryProvider = orchestrator.primaryProvider || (mode === 'local' ? 'ollama' : 'claude');
  const fallback = orchestrator.fallbackProviders?.length
    ? orchestrator.fallbackProviders
    : (mode === 'local' ? ['ollama'] : [primaryProvider]);

  return {
    ...orchestrator,
    mode,
    primaryProvider,
    fallbackProviders: fallback as AIProvider[],
    autoRouting: orchestrator.autoRouting ?? true,
    protocollo100x: orchestrator.protocollo100x ?? true,
  };
}

export const useAppStore = create<AppState>()(
  subscribeWithSelector(
    persist(
      (set, get) => ({
        conversations: [],
        activeConversationId: null,
        settings: defaultSettings,
        authToken: null,
        authUser: null,
        sidebarOpen: true,
        settingsOpen: false,
        isStreaming: false,
        abortController: null,
        currentPage: 'chat' as AppPage,

        createConversation: () => {
          const id = crypto.randomUUID();
          const s = get().settings;
          const newConv: Conversation = {
            id,
            title: 'Nuova conversazione',
            messages: [],
            model: s.orchestrator.mode === 'local'
              ? (s.ollamaModel || 'qwen2.5-coder:3b')
              : 'claude-sonnet-4-20250514',
            provider: s.orchestrator.primaryProvider,
            mode: s.orchestrator.mode,
            createdAt: Date.now(),
            updatedAt: Date.now(),
          };
          set(state => ({
            conversations: [newConv, ...state.conversations],
            activeConversationId: id,
          }));
          return id;
        },

        setActiveConversation: (id) => set({ activeConversationId: id }),

        addMessage: (conversationId, message) => {
          set(state => ({
            conversations: state.conversations.map(conv =>
              conv.id === conversationId
                ? {
                  ...conv,
                  messages: [...conv.messages, message],
                  updatedAt: Date.now(),
                  title: conv.messages.length === 0 && message.role === 'user'
                    ? message.content.slice(0, 50) + (message.content.length > 50 ? '...' : '')
                    : conv.title,
                }
                : conv
            ),
          }));
        },

        updateSettings: (newSettings) => {
          set(state => ({
            settings: {
              ...state.settings,
              ...newSettings,
              orchestrator: normalizeOrchestrator({
                ...state.settings.orchestrator,
                ...(newSettings.orchestrator || {}),
              }),
            },
          }));
        },

        setMode: (mode) => {
          set(state => ({
            settings: {
              ...state.settings,
              orchestrator: normalizeOrchestrator({
                ...state.settings.orchestrator,
                mode,
                primaryProvider: mode === 'local' ? 'ollama' : state.settings.orchestrator.primaryProvider,
              }),
            },
          }));
        },

        setProvider: (provider) => {
          set(state => ({
            settings: {
              ...state.settings,
              orchestrator: normalizeOrchestrator({
                ...state.settings.orchestrator,
                primaryProvider: provider,
              }),
            },
          }));
        },

        setOllamaModel: (model) => {
          set(state => ({
            settings: {
              ...state.settings,
              ollamaModel: model,
            },
          }));
        },

        toggleSidebar: () => set(state => ({ sidebarOpen: !state.sidebarOpen })),
        toggleSettings: () => set(state => ({ settingsOpen: !state.settingsOpen })),
        setStreaming: (streaming) => set({ isStreaming: streaming }),
        setAbortController: (controller) => set({ abortController: controller }),
        stopStreaming: () => {
          const { abortController } = get();
          if (abortController) {
            abortController.abort();
          }
          set({ isStreaming: false, abortController: null });
        },

        deleteConversation: (id) => {
          set(state => ({
            conversations: state.conversations.filter(c => c.id !== id),
            activeConversationId: state.activeConversationId === id ? null : state.activeConversationId,
          }));
          // Best-effort: elimina anche nel backend
          deleteBackendConversation(id).catch(() => { });
        },

        syncConversationId: (localId, backendId) => {
          if (localId === backendId) return;
          set(state => ({
            conversations: state.conversations.map(c =>
              c.id === localId ? { ...c, id: backendId } : c
            ),
            activeConversationId: state.activeConversationId === localId ? backendId : state.activeConversationId,
          }));
        },

        loadConversationsFromBackend: async () => {
          try {
            const backendConvs = await fetchConversations(50);
            const mapped: Conversation[] = backendConvs.map((bc: BackendConversation) => ({
              id: bc.id,
              title: bc.title,
              messages: (bc.messages || []).map((m) => ({
                id: m.id,
                role: m.role as 'user' | 'assistant',
                content: m.content,
                provider: (m.provider || undefined) as AIProvider | undefined,
                model: m.model || undefined,
                timestamp: m.timestamp * 1000,
                latencyMs: m.latency_ms || undefined,
                tokensUsed: m.tokens_used || undefined,
                verified: m.verified === 1 ? true : m.verified === 0 ? false : undefined,
                qualityScore: m.quality_score || undefined,
              })),
              model: bc.primary_provider || 'ollama',
              provider: (bc.primary_provider || 'ollama') as AIProvider,
              mode: bc.mode as AIMode,
              createdAt: bc.created_at * 1000,
              updatedAt: bc.updated_at * 1000,
            }));

            // Merge: mantieni conversazioni locali senza duplicati
            set(state => {
              const backendIds = new Set(mapped.map(c => c.id));
              const localOnly = state.conversations.filter(c => !backendIds.has(c.id));
              return { conversations: [...mapped, ...localOnly] };
            });
          } catch {
            // Backend non raggiungibile — mantieni conversazioni locali
          }
        },

        setCurrentPage: (page) => set({ currentPage: page }),

        activateFullOrchestration: () => {
          set(state => ({
            settings: {
              ...state.settings,
              orchestrator: normalizeOrchestrator({
                ...state.settings.orchestrator,
                autoRouting: true,
                crossCheckEnabled: true,
                ragEnabled: true,
                strictEvidenceMode: true,
              }),
            },
          }));
        },

        resetToLocal: () => {
          set(state => ({
            settings: {
              ...state.settings,
              orchestrator: normalizeOrchestrator({
                ...defaultSettings.orchestrator,
                mode: 'local',
                primaryProvider: 'ollama',
                fallbackProviders: ['ollama'],
              }),
              ollamaModel: state.settings.ollamaModel || defaultSettings.ollamaModel,
            },
          }));
        },

        setAuth: (token, user) => set({ authToken: token, authUser: user }),
        clearAuth: () => set({ authToken: null, authUser: null }),
      }),
      {
        name: 'vio83-ai-orchestra-storage',
        version: STORE_VERSION,
        partialize: (state) => {
          // eslint-disable-next-line @typescript-eslint/no-unused-vars
          const { abortController, isStreaming, ...rest } = state;
          return rest;
        },
        migrate: (persistedState: unknown, version: number) => {
          // Fast path: skip migration if version matches
          if (version === STORE_VERSION) return persistedState as Record<string, unknown>;

          const ps = (persistedState || {}) as Record<string, unknown>;
          const currentSettings = (ps.settings || {}) as Record<string, unknown>;
          const mergedSettings = {
            ...defaultSettings,
            ...currentSettings,
            apiKeys: currentSettings.apiKeys || [],
            ollamaHost: currentSettings.ollamaHost || defaultSettings.ollamaHost,
            ollamaModel: currentSettings.ollamaModel || defaultSettings.ollamaModel,
          };

          if (version < STORE_VERSION) {
            console.warn('[VIO83] Migrazione store v' + version + ' -> v' + STORE_VERSION);
          }

          return {
            ...ps,
            settings: {
              ...mergedSettings,
              orchestrator: normalizeOrchestrator(
                mergedSettings.orchestrator || defaultSettings.orchestrator,
              ),
            },
          };
        },
      }
    )
  )
);
