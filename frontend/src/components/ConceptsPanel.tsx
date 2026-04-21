import { useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { useChatStore } from '@/stores/useChatStore';
import { cn } from '@/lib/cn';
import {
  BookOpen,
  Brain,
  Cpu,
  Database,
  GitBranch,
  Info,
  LineChart,
  Network,
  Package,
  Scissors,
  Sigma,
  Target,
  X,
} from 'lucide-react';
import type { ReactNode } from 'react';

interface Concept {
  name: string;
  icon: ReactNode;
  summary: string;
  code: string;
  example: string;
  color: string;
}

const CONCEPTS: Concept[] = [
  {
    name: 'LangChain · LCEL + Pydantic',
    icon: <Package className="w-4 h-4" />,
    summary:
      'ChatPromptTemplate | llm.bind_tools — Runnables componíveis com saída tipada via with_structured_output.',
    code: 'arquimedes/chains.py · arquimedes/schemas.py',
    example: 'Explique autovetores com uma analogia geométrica.',
    color: 'text-violet-300 border-violet-500/30 bg-violet-500/10',
  },
  {
    name: 'LangGraph · router + subgraph',
    icon: <Network className="w-4 h-4" />,
    summary:
      'StateGraph com router de entrada, nó rag_retrieve, ToolNode, write_memory e subgraph plan→step→verify.',
    code: 'arquimedes/agent.py · arquimedes/subgraphs/derivation.py',
    example: 'Derive passo a passo o gradiente da perda MSE.',
    color: 'text-indigo-300 border-indigo-500/30 bg-indigo-500/10',
  },
  {
    name: 'RAG · BM25 + denso',
    icon: <BookOpen className="w-4 h-4" />,
    summary:
      'ChromaDB + Reciprocal Rank Fusion de BM25 e retrieval denso, rerank opcional com cross-encoder.',
    code: 'arquimedes/rag/retrieval.py',
    example: 'Cite o livro-texto sobre o Teorema de Bayes.',
    color: 'text-cyan-300 border-cyan-500/30 bg-cyan-500/10',
  },
  {
    name: 'Chunks · LaTeX-aware',
    icon: <Scissors className="w-4 h-4" />,
    summary:
      'Protege blocos $$…$$ de serem cortados no meio da fórmula; modo hierárquico pai/filho para retrieval expandido.',
    code: 'arquimedes/rag/chunking.py',
    example: 'Cite um capítulo que defina a matriz Jacobiana.',
    color: 'text-emerald-300 border-emerald-500/30 bg-emerald-500/10',
  },
  {
    name: 'Fine-tuning · QLoRA em GSM8K',
    icon: <Cpu className="w-4 h-4" />,
    summary:
      'QLoRA 4-bit em Qwen2.5-1.5B publicado no HF Hub. Runtime: GPU local → Inference API → fallback honesto.',
    code: 'arquimedes/finetuning/ · arquimedes/tools/finetuned_solver.py',
    example: 'Use o modelo fine-tuned: Maria tem 23 maçãs, deu 8...',
    color: 'text-orange-300 border-orange-500/30 bg-orange-500/10',
  },
  {
    name: 'Tools · 9 funções decoradas',
    icon: <Sigma className="w-4 h-4" />,
    summary:
      'Ensino + RAG + SymPy + matplotlib + derivação subgraph + solver fine-tuned — uma lista, dois consumidores (LangGraph + MCP).',
    code: 'arquimedes/tools/',
    example: 'Calcule a derivada de 3x² + 5x − 7 com o SymPy.',
    color: 'text-lime-300 border-lime-500/30 bg-lime-500/10',
  },
  {
    name: 'MCP · stdio + SSE',
    icon: <GitBranch className="w-4 h-4" />,
    summary:
      'As mesmas @tool expostas ao Claude Desktop / Cursor / Cline; schemas introspectados do LangChain args_schema.',
    code: 'arquimedes/mcp_server/ · docs/arquimedes-mcp.md',
    example: 'Veja docs/arquimedes-mcp.md para configurar o cliente.',
    color: 'text-pink-300 border-pink-500/30 bg-pink-500/10',
  },
  {
    name: 'HuggingFace · 3 pontos de contato',
    icon: <Brain className="w-4 h-4" />,
    summary:
      'Prefix hf/<repo> na fábrica de LLMs (Inference API), fallback de embeddings MiniLM, push/pull do adapter LoRA.',
    code: 'shared/llm.py · arquimedes/rag/embeddings.py',
    example: 'Plote f(x)=x³−3x entre −3 e 3 marcando pontos críticos.',
    color: 'text-rose-300 border-rose-500/30 bg-rose-500/10',
  },
  {
    name: 'Memória · semântica + Postgres',
    icon: <Database className="w-4 h-4" />,
    summary:
      'Duas camadas: checkpointer por thread + store de longo prazo em Chroma/pgvector com similaridade sobre fatos do aluno.',
    code: 'shared/memory.py · shared/semantic_store.py · shared/postgres_store.py',
    example: 'Quais tópicos cobrimos na nossa última sessão?',
    color: 'text-sky-300 border-sky-500/30 bg-sky-500/10',
  },
];

export function ConceptsPanel() {
  const [open, setOpen] = useState(false);
  const sendMessage = useChatStore((s) => s.sendMessage);
  const setAgent = useChatStore((s) => s.setActiveAgent);

  const onExample = (q: string) => {
    setAgent('arquimedes');
    setOpen(false);
    setTimeout(() => sendMessage(q), 50);
  };

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        title="Como funciona — 9 conceitos de AI Engineering"
        className={cn(
          'fixed bottom-4 right-4 z-40',
          'flex items-center gap-2 px-3 py-2 rounded-full',
          'bg-surface-card border border-surface-border',
          'text-text-secondary hover:text-text-primary',
          'hover:border-accent/50 hover:bg-accent-subtle',
          'transition-all duration-150 shadow-lg',
        )}
      >
        <Info className="w-4 h-4" />
        <span className="text-xs font-medium">Como funciona</span>
      </button>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
            onClick={() => setOpen(false)}
          >
            <motion.div
              initial={{ opacity: 0, y: 16, scale: 0.97 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 12, scale: 0.97 }}
              transition={{ duration: 0.28, ease: 'easeOut' }}
              className="relative w-full max-w-4xl max-h-[85vh] overflow-y-auto m-4 p-6 rounded-2xl bg-surface-card border border-surface-border"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h2 className="text-xl font-bold text-text-primary font-display">
                    Arquimedes · 9 conceitos de AI Engineering
                  </h2>
                  <p className="text-sm text-text-secondary mt-1">
                    Clique em qualquer exemplo para mandá-lo ao agente e observar o trace das tools.
                  </p>
                </div>
                <button
                  onClick={() => setOpen(false)}
                  className="p-2 rounded-lg text-text-muted hover:text-text-primary hover:bg-surface-hover"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              <div className="grid md:grid-cols-2 gap-3">
                {CONCEPTS.map((c, i) => (
                  <motion.div
                    key={c.name}
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.28, delay: i * 0.04 }}
                    className={cn(
                      'p-4 rounded-xl border',
                      'bg-surface border-surface-border',
                    )}
                  >
                    <div className={cn('inline-flex items-center gap-2 px-2 py-1 rounded-md border text-xs font-medium', c.color)}>
                      {c.icon}
                      <span>{c.name}</span>
                    </div>
                    <p className="text-sm text-text-secondary mt-2 leading-relaxed">
                      {c.summary}
                    </p>
                    <p className="text-[11px] font-mono text-text-muted mt-2">{c.code}</p>
                    <button
                      onClick={() => onExample(c.example)}
                      className={cn(
                        'w-full text-left mt-3 px-3 py-2 rounded-lg text-xs',
                        'bg-surface-hover border border-surface-border',
                        'text-text-secondary hover:text-text-primary',
                        'hover:border-accent/40 hover:bg-accent-subtle',
                        'transition-all duration-150',
                      )}
                    >
                      <Target className="w-3 h-3 inline mr-1.5" />
                      Tente: {c.example}
                    </button>
                  </motion.div>
                ))}
              </div>

              <div className="mt-5 pt-4 border-t border-surface-border flex flex-wrap gap-2 items-center text-xs text-text-muted">
                <LineChart className="w-3 h-3" />
                <span>
                  Cada turno é rastreado no LangSmith (projeto{' '}
                  <code className="text-text-secondary">agents-demo-arquimedes</code>) —
                  veja <code>docs/observability.md</code>.
                </span>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
