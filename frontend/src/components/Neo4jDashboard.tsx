import { useEffect, useState } from 'react';
import { fetchNeo4jOverview, Neo4jOverview } from '../lib/api';

export function Neo4jDashboard() {
  const [data, setData] = useState<Neo4jOverview | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const res = await fetchNeo4jOverview();
      setData(res);
    } catch (e: any) {
      setError(e?.message || 'Failed to load Neo4j overview');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    const t = setInterval(load, 15000);
    return () => clearInterval(t);
  }, []);

  return (
    <div style={{ display: 'grid', gap: 16 }}>
      <div style={styles.headerRow}>
        <h3 style={{ margin: 0 }}>Neo4j / AuraDB Overview</h3>
        <button onClick={load} style={styles.refreshButton} disabled={loading}>
          {loading ? 'Refreshing…' : 'Refresh'}
        </button>
      </div>

      {error && (
        <section style={styles.errorCard}>
          <strong>⚠️ Error:</strong> {error}
        </section>
      )}

      {!error && (
        <>
          <section style={styles.card}>
            <h4 style={styles.h4}>Database Info</h4>
            {data?.db_info?.components?.length ? (
              <ul style={styles.list}>
                {data.db_info.components.map((c, i) => (
                  <li key={i}>
                    <strong>{c.name || 'Neo4j'}</strong>{' '}
                    {c.versions && c.versions.length ? `v${c.versions[0]}` : ''}{' '}
                    {c.edition ? `(${c.edition})` : ''}
                  </li>
                ))}
              </ul>
            ) : (
              <p style={styles.muted}>Component info not available.</p>
            )}
          </section>

          <section style={styles.cardRow}>
            <div style={styles.card}>
              <h4 style={styles.h4}>Node Counts</h4>
              <table style={styles.table}>
                <thead>
                  <tr><th style={styles.th}>Label</th><th style={styles.th}>Count</th></tr>
                </thead>
                <tbody>
                  {data?.graph_stats?.node_counts?.map((n, idx) => (
                    <tr key={idx}><td style={styles.td}>{n.label}</td><td style={styles.tdRight}>{n.count}</td></tr>
                  )) || null}
                </tbody>
              </table>
              <div style={styles.smallMuted}>Communities: {data?.graph_stats?.community_count ?? 0}</div>
            </div>
            <div style={styles.card}>
              <h4 style={styles.h4}>Relationship Counts</h4>
              <table style={styles.table}>
                <thead>
                  <tr><th style={styles.th}>Type</th><th style={styles.th}>Count</th></tr>
                </thead>
                <tbody>
                  {data?.graph_stats?.relationship_counts?.map((r, idx) => (
                    <tr key={idx}><td style={styles.td}>{r.type}</td><td style={styles.tdRight}>{r.count}</td></tr>
                  )) || null}
                </tbody>
              </table>
            </div>
          </section>

          <section style={styles.cardRow}>
            <div style={styles.card}>
              <h4 style={styles.h4}>Top Connected Entities</h4>
              <table style={styles.table}>
                <thead>
                  <tr><th style={styles.th}>Name</th><th style={styles.th}>Type</th><th style={styles.thRight}>Degree</th></tr>
                </thead>
                <tbody>
                  {data?.top_connected_entities?.map((e, idx) => (
                    <tr key={idx}>
                      <td style={styles.td}>{e.name}</td>
                      <td style={styles.td}>{e.type}</td>
                      <td style={styles.tdRight}>{(e as any).degree}</td>
                    </tr>
                  )) || null}
                </tbody>
              </table>
            </div>
            <div style={styles.card}>
              <h4 style={styles.h4}>Top Important Entities</h4>
              <table style={styles.table}>
                <thead>
                  <tr><th style={styles.th}>Name</th><th style={styles.th}>Type</th><th style={styles.thRight}>Score</th></tr>
                </thead>
                <tbody>
                  {data?.top_important_entities?.map((e, idx) => (
                    <tr key={idx}>
                      <td style={styles.td}>{e.name}</td>
                      <td style={styles.td}>{e.type}</td>
                      <td style={styles.tdRight}>{(e as any).importance_score}</td>
                    </tr>
                  )) || null}
                </tbody>
              </table>
            </div>
          </section>

          <section style={styles.card}>
            <h4 style={styles.h4}>Schema Summary</h4>
            <div style={styles.schemaRow}>
              <div>
                <div style={styles.smallLabel}>Labels</div>
                <div style={styles.badgeRow}>
                  {data?.labels?.map((l, i) => <span key={i} style={styles.badge}>{l}</span>) || <span style={styles.muted}>N/A</span>}
                </div>
              </div>
              <div>
                <div style={styles.smallLabel}>Relationship Types</div>
                <div style={styles.badgeRow}>
                  {data?.relationship_types?.map((t, i) => <span key={i} style={styles.badge}>{t}</span>) || <span style={styles.muted}>N/A</span>}
                </div>
              </div>
            </div>
          </section>
        </>
      )}
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  headerRow: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center'
  },
  refreshButton: {
    padding: '6px 12px',
    borderRadius: 6,
    border: '1px solid #cbd5e1',
    background: '#f8fafc',
    cursor: 'pointer'
  },
  card: {
    background: 'white',
    border: '1px solid #e2e8f0',
    borderRadius: 12,
    padding: 16,
    boxShadow: '0 1px 2px rgba(0,0,0,0.03)'
  },
  cardRow: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: 16
  },
  h4: { margin: '0 0 10px 0' },
  list: { margin: 0, paddingLeft: 18 },
  muted: { opacity: 0.7 },
  smallMuted: { opacity: 0.7, fontSize: 12, marginTop: 8 },
  table: { width: '100%', borderCollapse: 'collapse' },
  th: { textAlign: 'left', borderBottom: '1px solid #e2e8f0', padding: '6px 4px' },
  thRight: { textAlign: 'right', borderBottom: '1px solid #e2e8f0', padding: '6px 4px' },
  td: { padding: '6px 4px', borderBottom: '1px solid #f1f5f9' },
  tdRight: { padding: '6px 4px', borderBottom: '1px solid #f1f5f9', textAlign: 'right' },
  schemaRow: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 },
  smallLabel: { fontSize: 12, opacity: 0.7, marginBottom: 6 },
  badgeRow: { display: 'flex', gap: 6, flexWrap: 'wrap' },
  badge: {
    display: 'inline-block',
    padding: '4px 8px',
    borderRadius: 999,
    background: '#eef2ff',
    color: '#3730a3',
    fontSize: 12,
    border: '1px solid #c7d2fe'
  },
  errorCard: {
    background: '#fef2f2',
    border: '1px solid #fecaca',
    borderRadius: 12,
    padding: 16,
    color: '#991b1b'
  }
};


