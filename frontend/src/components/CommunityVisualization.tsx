import { useEffect, useRef, useState } from 'react';
import { fetchAuraCommunityGraph, AuraCommunityGraphResponse } from '../lib/api';

// Color palette for communities
const COMMUNITY_COLORS = [
  '#3b82f6', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6',
  '#ec4899', '#06b6d4', '#84cc16', '#f97316', '#6366f1',
  '#14b8a6', '#a855f7', '#f43f5e', '#0ea5e9', '#22c55e'
];

interface CommunityVisualizationProps {
  communityId?: number | null;
  maxNodes?: number;
  maxCommunities?: number;
}

export function CommunityVisualization({ 
  communityId = null, 
  maxNodes = 200,
  maxCommunities = 10 
}: CommunityVisualizationProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const networkRef = useRef<any>(null);
  const [data, setData] = useState<AuraCommunityGraphResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedCommunity, setSelectedCommunity] = useState<number | null>(communityId);

  useEffect(() => {
    loadGraphData();
  }, [selectedCommunity, maxNodes, maxCommunities]);

  useEffect(() => {
    if (data && containerRef.current && !networkRef.current) {
      initializeNetwork();
    }
    return () => {
      if (networkRef.current) {
        networkRef.current.destroy();
        networkRef.current = null;
      }
    };
  }, [data]);

  async function loadGraphData() {
    setLoading(true);
    setError(null);
    try {
      const graphData = await fetchAuraCommunityGraph(
        selectedCommunity || undefined,
        maxNodes,
        maxCommunities
      );
      setData(graphData);
      
      // Reinitialize network if it exists
      if (networkRef.current && containerRef.current) {
        networkRef.current.destroy();
        networkRef.current = null;
        setTimeout(() => initializeNetwork(), 100);
      }
    } catch (e: any) {
      setError(e?.message || 'Failed to load community graph');
    } finally {
      setLoading(false);
    }
  }

  function initializeNetwork() {
    if (!data || !containerRef.current) return;

    // Check if vis-network is already loaded
    // @ts-ignore
    let vis = (window as any).vis;
    
    const loadVisNetwork = () => {
      // @ts-ignore
      vis = (window as any).vis;
      if (!vis || !vis.Network) {
        // Load vis-network dynamically
        const script = document.createElement('script');
        script.src = '/lib/vis-9.1.2/vis-network.min.js';
        script.onload = () => {
          // @ts-ignore
          vis = (window as any).vis;
          if (!vis || !vis.Network) {
            setError('Failed to load vis-network library');
            return;
          }
          createNetwork(vis);
        };
        script.onerror = () => {
          setError('Failed to load vis-network library. Make sure /lib/vis-9.1.2/vis-network.min.js is accessible.');
        };
        document.body.appendChild(script);
        
        // Load CSS
        const link = document.createElement('link');
        link.rel = 'stylesheet';
        link.href = '/lib/vis-9.1.2/vis-network.css';
        if (!document.querySelector(`link[href="${link.href}"]`)) {
          document.head.appendChild(link);
        }
      } else {
        createNetwork(vis);
      }
    };

    const createNetwork = (vis: any) => {
      if (!containerRef.current) return;

      // Create color mapping for communities
      const communityColorMap: Record<number, string> = {};
      if (data.communities) {
        data.communities.forEach((cid, idx) => {
          communityColorMap[cid] = COMMUNITY_COLORS[idx % COMMUNITY_COLORS.length];
        });
      }

      // Format nodes with colors
      const nodes = data.nodes.map((node: any) => {
        const communityId = node.community_id;
        const color = communityId ? communityColorMap[communityId] : '#94a3b8';
        
        return {
          id: node.id,
          label: node.label || node.name || 'Unknown',
          title: node.title || `${node.label} (${node.type})`,
          color: {
            background: color,
            border: color,
            highlight: {
              background: color,
              border: '#ffffff'
            }
          },
          font: {
            color: '#ffffff',
            size: 12
          },
          shape: 'dot',
          size: 16,
          community_id: communityId,
          type: node.type
        };
      });

      // Format edges
      const edges = data.edges.map((edge: any) => ({
        from: edge.from,
        to: edge.to,
        label: edge.label || edge.type || '',
        arrows: 'to',
        color: {
          color: 'rgba(148, 163, 184, 0.5)',
          highlight: 'rgba(59, 130, 246, 0.8)'
        },
        width: 1,
        smooth: {
          type: 'continuous',
          roundness: 0.5
        }
      }));

      const networkData = { nodes, edges };

      const options = {
        nodes: {
          borderWidth: 2,
          shadow: {
            enabled: true,
            color: 'rgba(0,0,0,0.3)',
            size: 5,
            x: 2,
            y: 2
          },
          font: {
            size: 12,
            face: 'system-ui',
            color: '#ffffff'
          }
        },
        edges: {
          width: 1.5,
          shadow: {
            enabled: true,
            color: 'rgba(0,0,0,0.2)',
            size: 3
          },
          font: {
            size: 10,
            color: '#94a3b8',
            align: 'middle'
          },
          smooth: {
            type: 'continuous',
            roundness: 0.5
          }
        },
        physics: {
          enabled: true,
          stabilization: {
            enabled: true,
            iterations: 200,
            fit: true
          },
          barnesHut: {
            gravitationalConstant: -2000,
            centralGravity: 0.1,
            springLength: 200,
            springConstant: 0.04,
            damping: 0.09
          }
        },
        interaction: {
          hover: true,
          tooltipDelay: 100,
          zoomView: true,
          dragView: true
        },
        layout: {
          improvedLayout: true,
          clusterThreshold: 150
        }
      };

      networkRef.current = new vis.Network(containerRef.current, networkData, options);

      // Add event listeners
      networkRef.current.on('click', (params: any) => {
        if (params.nodes.length > 0) {
          const nodeId = params.nodes[0];
          const node = nodes.find((n: any) => n.id === nodeId);
          if (node) {
            console.log('Selected node:', node);
          }
        }
      });

      networkRef.current.on('stabilizationEnd', () => {
        networkRef.current.fit({
          animation: {
            duration: 1000,
            easingFunction: 'easeInOutQuad'
          }
        });
      });
    };

    loadVisNetwork();
  }

  if (loading) {
    return (
      <div style={styles.container}>
        <div style={styles.loading}>Loading community visualization...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={styles.container}>
        <div style={styles.error}>⚠️ {error}</div>
        <button onClick={loadGraphData} style={styles.retryButton}>
          Retry
        </button>
      </div>
    );
  }

  if (!data || data.nodes.length === 0) {
    return (
      <div style={styles.container}>
        <div style={styles.empty}>No community data available. Run community detection first.</div>
      </div>
    );
  }

  return (
    <div style={styles.wrapper}>
      <div style={styles.controls}>
        <div style={styles.controlGroup}>
          <label style={styles.label}>Filter by Community:</label>
          <select
            value={selectedCommunity || ''}
            onChange={(e) => setSelectedCommunity(e.target.value ? parseInt(e.target.value) : null)}
            style={styles.select}
          >
            <option value="">All Communities</option>
            {data.communities?.map((cid) => (
              <option key={cid} value={cid}>
                Community {cid}
              </option>
            ))}
          </select>
        </div>
        <div style={styles.stats}>
          <span style={styles.statItem}>Nodes: {data.node_count}</span>
          <span style={styles.statItem}>Edges: {data.edge_count}</span>
          <span style={styles.statItem}>Communities: {data.communities?.length || 0}</span>
        </div>
        <button onClick={loadGraphData} style={styles.refreshButton}>
          🔄 Refresh
        </button>
      </div>
      <div ref={containerRef} style={styles.graphContainer} />
      {data.communities && data.communities.length > 0 && (
        <div style={styles.legend}>
          <div style={styles.legendTitle}>Community Colors:</div>
          <div style={styles.legendItems}>
            {data.communities.slice(0, 15).map((cid, idx) => (
              <div key={cid} style={styles.legendItem}>
                <div
                  style={{
                    ...styles.legendColor,
                    background: COMMUNITY_COLORS[idx % COMMUNITY_COLORS.length]
                  }}
                />
                <span style={styles.legendLabel}>Community {cid}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  wrapper: {
    display: 'flex',
    flexDirection: 'column',
    gap: 12,
    height: '100%'
  },
  container: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: 400,
    padding: 24
  },
  controls: {
    display: 'flex',
    alignItems: 'center',
    gap: 16,
    padding: 12,
    background: 'rgba(30, 41, 59, 0.6)',
    borderRadius: 8,
    border: '1px solid rgba(59, 130, 246, 0.2)',
    flexWrap: 'wrap'
  },
  controlGroup: {
    display: 'flex',
    alignItems: 'center',
    gap: 8
  },
  label: {
    fontSize: 13,
    color: '#cbd5e1',
    fontWeight: 500
  },
  select: {
    padding: '6px 12px',
    borderRadius: 6,
    border: '1px solid rgba(59, 130, 246, 0.3)',
    background: 'rgba(15, 23, 42, 0.5)',
    color: '#e2e8f0',
    fontSize: 13
  },
  stats: {
    display: 'flex',
    gap: 16,
    fontSize: 12,
    color: '#94a3b8'
  },
  statItem: {
    padding: '4px 8px',
    background: 'rgba(59, 130, 246, 0.1)',
    borderRadius: 4
  },
  refreshButton: {
    padding: '6px 12px',
    borderRadius: 6,
    border: '1px solid rgba(59, 130, 246, 0.3)',
    background: 'rgba(15, 23, 42, 0.5)',
    color: '#60a5fa',
    cursor: 'pointer',
    fontSize: 13,
    marginLeft: 'auto'
  },
  graphContainer: {
    width: '100%',
    height: '600px',
    minHeight: 400,
    background: 'rgba(15, 23, 42, 0.3)',
    borderRadius: 8,
    border: '1px solid rgba(59, 130, 246, 0.2)',
    overflow: 'hidden'
  },
  loading: {
    color: '#94a3b8',
    fontSize: 14
  },
  error: {
    color: '#fca5a5',
    fontSize: 14,
    marginBottom: 12
  },
  empty: {
    color: '#94a3b8',
    fontSize: 14
  },
  retryButton: {
    padding: '8px 16px',
    borderRadius: 6,
    border: '1px solid rgba(59, 130, 246, 0.3)',
    background: 'rgba(59, 130, 246, 0.2)',
    color: '#60a5fa',
    cursor: 'pointer',
    fontSize: 13
  },
  legend: {
    padding: 12,
    background: 'rgba(30, 41, 59, 0.6)',
    borderRadius: 8,
    border: '1px solid rgba(59, 130, 246, 0.2)'
  },
  legendTitle: {
    fontSize: 12,
    fontWeight: 600,
    color: '#cbd5e1',
    marginBottom: 8
  },
  legendItems: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: 12
  },
  legendItem: {
    display: 'flex',
    alignItems: 'center',
    gap: 6
  },
  legendColor: {
    width: 16,
    height: 16,
    borderRadius: 4,
    border: '1px solid rgba(255, 255, 255, 0.2)'
  },
  legendLabel: {
    fontSize: 11,
    color: '#94a3b8'
  }
};

