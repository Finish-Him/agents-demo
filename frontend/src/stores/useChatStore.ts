import { create } from 'zustand';
import { streamChat, type AgentInfo, type ModelInfo } from '@/lib/api';

/* ── Types ─────────────────────────────────────────────────────────── */

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: number;
  toolCall?: string; // e.g. "lookup_regulation"
}

interface ChatState {
  /* Data */
  messages: Message[];
  activeAgent: string;
  selectedModel: string;
  threadId: string;
  userId: string;

  /* Agent/model catalog (fetched once) */
  agents: Record<string, AgentInfo>;
  models: ModelInfo[];
  defaultModel: string;

  /* UI state */
  isStreaming: boolean;
  activeTool: string | null;

  /* Actions */
  setAgents: (agents: Record<string, AgentInfo>) => void;
  setModels: (models: ModelInfo[], defaultModel: string) => void;
  setActiveAgent: (agent: string) => void;
  setSelectedModel: (model: string) => void;
  sendMessage: (text: string) => void;
  clearMessages: () => void;
  abort: () => void;
}

let abortController: AbortController | null = null;

function uid(): string {
  return Math.random().toString(36).slice(2, 10) + Date.now().toString(36);
}

export const useChatStore = create<ChatState>((set, get) => ({
  messages: [],
  activeAgent: 'prometheus',
  selectedModel: '',
  threadId: uid(),
  userId: 'demo-user',
  agents: {},
  models: [],
  defaultModel: '',
  isStreaming: false,
  activeTool: null,

  setAgents: (agents) => set({ agents }),
  setModels: (models, defaultModel) =>
    set((s) => ({
      models,
      defaultModel,
      selectedModel: s.selectedModel || defaultModel,
    })),

  setActiveAgent: (agent) =>
    set({
      activeAgent: agent,
      messages: [],
      threadId: uid(),
      activeTool: null,
    }),

  setSelectedModel: (model) => set({ selectedModel: model }),

  clearMessages: () =>
    set({ messages: [], threadId: uid(), activeTool: null }),

  abort: () => {
    abortController?.abort();
    abortController = null;
    set({ isStreaming: false, activeTool: null });
  },

  sendMessage: (text) => {
    const { activeAgent, selectedModel, threadId, userId, isStreaming } = get();
    if (isStreaming || !text.trim()) return;

    const userMsg: Message = {
      id: uid(),
      role: 'user',
      content: text.trim(),
      timestamp: Date.now(),
    };

    const assistantMsg: Message = {
      id: uid(),
      role: 'assistant',
      content: '',
      timestamp: Date.now(),
    };

    set((s) => ({
      messages: [...s.messages, userMsg, assistantMsg],
      isStreaming: true,
      activeTool: null,
    }));

    const assistantId = assistantMsg.id;

    abortController = streamChat(
      activeAgent,
      text.trim(),
      selectedModel,
      threadId,
      userId,
      {
        onToken: (token) => {
          set((s) => ({
            messages: s.messages.map((m) =>
              m.id === assistantId
                ? { ...m, content: m.content + token }
                : m,
            ),
          }));
        },
        onToolStart: (name) => {
          set({ activeTool: name });
        },
        onToolEnd: () => {
          set({ activeTool: null });
        },
        onMetadata: (data) => {
          set({ threadId: data.thread_id });
        },
        onDone: () => {
          set({ isStreaming: false, activeTool: null });
          abortController = null;
        },
        onError: (err) => {
          set((s) => ({
            isStreaming: false,
            activeTool: null,
            messages: s.messages.map((m) =>
              m.id === assistantId
                ? { ...m, content: m.content || `Error: ${err.message}` }
                : m,
            ),
          }));
          abortController = null;
        },
      },
    );
  },
}));
