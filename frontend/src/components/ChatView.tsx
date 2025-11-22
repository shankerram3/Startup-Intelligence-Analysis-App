import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { postJson, QueryRequest, QueryResponse } from '../lib/api';
import { useTypewriter } from '../hooks/useTypewriter';

type ChatMessage = {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  meta?: any;
  isTyping?: boolean;
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
  const shouldAutoScrollRef = useRef(true);
  const lastMessageIdRef = useRef<string>('m0');

  // Auto-scroll function - use useCallback to stabilize the reference
  const scrollToBottom = useCallback((behavior: ScrollBehavior = 'smooth') => {
    if (listRef.current) {
      // Always scroll if shouldAutoScroll is true, or if content is growing
      if (shouldAutoScrollRef.current) {
        // Use requestAnimationFrame for smoother scrolling
        requestAnimationFrame(() => {
          if (listRef.current) {
            listRef.current.scrollTo({
              top: listRef.current.scrollHeight,
              behavior
            });
          }
        });
      }
    }
  }, []);

  // Check if user scrolled up manually
  const handleScroll = useCallback(() => {
    if (listRef.current) {
      const { scrollTop, scrollHeight, clientHeight } = listRef.current;
      const distanceFromBottom = scrollHeight - scrollTop - clientHeight;
      const isNearBottom = distanceFromBottom < 100; // 100px threshold
      shouldAutoScrollRef.current = isNearBottom;
      
      // If user scrolls back to bottom, re-enable autoscroll
      if (isNearBottom) {
        shouldAutoScrollRef.current = true;
      }
    }
  }, []);

  // Auto-scroll when new messages are added
  useEffect(() => {
    const lastMessage = messages[messages.length - 1];
    if (lastMessage && lastMessage.id !== lastMessageIdRef.current) {
      lastMessageIdRef.current = lastMessage.id;
      // Ensure autoscroll is enabled when new message arrives
      shouldAutoScrollRef.current = true;
      // Use instant scroll for new messages, then smooth for typing
      requestAnimationFrame(() => {
        scrollToBottom('auto');
      });
    }
  }, [messages.length, scrollToBottom]);

  // Auto-scroll when user sends a message
  useEffect(() => {
    if (loading) {
      // Scroll immediately when user sends message
      requestAnimationFrame(() => {
        scrollToBottom('smooth');
      });
    }
  }, [loading, scrollToBottom]);

  // Continuous autoscroll during typing - use interval for more reliable scrolling
  useEffect(() => {
    const hasTypingMessage = messages.some(m => {
      // Check if message is assistant and either isTyping is true or undefined (defaults to typing)
      return m.role === 'assistant' && (m.isTyping === true || m.isTyping === undefined);
    });
    
    if (hasTypingMessage) {
      // Always enable autoscroll when typing
      shouldAutoScrollRef.current = true;
      
      const interval = setInterval(() => {
        if (listRef.current) {
          const { scrollTop, scrollHeight, clientHeight } = listRef.current;
          const distanceFromBottom = scrollHeight - scrollTop - clientHeight;
          
          // Always scroll to bottom during typing if autoscroll is enabled
          if (shouldAutoScrollRef.current && distanceFromBottom > 5) {
            listRef.current.scrollTo({
              top: scrollHeight,
              behavior: 'smooth'
            });
          }
        }
      }, 50); // Check more frequently (every 50ms) for smoother scrolling
      
      return () => clearInterval(interval);
    }
  }, [messages]);

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
        meta: { intent: res.intent },
        isTyping: true
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
      <div 
        ref={listRef} 
        style={styles.messages}
        onScroll={handleScroll}
      >
        {messages.map((m) => (
          <ChatMessageBubble key={m.id} message={m} onContentChange={scrollToBottom} />
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

function ChatMessageBubble({ 
  message: m, 
  onContentChange 
}: { 
  message: ChatMessage;
  onContentChange?: () => void;
}) {
  const shouldType = m.role === 'assistant' && (m.isTyping === true || m.isTyping === undefined);
  const { displayedText, isTyping } = useTypewriter(
    m.content,
    { enabled: shouldType }
  );

  // Trigger scroll on content change during typing (debounced)
  const scrollTimeoutRef = useRef<NodeJS.Timeout>();
  const prevIsTypingRef = useRef(false);
  const prevDisplayedLengthRef = useRef(0);
  
  useEffect(() => {
    // Scroll immediately when typing starts
    if (isTyping && !prevIsTypingRef.current && onContentChange) {
      requestAnimationFrame(() => {
        onContentChange();
      });
    }
    prevIsTypingRef.current = isTyping;

    // Scroll during typing as content changes (debounced)
    if (isTyping && onContentChange && displayedText.length > prevDisplayedLengthRef.current) {
      // Clear any pending scroll
      if (scrollTimeoutRef.current) {
        clearTimeout(scrollTimeoutRef.current);
      }
      // Scroll more frequently during typing for smoother experience
      scrollTimeoutRef.current = setTimeout(() => {
        onContentChange();
      }, 20); // Reduced debounce for more responsive scrolling
    }
    prevDisplayedLengthRef.current = displayedText.length;
    
    return () => {
      if (scrollTimeoutRef.current) {
        clearTimeout(scrollTimeoutRef.current);
      }
    };
  }, [displayedText, isTyping, onContentChange]);

  return (
    <div style={{ ...styles.bubble, ...bubbleStyleFor(m.role) }}>
      {m.role !== 'system' && (
        <div style={styles.bubbleHeader}>
          <span style={styles.badge}>{m.role === 'user' ? 'You' : 'Assistant'}</span>
          {m.meta?.intent?.intent && (
            <span style={styles.intentTag}>{m.meta.intent.intent}</span>
          )}
          {isTyping && <span style={styles.typingIndicator}>●</span>}
        </div>
      )}
      <div style={styles.bubbleContent}>
        {m.role === 'assistant' ? (
          <>
            {displayedText ? (
              <ReactMarkdown
                components={{
                  p: ({ children }) => <p style={{ margin: '0 0 12px 0' }}>{children}</p>,
                  strong: ({ children }) => <strong style={{ fontWeight: 600, color: 'inherit' }}>{children}</strong>,
                  ul: ({ children }) => <ul style={{ margin: '8px 0', paddingLeft: '20px' }}>{children}</ul>,
                  ol: ({ children }) => <ol style={{ margin: '8px 0', paddingLeft: '20px' }}>{children}</ol>,
                  li: ({ children }) => <li style={{ margin: '4px 0' }}>{children}</li>,
                  em: ({ children }) => <em style={{ fontStyle: 'italic' }}>{children}</em>
                }}
              >
                {displayedText}
              </ReactMarkdown>
            ) : (
              <span style={{ opacity: 0.5 }}>...</span>
            )}
            {isTyping && <span style={styles.typewriterCursor}>▊</span>}
          </>
        ) : (
          m.content
        )}
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
    margin: '10px auto',
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
  typingIndicator: {
    fontSize: 10,
    color: '#0ea5e9',
    animation: 'pulse 1.5s ease-in-out infinite',
    marginLeft: 4
  },
  typewriterCursor: {
    display: 'inline-block',
    marginLeft: 2,
    color: '#0ea5e9',
    animation: 'blink 1s infinite',
    fontWeight: 'bold'
  },
  bubbleContent: {
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


