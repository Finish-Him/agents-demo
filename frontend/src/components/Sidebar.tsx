import { cn } from '@/lib/cn';
import { useChatStore } from '@/stores/useChatStore';
import { AgentCard } from './AgentCard';
import { ModelPicker } from './ModelPicker';
import { GraduationCap, Plus, Github } from 'lucide-react';

const AGENT_EMOJIS: Record<string, string> = {
  prometheus: '🛡️',
  arquimedes: '🎓',
  atlas: '🗺️',
};

export function Sidebar() {
  const agents = useChatStore((s) => s.agents);
  const activeAgent = useChatStore((s) => s.activeAgent);
  const setActiveAgent = useChatStore((s) => s.setActiveAgent);
  const clearMessages = useChatStore((s) => s.clearMessages);

  const agentKeys = Object.keys(agents);

  return (
    <aside
      className={cn(
        'flex flex-col w-72 border-r border-surface-border',
        'bg-surface-card shrink-0',
      )}
    >
      {/* Header */}
      <div className="p-4 border-b border-surface-border">
        <div className="flex items-center gap-2 mb-1">
          <GraduationCap className="w-5 h-5 text-accent" />
          <h1 className="text-lg font-bold text-text-primary font-display tracking-tight">
            Arquimedes
          </h1>
        </div>
        <p className="text-xs text-text-muted leading-snug">
          Agente tutor de matemática para ML —{' '}
          <span className="text-mouts">Mouts IT</span> ×{' '}
          <span className="text-ambev">AmBev</span>
        </p>
      </div>

      {/* Agent list */}
      <div className="flex-1 overflow-y-auto p-3 space-y-2">
        <p className="text-[11px] font-medium text-text-muted uppercase tracking-[0.18em] px-1 mb-2">
          Agentes
        </p>
        {agentKeys.map((key) => (
          <AgentCard
            key={key}
            agentKey={key}
            emoji={AGENT_EMOJIS[key] || '🤖'}
            name={agents[key].name}
            description={agents[key].description}
            isActive={activeAgent === key}
            onClick={() => setActiveAgent(key)}
          />
        ))}
      </div>

      {/* Bottom controls */}
      <div className="p-3 border-t border-surface-border space-y-3">
        <ModelPicker />

        <button
          onClick={clearMessages}
          className={cn(
            'flex items-center gap-2 w-full px-3 py-2 rounded-lg text-sm',
            'text-text-secondary hover:text-text-primary',
            'hover:bg-surface-hover transition-colors',
          )}
        >
          <Plus className="w-4 h-4" />
          Nova conversa
        </button>

        <a
          href="https://github.com/Finish-Him/agents-demo"
          target="_blank"
          rel="noopener noreferrer"
          className={cn(
            'flex items-center gap-2 w-full px-3 py-2 rounded-lg text-sm',
            'text-text-muted hover:text-text-secondary transition-colors',
          )}
        >
          <Github className="w-4 h-4" />
          Código-fonte
        </a>
      </div>
    </aside>
  );
}
