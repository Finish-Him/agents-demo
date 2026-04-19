import ReactMarkdown from 'react-markdown';
import rehypeHighlight from 'rehype-highlight';
import { cn } from '@/lib/cn';
import type { Message } from '@/stores/useChatStore';
import { User, Bot } from 'lucide-react';

interface ChatMessageProps {
  message: Message;
}

export function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === 'user';

  return (
    <div
      className={cn(
        'flex gap-3 py-4 px-2 rounded-xl',
        isUser ? '' : 'bg-surface-card/50',
      )}
    >
      {/* Avatar */}
      <div
        className={cn(
          'flex items-center justify-center w-8 h-8 rounded-lg shrink-0 mt-0.5',
          isUser ? 'bg-accent/20 text-accent' : 'bg-emerald-500/20 text-emerald-400',
        )}
      >
        {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
      </div>

      {/* Content */}
      <div className="min-w-0 flex-1">
        <p
          className={cn(
            'text-xs font-medium mb-1',
            isUser ? 'text-accent' : 'text-emerald-400',
          )}
        >
          {isUser ? 'You' : 'Assistant'}
        </p>

        {isUser ? (
          <p className="text-sm text-text-primary leading-relaxed whitespace-pre-wrap">
            {message.content}
          </p>
        ) : (
          <div className="prose-chat text-sm text-text-primary">
            {message.content ? (
              <ReactMarkdown rehypePlugins={[rehypeHighlight]}>
                {message.content}
              </ReactMarkdown>
            ) : null}
          </div>
        )}
      </div>
    </div>
  );
}
