import { motion } from 'framer-motion';
import { ArrowRight, Sparkles } from 'lucide-react';
import leverSvg from '@/assets/arquimedes-lever.svg';
import { useChatStore } from '@/stores/useChatStore';
import { cn } from '@/lib/cn';

const SUGESTOES = [
  'Explique autovetores com uma analogia geométrica e cite o livro-texto.',
  'Derive o gradiente da função de perda MSE passo a passo.',
  'Exercício intermediário de Teorema de Bayes — depois corrija minha resposta.',
  'Plote f(x) = x³ − 3x e marque os pontos críticos.',
];

export function HeroArquimedes() {
  const sendMessage = useChatStore((s) => s.sendMessage);

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="max-w-3xl mx-auto px-6 py-10 space-y-8">
        {/* Hero block */}
        <motion.section
          initial={{ opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.55, ease: 'easeOut' }}
          className="relative overflow-hidden rounded-3xl border border-surface-border bg-surface-card"
        >
          <div className="absolute inset-0 bg-hero-glow opacity-80 pointer-events-none" />

          <div className="relative grid md:grid-cols-5 gap-6 p-8 md:p-10">
            <div className="md:col-span-3 space-y-4">
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.1 }}
                className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-accent-subtle border border-accent/30 text-accent text-[11px] font-medium"
              >
                <Sparkles className="w-3 h-3" />
                <span>Arquimedes · tutor de matemática para ML</span>
              </motion.div>

              <h1 className="font-display text-4xl md:text-5xl leading-tight text-text-primary">
                Matemática que <span className="text-mouts">ensina</span>,
                demonstrações que <span className="text-ambev">convencem</span>.
              </h1>

              <p className="text-text-secondary leading-relaxed text-[15px]">
                Agente adaptativo que cobre álgebra linear, cálculo,
                probabilidade e estatística — com RAG sobre Strang,
                Deisenroth e OpenStax, derivações passo a passo com SymPy
                e um modelo fine-tuned via LoRA para resolver problemas
                do GSM8K.
              </p>

              <div className="flex flex-wrap items-center gap-x-4 gap-y-2 pt-2 text-[11px] text-text-muted uppercase tracking-wider font-medium">
                <span>LangGraph</span>
                <span>·</span>
                <span>RAG híbrido</span>
                <span>·</span>
                <span>LoRA</span>
                <span>·</span>
                <span>MCP</span>
                <span>·</span>
                <span>Memória semântica</span>
              </div>
            </div>

            <div className="md:col-span-2 flex items-center justify-center">
              <motion.img
                src={leverSvg}
                alt="Alavanca de Arquimedes"
                className="w-full max-w-[320px] animate-glow"
                initial={{ opacity: 0, scale: 0.92, rotate: -4 }}
                animate={{ opacity: 1, scale: 1, rotate: 0 }}
                transition={{ duration: 0.7, delay: 0.15, ease: 'easeOut' }}
              />
            </div>
          </div>
        </motion.section>

        {/* Example prompts */}
        <motion.section
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.35 }}
          className="space-y-3"
        >
          <div className="flex items-center justify-between">
            <p className="text-[11px] uppercase tracking-[0.18em] text-text-muted font-medium">
              Comece por aqui
            </p>
            <p className="text-[11px] text-text-muted">
              clique e observe o trace das tools
            </p>
          </div>
          <div className="grid sm:grid-cols-2 gap-2.5">
            {SUGESTOES.map((q, i) => (
              <motion.button
                key={i}
                onClick={() => sendMessage(q)}
                whileHover={{ y: -2 }}
                whileTap={{ scale: 0.98 }}
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.35, delay: 0.45 + i * 0.06 }}
                className={cn(
                  'group text-left px-4 py-3 rounded-xl text-[13px]',
                  'border border-surface-border bg-surface-card',
                  'text-text-secondary hover:text-text-primary',
                  'hover:border-accent/40 hover:bg-accent-subtle',
                  'transition-colors duration-150',
                )}
              >
                <span className="flex items-start justify-between gap-3">
                  <span>{q}</span>
                  <ArrowRight className="w-3.5 h-3.5 shrink-0 mt-0.5 text-text-muted group-hover:text-accent transition-colors" />
                </span>
              </motion.button>
            ))}
          </div>
        </motion.section>
      </div>
    </div>
  );
}
