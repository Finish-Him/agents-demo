/* ── Types ─────────────────────────────────────────────────────────── */

export interface AgentInfo {
  name: string;
  description: string;
  lang: string;
  examples: string[];
}

export interface ModelInfo {
  id: string;
  name: string;
  speed: string;
}

export interface ModelsResponse {
  default: string;
  available: ModelInfo[];
}

/* ── Fetch helpers ─────────────────────────────────────────────────── */

export async function fetchAgents(): Promise<Record<string, AgentInfo>> {
  const res = await fetch('/agents');
  if (!res.ok) throw new Error('Failed to fetch agents');
  return res.json();
}

export async function fetchModels(): Promise<ModelsResponse> {
  const res = await fetch('/models');
  if (!res.ok) throw new Error('Failed to fetch models');
  return res.json();
}

/* ── SSE Streaming ─────────────────────────────────────────────────── */

export interface StreamCallbacks {
  onToken: (token: string) => void;
  onToolStart?: (name: string) => void;
  onToolEnd?: (name: string) => void;
  onMetadata?: (data: { thread_id: string; agent: string }) => void;
  onDone: () => void;
  onError: (error: Error) => void;
}

type SSEEvent = { event: string; data: string };

/**
 * Parse the Server-Sent-Events wire format: records separated by blank
 * lines, each record containing one or more ``field: value`` lines.
 * Multi-line ``data`` fields are joined with newlines.
 */
function parseSSEBuffer(buffer: string): { events: SSEEvent[]; rest: string } {
  const events: SSEEvent[] = [];
  const parts = buffer.split(/\r?\n\r?\n/);
  const rest = parts.pop() ?? '';

  for (const raw of parts) {
    if (!raw.trim()) continue;
    let eventName = 'message';
    const dataLines: string[] = [];
    for (const line of raw.split(/\r?\n/)) {
      if (line.startsWith(':')) continue; // comment
      const sep = line.indexOf(':');
      if (sep === -1) continue;
      const field = line.slice(0, sep);
      let value = line.slice(sep + 1);
      if (value.startsWith(' ')) value = value.slice(1);
      if (field === 'event') eventName = value;
      else if (field === 'data') dataLines.push(value);
    }
    events.push({ event: eventName, data: dataLines.join('\n') });
  }
  return { events, rest };
}

function dispatch(ev: SSEEvent, cb: StreamCallbacks) {
  switch (ev.event) {
    case 'metadata':
      try {
        cb.onMetadata?.(JSON.parse(ev.data));
      } catch {
        /* ignore */
      }
      return;
    case 'token':
      cb.onToken(ev.data);
      return;
    case 'tool_start':
      cb.onToolStart?.(ev.data);
      return;
    case 'tool_end':
      cb.onToolEnd?.(ev.data);
      return;
    case 'done':
      cb.onDone();
      return;
    default:
      // Fallback: bare data line with JSON containing thread_id
      try {
        const parsed = JSON.parse(ev.data);
        if (parsed && typeof parsed === 'object' && 'thread_id' in parsed) {
          cb.onMetadata?.(parsed);
          return;
        }
      } catch {
        /* ignore */
      }
      if (ev.data) cb.onToken(ev.data);
  }
}

export function streamChat(
  agentName: string,
  message: string,
  model: string,
  threadId: string,
  userId: string,
  callbacks: StreamCallbacks,
): AbortController {
  const controller = new AbortController();

  (async () => {
    try {
      const res = await fetch(`/chat/${agentName}/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message,
          thread_id: threadId,
          user_id: userId,
          model_name: model,
        }),
        signal: controller.signal,
      });

      if (!res.ok) {
        const text = await res.text();
        throw new Error(`API error ${res.status}: ${text}`);
      }
      const reader = res.body?.getReader();
      if (!reader) throw new Error('No response body');

      const decoder = new TextDecoder();
      let buffer = '';
      let doneEmitted = false;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const { events, rest } = parseSSEBuffer(buffer);
        buffer = rest;
        for (const ev of events) {
          dispatch(ev, callbacks);
          if (ev.event === 'done') doneEmitted = true;
        }
      }
      if (buffer.trim()) {
        const { events } = parseSSEBuffer(buffer + '\n\n');
        for (const ev of events) {
          dispatch(ev, callbacks);
          if (ev.event === 'done') doneEmitted = true;
        }
      }
      if (!doneEmitted) callbacks.onDone();
    } catch (err) {
      if ((err as Error).name !== 'AbortError') {
        callbacks.onError(err as Error);
      }
    }
  })();

  return controller;
}
