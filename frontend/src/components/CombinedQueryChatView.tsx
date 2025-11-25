import { useCallback, useEffect, useRef, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { postJson, QueryRequest, QueryResponse } from '../lib/api';
import { useTypewriter } from '../hooks/useTypewriter';
import { GraphTraversalAnimation } from './GraphTraversalAnimation';

type ChatMessage = {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  meta?: any;
  isTyping?: boolean;
};

type QueryTemplate = {
  name: string;
  question: string;
  category: string;
};

type ChatHistory = {
  id: string;
  title: string;
  messages: ChatMessage[];
  timestamp: Date;
  lastUpdated: Date;
};

const QUERY_TEMPLATES: QueryTemplate[] = [
  { name: 'Recent Funding', question: 'Which AI startups raised funding recently?', category: 'Funding' },
  { name: 'SF Companies', question: 'Which AI companies are based in San Francisco?', category: 'Location' },
  { name: 'Founded After 2020', question: 'What companies were founded after 2020?', category: 'Company Info' },
  { name: 'PyTorch Users', question: 'Which startups use PyTorch for machine learning?', category: 'Technology' },
  { name: 'Series B Companies', question: 'Which Series B companies raised over $100M?', category: 'Funding' },
  { name: 'Founders', question: 'What companies did Dario Amodei found?', category: 'People' },
  { name: 'Investors', question: 'Which investors funded OpenAI?', category: 'Investors' },
  { name: 'Acquisitions', question: 'Which companies were acquired in the last year?', category: 'M&A' },
  { name: 'Product Focus', question: 'Which companies are building AI assistants?', category: 'Products' },
  { name: 'Market Leaders', question: 'Who are the leading companies in autonomous vehicles?', category: 'Market' }
];

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

// Load chat history from localStorage
function loadChatHistory(): ChatHistory[] {
  try {
    const saved = localStorage.getItem('chat-history');
    if (saved) {
      const parsed = JSON.parse(saved);
      return parsed.map((h: any) => ({
        ...h,
        timestamp: new Date(h.timestamp),
        lastUpdated: new Date(h.lastUpdated),
        messages: h.messages || []
      }));
    }
  } catch (e) {
    console.error('Failed to load chat history:', e);
  }
  return [];
}

// Save chat history to localStorage
function saveChatHistory(history: ChatHistory[]) {
  try {
    localStorage.setItem('chat-history', JSON.stringify(history));
  } catch (e) {
    console.error('Failed to save chat history:', e);
  }
}

// Load current conversation from localStorage
function loadCurrentConversation(): { messages: ChatMessage[], chatId: string | null } {
  try {
    const saved = localStorage.getItem('current-conversation');
    if (saved) {
      const parsed = JSON.parse(saved);
      return {
        messages: parsed.messages || [],
        chatId: parsed.chatId || null
      };
    }
  } catch (e) {
    console.error('Failed to load current conversation:', e);
  }
  return {
    messages: [{
      id: 'm0',
      role: 'system',
      content: 'Ask about companies, investors, people, or technologies. I will answer using the knowledge graph.'
    }],
    chatId: null
  };
}

// Save current conversation to localStorage
function saveCurrentConversation(messages: ChatMessage[], chatId: string | null) {
  try {
    localStorage.setItem('current-conversation', JSON.stringify({
      messages: messages.map(m => ({ ...m, isTyping: false })),
      chatId
    }));
  } catch (e) {
    console.error('Failed to save current conversation:', e);
  }
}

export function CombinedQueryChatView() {
  const initialConversation = loadCurrentConversation();
  const [messages, setMessages] = useState<ChatMessage[]>(initialConversation.messages);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [returnContext, setReturnContext] = useState(false);
  const [useLlm, setUseLlm] = useState(true);
  const [returnTraversal, setReturnTraversal] = useState(true);
  const [showTemplates, setShowTemplates] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState<string>('All');
  const [chatHistory, setChatHistory] = useState<ChatHistory[]>(() => loadChatHistory());
  const [currentChatId, setCurrentChatId] = useState<string | null>(initialConversation.chatId);
  const listRef = useRef<HTMLDivElement | null>(null);
  const shouldAutoScrollRef = useRef(true);
  const lastMessageIdRef = useRef<string>('m0');

  // Auto-scroll function
  const scrollToBottom = useCallback((behavior: ScrollBehavior = 'smooth') => {
    if (listRef.current && shouldAutoScrollRef.current) {
      requestAnimationFrame(() => {
        if (listRef.current) {
          listRef.current.scrollTo({
            top: listRef.current.scrollHeight,
            behavior
          });
        }
      });
    }
  }, []);

  // Check if user scrolled up manually
  const handleScroll = useCallback(() => {
    if (listRef.current) {
      const { scrollTop, scrollHeight, clientHeight } = listRef.current;
      const distanceFromBottom = scrollHeight - scrollTop - clientHeight;
      const isNearBottom = distanceFromBottom < 100;
      shouldAutoScrollRef.current = isNearBottom;
    }
  }, []);

  // Auto-scroll when new messages are added
  useEffect(() => {
    const lastMessage = messages[messages.length - 1];
    if (lastMessage && lastMessage.id !== lastMessageIdRef.current) {
      lastMessageIdRef.current = lastMessage.id;
      shouldAutoScrollRef.current = true;
      requestAnimationFrame(() => {
        scrollToBottom('auto');
      });
    }
  }, [messages.length, scrollToBottom]);

  // Continuous autoscroll during typing
  useEffect(() => {
    const hasTypingMessage = messages.some(m => 
      m.role === 'assistant' && (m.isTyping === true || m.isTyping === undefined)
    );
    
    if (hasTypingMessage) {
      shouldAutoScrollRef.current = true;
      const interval = setInterval(() => {
        if (listRef.current) {
          const { scrollTop, scrollHeight, clientHeight } = listRef.current;
          const distanceFromBottom = scrollHeight - scrollTop - clientHeight;
          if (shouldAutoScrollRef.current && distanceFromBottom > 5) {
            listRef.current.scrollTo({
              top: scrollHeight,
              behavior: 'smooth'
            });
          }
        }
      }, 50);
      return () => clearInterval(interval);
    }
  }, [messages]);

  // Save current conversation to localStorage whenever messages or chatId changes
  useEffect(() => {
    // Only save if there are user messages (not just the system message)
    const hasUserMessages = messages.some(m => m.role === 'user');
    if (hasUserMessages) {
      saveCurrentConversation(messages, currentChatId);
    }
  }, [messages, currentChatId]);

  // Save conversation to history
  const saveToHistory = useCallback((msgs: ChatMessage[]) => {
    const userMessages = msgs.filter(m => m.role === 'user');
    if (userMessages.length === 0) return;

    const firstUserMessage = userMessages[0].content;
    const title = firstUserMessage.length > 50 
      ? firstUserMessage.substring(0, 50) + '...' 
      : firstUserMessage;

    const chatToSave: ChatHistory = {
      id: currentChatId || generateUUID(),
      title,
      messages: msgs.map(m => ({ ...m, isTyping: false })),
      timestamp: currentChatId 
        ? (chatHistory.find(h => h.id === currentChatId)?.timestamp || new Date())
        : new Date(),
      lastUpdated: new Date()
    };

    setChatHistory((prev) => {
      const filtered = prev.filter(h => h.id !== chatToSave.id);
      const updated = [chatToSave, ...filtered].slice(0, 50); // Keep last 50 chats
      saveChatHistory(updated);
      return updated;
    });

    if (!currentChatId) {
      setCurrentChatId(chatToSave.id);
    }
  }, [currentChatId, chatHistory]);

  async function send() {
    const text = input.trim();
    if (!text || loading) return;
    setInput('');
    const userMsg: ChatMessage = { id: generateUUID(), role: 'user', content: text };
    const loadingMsgId = generateUUID();
    const loadingMsg: ChatMessage = {
      id: loadingMsgId,
      role: 'assistant',
      content: '',
      isTyping: true
    };
    
    setMessages((prev) => {
      const updated = [...prev, userMsg, loadingMsg];
      return updated;
    });

    setLoading(true);
    try {
      const body: QueryRequest = { 
        question: text, 
        return_context: returnContext, 
        use_llm: useLlm,
        return_traversal: returnTraversal
      };
      const res = await postJson<QueryRequest, QueryResponse>('/query', body);
      const answer = (res.answer && String(res.answer).trim()) || 'No answer found.';
      
      // Replace loading message with actual response
      setMessages((prev) => {
        const withoutLoading = prev.filter(m => m.id !== loadingMsgId);
      const assistantMsg: ChatMessage = {
        id: generateUUID(),
        role: 'assistant',
        content: answer,
        meta: { intent: res.intent, context: res.context, traversal: res.traversal },
        isTyping: true
      };
        const updated = [...withoutLoading, assistantMsg];
        // Save after receiving response
        setTimeout(() => saveToHistory(updated), 100);
        return updated;
      });
    } catch (err: any) {
      // Replace loading message with error
      setMessages((prev) => {
        const withoutLoading = prev.filter(m => m.id !== loadingMsgId);
        const updated: ChatMessage[] = [
          ...withoutLoading,
          { id: generateUUID(), role: 'assistant' as const, content: err?.message || 'Request failed' }
        ];
        setTimeout(() => saveToHistory(updated), 100);
        return updated;
      });
    } finally {
      setLoading(false);
    }
  }

  function startNewChat() {
    const newMessages = [{
      id: 'm0',
      role: 'system',
      content: 'Ask about companies, investors, people, or technologies. I will answer using the knowledge graph.'
    }];
    setMessages(newMessages);
    setCurrentChatId(null);
    setInput('');
    // Clear current conversation from localStorage
    saveCurrentConversation(newMessages, null);
  }

  function loadChat(historyItem: ChatHistory) {
    setMessages(historyItem.messages);
    setCurrentChatId(historyItem.id);
    setInput('');
    // Scroll to bottom when loading chat
    setTimeout(() => scrollToBottom('auto'), 100);
  }

  function deleteChat(chatId: string, e: React.MouseEvent) {
    e.stopPropagation();
    setChatHistory((prev) => {
      const filtered = prev.filter(h => h.id !== chatId);
      saveChatHistory(filtered);
      if (currentChatId === chatId) {
        startNewChat();
      }
      return filtered;
    });
  }

  function onKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  }

  function useTemplate(template: QueryTemplate) {
    setInput(template.question);
  }

  const categories = ['All', ...Array.from(new Set(QUERY_TEMPLATES.map(t => t.category)))];
  const filteredTemplates = selectedCategory === 'All'
    ? QUERY_TEMPLATES
    : QUERY_TEMPLATES.filter(t => t.category === selectedCategory);

  return (
    <div style={{
      ...styles.root,
      gridTemplateColumns: showTemplates ? '240px 1fr 290px' : '240px 1fr'
    }}>
      <style>{`
        @keyframes bounce {
          0%, 80%, 100% {
            transform: scale(0);
            opacity: 0.5;
          }
          40% {
            transform: scale(1);
            opacity: 1;
          }
        }
        @keyframes pulse {
          0%, 100% {
            opacity: 1;
          }
          50% {
            opacity: 0.5;
          }
        }
        @keyframes blink {
          0%, 49% {
            opacity: 1;
          }
          50%, 100% {
            opacity: 0;
          }
        }
        [data-spinner-dot]:nth-child(1) {
          animation-delay: -0.32s;
        }
        [data-spinner-dot]:nth-child(2) {
          animation-delay: -0.16s;
        }
      `}</style>
      {/* Left Sidebar: Chat History */}
      <aside style={styles.historySidebar}>
        <div style={styles.historyHeader}>
          <h3 style={{ margin: 0 }}>💬 History</h3>
          <button onClick={startNewChat} style={styles.newChatButton} title="New Chat">
            ➕
          </button>
        </div>
        {chatHistory.length === 0 ? (
          <p style={styles.emptyState}>No chat history yet. Start a conversation!</p>
        ) : (
          <div style={styles.historyList}>
            {chatHistory.map((item) => (
              <div
                key={item.id}
                onClick={() => loadChat(item)}
                style={{
                  ...styles.historyItem,
                  ...(currentChatId === item.id ? styles.historyItemActive : {})
                }}
              >
                <div style={styles.historyItemContent}>
                  <div style={styles.historyTitle}>{item.title}</div>
                  <div style={styles.historyMeta}>
                    {item.lastUpdated.toLocaleDateString()} {item.lastUpdated.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </div>
                </div>
                <button
                  onClick={(e) => deleteChat(item.id, e)}
                  style={styles.deleteButton}
                  title="Delete chat"
                  onMouseEnter={(e) => { e.currentTarget.style.opacity = '1'; }}
                  onMouseLeave={(e) => { e.currentTarget.style.opacity = '0.5'; }}
                >
                  ×
                </button>
              </div>
            ))}
          </div>
        )}
      </aside>

      {/* Middle: Chat Container */}
      <div style={styles.chatContainer}>
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
          <div style={styles.optionsBar}>
            <label style={styles.checkbox}>
              <input 
                type="checkbox" 
                checked={returnContext} 
                onChange={(e) => setReturnContext(e.target.checked)} 
              />
              <span>Show context</span>
            </label>
            <label style={styles.checkbox}>
              <input 
                type="checkbox" 
                checked={useLlm} 
                onChange={(e) => setUseLlm(e.target.checked)} 
              />
              <span>Use LLM</span>
            </label>
            <label style={styles.checkbox}>
              <input 
                type="checkbox" 
                checked={returnTraversal} 
                onChange={(e) => setReturnTraversal(e.target.checked)} 
              />
              <span>Show Graph</span>
            </label>
            <button
              onClick={() => setShowTemplates(!showTemplates)}
              style={styles.templatesToggle}
            >
              {showTemplates ? '🔽 Hide Templates' : '▶ Show Templates'}
            </button>
          </div>
          <div style={styles.inputRow}>
            <textarea
              placeholder="Ask a question about companies, investors, people, or technologies..."
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
      </div>

      {/* Right Sidebar: Templates */}
      {showTemplates && (
        <aside style={styles.templatesSidebar}>
          <section style={styles.card}>
            <h3 style={{ marginTop: 0, color: '#ffffff' }}>📋 Query Templates</h3>
            <p style={styles.hint}>Click any template to use it</p>

            <div style={styles.categoryFilter}>
              {categories.map(cat => (
                <button
                  key={cat}
                  onClick={() => setSelectedCategory(cat)}
                  style={{
                    ...styles.categoryButton,
                    ...(selectedCategory === cat ? styles.categoryButtonActive : {})
                  }}
                >
                  {cat}
                </button>
              ))}
            </div>

            <div style={styles.templatesGrid}>
              {filteredTemplates.map((template, idx) => (
                <button
                  key={idx}
                  onClick={() => useTemplate(template)}
                  style={styles.templateCard}
                >
                  <div style={styles.templateCategory}>{template.category}</div>
                  <div style={styles.templateName}>{template.name}</div>
                  <div style={styles.templateQuestion}>{template.question}</div>
                </button>
              ))}
            </div>
          </section>
        </aside>
      )}
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
  const shouldType = m.role === 'assistant' && m.content && (m.isTyping === true || m.isTyping === undefined);
  const { displayedText, isTyping } = useTypewriter(
    m.content || '',
    { enabled: !!shouldType }
  );

  const scrollTimeoutRef = useRef<ReturnType<typeof setTimeout>>();
  const prevIsTypingRef = useRef(false);
  const prevDisplayedLengthRef = useRef(0);
  
  useEffect(() => {
    if (isTyping && !prevIsTypingRef.current && onContentChange) {
      requestAnimationFrame(() => {
        onContentChange();
      });
    }
    prevIsTypingRef.current = isTyping;

    if (isTyping && onContentChange && displayedText.length > prevDisplayedLengthRef.current) {
      if (scrollTimeoutRef.current) {
        clearTimeout(scrollTimeoutRef.current);
      }
      scrollTimeoutRef.current = setTimeout(() => {
        onContentChange();
      }, 20);
    }
    prevDisplayedLengthRef.current = displayedText.length;
    
    return () => {
      if (scrollTimeoutRef.current) {
        clearTimeout(scrollTimeoutRef.current);
      }
    };
  }, [displayedText, isTyping, onContentChange]);

  // Show loading indicator if message is empty and isTyping is true
  const isLoading = m.role === 'assistant' && !m.content && (m.isTyping === true || m.isTyping === undefined);

  return (
    <div style={{ ...styles.bubble, ...bubbleStyleFor(m.role) }}>
      {m.role !== 'system' && (
        <div style={styles.bubbleHeader}>
          <span style={styles.badge}>{m.role === 'user' ? 'You' : 'Assistant'}</span>
          {m.meta?.intent?.intent && (
            <span style={styles.intentTag}>{m.meta.intent.intent}</span>
          )}
          {(isTyping || isLoading) && <span style={styles.typingIndicator}>●</span>}
        </div>
      )}
      <div style={{
        ...styles.bubbleContent,
        ...(m.role === 'system' ? { textAlign: 'center' } : {})
      }}>
        {m.role === 'assistant' ? (
          <>
            {isLoading ? (
              <LoadingIndicator />
            ) : displayedText ? (
              <>
              <ReactMarkdown
                components={{
                  p: ({ children }) => <p style={{ margin: '0 0 12px 0', color: '#ffffff' }}>{children}</p>,
                  strong: ({ children }) => <strong style={{ fontWeight: 600, color: '#ffffff' }}>{children}</strong>,
                  ul: ({ children }) => <ul style={{ margin: '8px 0', paddingLeft: '20px', color: '#ffffff' }}>{children}</ul>,
                  ol: ({ children }) => <ol style={{ margin: '8px 0', paddingLeft: '20px', color: '#ffffff' }}>{children}</ol>,
                  li: ({ children }) => <li style={{ margin: '4px 0', color: '#ffffff' }}>{children}</li>,
                  em: ({ children }) => <em style={{ fontStyle: 'italic', color: '#ffffff' }}>{children}</em>
                }}
              >
                {displayedText}
              </ReactMarkdown>
                {isTyping && <span style={styles.typewriterCursor}>▊</span>}
              </>
            ) : (
              <span style={{ opacity: 0.5 }}>...</span>
            )}
          </>
        ) : (
          <span style={{ color: '#ffffff' }}>{m.content}</span>
        )}
      </div>
      {m.role === 'assistant' && m.meta?.traversal && (
        <GraphTraversalAnimation 
          traversalData={m.meta.traversal} 
        />
      )}
      {m.role === 'assistant' && m.meta?.context && (
        <details style={{ marginTop: 12 }}>
          <summary style={styles.detailsSummary}>📊 Context Data</summary>
          <ContextDataDisplay context={m.meta.context} />
        </details>
      )}
    </div>
  );
}

function LoadingIndicator() {
  const [dots, setDots] = useState('');

  useEffect(() => {
    const interval = setInterval(() => {
      setDots(prev => {
        if (prev === '...') return '';
        return prev + '.';
      });
    }, 500);
    return () => clearInterval(interval);
  }, []);

  return (
    <div style={styles.loadingContainer}>
      <div style={styles.loadingSpinner}>
        <div data-spinner-dot style={styles.spinnerDot}></div>
        <div data-spinner-dot style={styles.spinnerDot}></div>
        <div data-spinner-dot style={styles.spinnerDot}></div>
      </div>
      <span style={styles.loadingText}>Generating response{dots}</span>
    </div>
  );
}

function ContextDataDisplay({ context }: { context: any }) {
  // Handle array of context items
  if (Array.isArray(context)) {
    if (context.length === 0) {
      return <div style={styles.contextEmpty}>No context data available.</div>;
    }
    
    // Check if this is article context (has url/title/text) or entity context (has name/description)
    const firstItem = context[0];
    const isArticleContext = firstItem && (firstItem.url || firstItem.title || firstItem.text);
    
    return (
      <div style={styles.contextContainer}>
        <div style={styles.contextHeader}>
          Found {context.length} {context.length === 1 ? 'result' : 'results'}
        </div>
        <div style={styles.contextList}>
          {context.map((item: any, index: number) => {
            // Article context display
            if (isArticleContext) {
              return (
                <div key={item.article_id || item.url || index} style={styles.contextItem}>
                  <div style={styles.contextItemHeader}>
                    <h4 style={styles.contextItemName}>{item.title || 'Untitled Article'}</h4>
                    {item.score !== undefined && (
                      <span style={styles.contextBadge}>Score: {item.score.toFixed(3)}</span>
                    )}
                  </div>
                  
                  {item.url && (
                    <div style={styles.contextMetaRow}>
                      <strong style={{ color: '#ffffff' }}>Source:</strong>{' '}
                      <a 
                        href={item.url} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        style={styles.contextLink}
                      >
                        {item.url}
                      </a>
                    </div>
                  )}
                  
                  {item.text && (
                    <div style={styles.contextDescription}>
                      {item.text.length > 300 ? `${item.text.substring(0, 300)}...` : item.text}
                    </div>
                  )}
                  
                  {item.article_id && (
                    <div style={styles.contextMetaRow}>
                      <strong style={{ color: '#ffffff' }}>Article ID:</strong> <code style={styles.contextCode}>{item.article_id}</code>
                    </div>
                  )}
                </div>
              );
            }
            
            // Entity context display (original format)
            return (
              <div key={item.id || index} style={styles.contextItem}>
                <div style={styles.contextItemHeader}>
                  <h4 style={styles.contextItemName}>{item.name || item.id || `Item ${index + 1}`}</h4>
                  {item.mention_count !== undefined && (
                    <span style={styles.contextBadge}>{item.mention_count} mentions</span>
                  )}
                </div>
                
                {item.description && (
                  <div style={styles.contextDescription}>{item.description}</div>
                )}
                
                {(item.url || (item.article_urls && item.article_urls.length > 0)) && (
                  <div style={styles.contextMetaRow}>
                    <strong style={{ color: '#ffffff' }}>Source {item.article_urls && item.article_urls.length > 1 ? 'Articles' : 'Article'}:</strong>
                    <div style={styles.contextUrls}>
                      {item.url ? (
                        <a 
                          href={item.url} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          style={styles.contextLink}
                        >
                          {item.url}
                        </a>
                      ) : null}
                      {item.article_urls && item.article_urls.length > 0 && (
                        <>
                          {item.article_urls.map((url: string, idx: number) => (
                            <a 
                              key={idx}
                              href={url} 
                              target="_blank" 
                              rel="noopener noreferrer"
                              style={styles.contextLink}
                            >
                              {url}
                            </a>
                          ))}
                        </>
                      )}
                    </div>
                  </div>
                )}
                
                <div style={styles.contextMeta}>
                  {item.investors && Array.isArray(item.investors) && item.investors.length > 0 && (
                    <div style={styles.contextMetaRow}>
                      <strong style={{ color: '#ffffff' }}>Investors:</strong>
                      <div style={styles.contextTags}>
                        {item.investors.map((investor: string, i: number) => (
                          <span key={i} style={styles.contextTag}>{investor}</span>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  {item.investor_count !== undefined && item.investor_count > 0 && (
                    <div style={styles.contextMetaRow}>
                      <strong style={{ color: '#ffffff' }}>Investor Count:</strong> {item.investor_count}
                    </div>
                  )}
                  
                  {item.latest_announcement && (
                    <div style={styles.contextMetaRow}>
                      <strong style={{ color: '#ffffff' }}>Latest Announcement:</strong>{' '}
                      {new Date(item.latest_announcement).toLocaleDateString('en-US', {
                        year: 'numeric',
                        month: 'short',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit'
                      })}
                    </div>
                  )}
                  
                  {item.id && (
                    <div style={styles.contextMetaRow}>
                      <strong style={{ color: '#ffffff' }}>ID:</strong> <code style={styles.contextCode}>{item.id}</code>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    );
  }
  
  // Handle object context
  if (typeof context === 'object' && context !== null) {
    return (
      <div style={styles.contextContainer}>
        <pre style={styles.jsonPre}>{JSON.stringify(context, null, 2)}</pre>
      </div>
    );
  }
  
  // Fallback to string display
  return (
    <div style={styles.contextContainer}>
      <pre style={styles.jsonPre}>{String(context)}</pre>
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
    gridTemplateColumns: '240px 2fr 290px',
    gap: 16,
    height: '100%',
    minHeight: 0,
    width: '100%',
    boxSizing: 'border-box',
    maxWidth: '100%',
    overflow: 'hidden'
  },
  historySidebar: {
    display: 'flex',
    flexDirection: 'column',
    overflow: 'hidden',
    background: '#1e293b',
    border: '1px solid rgba(51, 65, 85, 0.5)',
    borderRadius: 12,
    padding: 16,
    boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
    height: '96%',
    minHeight: 700
  },
  chatContainer: {
    display: 'grid',
    gridTemplateRows: '1fr auto',
    background: '#1e293b',
    border: '1px solid rgba(51, 65, 85, 0.5)',
    borderRadius: 12,
    overflow: 'hidden',
    height: '100%',
    minHeight: 700
  },
  messages: {
    padding: 16,
    overflowY: 'auto',
    background: '#1e293b',
    flex: 1,
    minHeight: 0
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
    background: 'rgba(59, 130, 246, 0.2)',
    border: '1px solid #93c5fd'
  },
  bubbleAssistant: {
    marginRight: 'auto',
    background: '#334155',
    border: '1px solid #cbd5e1'
  },
  bubbleSystem: {
    margin: '10px auto',
    background: 'rgba(245, 158, 11, 0.1)',
    border: '1px solid #fed7aa',
    textAlign: 'center'
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
    background: '#3b82f6',
    color: 'white',
    borderRadius: 999
  },
  intentTag: {
    fontSize: 12,
    padding: '2px 6px',
    background: '#475569',
    borderRadius: 999,
    color: '#ffffff'
  },
  typingIndicator: {
    fontSize: 10,
    color: '#ffffff',
    animation: 'pulse 1.5s ease-in-out infinite',
    marginLeft: 4
  },
  typewriterCursor: {
    display: 'inline-block',
    marginLeft: 2,
    color: '#ffffff',
    animation: 'blink 1s infinite',
    fontWeight: 'bold'
  },
  bubbleContent: {
    lineHeight: 1.55,
    color: '#ffffff'
  },
  composer: {
    background: '#1e293b',
    padding: 12
  },
  optionsBar: {
    display: 'flex',
    gap: 12,
    alignItems: 'center',
    marginBottom: 8,
    flexWrap: 'wrap'
  },
  checkbox: {
    display: 'flex',
    alignItems: 'center',
    gap: 6,
    cursor: 'pointer',
    fontSize: 13,
    color: '#ffffff'
  },
  templatesToggle: {
    padding: '4px 10px',
    borderRadius: 6,
    border: '1px solid rgba(71, 85, 105, 0.5)',
    background: '#1e293b',
    cursor: 'pointer',
    fontSize: 12,
    marginLeft: 'auto',
    color: '#ffffff'
  },
  inputRow: {
    display: 'flex',
    gap: 8
  },
  input: {
    flex: 1,
    borderRadius: 10,
    border: '1px solid rgba(71, 85, 105, 0.5)',
    padding: 10,
    fontSize: 14,
    background: '#334155',
    color: '#f1f5f9',
    fontFamily: 'inherit',
    resize: 'none'
  },
  sendButton: {
    padding: '10px 16px',
    borderRadius: 10,
    border: '1px solid #2563eb',
    background: '#3b82f6',
    color: 'white',
    cursor: 'pointer',
    fontWeight: 600,
    fontSize: 14,
    whiteSpace: 'nowrap'
  },
  templatesSidebar: {
    display: 'flex',
    flexDirection: 'column',
    gap: 16,
    overflowY: 'auto',
    height: '100%',
    minHeight: 700,
    maxHeight: 'calc(100vh - 140px)'
  },
  historyHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12
  },
  newChatButton: {
    padding: '4px 8px',
    borderRadius: 6,
    border: '1px solid rgba(71, 85, 105, 0.5)',
    background: '#1e293b',
    cursor: 'pointer',
    fontSize: 16,
    lineHeight: 1,
    transition: 'all 0.2s'
  },
  historyList: {
    display: 'flex',
    flexDirection: 'column',
    gap: 8,
    overflowY: 'auto',
    flex: 1,
    minHeight: 0
  },
  historyItem: {
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    padding: 10,
    borderRadius: 8,
    border: '1px solid rgba(51, 65, 85, 0.5)',
    background: '#1e293b',
    cursor: 'pointer',
    transition: 'all 0.2s',
    position: 'relative'
  },
  historyItemActive: {
    background: 'rgba(59, 130, 246, 0.2)',
    borderColor: '#3b82f6'
  },
  historyItemContent: {
    flex: 1,
    minWidth: 0
  },
  historyTitle: {
    fontSize: 13,
    fontWeight: 500,
    marginBottom: 4,
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    whiteSpace: 'nowrap',
    color: '#ffffff'
  },
  historyMeta: {
    fontSize: 11,
    opacity: 0.6,
    color: '#ffffff'
  },
  deleteButton: {
    padding: '2px 6px',
    borderRadius: 4,
    border: 'none',
    background: 'transparent',
    cursor: 'pointer',
    fontSize: 18,
    lineHeight: 1,
    opacity: 0.5,
    transition: 'opacity 0.2s',
    flexShrink: 0
  },
  emptyState: {
    fontSize: 13,
    opacity: 0.6,
    textAlign: 'center',
    padding: 20,
    fontStyle: 'italic',
    color: '#ffffff'
  },
  card: {
    background: '#1e293b',
    border: '1px solid rgba(51, 65, 85, 0.5)',
    borderRadius: 12,
    padding: 16,
    boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
    display: 'flex',
    flexDirection: 'column',
    height: '100%',
    overflow: 'hidden'
  },
  hint: {
    fontSize: 13,
    opacity: 0.7,
    margin: '0 0 12px',
    color: '#ffffff'
  },
  categoryFilter: {
    display: 'flex',
    gap: 6,
    flexWrap: 'wrap',
    marginBottom: 16
  },
  categoryButton: {
    padding: '6px 12px',
    borderRadius: 6,
    border: '1px solid rgba(51, 65, 85, 0.5)',
    background: '#1e293b',
    cursor: 'pointer',
    fontSize: 12,
    transition: 'all 0.2s',
    color: '#ffffff'
  },
  categoryButtonActive: {
    background: '#3b82f6',
    borderColor: '#0284c7',
    color: 'white'
  },
  templatesGrid: {
    display: 'flex',
    flexDirection: 'column',
    gap: 8,
    overflowY: 'auto',
    flex: 1,
    minHeight: 0,
    maxHeight: 'calc(100vh - 400px)'
  },
  templateCard: {
    padding: 10,
    borderRadius: 8,
    border: '1px solid rgba(51, 65, 85, 0.5)',
    background: '#1e293b',
    cursor: 'pointer',
    textAlign: 'left',
    transition: 'all 0.2s'
  },
  templateCategory: {
    fontSize: 11,
    color: '#ffffff',
    fontWeight: 600,
    marginBottom: 4
  },
  templateName: {
    fontSize: 13,
    fontWeight: 600,
    marginBottom: 4,
    color: '#ffffff'
  },
  templateQuestion: {
    fontSize: 12,
    opacity: 0.7,
    lineHeight: 1.4,
    color: '#ffffff'
  },
  detailsSummary: {
    cursor: 'pointer',
    fontWeight: 600,
    fontSize: 12,
    padding: 6,
    background: '#1e293b',
    borderRadius: 6,
    color: '#ffffff'
  },
  jsonPre: {
    background: '#0f172a',
    color: '#ffffff',
    padding: 12,
    borderRadius: 8,
    overflow: 'auto',
    fontSize: 11,
    marginTop: 8,
    maxHeight: 300
  },
  contextContainer: {
    background: '#1e293b',
    border: '1px solid rgba(51, 65, 85, 0.5)',
    borderRadius: 8,
    padding: 12,
    marginTop: 8,
    maxHeight: 400,
    overflowY: 'auto'
  },
  contextHeader: {
    fontSize: 13,
    fontWeight: 600,
    color: '#f1f5f9',
    marginBottom: 12,
    paddingBottom: 8,
    borderBottom: '1px solid rgba(51, 65, 85, 0.5)'
  },
  contextList: {
    display: 'flex',
    flexDirection: 'column',
    gap: 12
  },
  contextItem: {
    background: '#1e293b',
    border: '1px solid rgba(51, 65, 85, 0.5)',
    borderRadius: 8,
    padding: 12,
    transition: 'all 0.2s'
  },
  contextItemHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8
  },
  contextItemName: {
    margin: 0,
    fontSize: 15,
    fontWeight: 600,
    color: '#f1f5f9'
  },
  contextBadge: {
    fontSize: 11,
    padding: '4px 8px',
    background: 'rgba(59, 130, 246, 0.2)',
    color: '#ffffff',
    borderRadius: 4,
    fontWeight: 500
  },
  contextDescription: {
    fontSize: 13,
    lineHeight: 1.6,
    color: '#ffffff',
    marginBottom: 10,
    padding: 8,
    background: '#1e293b',
    borderRadius: 6
  },
  contextMeta: {
    display: 'flex',
    flexDirection: 'column',
    gap: 6,
    fontSize: 12,
    color: '#ffffff'
  },
  contextMetaRow: {
    display: 'flex',
    flexDirection: 'column',
    gap: 6,
    lineHeight: 1.5
  },
  contextTags: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: 4,
    flex: 1
  },
  contextTag: {
    fontSize: 11,
    padding: '3px 8px',
    background: '#475569',
    color: '#ffffff',
    borderRadius: 4,
    whiteSpace: 'nowrap'
  },
  contextCode: {
    fontSize: 11,
    padding: '2px 6px',
    background: '#334155',
    color: '#f1f5f9',
    borderRadius: 4,
    fontFamily: 'monospace'
  },
  contextUrls: {
    display: 'flex',
    flexDirection: 'column',
    gap: 6,
    marginTop: 4
  },
  contextLink: {
    color: '#ffffff',
    textDecoration: 'none',
    fontSize: 12,
    wordBreak: 'break-all',
    transition: 'all 0.2s',
    lineHeight: 1.4
  },
  contextEmpty: {
    padding: 16,
    textAlign: 'center',
    color: '#ffffff',
    fontSize: 13
  },
  tipsList: {
    margin: 0,
    paddingLeft: 20,
    fontSize: 13,
    lineHeight: 2,
    color: '#ffffff'
  },
  loadingContainer: {
    display: 'flex',
    alignItems: 'center',
    gap: 12,
    padding: '8px 0'
  },
  loadingSpinner: {
    display: 'flex',
    gap: 4
  },
  spinnerDot: {
    width: 8,
    height: 8,
    borderRadius: '50%',
    background: '#3b82f6',
    animation: 'bounce 1.4s ease-in-out infinite both'
  },
  loadingText: {
    color: '#ffffff',
    fontSize: 14,
    fontStyle: 'italic'
  }
};

