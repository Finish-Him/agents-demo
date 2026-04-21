import { motion } from 'framer-motion';
import moutsMark from '@/assets/mouts-mark.svg';
import ambevMark from '@/assets/ambev-mark.svg';
import { ArrowRight } from 'lucide-react';

export function BrandBanner() {
  return (
    <motion.div
      initial={{ opacity: 0, y: -8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: 'easeOut' }}
      className="h-11 px-4 flex items-center justify-between border-b border-surface-border bg-brand-gradient backdrop-blur-md"
    >
      {/* Left: Mouts — the path */}
      <div className="flex items-center gap-2">
        <span className="text-[10px] uppercase tracking-[0.18em] text-text-muted font-medium hidden sm:inline">
          Processo
        </span>
        <img src={moutsMark} alt="Mouts IT" className="h-5 w-auto" />
      </div>

      {/* Center: pipeline */}
      <div className="hidden md:flex items-center gap-2 text-text-secondary">
        <span className="text-[11px] font-medium">AI Engineer · PJ</span>
        <ArrowRight className="w-3.5 h-3.5 text-text-muted" />
        <span className="text-[11px] font-medium">Entrevista Técnica</span>
      </div>

      {/* Right: AmBev — the destination */}
      <div className="flex items-center gap-2">
        <img src={ambevMark} alt="AmBev" className="h-5 w-auto" />
        <span className="text-[10px] uppercase tracking-[0.18em] text-text-muted font-medium hidden sm:inline">
          Cliente
        </span>
      </div>
    </motion.div>
  );
}
