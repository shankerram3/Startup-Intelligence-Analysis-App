import { useState } from 'react';
import { postJson, QueryRequest, QueryResponse } from '../lib/api';

export function QueryView() {
  const [question, setQuestion] = useState('Which AI startups raised funding recently?');
  const [returnContext, setReturnContext] = useState(false);
  const [useLlm, setUseLlm] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<QueryResponse | null>(null);

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
    } catch (err: any) {
      setError(err?.message || 'Request failed');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <section style={styles.card}>
        <form onSubmit={onSubmit}>
          <label style={styles.label}>Question</label>
          <textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Ask a question..."
            rows={3}
            style={styles.textarea}
            required
          />

          <div style={styles.row}>
            <label style={styles.checkboxLabel}>
              <input type="checkbox" checked={returnContext} onChange={(e) => setReturnContext(e.target.checked)} />
              Return context
            </label>
            <label style={styles.checkboxLabel}>
              <input type="checkbox" checked={useLlm} onChange={(e) => setUseLlm(e.target.checked)} />
              Use LLM
            </label>
          </div>

          <button type="submit" style={styles.primaryButton} disabled={loading}>
            {loading ? 'Running...' : 'Run Query'}
          </button>
        </form>
      </section>

      {error && (
        <section style={{ ...styles.card, borderColor: '#fecaca', background: '#fef2f2' }}>
          <strong style={{ color: '#b91c1c' }}>Error:</strong> {error}
        </section>
      )}

      {result && (
        <section style={styles.card}>
          <h3 style={{ marginTop: 0 }}>Answer</h3>
          <p style={{ whiteSpace: 'pre-wrap', lineHeight: 1.6 }}>{result.answer ?? 'No answer returned.'}</p>

          <details style={{ marginTop: 16 }}>
            <summary style={styles.summary}>Intent</summary>
            <pre style={styles.pre}>{JSON.stringify(result.intent, null, 2)}</pre>
          </details>

          {typeof result.context !== 'undefined' && (
            <details style={{ marginTop: 12 }}>
              <summary style={styles.summary}>Context</summary>
              <pre style={styles.pre}>{JSON.stringify(result.context, null, 2)}</pre>
            </details>
          )}
        </section>
      )}
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  card: {
    background: 'white',
    border: '1px solid #e2e8f0',
    borderRadius: 12,
    padding: 16,
    boxShadow: '0 1px 2px rgba(0,0,0,0.03)',
    marginBottom: 16
  },
  label: {
    display: 'block',
    fontWeight: 600,
    marginBottom: 6
  },
  textarea: {
    width: '100%',
    borderRadius: 8,
    border: '1px solid #cbd5e1',
    padding: 10,
    fontSize: 14,
    background: '#f8fafc'
  },
  row: {
    display: 'flex',
    gap: 16,
    alignItems: 'center',
    marginTop: 10,
    marginBottom: 10
  },
  checkboxLabel: {
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    cursor: 'pointer'
  },
  primaryButton: {
    padding: '8px 12px',
    borderRadius: 8,
    border: '1px solid #0284c7',
    background: '#0ea5e9',
    color: 'white',
    cursor: 'pointer'
  },
  summary: {
    cursor: 'pointer',
    fontWeight: 600
  },
  pre: {
    background: '#0b1220',
    color: '#e2e8f0',
    padding: 12,
    borderRadius: 8,
    overflowX: 'auto'
  }
};


