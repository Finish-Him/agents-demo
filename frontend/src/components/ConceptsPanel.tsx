import { useState } from 'react';
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
    name: 'LangChain (LCEL + Pydantic)',
    icon: <Package className="w-4 h-4" />,
    summary:
      'ChatPromptTemplate | llm.bind_tools — composable Runnables with typed outputs via with_structured_output.',
    code: 'arquimedes/chains.py, arquimedes/schemas.py',
    example: 'Explain eigenvectors with a geometric analogy.',
    color: 'text-violet-300 border-violet-500/30 bg-violet-500/10',
  },
  {
    name: 'LangGraph (router + subgraph)',
    icon: <Network className="w-4 h-4" />,
    summary:
      'StateGraph with entry router, rag_retrieve node, ToolNode, write_memory, and a plan→step→verify subgraph.',
    code: 'arquimedes/agent.py, arquimedes/subgraphs/derivation.py',
    example: 'Derive step by step: gradient of MSE loss.',
    color: 'text-indigo-300 border-indigo-500/30 bg-indigo-500/10',
  },
  {
    name: 'RAG (hybrid BM25 + dense)',
    icon: <BookOpen className="w-4 h-4" />,
    summary:
      'ChromaDB + Reciprocal Rank Fusion of BM25 and dense retrieval, optional cross-encoder rerank.',
    code: 'arquimedes/rag/retrieval.py',
    example: 'Cite the textbook on Bayes\' theorem.',
    color: 'text-cyan-300 border-cyan-500/30 bg-cyan-500/10',
  },
  {
    name: 'Chunks (LaTeX-aware)',
    icon: <Scissors className="w-4 h-4" />,
    summary:
      'Protects $$…$$ blocks from being split mid-formula; hierarchical parent/child mode for parent-expansion retrieval.',
    code: 'arquimedes/rag/chunking.py',
    example: 'Quote a chapter that defines the Jacobian.',
    color: 'text-emerald-300 border-emerald-500/30 bg-emerald-500/10',
  },
  {
    name: 'Fine-tuning (QLoRA on GSM8K)',
    icon: <Cpu className="w-4 h-4" />,
    summary:
      '4-bit QLoRA over Qwen2.5-1.5B pushed to the HF Hub. Runtime loader: local GPU → Inference API → graceful fallback.',
    code: 'arquimedes/finetuning/, arquimedes/tools/finetuned_solver.py',
    example: 'Solve with the fine-tuned model: Maria has 23 apples...',
    color: 'text-orange-300 border-orange-500/30 bg-orange-500/10',
  },
  {
    name: 'Tools (9 decorated funcs)',
    icon: <Sigma className="w-4 h-4" />,
    summary:
      'Teaching + RAG + SymPy + matplotlib + derivation subgraph + fine-tuned solver — one list, two consumers (LangGraph + MCP).',
    code: 'arquimedes/tools/',
    example: 'Compute the derivative of 3x^2 + 5x - 7 with SymPy.',
    color: 'text-lime-300 border-lime-500/30 bg-lime-500/10',
  },
  {
    name: 'MCP server (stdio + SSE)',
    icon: <GitBranch className="w-4 h-4" />,
    summary:
      'Same @tool functions exposed to Claude Desktop / Cursor / Cline; schemas introspected from the LangChain args_schema.',
    code: 'arquimedes/mcp_server/, docs/arquimedes-mcp.md',
    example: 'See docs/arquimedes-mcp.md for client configs.',
    color: 'text-pink-300 border-pink-500/30 bg-pink-500/10',
  },
  {
    name: 'HuggingFace (3 touchpoints)',
    icon: <Brain className="w-4 h-4" />,
    summary:
      'hf/<repo> prefix in the LLM factory (Inference API), MiniLM embedding fallback, LoRA adapter push/pull.',
    code: 'shared/llm.py, arquimedes/rag/embeddings.py',
    example: 'Plot f(x)=x^3-3x from -3 to 3 and mark critical points.',
    color: 'text-rose-300 border-rose-500/30 bg-rose-500/10',
  },
  {
    name: 'Memory (semantic + Postgres)',
    icon: <Database className="w-4 h-4" />,
    summary:
      'Two tiers: thread checkpointer + Chroma/pgvector long-term store with similarity search over learner facts.',
    code: 'shared/memory.py, shared/semantic_store.py, shared/postgres_store.py',
    example: 'What topics did we cover last session?',
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
        title="How it works — 9 AI engineering concepts"
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
        <span className="text-xs font-medium">How it works</span>
      </button>

      {open && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
          onClick={() => setOpen(false)}
        >
          <div
            className="relative w-full max-w-4xl max-h-[85vh] overflow-y-auto m-4 p-6 rounded-2xl bg-surface-card border border-surface-border"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-start justify-between mb-4">
              <div>
                <h2 className="text-xl font-bold text-text-primary">
                  Archimedes — 9 AI Engineering Concepts
                </h2>
                <p className="text-sm text-text-secondary mt-1">
                  Click any example to send it to the agent and watch the tool trace fire.
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
              {CONCEPTS.map((c) => (
                <div
                  key={c.name}
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
                    Try: {c.example}
                  </button>
                </div>
              ))}
            </div>

            <div className="mt-5 pt-4 border-t border-surface-border flex flex-wrap gap-2 items-center text-xs text-text-muted">
              <LineChart className="w-3 h-3" />
              <span>
                Every turn is traced in LangSmith (project{' '}
                <code className="text-text-secondary">agents-demo-arquimedes</code>) —
                see <code>docs/observability.md</code>.
              </span>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
