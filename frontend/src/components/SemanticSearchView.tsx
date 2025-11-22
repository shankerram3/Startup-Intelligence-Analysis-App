import { useState } from 'react';
import { postJson, SemanticSearchRequest, SemanticSearchResponse } from '../lib/api';

export function SemanticSearchView() {
  const [query, setQuery] = useState('artificial intelligence');
  const [topK, setTopK] = useState(10);
  const [entityType, setEntityType] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<SemanticSearchResponse | null>(null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setData(null);
    try {
      const body: SemanticSearchRequest = {
        query,
        top_k: topK,
        entity_type: entityType || undefined
      };
      const res = await postJson<SemanticSearchRequest, SemanticSearchResponse>('/search/semantic', body);
      setData(res);
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
          <label style={styles.label}>Query</label>
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search..."
            style={styles.input}
            required
          />

          <div style={styles.row}>
            <div>
              <label style={styles.label}>Top K</label>
              <input
                type="number"
                min={1}
                max={50}
                value={topK}
                onChange={(e) => setTopK(Number(e.target.value))}
                style={styles.input}
              />
            </div>

            <div>
              <label style={styles.label}>Entity Type (optional)</label>
              <input
                value={entityType}
                onChange={(e) => setEntityType(e.target.value)}
                placeholder="Company, Person, Investor..."
                style={styles.input}
              />
            </div>
          </div>

          <button type="submit" style={styles.primaryButton} disabled={loading}>
            {loading ? 'Searching...' : 'Search'}
          </button>
        </form>
      </section>

      {error && (
        <section style={{ ...styles.card, borderColor: '#fecaca', background: '#fef2f2' }}>
          <strong style={{ color: '#b91c1c' }}>Error:</strong> {error}
        </section>
      )}

      {data && (
        <section style={styles.card}>
          <h3 style={{ marginTop: 0 }}>Results ({data.count})</h3>
          {data.results.length === 0 ? (
            <p>No results.</p>
          ) : (
            <ol style={{ paddingLeft: 18 }}>
              {data.results.map((item, idx) => (
                <li key={idx} style={{ marginBottom: 12 }}>
                  <pre style={styles.pre}>{JSON.stringify(item, null, 2)}</pre>
                </li>
              ))}
            </ol>
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
  input: {
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
    alignItems: 'flex-start',
    margin: '10px 0'
  },
  primaryButton: {
    padding: '8px 12px',
    borderRadius: 8,
    border: '1px solid #0284c7',
    background: '#0ea5e9',
    color: 'white',
    cursor: 'pointer'
  },
  pre: {
    background: '#0b1220',
    color: '#e2e8f0',
    padding: 12,
    borderRadius: 8,
    overflowX: 'auto'
  }
};


