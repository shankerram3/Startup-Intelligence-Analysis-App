import { useEffect, useMemo, useRef, useState } from 'react';
import { postJson, QueryRequest, QueryResponse } from '../lib/api';

type ChatMessage = {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  meta?: any;
};

// Polyfill for crypto.randomUUID (not available in all browsers)
function generateUUID(): string {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  // Fallback UUID v4 generator
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

export function ChatView() {
  const [messages, setMessages] = useState<ChatMessage[]>(() => [
    {
      id: 'm0',
      role: 'system',
      content: 'Ask about companies, investors, people, or technologies. I will answer using the knowledge graph.'
    }
  ]);
  const [input, setInput] = useState('What AI startups raised funding recently?');
  const [loading, setLoading] = useState(false);
  const listRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight, behavior: 'smooth' });
  }, [messages.length]);

  async function send() {
    const text = input.trim();
    if (!text || loading) return;
    setInput('');
    const userMsg: ChatMessage = { id: generateUUID(), role: 'user', content: text };
    setMessages((prev) => [...prev, userMsg]);

    setLoading(true);
    try {
      const body: QueryRequest = { question: text, return_context: false, use_llm: true };
      const res = await postJson<QueryRequest, QueryResponse>('/query', body);
      const answer = (res.answer && String(res.answer).trim()) || 'No answer found.';
      const assistantMsg: ChatMessage = {
        id: generateUUID(),
        role: 'assistant',
        content: answer,
        meta: { intent: res.intent }
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        { id: generateUUID(), role: 'assistant', content: err?.message || 'Request failed' }
      ]);
    } finally {
      setLoading(false);
    }
  }

  function onKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  }

  return (
    <div style={styles.root}>
      <div ref={listRef} style={styles.messages}>
        {messages.map((m) => (
          <div key={m.id} style={{ ...styles.bubble, ...bubbleStyleFor(m.role) }}>
            {m.role !== 'system' && (
              <div style={styles.bubbleHeader}>
                <span style={styles.badge}>{m.role === 'user' ? 'You' : 'Assistant'}</span>
                {m.meta?.intent?.intent && (
                  <span style={styles.intentTag}>{m.meta.intent.intent}</span>
                )}
              </div>
            )}
            <div style={styles.bubbleContent}>{m.content}</div>
          </div>
        ))}
      </div>

      <div style={styles.composer}>
        <textarea
          placeholder="Type your question..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={onKeyDown}
          rows={2}
          style={styles.input}
        />
        <button onClick={send} style={styles.sendButton} disabled={loading || !input.trim()}>
          {loading ? 'Sending...' : 'Send'}
        </button>
      </div>
    </div>
  );
}

function bubbleStyleFor(role: ChatMessage['role']): React.CSSProperties {
  if (role === 'user') return styles.bubbleUser;
  if (role === 'assistant') return styles.bubbleAssistant;
  return styles.bubbleSystem;
}

const styles: Record<string, React.CSSProperties> = {
  root: {
    display: 'grid',
    gridTemplateRows: '1fr auto',
    height: '70vh',
    background: 'white',
    border: '1px solid #e2e8f0',
    borderRadius: 12,
    overflow: 'hidden'
  },
  messages: {
    padding: 16,
    overflowY: 'auto',
    background: '#f8fafc'
  },
  bubble: {
    maxWidth: '75%',
    marginBottom: 10,
    padding: '10px 12px',
    borderRadius: 12,
    boxShadow: '0 1px 2px rgba(0,0,0,0.04)'
  },
  bubbleUser: {
    marginLeft: 'auto',
    background: '#dbeafe',
    border: '1px solid #93c5fd'
  },
  bubbleAssistant: {
    marginRight: 'auto',
    background: '#f1f5f9',
    border: '1px solid #cbd5e1'
  },
  bubbleSystem: {
    margin: '0 auto',
    background: '#fff7ed',
    border: '1px solid #fed7aa'
  },
  bubbleHeader: {
    display: 'flex',
    gap: 8,
    alignItems: 'center',
    marginBottom: 6
  },
  badge: {
    fontSize: 12,
    padding: '2px 6px',
    background: '#0ea5e9',
    color: 'white',
    borderRadius: 999
  },
  intentTag: {
    fontSize: 12,
    padding: '2px 6px',
    background: '#e2e8f0',
    borderRadius: 999,
    color: '#334155'
  },
  bubbleContent: {
    whiteSpace: 'pre-wrap',
    lineHeight: 1.55
  },
  composer: {
    display: 'flex',
    gap: 8,
    padding: 12,
    borderTop: '1px solid #e2e8f0',
    background: 'white'
  },
  input: {
    flex: 1,
    borderRadius: 10,
    border: '1px solid #cbd5e1',
    padding: 10,
    fontSize: 14,
    background: '#f8fafc'
  },
  sendButton: {
    padding: '10px 14px',
    borderRadius: 10,
    border: '1px solid #0284c7',
    background: '#0ea5e9',
    color: 'white',
    cursor: 'pointer'
  }
};


