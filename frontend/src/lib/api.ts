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

export function streamChat(
  agentName: string,
  message: string,
  model: string,
  threadId: string,
  userId: string,
  callbacks: StreamCallbacks,
): AbortController {
  const controller = new AbortController();

  fetch(`/chat/${agentName}/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message,
      thread_id: threadId,
      user_id: userId,
      model_name: model,
    }),
    signal: controller.signal,
  })
    .then(async (res) => {
      if (!res.ok) {
        const text = await res.text();
        throw new Error(`API error ${res.status}: ${text}`);
      }

      const reader = res.body?.getReader();
      if (!reader) throw new Error('No response body');

      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('event:')) {
            const eventType = line.slice(6).trim();

            // Next line should be data:
            const dataLineIdx = lines.indexOf(line) + 1;
            if (dataLineIdx < lines.length) {
              const dataLine = lines[dataLineIdx];
              if (dataLine?.startsWith('data:')) {
                const data = dataLine.slice(5).trim();
                handleSSEEvent(eventType, data, callbacks);
              }
            }
          } else if (line.startsWith('data:')) {
            // sse-starlette format: "event: X\ndata: Y\n\n"
            // Sometimes just data lines — try to parse as JSON
            const data = line.slice(5).trim();
            if (data) {
              // Try to detect event type from data content
              try {
                const parsed = JSON.parse(data);
                if (parsed.thread_id) {
                  callbacks.onMetadata?.(parsed);
                }
              } catch {
                // Plain token text
                callbacks.onToken(data);
              }
            }
          }
        }
      }

      callbacks.onDone();
    })
    .catch((err: Error) => {
      if (err.name !== 'AbortError') {
        callbacks.onError(err);
      }
    });

  return controller;
}

function handleSSEEvent(
  eventType: string,
  data: string,
  callbacks: StreamCallbacks,
) {
  switch (eventType) {
    case 'metadata':
      try {
        callbacks.onMetadata?.(JSON.parse(data));
      } catch { /* ignore */ }
      break;
    case 'token':
      callbacks.onToken(data);
      break;
    case 'tool_start':
      callbacks.onToolStart?.(data);
      break;
    case 'tool_end':
      callbacks.onToolEnd?.(data);
      break;
    case 'done':
      callbacks.onDone();
      break;
  }
}
