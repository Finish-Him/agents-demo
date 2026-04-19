import { useEffect, useRef } from 'react';
import { useChatStore } from '@/stores/useChatStore';
import { ChatMessage } from './ChatMessage';
import { WelcomeScreen } from './WelcomeScreen';
import { ToolCallBadge } from './ToolCallBadge';
import { cn } from '@/lib/cn';

export function ChatPanel() {
  const messages = useChatStore((s) => s.messages);
  const isStreaming = useChatStore((s) => s.isStreaming);
  const activeTool = useChatStore((s) => s.activeTool);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, activeTool]);

  if (messages.length === 0) {
    return <WelcomeScreen />;
  }

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="max-w-3xl mx-auto px-4 py-6 space-y-1">
        {messages.map((msg) => (
          <ChatMessage key={msg.id} message={msg} />
        ))}

        {/* Tool call indicator */}
        {activeTool && <ToolCallBadge tool={activeTool} />}

        {/* Typing indicator */}
        {isStreaming &&
          messages.length > 0 &&
          messages[messages.length - 1].content === '' && (
            <div className="flex items-center gap-1.5 px-4 py-3">
              <div
                className={cn(
                  'w-2 h-2 rounded-full bg-accent animate-pulse-dot',
                )}
                style={{ animationDelay: '0s' }}
              />
              <div
                className="w-2 h-2 rounded-full bg-accent animate-pulse-dot"
                style={{ animationDelay: '0.2s' }}
              />
              <div
                className="w-2 h-2 rounded-full bg-accent animate-pulse-dot"
                style={{ animationDelay: '0.4s' }}
              />
            </div>
          )}

        <div ref={bottomRef} />
      </div>
    </div>
  );
}
