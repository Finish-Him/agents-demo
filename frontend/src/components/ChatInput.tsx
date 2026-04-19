import { useState, useRef, useCallback } from 'react';
import { useChatStore } from '@/stores/useChatStore';
import { cn } from '@/lib/cn';
import { Send, Square } from 'lucide-react';

export function ChatInput() {
  const [text, setText] = useState('');
  const sendMessage = useChatStore((s) => s.sendMessage);
  const isStreaming = useChatStore((s) => s.isStreaming);
  const abort = useChatStore((s) => s.abort);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSend = useCallback(() => {
    if (!text.trim() || isStreaming) return;
    sendMessage(text);
    setText('');
    // Reset textarea height
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  }, [text, isStreaming, sendMessage]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setText(e.target.value);
    // Auto-resize
    const el = e.target;
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 200) + 'px';
  };

  return (
    <div className="border-t border-surface-border bg-surface-card/80 backdrop-blur-sm">
      <div className="max-w-3xl mx-auto px-4 py-3">
        <div
          className={cn(
            'flex items-end gap-2 rounded-xl border border-surface-border',
            'bg-surface px-3 py-2',
            'focus-within:border-accent/50 focus-within:ring-1 focus-within:ring-accent/20',
            'transition-all',
          )}
        >
          <textarea
            ref={textareaRef}
            value={text}
            onChange={handleInput}
            onKeyDown={handleKeyDown}
            placeholder="Send a message..."
            rows={1}
            className={cn(
              'flex-1 resize-none bg-transparent text-sm text-text-primary',
              'placeholder:text-text-muted outline-none',
              'max-h-[200px]',
            )}
          />

          {isStreaming ? (
            <button
              onClick={abort}
              className={cn(
                'flex items-center justify-center w-8 h-8 rounded-lg shrink-0',
                'bg-red-500/20 text-red-400 hover:bg-red-500/30',
                'transition-colors',
              )}
              title="Stop generating"
            >
              <Square className="w-4 h-4" />
            </button>
          ) : (
            <button
              onClick={handleSend}
              disabled={!text.trim()}
              className={cn(
                'flex items-center justify-center w-8 h-8 rounded-lg shrink-0',
                'transition-colors',
                text.trim()
                  ? 'bg-accent text-white hover:bg-accent-hover'
                  : 'bg-surface-hover text-text-muted cursor-not-allowed',
              )}
              title="Send message"
            >
              <Send className="w-4 h-4" />
            </button>
          )}
        </div>

        <p className="text-[10px] text-text-muted text-center mt-2">
          Powered by LangGraph + OpenRouter — Built by Moises Alves for Factored.ai
        </p>
      </div>
    </div>
  );
}
