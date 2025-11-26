import { useEffect, useRef, useState } from 'react';
import { TraversalData } from '../lib/api';

interface GraphTraversalAnimationProps {
  traversalData: TraversalData | null;
  onComplete?: () => void;
  skipAnimation?: boolean; // If true, show final state immediately without animation
}

export function GraphTraversalAnimation({ 
  traversalData, 
  onComplete,
  skipAnimation = false
}: GraphTraversalAnimationProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const networkRef = useRef<any>(null);
  const [isAnimating, setIsAnimating] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const animationTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (!traversalData || !containerRef.current) return;

    // Load vis-network if not already loaded
    // @ts-ignore
    let vis = (window as any).vis;
    
    const loadVisNetwork = () => {
      // @ts-ignore
      vis = (window as any).vis;
      if (!vis || !vis.Network) {
        const script = document.createElement('script');
        script.src = '/lib/vis-9.1.2/vis-network.min.js';
        script.onload = () => {
          // @ts-ignore
          vis = (window as any).vis;
          if (vis && vis.Network) {
            initializeNetwork(vis);
          }
        };
        script.onerror = () => {
          console.error('Failed to load vis-network library');
        };
        document.body.appendChild(script);
        
        const link = document.createElement('link');
        link.rel = 'stylesheet';
        link.href = '/lib/vis-9.1.2/vis-network.css';
        document.head.appendChild(link);
      } else {
        initializeNetwork(vis);
      }
    };

    function initializeNetwork(vis: any) {
      if (!containerRef.current || !traversalData) return;

      // Destroy existing network
      if (networkRef.current) {
        networkRef.current.destroy();
        networkRef.current = null;
      }

      // Prepare initial data (all nodes/edges but not visible)
      const nodes = traversalData.nodes.map(node => ({
        id: node.id,
        label: node.label || node.id,
        title: `${node.type}: ${node.description || node.label}`,
        color: {
          background: '#334155',
          border: '#64748b',
          highlight: {
            background: '#3b82f6',
            border: '#2563eb'
          }
        },
        font: { color: '#ffffff', size: 14 },
        shape: 'dot',
        size: 20,
        hidden: true // Start hidden
      }));

      const edges = traversalData.edges.map(edge => ({
        id: edge.id,
        from: edge.from,
        to: edge.to,
        label: edge.label || edge.type,
        title: edge.type,
        color: {
          color: '#64748b',
          highlight: '#3b82f6',
          opacity: 0.3
        },
        width: 2,
        hidden: true, // Start hidden
        arrows: {
          to: {
            enabled: true,
            scaleFactor: 0.8
          }
        }
      }));

      const data = { nodes, edges };

      const options = {
        nodes: {
          shape: 'dot',
          size: 20,
          font: {
            size: 14,
            color: '#ffffff'
          },
          borderWidth: 2,
          shadow: {
            enabled: true,
            color: 'rgba(59, 130, 246, 0.3)',
            size: 10
          }
        },
        edges: {
          width: 2,
          color: {
            color: '#64748b',
            highlight: '#3b82f6'
          },
          smooth: {
            type: 'continuous',
            roundness: 0.5
          },
          arrows: {
            to: {
              enabled: true,
              scaleFactor: 0.8
            }
          },
          shadow: {
            enabled: true,
            color: 'rgba(59, 130, 246, 0.2)',
            size: 5
          }
        },
        physics: {
          enabled: true,
          stabilization: {
            enabled: true,
            iterations: 100,
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
          hierarchical: {
            enabled: false
          }
        }
      };

      networkRef.current = new vis.Network(containerRef.current, data, options);

      // Start animation or show final state
      if (skipAnimation) {
        showFinalState();
      } else {
        startAnimation();
      }
    }

    function showFinalState() {
      if (!traversalData || !networkRef.current) return;
      
      setIsAnimating(false);
      
      // Show all nodes and edges immediately
      const nodes = networkRef.current.body.data.nodes;
      const edges = networkRef.current.body.data.edges;
      
      // Show all nodes
      traversalData.nodes.forEach(node => {
        nodes.update({
          id: node.id,
          hidden: false,
          color: {
            background: '#10b981',
            border: '#059669',
            highlight: {
              background: '#34d399',
              border: '#10b981'
            }
          },
          size: 20
        });
      });
      
      // Show all edges
      traversalData.edges.forEach(edge => {
        edges.update({
          id: edge.id,
          hidden: false,
          color: {
            color: '#64748b',
            highlight: '#3b82f6',
            opacity: 1
          },
          width: 2
        });
      });
      
      // Fit network to show all nodes
      setTimeout(() => {
        try {
          networkRef.current.fit({
            animation: {
              duration: 500,
              easingFunction: 'easeInOutQuad'
            }
          });
          // Call onComplete after the fit animation completes (500ms duration + small buffer)
          if (onComplete) {
            setTimeout(() => {
              onComplete();
            }, 550); // 500ms animation + 50ms buffer
          }
        } catch (e) {
          // Ignore fit errors, but still call onComplete
          if (onComplete) {
            onComplete();
          }
        }
      }, 100);
    }

    function startAnimation() {
      if (!traversalData || !networkRef.current) return;
      
      setIsAnimating(true);
      setCurrentStep(0);
      
      // Clear any existing timeout
      if (animationTimeoutRef.current) {
        clearTimeout(animationTimeoutRef.current);
      }

      // Reset all nodes and edges to hidden
      const allNodeIds = traversalData.nodes.map(n => n.id);
      const allEdgeIds = traversalData.edges.map(e => e.id);
      
      // Reset data using the data manipulation API
      const nodes = networkRef.current.body.data.nodes;
      const edges = networkRef.current.body.data.edges;
      
      // Clear existing data
      nodes.clear();
      edges.clear();
      
      // Add all nodes and edges (hidden initially)
      nodes.add(traversalData.nodes.map(node => ({
        id: node.id,
        label: node.label || node.id,
        title: `${node.type}: ${node.description || node.label}`,
        color: {
          background: '#334155',
          border: '#64748b',
          highlight: {
            background: '#3b82f6',
            border: '#2563eb'
          }
        },
        font: { color: '#ffffff', size: 14 },
        shape: 'dot',
        size: 20,
        hidden: true
      })));
      
      edges.add(traversalData.edges.map(edge => ({
        id: edge.id,
        from: edge.from,
        to: edge.to,
        label: edge.label || edge.type,
        title: edge.type,
        color: {
          color: '#64748b',
          highlight: '#3b82f6',
          opacity: 0.3
        },
        width: 2,
        hidden: true,
        arrows: {
          to: {
            enabled: true,
            scaleFactor: 0.8
          }
        }
      })));

      // Animate nodes and edges in order
      let step = 0;
      const nodeOrder = traversalData.node_order || [];
      const edgeOrder = traversalData.edge_order || [];
      const allSteps = [...nodeOrder, ...edgeOrder];
      
      function animateNext() {
        if (step >= allSteps.length) {
          setIsAnimating(false);
          if (onComplete) {
            onComplete();
          }
          return;
        }

        const currentId = allSteps[step];
        setCurrentStep(step + 1);

        // Check if it's a node or edge
        const isNode = nodeOrder.includes(currentId);
        
        if (isNode) {
          // Show and highlight node using data manipulation
          const nodes = networkRef.current.body.data.nodes;
          const node = nodes.get(currentId);
          
          if (node) {
            // Update node to be visible and highlighted
            nodes.update({
              id: currentId,
              hidden: false,
              color: {
                background: '#3b82f6',
                border: '#2563eb',
                highlight: {
                  background: '#60a5fa',
                  border: '#3b82f6'
                }
              },
              size: 25
            });
            
            // Pulse animation after a delay
            setTimeout(() => {
              nodes.update({
                id: currentId,
                size: 20,
                color: {
                  background: '#10b981',
                  border: '#059669',
                  highlight: {
                    background: '#34d399',
                    border: '#10b981'
                  }
                }
              });
            }, 300);
          }
        } else {
          // Show edge
          const edges = networkRef.current.body.data.edges;
          const edge = edges.get(currentId);
          
          if (edge) {
            edges.update({
              id: currentId,
              hidden: false,
              color: {
                color: '#3b82f6',
                highlight: '#60a5fa',
                opacity: 1
              },
              width: 3
            });
          }
        }

        // Fit network to show new nodes periodically
        if (step % 5 === 0 || step === allSteps.length - 1) {
          setTimeout(() => {
            try {
              networkRef.current.fit({
                animation: {
                  duration: 500,
                  easingFunction: 'easeInOutQuad'
                }
              });
            } catch (e) {
              // Ignore fit errors
            }
          }, 100);
        }

        step++;
        animationTimeoutRef.current = setTimeout(animateNext, 400); // 400ms delay between steps
      }

      // Start animation after a short delay
      animationTimeoutRef.current = setTimeout(() => {
        animateNext();
      }, 500);
    }

    loadVisNetwork();

    return () => {
      if (animationTimeoutRef.current) {
        clearTimeout(animationTimeoutRef.current);
      }
      if (networkRef.current) {
        networkRef.current.destroy();
        networkRef.current = null;
      }
    };
  }, [traversalData, onComplete, skipAnimation]);

  if (!traversalData || traversalData.nodes.length === 0) {
    return null;
  }

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h4 style={styles.title}>🔍 Graph Traversal</h4>
        {isAnimating && (
          <div style={styles.progress}>
            <span style={styles.progressText}>
              Step {currentStep} / {traversalData.node_order.length + traversalData.edge_order.length}
            </span>
          </div>
        )}
      </div>
      <div ref={containerRef} style={styles.graphContainer} />
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    background: '#1e293b',
    border: '1px solid rgba(51, 65, 85, 0.5)',
    borderRadius: 8,
    padding: 12,
    marginTop: 12,
    maxHeight: 500
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12
  },
  title: {
    margin: 0,
    fontSize: 14,
    fontWeight: 600,
    color: '#ffffff'
  },
  progress: {
    fontSize: 12,
    color: '#94a3b8'
  },
  progressText: {
    color: '#94a3b8'
  },
  graphContainer: {
    width: '100%',
    height: 400,
    background: '#0f172a',
    borderRadius: 6,
    border: '1px solid rgba(51, 65, 85, 0.3)'
  }
};

