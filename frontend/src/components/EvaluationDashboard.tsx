import { useEffect, useState } from 'react';
import { 
  runEvaluation, 
  getSampleEvaluationDataset,
  EvaluationRequest,
  EvaluationResponse,
  EvaluationQuery
} from '../lib/api';

export function EvaluationDashboard() {
  const [evaluationResult, setEvaluationResult] = useState<EvaluationResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [queries, setQueries] = useState<EvaluationQuery[]>([]);
  const [useSampleDataset, setUseSampleDataset] = useState(true);
  const [useLLM, setUseLLM] = useState(true);

  useEffect(() => {
    loadSampleDataset();
  }, []);

  async function loadSampleDataset() {
    try {
      const data = await getSampleEvaluationDataset();
      setQueries(data.queries);
    } catch (e: any) {
      console.error('Failed to load sample dataset:', e);
    }
  }

  async function handleRunEvaluation() {
    setLoading(true);
    setError(null);
    setEvaluationResult(null);

    try {
      const request: EvaluationRequest = {
        queries: useSampleDataset ? [] : queries,
        use_sample_dataset: useSampleDataset,
        use_llm: useLLM
      };

      const result = await runEvaluation(request);
      setEvaluationResult(result);
    } catch (e: any) {
      setError(e?.message || 'Failed to run evaluation');
    } finally {
      setLoading(false);
    }
  }

  function addQuery() {
    setQueries([...queries, { query: '', expected_answer: '' }]);
  }

  function updateQuery(index: number, field: 'query' | 'expected_answer', value: string) {
    const updated = [...queries];
    updated[index] = { ...updated[index], [field]: value };
    setQueries(updated);
  }

  function removeQuery(index: number) {
    setQueries(queries.filter((_, i) => i !== index));
  }

  return (
    <div style={{ display: 'grid', gap: 24, minHeight: 0 }}>
      <style>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
        .metric-badge {
          transition: all 0.2s ease;
        }
        .metric-badge:hover {
          transform: scale(1.05);
        }
      `}</style>

      {/* Header */}
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center', 
        flexWrap: 'wrap', 
        gap: 16,
        padding: '20px 24px',
        background: 'linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(139, 92, 246, 0.1) 100%)',
        borderRadius: 16,
        border: '1px solid rgba(59, 130, 246, 0.2)',
        boxShadow: '0 4px 20px rgba(0, 0, 0, 0.2)'
      }}>
        <div>
          <h1 style={{ 
            margin: 0, 
            fontSize: 32, 
            fontWeight: 700, 
            background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)', 
            WebkitBackgroundClip: 'text', 
            WebkitTextFillColor: 'transparent',
            marginBottom: 8
          }}>
            🧪 Evaluation Dashboard
          </h1>
          <p style={{ margin: 0, color: '#94a3b8', fontSize: 14 }}>
            Measure query quality, performance, and system health
          </p>
        </div>
      </div>

      {/* Configuration */}
      <div style={{
        padding: 24,
        background: 'rgba(30, 41, 59, 0.6)',
        borderRadius: 16,
        border: '1px solid rgba(59, 130, 246, 0.2)'
      }}>
        <h3 style={{ margin: '0 0 20px', fontSize: 18, fontWeight: 600, color: '#f1f5f9' }}>
          Evaluation Configuration
        </h3>
        
        <div style={{ display: 'grid', gap: 16 }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: 12, cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={useSampleDataset}
              onChange={(e) => setUseSampleDataset(e.target.checked)}
              style={{ width: 18, height: 18, cursor: 'pointer' }}
            />
            <span style={{ color: '#cbd5e1', fontSize: 14 }}>
              Use sample evaluation dataset (5 predefined queries)
            </span>
          </label>

          <label style={{ display: 'flex', alignItems: 'center', gap: 12, cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={useLLM}
              onChange={(e) => setUseLLM(e.target.checked)}
              style={{ width: 18, height: 18, cursor: 'pointer' }}
            />
            <span style={{ color: '#cbd5e1', fontSize: 14 }}>
              Use LLM for answer generation (recommended)
            </span>
          </label>

          {!useSampleDataset && (
            <div style={{ marginTop: 16 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                <h4 style={{ margin: 0, fontSize: 14, fontWeight: 600, color: '#cbd5e1' }}>
                  Custom Queries
                </h4>
                <button
                  onClick={addQuery}
                  style={{
                    padding: '6px 12px',
                    background: 'rgba(59, 130, 246, 0.2)',
                    border: '1px solid rgba(59, 130, 246, 0.3)',
                    borderRadius: 6,
                    color: '#60a5fa',
                    cursor: 'pointer',
                    fontSize: 12,
                    fontWeight: 500
                  }}
                >
                  + Add Query
                </button>
              </div>
              <div style={{ display: 'grid', gap: 12 }}>
                {queries.map((q, i) => (
                  <div
                    key={i}
                    style={{
                      padding: 16,
                      background: 'rgba(15, 23, 42, 0.6)',
                      borderRadius: 12,
                      border: '1px solid rgba(59, 130, 246, 0.2)'
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                      <span style={{ fontSize: 12, color: '#94a3b8', fontWeight: 500 }}>
                        Query {i + 1}
                      </span>
                      <button
                        onClick={() => removeQuery(i)}
                        style={{
                          padding: '4px 8px',
                          background: 'rgba(239, 68, 68, 0.2)',
                          border: '1px solid rgba(239, 68, 68, 0.3)',
                          borderRadius: 4,
                          color: '#fca5a5',
                          cursor: 'pointer',
                          fontSize: 11
                        }}
                      >
                        Remove
                      </button>
                    </div>
                    <input
                      type="text"
                      placeholder="Enter query..."
                      value={q.query}
                      onChange={(e) => updateQuery(i, 'query', e.target.value)}
                      style={{
                        width: '100%',
                        padding: '10px 12px',
                        marginBottom: 8,
                        background: 'rgba(15, 23, 42, 0.8)',
                        border: '1px solid rgba(59, 130, 246, 0.3)',
                        borderRadius: 8,
                        color: '#f1f5f9',
                        fontSize: 14
                      }}
                    />
                    <input
                      type="text"
                      placeholder="Expected answer (optional, for accuracy measurement)..."
                      value={q.expected_answer || ''}
                      onChange={(e) => updateQuery(i, 'expected_answer', e.target.value)}
                      style={{
                        width: '100%',
                        padding: '10px 12px',
                        background: 'rgba(15, 23, 42, 0.8)',
                        border: '1px solid rgba(59, 130, 246, 0.3)',
                        borderRadius: 8,
                        color: '#f1f5f9',
                        fontSize: 13
                      }}
                    />
                  </div>
                ))}
                {queries.length === 0 && (
                  <div style={{ textAlign: 'center', padding: 24, color: '#94a3b8' }}>
                    No custom queries. Click "Add Query" to add one, or use the sample dataset.
                  </div>
                )}
              </div>
            </div>
          )}

          <button
            onClick={handleRunEvaluation}
            disabled={loading || (!useSampleDataset && queries.length === 0)}
            style={{
              padding: '12px 24px',
              background: loading
                ? 'rgba(100, 116, 139, 0.2)'
                : 'linear-gradient(135deg, rgba(59, 130, 246, 0.3) 0%, rgba(37, 99, 235, 0.2) 100%)',
              border: '1px solid rgba(59, 130, 246, 0.4)',
              borderRadius: 8,
              color: '#60a5fa',
              cursor: loading || (!useSampleDataset && queries.length === 0) ? 'not-allowed' : 'pointer',
              fontSize: 15,
              fontWeight: 600,
              transition: 'all 0.2s ease',
              boxShadow: '0 2px 8px rgba(59, 130, 246, 0.2)'
            }}
            onMouseEnter={(e) => {
              if (!loading && (useSampleDataset || queries.length > 0)) {
                e.currentTarget.style.background = 'linear-gradient(135deg, rgba(59, 130, 246, 0.4) 0%, rgba(37, 99, 235, 0.3) 100%)';
                e.currentTarget.style.transform = 'translateY(-1px)';
              }
            }}
            onMouseLeave={(e) => {
              if (!loading) {
                e.currentTarget.style.background = 'linear-gradient(135deg, rgba(59, 130, 246, 0.3) 0%, rgba(37, 99, 235, 0.2) 100%)';
                e.currentTarget.style.transform = 'translateY(0)';
              }
            }}
          >
            {loading ? (
              <>
                <span style={{ 
                  display: 'inline-block',
                  width: 16,
                  height: 16,
                  border: '2px solid rgba(96, 165, 250, 0.3)',
                  borderTop: '2px solid #60a5fa',
                  borderRadius: '50%',
                  animation: 'spin 1s linear infinite',
                  marginRight: 8,
                  verticalAlign: 'middle'
                }}></span>
                Running Evaluation...
              </>
            ) : (
              '🚀 Run Evaluation'
            )}
          </button>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div style={{
          padding: 16,
          background: 'rgba(239, 68, 68, 0.1)',
          border: '1px solid rgba(239, 68, 68, 0.3)',
          borderRadius: 12,
          color: '#fca5a5'
        }}>
          ⚠️ {error}
        </div>
      )}

      {/* Results */}
      {evaluationResult && (
        <div style={{ display: 'grid', gap: 24 }}>
          {/* Summary Cards */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 16 }}>
            <MetricBadge
              title="Success Rate"
              value={`${((evaluationResult.summary.successful_queries / evaluationResult.summary.total_queries) * 100).toFixed(1)}%`}
              color="#10b981"
              icon="✅"
            />
            <MetricBadge
              title="Avg Latency"
              value={`${evaluationResult.summary.avg_latency_ms.toFixed(0)}ms`}
              color="#3b82f6"
              icon="⚡"
            />
            <MetricBadge
              title="Avg Relevance"
              value={(evaluationResult.summary.avg_relevance * 100).toFixed(1) + '%'}
              color="#8b5cf6"
              icon="🎯"
            />
            <MetricBadge
              title="Avg Accuracy"
              value={evaluationResult.summary.avg_accuracy > 0 ? (evaluationResult.summary.avg_accuracy * 100).toFixed(1) + '%' : 'N/A'}
              color="#f59e0b"
              icon="✓"
            />
            <MetricBadge
              title="Total Cost"
              value={`$${evaluationResult.summary.total_cost_usd.toFixed(4)}`}
              color="#ef4444"
              icon="💰"
            />
            <MetricBadge
              title="Cache Hit Rate"
              value={(evaluationResult.summary.cache_hit_rate * 100).toFixed(1) + '%'}
              color="#06b6d4"
              icon="💾"
            />
          </div>

          {/* Detailed Summary */}
          <div style={{
            padding: 24,
            background: 'rgba(30, 41, 59, 0.6)',
            borderRadius: 16,
            border: '1px solid rgba(59, 130, 246, 0.2)'
          }}>
            <h3 style={{ margin: '0 0 20px', fontSize: 18, fontWeight: 600, color: '#f1f5f9' }}>
              Evaluation Summary
            </h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: 16 }}>
              <SummarySection title="Performance" icon="⚡">
                <SummaryItem label="Total Queries" value={evaluationResult.summary.total_queries} />
                <SummaryItem label="Successful" value={evaluationResult.summary.successful_queries} color="#10b981" />
                <SummaryItem label="Failed" value={evaluationResult.summary.failed_queries} color="#ef4444" />
                <SummaryItem label="P50 Latency" value={`${evaluationResult.summary.p50_latency_ms.toFixed(0)}ms`} />
                <SummaryItem label="P95 Latency" value={`${evaluationResult.summary.p95_latency_ms.toFixed(0)}ms`} />
                <SummaryItem label="P99 Latency" value={`${evaluationResult.summary.p99_latency_ms.toFixed(0)}ms`} />
                <SummaryItem label="Total Tokens" value={evaluationResult.summary.total_tokens.toLocaleString()} />
              </SummarySection>

              <SummarySection title="Quality Metrics" icon="🎯">
                <SummaryItem label="Relevance" value={(evaluationResult.summary.avg_relevance * 100).toFixed(1) + '%'} />
                <SummaryItem label="Accuracy" value={evaluationResult.summary.avg_accuracy > 0 ? (evaluationResult.summary.avg_accuracy * 100).toFixed(1) + '%' : 'N/A'} />
                <SummaryItem label="Completeness" value={evaluationResult.summary.avg_completeness > 0 ? (evaluationResult.summary.avg_completeness * 100).toFixed(1) + '%' : 'N/A'} />
                <SummaryItem label="Coherence" value={(evaluationResult.summary.avg_coherence * 100).toFixed(1) + '%'} />
              </SummarySection>

              <SummarySection title="RAG Metrics" icon="🔍">
                <SummaryItem label="Context Relevance" value={(evaluationResult.summary.avg_context_relevance * 100).toFixed(1) + '%'} />
                <SummaryItem label="Answer Faithfulness" value={(evaluationResult.summary.avg_answer_faithfulness * 100).toFixed(1) + '%'} />
                <SummaryItem label="Answer Relevancy" value={(evaluationResult.summary.avg_answer_relevancy * 100).toFixed(1) + '%'} />
              </SummarySection>
            </div>
          </div>

          {/* Individual Results */}
          <div style={{
            padding: 24,
            background: 'rgba(30, 41, 59, 0.6)',
            borderRadius: 16,
            border: '1px solid rgba(59, 130, 246, 0.2)'
          }}>
            <h3 style={{ margin: '0 0 20px', fontSize: 18, fontWeight: 600, color: '#f1f5f9' }}>
              Individual Query Results
            </h3>
            <div style={{ display: 'grid', gap: 12 }}>
              {evaluationResult.results.map((result, i) => (
                <QueryResultCard key={i} result={result} index={i} />
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function MetricBadge({ title, value, color, icon }: {
  title: string;
  value: string;
  color: string;
  icon: string;
}) {
  return (
    <div className="metric-badge" style={{
      padding: 20,
      background: `linear-gradient(135deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.6) 100%)`,
      borderRadius: 12,
      border: `1px solid ${color}40`,
      boxShadow: `0 4px 12px ${color}15`,
      textAlign: 'center'
    }}>
      <div style={{ fontSize: 24, marginBottom: 8 }}>{icon}</div>
      <div style={{ fontSize: 28, fontWeight: 700, color, marginBottom: 4 }}>{value}</div>
      <div style={{ fontSize: 11, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
        {title}
      </div>
    </div>
  );
}

function SummarySection({ title, icon, children }: {
  title: string;
  icon: string;
  children: React.ReactNode;
}) {
  return (
    <div style={{
      padding: 16,
      background: 'rgba(15, 23, 42, 0.4)',
      borderRadius: 12,
      border: '1px solid rgba(59, 130, 246, 0.1)'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
        <span style={{ fontSize: 18 }}>{icon}</span>
        <h4 style={{ margin: 0, fontSize: 14, fontWeight: 600, color: '#cbd5e1' }}>{title}</h4>
      </div>
      <div style={{ display: 'grid', gap: 8 }}>
        {children}
      </div>
    </div>
  );
}

function SummaryItem({ label, value, color }: {
  label: string;
  value: string | number;
  color?: string;
}) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: 13 }}>
      <span style={{ color: '#94a3b8' }}>{label}</span>
      <span style={{ color: color || '#cbd5e1', fontWeight: 600 }}>{value}</span>
    </div>
  );
}

function QueryResultCard({ result, index }: {
  result: any;
  index: number;
}) {
  const isSuccess = result.success;
  const hasExpected = result.expected_answer;

  return (
    <div style={{
      padding: 20,
      background: isSuccess 
        ? 'rgba(15, 23, 42, 0.6)' 
        : 'rgba(239, 68, 68, 0.1)',
      borderRadius: 12,
      border: `1px solid ${isSuccess ? 'rgba(59, 130, 246, 0.2)' : 'rgba(239, 68, 68, 0.3)'}`
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 16 }}>
        <div style={{ flex: 1 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
            <span style={{ 
              fontSize: 12, 
              color: '#94a3b8', 
              fontWeight: 600,
              background: 'rgba(59, 130, 246, 0.1)',
              padding: '2px 8px',
              borderRadius: 4
            }}>
              Query {index + 1}
            </span>
            {isSuccess ? (
              <span style={{ 
                fontSize: 11, 
                color: '#10b981',
                background: 'rgba(16, 185, 129, 0.1)',
                padding: '2px 8px',
                borderRadius: 4
              }}>
                ✓ Success
              </span>
            ) : (
              <span style={{ 
                fontSize: 11, 
                color: '#ef4444',
                background: 'rgba(239, 68, 68, 0.1)',
                padding: '2px 8px',
                borderRadius: 4
              }}>
                ✗ Failed
              </span>
            )}
          </div>
          <div style={{ fontSize: 14, fontWeight: 600, color: '#cbd5e1', marginBottom: 4 }}>
            {result.query}
          </div>
        </div>
        <div style={{ fontSize: 11, color: '#94a3b8', textAlign: 'right' }}>
          {result.latency_ms.toFixed(0)}ms
        </div>
      </div>

      {result.actual_answer && (
        <div style={{ marginBottom: 12 }}>
          <div style={{ fontSize: 11, color: '#94a3b8', marginBottom: 4, fontWeight: 500 }}>
            Answer:
          </div>
          <div style={{ 
            fontSize: 13, 
            color: '#cbd5e1', 
            lineHeight: 1.6,
            padding: 12,
            background: 'rgba(15, 23, 42, 0.4)',
            borderRadius: 8,
            maxHeight: 150,
            overflowY: 'auto'
          }}>
            {result.actual_answer}
          </div>
        </div>
      )}

      {hasExpected && (
        <div style={{ marginBottom: 12 }}>
          <div style={{ fontSize: 11, color: '#94a3b8', marginBottom: 4, fontWeight: 500 }}>
            Expected:
          </div>
          <div style={{ 
            fontSize: 12, 
            color: '#94a3b8', 
            fontStyle: 'italic',
            padding: 8,
            background: 'rgba(15, 23, 42, 0.3)',
            borderRadius: 6
          }}>
            {result.expected_answer}
          </div>
        </div>
      )}

      {result.error && (
        <div style={{ 
          padding: 12, 
          background: 'rgba(239, 68, 68, 0.1)', 
          borderRadius: 8,
          border: '1px solid rgba(239, 68, 68, 0.3)',
          color: '#fca5a5',
          fontSize: 12,
          marginBottom: 12
        }}>
          Error: {result.error}
        </div>
      )}

      {/* Metrics Grid */}
      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))', 
        gap: 8,
        marginTop: 12,
        paddingTop: 12,
        borderTop: '1px solid rgba(59, 130, 246, 0.1)'
      }}>
        <MetricItem label="Relevance" value={result.relevance_score} />
        {hasExpected && <MetricItem label="Accuracy" value={result.accuracy_score} />}
        {hasExpected && <MetricItem label="Completeness" value={result.completeness_score} />}
        <MetricItem label="Coherence" value={result.coherence_score} />
        <MetricItem label="Context Rel" value={result.context_relevance} />
        <MetricItem label="Faithfulness" value={result.answer_faithfulness} />
        {result.tokens_used > 0 && (
          <MetricItem label="Tokens" value={result.tokens_used.toLocaleString()} />
        )}
        {result.cost_usd > 0 && (
          <MetricItem label="Cost" value={`$${result.cost_usd.toFixed(4)}`} />
        )}
      </div>
    </div>
  );
}

function MetricItem({ label, value }: {
  label: string;
  value: number | string;
}) {
  const numValue = typeof value === 'number' ? value : 0;
  const displayValue = typeof value === 'number' 
    ? (numValue * 100).toFixed(1) + '%' 
    : value;
  
  const color = typeof value === 'number'
    ? numValue >= 0.7 ? '#10b981' : numValue >= 0.4 ? '#f59e0b' : '#ef4444'
    : '#94a3b8';

  return (
    <div style={{
      padding: 8,
      background: 'rgba(15, 23, 42, 0.4)',
      borderRadius: 6,
      textAlign: 'center'
    }}>
      <div style={{ fontSize: 10, color: '#94a3b8', marginBottom: 4 }}>{label}</div>
      <div style={{ fontSize: 13, fontWeight: 600, color }}>{displayValue}</div>
    </div>
  );
}

