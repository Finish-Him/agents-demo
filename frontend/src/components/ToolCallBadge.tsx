import { cn } from '@/lib/cn';
import { Wrench } from 'lucide-react';

interface ToolCallBadgeProps {
  tool: string;
}

export function ToolCallBadge({ tool }: ToolCallBadgeProps) {
  return (
    <div className="flex items-center gap-2 px-4 py-2">
      <div
        className={cn(
          'inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs',
          'bg-amber-500/10 text-amber-400 border border-amber-500/20',
          'animate-pulse',
        )}
      >
        <Wrench className="w-3 h-3" />
        <span>
          Using: <span className="font-mono font-medium">{tool}</span>
        </span>
      </div>
    </div>
  );
}
