import { cn } from '@/lib/cn';
import type { ToolInvocation } from '@/stores/useChatStore';
import {
  BookOpen,
  Brain,
  Calculator,
  Cpu,
  GraduationCap,
  Library,
  LineChart,
  Sigma,
  Target,
  Wrench,
} from 'lucide-react';
import type { ReactNode } from 'react';

interface ToolTraceProps {
  calls: ToolInvocation[];
}

const TOOL_ICON: Record<string, ReactNode> = {
  assess_level: <Target className="w-3 h-3" />,
  generate_exercise: <GraduationCap className="w-3 h-3" />,
  explain_concept: <Brain className="w-3 h-3" />,
  find_resources: <Library className="w-3 h-3" />,
  search_knowledge_base: <BookOpen className="w-3 h-3" />,
  step_by_step_derive: <Sigma className="w-3 h-3" />,
  solve_symbolic: <Calculator className="w-3 h-3" />,
  plot_function: <LineChart className="w-3 h-3" />,
  solve_with_finetuned: <Cpu className="w-3 h-3" />,
};

const TOOL_COLOR: Record<string, string> = {
  assess_level: 'text-sky-400 bg-sky-500/10 border-sky-500/20',
  generate_exercise: 'text-amber-400 bg-amber-500/10 border-amber-500/20',
  explain_concept: 'text-fuchsia-400 bg-fuchsia-500/10 border-fuchsia-500/20',
  find_resources: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20',
  search_knowledge_base: 'text-cyan-400 bg-cyan-500/10 border-cyan-500/20',
  step_by_step_derive: 'text-violet-400 bg-violet-500/10 border-violet-500/20',
  solve_symbolic: 'text-lime-400 bg-lime-500/10 border-lime-500/20',
  plot_function: 'text-rose-400 bg-rose-500/10 border-rose-500/20',
  solve_with_finetuned: 'text-orange-400 bg-orange-500/10 border-orange-500/20',
};

function formatDuration(ms: number | undefined): string {
  if (!ms) return '';
  if (ms < 1000) return `${ms}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
}

export function ToolTrace({ calls }: ToolTraceProps) {
  if (!calls || calls.length === 0) return null;
  return (
    <div className="flex flex-wrap gap-1.5 mb-2">
      {calls.map((c, i) => {
        const dur = c.endedAt ? c.endedAt - c.startedAt : undefined;
        const pending = c.endedAt === undefined;
        return (
          <span
            key={i}
            title={pending ? 'running…' : `ran in ${formatDuration(dur)}`}
            className={cn(
              'inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-mono border',
              TOOL_COLOR[c.name] ??
                'text-slate-300 bg-slate-500/10 border-slate-500/20',
              pending && 'animate-pulse',
            )}
          >
            {TOOL_ICON[c.name] ?? <Wrench className="w-3 h-3" />}
            <span>{c.name}</span>
            {dur !== undefined && (
              <span className="opacity-60">· {formatDuration(dur)}</span>
            )}
          </span>
        );
      })}
    </div>
  );
}
