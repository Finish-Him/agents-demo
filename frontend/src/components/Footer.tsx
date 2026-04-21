import moutsMark from '@/assets/mouts-mark.svg';
import ambevMark from '@/assets/ambev-mark.svg';

export function Footer() {
  return (
    <footer
      className="border-t border-surface-border bg-surface-card/60 backdrop-blur-sm"
    >
      <div className="max-w-5xl mx-auto px-4 py-2 flex flex-wrap items-center justify-between gap-2">
        <p className="text-[10px] text-text-muted">
          Arquimedes · demo de processo seletivo ·{' '}
          <span className="text-text-secondary">LangGraph</span> ·{' '}
          <span className="text-text-secondary">FastAPI</span> ·{' '}
          <span className="text-text-secondary">Docker</span> ·{' '}
          <span className="text-text-secondary">Supabase</span>
        </p>
        <div className="flex items-center gap-2 text-[10px] text-text-muted">
          <span>construído para</span>
          <img src={moutsMark} alt="Mouts IT" className="h-3.5" />
          <span>×</span>
          <img src={ambevMark} alt="AmBev" className="h-3.5" />
        </div>
      </div>
    </footer>
  );
}
