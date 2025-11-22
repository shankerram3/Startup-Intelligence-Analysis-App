import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { postJson, QueryRequest, QueryResponse } from '../lib/api';
import { useTypewriter } from '../hooks/useTypewriter';

type QueryTemplate = {
  name: string;
  question: string;
  category: string;
};

type QueryHistory = {
  id: string;
  question: string;
  answer: string;
  timestamp: Date;
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

export function EnhancedQueryView() {
  const [question, setQuestion] = useState('Which AI startups raised funding recently?');
  const [returnContext, setReturnContext] = useState(false);
  const [useLlm, setUseLlm] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<QueryResponse | null>(null);
  const [history, setHistory] = useState<QueryHistory[]>([]);
  const [showTemplates, setShowTemplates] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState<string>('All');

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const body: QueryRequest = {
        question,
        return_context: returnContext,
        use_llm: useLlm
      };
      const res = await postJson<QueryRequest, QueryResponse>('/query', body);
      setResult(res);

      // Add to history
      if (res.answer) {
        setHistory(prev => [{
          id: Date.now().toString(),
          question,
          answer: res.answer || '',
          timestamp: new Date()
        }, ...prev].slice(0, 10)); // Keep last 10
      }
    } catch (err: any) {
      // Parse error message from API response
      let errorMessage = 'Request failed';
      if (err?.message) {
        errorMessage = err.message;
        // Try to parse JSON error response
        try {
          const parsed = JSON.parse(err.message);
          if (parsed.detail) {
            errorMessage = parsed.detail;
          }
        } catch {
          // Not JSON, use message as-is
        }
      }
      setError(errorMessage);
      setResult(null);
    } finally {
      setLoading(false);
    }
  }

  function useTemplate(template: QueryTemplate) {
    setQuestion(template.question);
    setShowTemplates(false);
  }

  function useHistoryItem(item: QueryHistory) {
    setQuestion(item.question);
  }

  const categories = ['All', ...Array.from(new Set(QUERY_TEMPLATES.map(t => t.category)))];
  const filteredTemplates = selectedCategory === 'All'
    ? QUERY_TEMPLATES
    : QUERY_TEMPLATES.filter(t => t.category === selectedCategory);

  return (
    <div style={styles.root}>
      <div style={styles.mainContent}>
        {/* Query Form */}
        <section style={styles.card}>
          <h3 style={{ marginTop: 0 }}>Ask a Question</h3>
          <form onSubmit={onSubmit}>
            <div style={styles.formGroup}>
              <label style={styles.label}>Your Question</label>
              <textarea
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="Ask anything about companies, investors, people, or technologies..."
                rows={3}
                style={styles.textarea}
                required
              />
            </div>

            <div style={styles.optionsRow}>
              <label style={styles.checkbox}>
                <input type="checkbox" checked={returnContext} onChange={(e) => setReturnContext(e.target.checked)} />
                <span>Show context data</span>
              </label>
              <label style={styles.checkbox}>
                <input type="checkbox" checked={useLlm} onChange={(e) => setUseLlm(e.target.checked)} />
                <span>Use LLM (better answers)</span>
              </label>
              <button
                type="button"
                onClick={() => setShowTemplates(!showTemplates)}
                style={styles.toggleButton}
              >
                {showTemplates ? '🔽 Hide Templates' : '▶ Show Templates'}
              </button>
            </div>

            <button type="submit" style={styles.submitButton} disabled={loading}>
              {loading ? '⏳ Querying...' : '🔍 Search Knowledge Graph'}
            </button>
          </form>
        </section>

        {/* Query Templates */}
        {showTemplates && (
          <section style={styles.card}>
            <h3 style={{ marginTop: 0 }}>📋 Query Templates</h3>
            <p style={styles.hint}>Click any template to use it as a starting point</p>

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
        )}

        {/* Error Display */}
        {error && (
          <section style={styles.errorCard}>
            <div style={styles.errorHeader}>
              <div style={styles.errorTitle}>
                <span style={styles.errorIcon}>⚠️</span>
                <strong>Query Failed</strong>
              </div>
              <button
                onClick={() => setError(null)}
                style={styles.errorDismiss}
                aria-label="Dismiss error"
              >
                ×
              </button>
            </div>
            <div style={styles.errorMessage}>{error}</div>
            <div style={styles.errorActions}>
              <button
                onClick={() => {
                  setError(null);
                  onSubmit({ preventDefault: () => {} } as React.FormEvent);
                }}
                style={styles.retryButton}
              >
                🔄 Retry Query
              </button>
            </div>
          </section>
        )}

        {/* Results Display */}
        {result && (
          <section style={styles.resultCard}>
            <div style={styles.resultHeader}>
              <h3 style={{ margin: 0 }}>✅ Answer</h3>
              {result.intent?.intent ? (
                <span style={styles.intentBadge}>
                  Intent: {String(result.intent.intent)}
                </span>
              ) : null}
            </div>

            <AnswerDisplay answer={result.answer} />

            {/* Intent Details */}
            <details style={{ marginTop: 16 }}>
              <summary style={styles.detailsSummary}>🎯 Query Intent & Routing</summary>
              <pre style={styles.jsonPre}>{JSON.stringify(result.intent, null, 2)}</pre>
            </details>

            {/* Context Data */}
            {typeof result.context !== 'undefined' && (
              <details style={{ marginTop: 12 }}>
                <summary style={styles.detailsSummary}>📊 Retrieved Context Data</summary>
                <pre style={styles.jsonPre}>{JSON.stringify(result.context, null, 2)}</pre>
              </details>
            )}
          </section>
        )}
      </div>

      {/* Sidebar: Query History */}
      <aside style={styles.sidebar}>
        <section style={styles.card}>
          <h3 style={{ marginTop: 0 }}>📜 Query History</h3>
          {history.length === 0 ? (
            <p style={styles.emptyState}>No queries yet. Try asking a question!</p>
          ) : (
            <div style={styles.historyList}>
              {history.map(item => (
                <button
                  key={item.id}
                  onClick={() => useHistoryItem(item)}
                  style={styles.historyItem}
                >
                  <div style={styles.historyQuestion}>{item.question}</div>
                  <div style={styles.historyMeta}>
                    {item.timestamp.toLocaleTimeString()}
                  </div>
                </button>
              ))}
            </div>
          )}
        </section>

        {/* Tips */}
        <section style={styles.card}>
          <h3 style={{ marginTop: 0 }}>💡 Query Tips</h3>
          <ul style={styles.tipsList}>
            <li>Be specific with company names</li>
            <li>Use time references (e.g., "recently", "in 2023")</li>
            <li>Ask about relationships (e.g., "funded by", "founded by")</li>
            <li>Filter by location, technology, or funding stage</li>
            <li>Combine multiple criteria in one query</li>
          </ul>
        </section>

        {/* Stats */}
        <section style={styles.card}>
          <h3 style={{ marginTop: 0 }}>📊 Query Stats</h3>
          <div style={styles.statItem}>
            <span style={styles.statLabel}>Total Queries:</span>
            <span style={styles.statValue}>{history.length}</span>
          </div>
          <div style={styles.statItem}>
            <span style={styles.statLabel}>Using LLM:</span>
            <span style={styles.statValue}>{useLlm ? 'Yes ✓' : 'No'}</span>
          </div>
          <div style={styles.statItem}>
            <span style={styles.statLabel}>Show Context:</span>
            <span style={styles.statValue}>{returnContext ? 'Yes ✓' : 'No'}</span>
          </div>
        </section>
      </aside>
    </div>
  );
}

