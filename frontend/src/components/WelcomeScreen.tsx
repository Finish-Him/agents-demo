import { useChatStore } from '@/stores/useChatStore';
import { cn } from '@/lib/cn';
import { Shield, GraduationCap, Globe } from 'lucide-react';

const AGENT_ICONS: Record<string, React.ReactNode> = {
  prometheus: <Shield className="w-8 h-8" />,
  arquimedes: <GraduationCap className="w-8 h-8" />,
  atlas: <Globe className="w-8 h-8" />,
};

const AGENT_COLORS: Record<string, string> = {
  prometheus: 'text-violet-400',
  arquimedes: 'text-amber-400',
  atlas: 'text-cyan-400',
};

export function WelcomeScreen() {
  const agents = useChatStore((s) => s.agents);
  const activeAgent = useChatStore((s) => s.activeAgent);
  const sendMessage = useChatStore((s) => s.sendMessage);
  const info = agents[activeAgent];

  if (!info) return null;

  return (
    <div className="flex-1 flex items-center justify-center p-6">
      <div className="max-w-lg text-center space-y-6">
        {/* Agent icon */}
        <div
          className={cn(
            'inline-flex items-center justify-center w-16 h-16 rounded-2xl',
            'bg-surface-card border border-surface-border',
            AGENT_COLORS[activeAgent] || 'text-accent',
          )}
        >
          {AGENT_ICONS[activeAgent] || <Shield className="w-8 h-8" />}
        </div>

        <div>
          <h2 className="text-2xl font-bold text-text-primary">{info.name}</h2>
          <p className="text-sm text-text-secondary mt-2 leading-relaxed">
            {info.description}
          </p>
        </div>

        {/* Example prompts */}
        <div className="space-y-2">
          <p className="text-xs text-text-muted uppercase tracking-wider font-medium">
            Experimente
          </p>
          <div className="grid gap-2">
            {info.examples.map((ex, i) => (
              <button
                key={i}
                onClick={() => sendMessage(ex)}
                className={cn(
                  'text-left px-4 py-3 rounded-xl text-sm',
                  'border border-surface-border bg-surface-card',
                  'text-text-secondary hover:text-text-primary',
                  'hover:border-accent/30 hover:bg-accent-subtle',
                  'transition-all duration-150',
                )}
              >
                {ex}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
