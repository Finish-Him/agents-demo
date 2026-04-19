import { cn } from '@/lib/cn';

interface AgentCardProps {
  agentKey: string;
  emoji: string;
  name: string;
  description: string;
  isActive: boolean;
  onClick: () => void;
}

export function AgentCard({
  emoji,
  name,
  description,
  isActive,
  onClick,
}: AgentCardProps) {
  return (
    <button
      onClick={onClick}
      className={cn(
        'w-full text-left p-3 rounded-xl transition-all duration-150',
        'border border-transparent',
        isActive
          ? 'bg-accent-subtle border-accent/30 shadow-sm'
          : 'hover:bg-surface-hover',
      )}
    >
      <div className="flex items-start gap-2.5">
        <span className="text-lg mt-0.5">{emoji}</span>
        <div className="min-w-0">
          <p
            className={cn(
              'text-sm font-semibold truncate',
              isActive ? 'text-accent-hover' : 'text-text-primary',
            )}
          >
            {name}
          </p>
          <p className="text-xs text-text-muted line-clamp-2 mt-0.5 leading-relaxed">
            {description}
          </p>
        </div>
      </div>
    </button>
  );
}