function AnswerDisplay({ answer }: { answer: string | null | undefined }) {
  const { displayedText, isTyping } = useTypewriter(answer || '', { enabled: !!answer });

  if (!answer) {
    return <div style={styles.answerBox}>No answer returned.</div>;
  }

  return (
    <div style={styles.answerBox}>
      <ReactMarkdown
        components={{
          p: ({ children }) => <p style={{ margin: '0 0 12px 0' }}>{children}</p>,
          strong: ({ children }) => <strong style={{ fontWeight: 600 }}>{children}</strong>,
          ul: ({ children }) => <ul style={{ margin: '8px 0', paddingLeft: '20px' }}>{children}</ul>,
          ol: ({ children }) => <ol style={{ margin: '8px 0', paddingLeft: '20px' }}>{children}</ol>,
          li: ({ children }) => <li style={{ margin: '4px 0' }}>{children}</li>
        }}
      >
        {displayedText}
      </ReactMarkdown>
      {isTyping && <span style={styles.typewriterCursor}>▊</span>}
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  root: {
    display: 'grid',
    gridTemplateColumns: '1fr 320px',
    gap: 16
  },
  mainContent: {
    display: 'flex',
    flexDirection: 'column',
    gap: 16
  },
  sidebar: {
    display: 'flex',
    flexDirection: 'column',
    gap: 16
  },
  card: {
    background: 'white',
    border: '1px solid #e2e8f0',
    borderRadius: 12,
    padding: 16,
    boxShadow: '0 1px 3px rgba(0,0,0,0.05)'
  },
  formGroup: {
    display: 'flex',
    flexDirection: 'column',
    gap: 6,
    marginBottom: 12
  },
  label: {
    fontWeight: 600,
    fontSize: 14
  },
  textarea: {
    borderRadius: 8,
    border: '1px solid #cbd5e1',
    padding: 12,
    fontSize: 14,
    fontFamily: 'inherit',
    resize: 'vertical',
    lineHeight: 1.5
  },
  optionsRow: {
    display: 'flex',
    gap: 16,
    alignItems: 'center',
    marginBottom: 12,
    flexWrap: 'wrap'
  },
  checkbox: {
    display: 'flex',
    alignItems: 'center',
    gap: 6,
    cursor: 'pointer',
    fontSize: 14
  },
  toggleButton: {
    padding: '6px 12px',
    borderRadius: 6,
    border: '1px solid #cbd5e1',
    background: '#f8fafc',
    cursor: 'pointer',
    fontSize: 13,
    marginLeft: 'auto'
  },
  submitButton: {
    width: '100%',
    padding: '12px 20px',
    borderRadius: 8,
    border: '1px solid #0284c7',
    background: '#0ea5e9',
    color: 'white',
    cursor: 'pointer',
    fontSize: 15,
    fontWeight: 600,
    transition: 'all 0.2s'
  },
  hint: {
    fontSize: 13,
    opacity: 0.7,
    margin: '0 0 12px'
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
    border: '1px solid #e2e8f0',
    background: '#f8fafc',
    cursor: 'pointer',
    fontSize: 12,
    transition: 'all 0.2s'
  },
  categoryButtonActive: {
    background: '#0ea5e9',
    borderColor: '#0284c7',
    color: 'white'
  },
  templatesGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))',
    gap: 12
  },
  templateCard: {
    padding: 12,
    borderRadius: 8,
    border: '1px solid #e2e8f0',
    background: '#f8fafc',
    cursor: 'pointer',
    textAlign: 'left',
    transition: 'all 0.2s'
  },
  templateCategory: {
    fontSize: 11,
    color: '#0ea5e9',
    fontWeight: 600,
    marginBottom: 4
  },
  templateName: {
    fontSize: 14,
    fontWeight: 600,
    marginBottom: 4
  },
  templateQuestion: {
    fontSize: 12,
    opacity: 0.7,
    lineHeight: 1.4
  },
  errorCard: {
    background: '#fef2f2',
    border: '2px solid #f87171',
    borderRadius: 12,
    padding: 16,
    color: '#991b1b',
    boxShadow: '0 4px 6px rgba(239, 68, 68, 0.1)',
    animation: 'slideIn 0.3s ease-out'
  },
  errorHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12
  },
  errorTitle: {
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    fontSize: 16,
    fontWeight: 600
  },
  errorIcon: {
    fontSize: 20
  },
  errorDismiss: {
    background: 'transparent',
    border: 'none',
    fontSize: 24,
    color: '#991b1b',
    cursor: 'pointer',
    padding: '0 8px',
    lineHeight: 1,
    opacity: 0.7,
    transition: 'opacity 0.2s'
  },
  errorMessage: {
    background: '#fee2e2',
    border: '1px solid #fecaca',
    borderRadius: 8,
    padding: 12,
    marginBottom: 12,
    fontSize: 14,
    lineHeight: 1.6,
    whiteSpace: 'pre-wrap',
    wordBreak: 'break-word'
  },
  errorActions: {
    display: 'flex',
    gap: 8,
    justifyContent: 'flex-end'
  },
  retryButton: {
    padding: '8px 16px',
    borderRadius: 6,
    border: '1px solid #dc2626',
    background: '#ef4444',
    color: 'white',
    cursor: 'pointer',
    fontSize: 14,
    fontWeight: 500,
    transition: 'all 0.2s'
  },
  resultCard: {
    background: 'white',
    border: '1px solid #10b981',
    borderRadius: 12,
    padding: 16,
    boxShadow: '0 4px 6px rgba(16, 185, 129, 0.1)'
  },
  resultHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12
  },
  intentBadge: {
    padding: '4px 12px',
    borderRadius: 6,
    background: '#dbeafe',
    color: '#1e40af',
    fontSize: 12,
    fontWeight: 600
  },
  answerBox: {
    background: '#f0fdf4',
    border: '1px solid #bbf7d0',
    borderRadius: 8,
    padding: 16,
    fontSize: 15,
    lineHeight: 1.7,
    position: 'relative'
  },
  typewriterCursor: {
    display: 'inline-block',
    marginLeft: 2,
    color: '#10b981',
    animation: 'blink 1s infinite',
    fontWeight: 'bold'
  },
  detailsSummary: {
    cursor: 'pointer',
    fontWeight: 600,
    fontSize: 14,
    padding: 8,
    background: '#f8fafc',
    borderRadius: 6
  },
  jsonPre: {
    background: '#0f172a',
    color: '#e2e8f0',
    padding: 12,
    borderRadius: 8,
    overflow: 'auto',
    fontSize: 12,
    marginTop: 8
  },
  historyList: {
    display: 'flex',
    flexDirection: 'column',
    gap: 8
  },
  historyItem: {
    padding: 10,
    borderRadius: 6,
    border: '1px solid #e2e8f0',
    background: '#f8fafc',
    cursor: 'pointer',
    textAlign: 'left',
    transition: 'all 0.2s'
  },
  historyQuestion: {
    fontSize: 13,
    marginBottom: 4,
    lineHeight: 1.4
  },
  historyMeta: {
    fontSize: 11,
    opacity: 0.6
  },
  emptyState: {
    fontSize: 13,
    opacity: 0.6,
    textAlign: 'center',
    padding: 20
  },
  tipsList: {
    margin: 0,
    paddingLeft: 20,
    fontSize: 13,
    lineHeight: 2
  },
  statItem: {
    display: 'flex',
    justifyContent: 'space-between',
    padding: '8px 0',
    borderBottom: '1px solid #e2e8f0',
    fontSize: 13
  },
  statLabel: {
    opacity: 0.7
  },
  statValue: {
    fontWeight: 600
  }
};
