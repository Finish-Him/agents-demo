import { useEffect } from 'react';
import { Sidebar } from '@/components/Sidebar';
import { ChatPanel } from '@/components/ChatPanel';
import { ChatInput } from '@/components/ChatInput';
import { ConceptsPanel } from '@/components/ConceptsPanel';
import { useChatStore } from '@/stores/useChatStore';
import { fetchAgents, fetchModels } from '@/lib/api';
import { Loader2 } from 'lucide-react';

export default function App() {
  const setAgents = useChatStore((s) => s.setAgents);
  const setModels = useChatStore((s) => s.setModels);
  const agents = useChatStore((s) => s.agents);

  useEffect(() => {
    fetchAgents().then(setAgents).catch(console.error);
    fetchModels()
      .then((m) => setModels(m.available, m.default))
      .catch(console.error);
  }, [setAgents, setModels]);

  if (Object.keys(agents).length === 0) {
    return (
      <div className="flex h-screen w-screen items-center justify-center bg-surface">
        <div className="flex flex-col items-center gap-3">
          <Loader2 className="w-8 h-8 text-accent animate-spin" />
          <p className="text-sm text-text-secondary">Loading agents...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-surface">
      <Sidebar />
      <main className="flex flex-1 flex-col min-w-0">
        <ChatPanel />
        <ChatInput />
      </main>
      <ConceptsPanel />
    </div>
  );
}
