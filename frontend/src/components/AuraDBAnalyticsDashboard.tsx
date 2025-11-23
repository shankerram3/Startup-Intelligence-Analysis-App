import { useEffect, useState } from 'react';
import {
  fetchNeo4jOverview,
  fetchAuraCommunities,
  fetchAuraCommunityStats,
  runAuraCommunityDetection,
  fetchAuraAnalytics,
  AuraCommunityDetectionRequest,
  AuraCommunityDetectionResponse,
  AuraCommunitiesResponse,
  AuraCommunityStats,
  AuraAnalyticsResponse
} from '../lib/api';
import { CommunityVisualization } from './CommunityVisualization';

export function AuraDBAnalyticsDashboard() {
  const [overview, setOverview] = useState<any>(null);
  const [communities, setCommunities] = useState<any[]>([]);
  const [communityStats, setCommunityStats] = useState<AuraCommunityStats | null>(null);
  const [analytics, setAnalytics] = useState<AuraAnalyticsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [detecting, setDetecting] = useState(false);
  const [detectionParams, setDetectionParams] = useState({
    algorithm: 'leiden',
    min_community_size: 3,
    graph_name: 'entity-graph'
  });

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const [overviewData, communitiesData, statsData, analyticsData] = await Promise.all([
        fetchNeo4jOverview().catch(() => null),
        fetchAuraCommunities(3, 50).catch(() => ({ communities: [], count: 0 })),
        fetchAuraCommunityStats().catch(() => null),
        fetchAuraAnalytics().catch(() => null)
      ]);
      
      setOverview(overviewData);
      setCommunities(communitiesData.communities || []);
      setCommunityStats(statsData);
      setAnalytics(analyticsData);
    } catch (e: any) {
      setError(e?.message || 'Failed to load analytics data');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    const t = setInterval(load, 30000); // Refresh every 30 seconds
    return () => clearInterval(t);
  }, []);

  async function handleCommunityDetection() {
    if (detecting) return;
    setDetecting(true);
    setError(null);
    try {
      const result = await runAuraCommunityDetection(detectionParams);
      // Reload data after detection
      await load();
      alert(`Community detection completed! Found ${result.total_communities} communities.`);
    } catch (e: any) {
      setError(e?.message || 'Failed to run community detection');
    } finally {
      setDetecting(false);
    }
  }

  return (
    <div style={{ display: 'grid', gap: 16, minHeight: 0 }}>
      <style>{`
        button[data-refresh-btn]:hover:not(:disabled) {
          background: rgba(59, 130, 246, 0.3) !important;
          border-color: rgba(59, 130, 246, 0.5) !important;
          transform: translateY(-1px);
        }
        button[data-detect-btn]:hover:not(:disabled) {
          background: linear-gradient(135deg, rgba(59, 130, 246, 0.4) 0%, rgba(37, 99, 235, 0.3) 100%) !important;
          box-shadow: 0 0 30px rgba(59, 130, 246, 0.4) !important;
          transform: translateY(-1px);
        }
        button[data-detect-btn]:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }
      `}</style>
      <div style={styles.headerRow}>
        <h3 style={{ margin: 0, color: '#e2e8f0' }}>AuraDB Analytics Dashboard</h3>
        <button onClick={load} data-refresh-btn style={styles.refreshButton} disabled={loading}>
          {loading ? 'Refreshing…' : '🔄 Refresh'}
        </button>
      </div>

      {error && (
        <section style={styles.errorCard}>
          <strong>⚠️ Error:</strong> {error}
        </section>
      )}

      {!error && (
        <>
          {/* Community Detection Controls */}
          <section style={styles.card}>
            <h4 style={styles.h4}>Community Detection (Aura Graph Analytics)</h4>
            <div style={styles.controlsGrid}>
              <div>
                <label style={styles.label}>Algorithm</label>
                <select
                  value={detectionParams.algorithm}
                  onChange={(e) => setDetectionParams({ ...detectionParams, algorithm: e.target.value })}
                  style={styles.select}
                >
                  <option value="leiden">Leiden</option>
                  <option value="louvain">Louvain</option>
                  <option value="label_propagation">Label Propagation</option>
                </select>
              </div>
              <div>
                <label style={styles.label}>Min Community Size</label>
                <input
                  type="number"
                  min={1}
                  max={100}
                  value={detectionParams.min_community_size}
                  onChange={(e) => setDetectionParams({ ...detectionParams, min_community_size: parseInt(e.target.value) || 3 })}
                  style={styles.input}
                />
              </div>
              <div>
                <label style={styles.label}>Graph Name</label>
                <input
                  type="text"
                  value={detectionParams.graph_name}
                  onChange={(e) => setDetectionParams({ ...detectionParams, graph_name: e.target.value })}
                  style={styles.input}
                />
              </div>
            </div>
            <button
              onClick={handleCommunityDetection}
              data-detect-btn
              style={styles.detectButton}
              disabled={detecting}
            >
              {detecting ? 'Running Detection...' : '🔍 Run Community Detection'}
            </button>
            {detecting && (
              <div style={styles.progressNote}>
                This may take a few minutes. The algorithm is running on Aura Graph Analytics...
              </div>
            )}
          </section>

          {/* Community Statistics */}
          {communityStats && (
            <section style={styles.cardRow}>
              <div style={styles.card}>
                <h4 style={styles.h4}>Community Statistics</h4>
                <div style={styles.statsGrid}>
                  <div style={styles.statItem}>
                    <div style={styles.statValue}>{communityStats.total_communities}</div>
                    <div style={styles.statLabel}>Total Communities</div>
                  </div>
                  <div style={styles.statItem}>
                    <div style={styles.statValue}>{communityStats.entities_in_communities}</div>
                    <div style={styles.statLabel}>Entities in Communities</div>
                  </div>
                  <div style={styles.statItem}>
                    <div style={styles.statValue}>{communityStats.coverage_percentage}%</div>
                    <div style={styles.statLabel}>Coverage</div>
                  </div>
                </div>
                {communityStats.size_distribution && (
                  <div style={styles.distribution}>
                    <div style={styles.distRow}>
                      <span>Min Size:</span>
                      <strong>{communityStats.size_distribution.min}</strong>
                    </div>
                    <div style={styles.distRow}>
                      <span>Max Size:</span>
                      <strong>{communityStats.size_distribution.max}</strong>
                    </div>
                    <div style={styles.distRow}>
                      <span>Avg Size:</span>
                      <strong>{communityStats.size_distribution.avg}</strong>
                    </div>
                    <div style={styles.distRow}>
                      <span>Median Size:</span>
                      <strong>{communityStats.size_distribution.median}</strong>
                    </div>
                  </div>
                )}
              </div>

              {/* Graph Overview */}
              {overview && (
                <div style={styles.card}>
                  <h4 style={styles.h4}>Graph Overview</h4>
                  <div style={styles.statsGrid}>
                    <div style={styles.statItem}>
                      <div style={styles.statValue}>
                        {overview.graph_stats?.node_counts?.reduce((sum: number, n: any) => sum + n.count, 0) || 0}
                      </div>
                      <div style={styles.statLabel}>Total Nodes</div>
                    </div>
                    <div style={styles.statItem}>
                      <div style={styles.statValue}>
                        {overview.graph_stats?.relationship_counts?.reduce((sum: number, r: any) => sum + r.count, 0) || 0}
                      </div>
                      <div style={styles.statLabel}>Total Relationships</div>
                    </div>
                    <div style={styles.statItem}>
                      <div style={styles.statValue}>{overview.graph_stats?.community_count || 0}</div>
                      <div style={styles.statLabel}>Communities</div>
                    </div>
                  </div>
                </div>
              )}
            </section>
          )}

          {/* Community Visualization */}
          <section style={styles.card}>
            <h4 style={styles.h4}>Community Visualization</h4>
            <CommunityVisualization maxNodes={200} maxCommunities={10} />
          </section>

          {/* Top Communities */}
          {communities.length > 0 && (
            <section style={styles.card}>
              <h4 style={styles.h4}>Top Communities (by size)</h4>
              <div style={styles.communitiesList}>
                {communities.slice(0, 10).map((comm: any, idx: number) => (
                  <div key={idx} style={styles.communityCard}>
                    <div style={styles.communityHeader}>
                      <span style={styles.communityId}>Community {comm.community_id}</span>
                      <span style={styles.communitySize}>{comm.size} entities</span>
                    </div>
                    <div style={styles.communityMembers}>
                      {comm.members?.slice(0, 5).map((m: any, i: number) => (
                        <span key={i} style={styles.memberTag}>
                          {m.name} ({m.type})
                        </span>
                      ))}
                      {comm.members?.length > 5 && (
                        <span style={styles.moreTag}>+{comm.members.length - 5} more</span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* Analytics Data */}
          {analytics && (
            <section style={styles.cardRow}>
              {/* Most Connected Entities */}
              {analytics.most_connected && analytics.most_connected.length > 0 && (
                <div style={styles.card}>
                  <h4 style={styles.h4}>Most Connected Entities</h4>
                  <table style={styles.table}>
                    <thead>
                      <tr>
                        <th style={styles.th}>Name</th>
                        <th style={styles.th}>Type</th>
                        <th style={styles.thRight}>Connections</th>
                      </tr>
                    </thead>
                    <tbody>
                      {analytics.most_connected.slice(0, 10).map((e: any, idx: number) => (
                        <tr key={idx}>
                          <td style={styles.td}>{e.name}</td>
                          <td style={styles.td}>{e.type}</td>
                          <td style={styles.tdRight}>{e.degree || e.connections}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {/* Most Important Entities */}
              {analytics.importance && analytics.importance.length > 0 && (
                <div style={styles.card}>
                  <h4 style={styles.h4}>Most Important Entities</h4>
                  <table style={styles.table}>
                    <thead>
                      <tr>
                        <th style={styles.th}>Name</th>
                        <th style={styles.th}>Type</th>
                        <th style={styles.thRight}>Score</th>
                      </tr>
                    </thead>
                    <tbody>
                      {analytics.importance.slice(0, 10).map((e: any, idx: number) => (
                        <tr key={idx}>
                          <td style={styles.td}>{e.name}</td>
                          <td style={styles.td}>{e.type}</td>
                          <td style={styles.tdRight}>{e.importance_score?.toFixed(2) || e.score?.toFixed(2)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </section>
          )}

          {/* Node and Relationship Counts */}
          {overview && (
            <section style={styles.cardRow}>
              <div style={styles.card}>
                <h4 style={styles.h4}>Node Counts by Label</h4>
                <table style={styles.table}>
                  <thead>
                    <tr>
                      <th style={styles.th}>Label</th>
                      <th style={styles.thRight}>Count</th>
                    </tr>
                  </thead>
                  <tbody>
                    {overview.graph_stats?.node_counts?.map((n: any, idx: number) => (
                      <tr key={idx}>
                        <td style={styles.td}>{n.label}</td>
                        <td style={styles.tdRight}>{n.count}</td>
                      </tr>
                    )) || null}
                  </tbody>
                </table>
              </div>
              <div style={styles.card}>
                <h4 style={styles.h4}>Relationship Counts by Type</h4>
                <table style={styles.table}>
                  <thead>
                    <tr>
                      <th style={styles.th}>Type</th>
                      <th style={styles.thRight}>Count</th>
                    </tr>
                  </thead>
                  <tbody>
                    {overview.graph_stats?.relationship_counts?.map((r: any, idx: number) => (
                      <tr key={idx}>
                        <td style={styles.td}>{r.type}</td>
                        <td style={styles.tdRight}>{r.count}</td>
                      </tr>
                    )) || null}
                  </tbody>
                </table>
              </div>
            </section>
          )}
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
    padding: '8px 16px',
    borderRadius: 8,
    border: '1px solid rgba(59, 130, 246, 0.3)',
    background: 'rgba(15, 23, 42, 0.5)',
    color: '#e2e8f0',
    cursor: 'pointer',
    fontSize: 14,
    transition: 'all 0.2s'
  },
  card: {
    background: 'rgba(30, 41, 59, 0.6)',
    border: '1px solid rgba(59, 130, 246, 0.2)',
    borderRadius: 12,
    padding: 16,
    boxShadow: '0 4px 16px rgba(0, 0, 0, 0.3)',
    backdropFilter: 'blur(10px)'
  },
  cardRow: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: 16
  },
  h4: { margin: '0 0 12px 0', fontSize: 16, fontWeight: 600, color: '#e2e8f0' },
  controlsGrid: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr 1fr',
    gap: 12,
    marginBottom: 12
  },
  label: {
    display: 'block',
    fontSize: 12,
    fontWeight: 600,
    marginBottom: 4,
    color: '#cbd5e1'
  },
  select: {
    width: '100%',
    padding: '8px',
    borderRadius: 6,
    border: '1px solid rgba(59, 130, 246, 0.3)',
    background: 'rgba(15, 23, 42, 0.5)',
    color: '#e2e8f0',
    fontSize: 14
  },
  input: {
    width: '100%',
    padding: '8px',
    borderRadius: 6,
    border: '1px solid rgba(59, 130, 246, 0.3)',
    background: 'rgba(15, 23, 42, 0.5)',
    color: '#e2e8f0',
    fontSize: 14
  },
  detectButton: {
    padding: '10px 20px',
    borderRadius: 8,
    border: '1px solid rgba(59, 130, 246, 0.5)',
    background: 'linear-gradient(135deg, rgba(59, 130, 246, 0.3) 0%, rgba(37, 99, 235, 0.2) 100%)',
    color: '#60a5fa',
    cursor: 'pointer',
    fontSize: 14,
    fontWeight: 600,
    width: '100%',
    transition: 'all 0.2s',
    boxShadow: '0 0 20px rgba(59, 130, 246, 0.2)'
  },
  progressNote: {
    marginTop: 12,
    padding: 8,
    background: 'rgba(251, 191, 36, 0.2)',
    borderRadius: 6,
    fontSize: 12,
    color: '#fbbf24',
    border: '1px solid rgba(251, 191, 36, 0.3)'
  },
  statsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(3, 1fr)',
    gap: 16,
    marginBottom: 16
  },
  statItem: {
    textAlign: 'center'
  },
  statValue: {
    fontSize: 24,
    fontWeight: 700,
    color: '#60a5fa',
    marginBottom: 4,
    textShadow: '0 0 10px rgba(59, 130, 246, 0.5)'
  },
  statLabel: {
    fontSize: 12,
    color: '#94a3b8',
    fontWeight: 500
  },
  distribution: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: 8,
    padding: 12,
    background: 'rgba(15, 23, 42, 0.5)',
    borderRadius: 8,
    border: '1px solid rgba(59, 130, 246, 0.2)'
  },
  distRow: {
    display: 'flex',
    justifyContent: 'space-between',
    fontSize: 13,
    color: '#cbd5e1'
  },
  communitiesList: {
    display: 'grid',
    gap: 12
  },
  communityCard: {
    padding: 12,
    background: 'rgba(15, 23, 42, 0.5)',
    borderRadius: 8,
    border: '1px solid rgba(59, 130, 246, 0.2)'
  },
  communityHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8
  },
  communityId: {
    fontWeight: 600,
    fontSize: 14,
    color: '#e2e8f0'
  },
  communitySize: {
    fontSize: 12,
    color: '#94a3b8',
    background: 'rgba(59, 130, 246, 0.2)',
    padding: '2px 8px',
    borderRadius: 12
  },
  communityMembers: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: 6
  },
  memberTag: {
    fontSize: 11,
    padding: '4px 8px',
    background: 'rgba(59, 130, 246, 0.2)',
    color: '#93c5fd',
    borderRadius: 12,
    border: '1px solid rgba(59, 130, 246, 0.3)'
  },
  moreTag: {
    fontSize: 11,
    padding: '4px 8px',
    background: 'rgba(148, 163, 184, 0.2)',
    color: '#94a3b8',
    borderRadius: 12
  },
  table: { width: '100%', borderCollapse: 'collapse' },
  th: { textAlign: 'left', borderBottom: '1px solid rgba(59, 130, 246, 0.3)', padding: '8px 4px', fontSize: 12, fontWeight: 600, color: '#cbd5e1' },
  thRight: { textAlign: 'right', borderBottom: '1px solid rgba(59, 130, 246, 0.3)', padding: '8px 4px', fontSize: 12, fontWeight: 600, color: '#cbd5e1' },
  td: { padding: '8px 4px', borderBottom: '1px solid rgba(59, 130, 246, 0.1)', fontSize: 13, color: '#e2e8f0' },
  tdRight: { padding: '8px 4px', borderBottom: '1px solid rgba(59, 130, 246, 0.1)', textAlign: 'right', fontSize: 13, color: '#e2e8f0' },
  errorCard: {
    background: 'rgba(239, 68, 68, 0.2)',
    border: '1px solid rgba(239, 68, 68, 0.4)',
    borderRadius: 12,
    padding: 16,
    color: '#fca5a5'
  }
};

