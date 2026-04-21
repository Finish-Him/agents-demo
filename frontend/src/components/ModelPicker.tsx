import { cn } from '@/lib/cn';
import { useChatStore } from '@/stores/useChatStore';
import { ChevronDown, Zap } from 'lucide-react';
import { useState, useRef, useEffect } from 'react';

export function ModelPicker() {
  const models = useChatStore((s) => s.models);
  const selectedModel = useChatStore((s) => s.selectedModel);
  const setSelectedModel = useChatStore((s) => s.setSelectedModel);
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  const current = models.find((m) => m.id === selectedModel);

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  if (!models.length) return null;

  return (
    <div ref={ref} className="relative">
      <p className="text-[11px] font-medium text-text-muted uppercase tracking-wider px-1 mb-1.5">
        Modelo
      </p>
      <button
        onClick={() => setOpen(!open)}
        className={cn(
          'flex items-center justify-between w-full px-3 py-2 rounded-lg text-sm',
          'bg-surface hover:bg-surface-hover border border-surface-border',
          'text-text-primary transition-colors',
        )}
      >
        <span className="truncate">{current?.name || 'Select model'}</span>
        <ChevronDown
          className={cn('w-4 h-4 text-text-muted transition-transform', open && 'rotate-180')}
        />
      </button>

      {open && (
        <div
          className={cn(
            'absolute bottom-full left-0 right-0 mb-1 z-50',
            'bg-surface-card border border-surface-border rounded-xl shadow-xl',
            'py-1 max-h-60 overflow-y-auto',
          )}
        >
          {models.map((m) => (
            <button
              key={m.id}
              onClick={() => {
                setSelectedModel(m.id);
                setOpen(false);
              }}
              className={cn(
                'flex items-center gap-2 w-full px-3 py-2 text-sm text-left',
                'hover:bg-surface-hover transition-colors',
                m.id === selectedModel
                  ? 'text-accent-hover bg-accent-subtle'
                  : 'text-text-primary',
              )}
            >
              {m.speed === 'fast' && (
                <Zap className="w-3.5 h-3.5 text-yellow-400 shrink-0" />
              )}
              <span className="truncate">{m.name}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
