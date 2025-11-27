import { useEffect, useState } from 'react';
import { fetchAnalyticsDashboard, fetchRecentCalls, AnalyticsDashboardResponse, RecentCall } from '../lib/api';

export function AnalyticsDashboard() {
  const [data, setData] = useState<AnalyticsDashboardResponse | null>(null);
  const [recentCalls, setRecentCalls] = useState<RecentCall[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [timePeriod, setTimePeriod] = useState(24);
  const [groupBy, setGroupBy] = useState<'hour' | 'day' | 'minute'>('hour');
  const [selectedCallType, setSelectedCallType] = useState<string>('all');
  const [refreshing, setRefreshing] = useState(false);

  async function loadData() {
    if (!refreshing) setRefreshing(true);
    setError(null);
    try {
      const [dashboardData, callsData] = await Promise.all([
        fetchAnalyticsDashboard(timePeriod, groupBy),
        fetchRecentCalls(50, selectedCallType === 'all' ? undefined : selectedCallType)
      ]);
      setData(dashboardData);
      setRecentCalls(callsData.calls);
    } catch (e: any) {
      setError(e?.message || 'Failed to load analytics');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, [timePeriod, groupBy, selectedCallType]);

  if (loading && !data) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 400 }}>
        <div style={{ textAlign: 'center', color: '#94a3b8' }}>
          <div style={{ 
            width: 48, 
            height: 48, 
            border: '4px solid rgba(59, 130, 246, 0.2)',
            borderTop: '4px solid #3b82f6',
            borderRadius: '50%',
            animation: 'spin 1s linear infinite',
            margin: '0 auto 16px'
          }}></div>
          <div style={{ fontSize: 16, fontWeight: 500 }}>Loading analytics...</div>
        </div>
      </div>
    );
  }

  if (error && !data) {
    return (
      <div style={{ 
        padding: 24, 
        background: 'rgba(239, 68, 68, 0.1)', 
        borderRadius: 12,
        border: '1px solid rgba(239, 68, 68, 0.3)',
        color: '#fca5a5',
        textAlign: 'center'
      }}>
        <div style={{ fontSize: 24, marginBottom: 8 }}>⚠️</div>
        <div style={{ fontSize: 16, fontWeight: 500 }}>{error}</div>
        <button
          onClick={loadData}
          style={{
            marginTop: 16,
            padding: '8px 16px',
            background: 'rgba(239, 68, 68, 0.2)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            borderRadius: 6,
            color: '#fca5a5',
            cursor: 'pointer',
            fontSize: 14
          }}
        >
          Retry
        </button>
      </div>
    );
  }

  if (!data) return null;

  const summary = data.summary;
  // Ensure time_series exists and is an object, handle empty case
  const timeSeriesEntries = data.time_series && typeof data.time_series === 'object' 
    ? Object.entries(data.time_series).slice(-20) // Last 20 data points
    : [];

  return (
    <div style={{ display: 'grid', gap: 24, minHeight: 0 }}>
      <style>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }
        @keyframes slideIn {
          from {
            opacity: 0;
            transform: translateY(10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        .metric-card {
          animation: slideIn 0.3s ease-out;
          transition: all 0.3s ease;
        }
        .metric-card:hover {
          transform: translateY(-2px);
          box-shadow: 0 8px 24px rgba(59, 130, 246, 0.3) !important;
        }
        .chart-card {
          animation: slideIn 0.4s ease-out;
        }
        .refresh-indicator {
          animation: pulse 1.5s ease-in-out infinite;
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
            📊 Analytics Dashboard
          </h1>
          <p style={{ margin: 0, color: '#94a3b8', fontSize: 14 }}>
            Monitor API calls, OpenAI usage, and system performance in real-time
            {refreshing && <span className="refresh-indicator" style={{ marginLeft: 8 }}>🔄</span>}
          </p>
        </div>
        <div style={{ display: 'flex', gap: 12, alignItems: 'center', flexWrap: 'wrap' }}>
          <select
            value={timePeriod}
            onChange={(e) => setTimePeriod(parseInt(e.target.value))}
            style={{
              padding: '10px 14px',
              background: 'rgba(15, 23, 42, 0.8)',
              border: '1px solid rgba(59, 130, 246, 0.3)',
              borderRadius: 8,
              color: '#f1f5f9',
              fontSize: 14,
              cursor: 'pointer',
              outline: 'none',
              transition: 'all 0.2s ease'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.borderColor = 'rgba(59, 130, 246, 0.5)';
              e.currentTarget.style.background = 'rgba(15, 23, 42, 0.9)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.borderColor = 'rgba(59, 130, 246, 0.3)';
              e.currentTarget.style.background = 'rgba(15, 23, 42, 0.8)';
            }}
          >
            <option value={1}>Last Hour</option>
            <option value={24}>Last 24 Hours</option>
            <option value={48}>Last 48 Hours</option>
            <option value={168}>Last 7 Days</option>
          </select>
          <select
            value={groupBy}
            onChange={(e) => setGroupBy(e.target.value as any)}
            style={{
              padding: '10px 14px',
              background: 'rgba(15, 23, 42, 0.8)',
              border: '1px solid rgba(59, 130, 246, 0.3)',
              borderRadius: 8,
              color: '#f1f5f9',
              fontSize: 14,
              cursor: 'pointer',
              outline: 'none',
              transition: 'all 0.2s ease'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.borderColor = 'rgba(59, 130, 246, 0.5)';
              e.currentTarget.style.background = 'rgba(15, 23, 42, 0.9)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.borderColor = 'rgba(59, 130, 246, 0.3)';
              e.currentTarget.style.background = 'rgba(15, 23, 42, 0.8)';
            }}
          >
            <option value="minute">By Minute</option>
            <option value="hour">By Hour</option>
            <option value="day">By Day</option>
          </select>
          <button
            onClick={loadData}
            disabled={refreshing}
            style={{
              padding: '10px 20px',
              background: refreshing 
                ? 'rgba(100, 116, 139, 0.2)' 
                : 'linear-gradient(135deg, rgba(59, 130, 246, 0.3) 0%, rgba(37, 99, 235, 0.2) 100%)',
              border: '1px solid rgba(59, 130, 246, 0.4)',
              borderRadius: 8,
              color: '#60a5fa',
              cursor: refreshing ? 'not-allowed' : 'pointer',
              fontSize: 14,
              fontWeight: 500,
              transition: 'all 0.2s ease',
              boxShadow: '0 2px 8px rgba(59, 130, 246, 0.2)'
            }}
            onMouseEnter={(e) => {
              if (!refreshing) {
                e.currentTarget.style.background = 'linear-gradient(135deg, rgba(59, 130, 246, 0.4) 0%, rgba(37, 99, 235, 0.3) 100%)';
                e.currentTarget.style.transform = 'translateY(-1px)';
                e.currentTarget.style.boxShadow = '0 4px 12px rgba(59, 130, 246, 0.3)';
              }
            }}
            onMouseLeave={(e) => {
              if (!refreshing) {
                e.currentTarget.style.background = 'linear-gradient(135deg, rgba(59, 130, 246, 0.3) 0%, rgba(37, 99, 235, 0.2) 100%)';
                e.currentTarget.style.transform = 'translateY(0)';
                e.currentTarget.style.boxShadow = '0 2px 8px rgba(59, 130, 246, 0.2)';
              }
            }}
          >
            {refreshing ? '⏳ Refreshing...' : '🔄 Refresh'}
          </button>
        </div>
      </div>

      {/* Summary Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 20 }}>
        <MetricCard
          title="API Calls"
          value={summary.total_api_calls.toLocaleString()}
          subtitle={`${summary.total_api_errors} errors`}
          color="#3b82f6"
          icon="📡"
          trend={summary.total_api_calls > 0 ? 'up' : 'neutral'}
        />
        <MetricCard
          title="OpenAI Calls"
          value={summary.total_openai_calls.toLocaleString()}
          subtitle={`${summary.total_openai_errors} errors`}
          color="#10b981"
          icon="🤖"
          trend={summary.total_openai_calls > 0 ? 'up' : 'neutral'}
        />
        <MetricCard
          title="OpenAI Tokens"
          value={summary.total_openai_tokens.toLocaleString()}
          subtitle={`${(summary.total_openai_tokens / 1000).toFixed(1)}K tokens`}
          color="#f59e0b"
          icon="🔢"
          trend={summary.total_openai_tokens > 0 ? 'up' : 'neutral'}
        />
        <MetricCard
          title="OpenAI Cost"
          value={`$${summary.total_openai_cost.toFixed(2)}`}
          subtitle={`${timePeriod}h period`}
          color="#ef4444"
          icon="💰"
          trend={summary.total_openai_cost > 0 ? 'up' : 'neutral'}
        />
        <MetricCard
          title="Queries"
          value={summary.total_query_executions.toLocaleString()}
          subtitle="GraphRAG queries"
          color="#8b5cf6"
          icon="🔍"
          trend={summary.total_query_executions > 0 ? 'up' : 'neutral'}
        />
        <MetricCard
          title="Neo4j Queries"
          value={summary.total_neo4j_queries.toLocaleString()}
          subtitle="Database queries"
          color="#06b6d4"
          icon="🗄️"
          trend={summary.total_neo4j_queries > 0 ? 'up' : 'neutral'}
        />
        {summary.total_articles_scraped !== undefined && (
          <MetricCard
            title="Articles Scraped"
            value={summary.total_articles_scraped.toLocaleString()}
            subtitle="Total scraped"
            color="#f97316"
            icon="📰"
            trend={summary.total_articles_scraped > 0 ? 'up' : 'neutral'}
          />
        )}
        {summary.total_articles_extracted !== undefined && (
          <MetricCard
            title="Articles Extracted"
            value={summary.total_articles_extracted.toLocaleString()}
            subtitle="Entities extracted"
            color="#ec4899"
            icon="🔍"
            trend={summary.total_articles_extracted > 0 ? 'up' : 'neutral'}
          />
        )}
        {summary.total_entities_extracted !== undefined && (
          <MetricCard
            title="Entities Extracted"
            value={summary.total_entities_extracted.toLocaleString()}
            subtitle="Total entities"
            color="#a855f7"
            icon="🏷️"
            trend={summary.total_entities_extracted > 0 ? 'up' : 'neutral'}
          />
        )}
      </div>

      {/* Time Series Charts */}
      {timeSeriesEntries.length > 0 ? (
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(450px, 1fr))', gap: 20 }}>
        <ChartCard title="API Calls Over Time" icon="📈">
          <EnhancedLineChart
            data={timeSeriesEntries}
            dataKey="api_calls"
            color="#3b82f6"
            gradientColor="rgba(59, 130, 246, 0.2)"
          />
        </ChartCard>
        <ChartCard title="OpenAI Calls Over Time" icon="🤖">
          <EnhancedLineChart
            data={timeSeriesEntries}
            dataKey="openai_calls"
            color="#10b981"
            gradientColor="rgba(16, 185, 129, 0.2)"
          />
        </ChartCard>
        <ChartCard title="OpenAI Cost Over Time" icon="💰">
          <EnhancedLineChart
            data={timeSeriesEntries}
            dataKey="openai_cost"
            color="#ef4444"
            gradientColor="rgba(239, 68, 68, 0.2)"
            formatValue={(v) => `$${v.toFixed(2)}`}
          />
        </ChartCard>
        <ChartCard title="OpenAI Tokens Over Time" icon="🔢">
          <EnhancedLineChart
            data={timeSeriesEntries}
            dataKey="openai_tokens"
            color="#f59e0b"
            gradientColor="rgba(245, 158, 11, 0.2)"
            formatValue={(v) => `${(v / 1000).toFixed(1)}K`}
          />
        </ChartCard>
          {timeSeriesEntries.some(([, d]) => d.articles_scraped) && (
            <ChartCard title="Articles Scraped Over Time" icon="📰">
              <EnhancedLineChart
                data={timeSeriesEntries}
                dataKey="articles_scraped"
                color="#f97316"
                gradientColor="rgba(249, 115, 22, 0.2)"
              />
            </ChartCard>
          )}
          {timeSeriesEntries.some(([, d]) => d.articles_extracted) && (
            <ChartCard title="Articles Extracted Over Time" icon="🔍">
              <EnhancedLineChart
                data={timeSeriesEntries}
                dataKey="articles_extracted"
                color="#ec4899"
                gradientColor="rgba(236, 72, 153, 0.2)"
              />
            </ChartCard>
          )}
          {timeSeriesEntries.some(([, d]) => d.entities_extracted) && (
            <ChartCard title="Entities Extracted Over Time" icon="🏷️">
              <EnhancedLineChart
                data={timeSeriesEntries}
                dataKey="entities_extracted"
                color="#a855f7"
                gradientColor="rgba(168, 85, 247, 0.2)"
              />
            </ChartCard>
          )}
      </div>
      ) : (
        <div style={{
          padding: 40,
          background: 'rgba(30, 41, 59, 0.6)',
          borderRadius: 16,
          border: '1px solid rgba(59, 130, 246, 0.2)',
          textAlign: 'center',
          color: '#94a3b8'
        }}>
          <div style={{ fontSize: 32, marginBottom: 12 }}>📊</div>
          <div style={{ fontSize: 16, fontWeight: 500, marginBottom: 8 }}>No time series data available</div>
          <div style={{ fontSize: 14 }}>Data will appear here once API calls are made</div>
        </div>
      )}

      {/* Pipeline Statistics */}
      {data.pipeline_stats && (
        <div style={{
          padding: 24,
          background: 'rgba(30, 41, 59, 0.6)',
          borderRadius: 16,
          border: '1px solid rgba(249, 115, 22, 0.2)',
          boxShadow: '0 4px 20px rgba(0, 0, 0, 0.2)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 20 }}>
            <span style={{ fontSize: 20 }}>⚙️</span>
            <h3 style={{ margin: 0, fontSize: 20, fontWeight: 600, color: '#f1f5f9' }}>
              Pipeline Statistics
            </h3>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 16 }}>
            <div style={{ padding: 16, background: 'rgba(15, 23, 42, 0.4)', borderRadius: 12 }}>
              <div style={{ fontSize: 12, color: '#94a3b8', marginBottom: 8 }}>Total Runs</div>
              <div style={{ fontSize: 24, fontWeight: 700, color: '#f97316' }}>
                {data.pipeline_stats.total_runs}
              </div>
            </div>
            <div style={{ padding: 16, background: 'rgba(15, 23, 42, 0.4)', borderRadius: 12 }}>
              <div style={{ fontSize: 12, color: '#94a3b8', marginBottom: 8 }}>Articles Scraped</div>
              <div style={{ fontSize: 24, fontWeight: 700, color: '#f97316' }}>
                {data.pipeline_stats.total_articles_scraped.toLocaleString()}
              </div>
            </div>
            <div style={{ padding: 16, background: 'rgba(15, 23, 42, 0.4)', borderRadius: 12 }}>
              <div style={{ fontSize: 12, color: '#94a3b8', marginBottom: 8 }}>Articles Extracted</div>
              <div style={{ fontSize: 24, fontWeight: 700, color: '#ec4899' }}>
                {data.pipeline_stats.total_articles_extracted.toLocaleString()}
              </div>
            </div>
            <div style={{ padding: 16, background: 'rgba(15, 23, 42, 0.4)', borderRadius: 12 }}>
              <div style={{ fontSize: 12, color: '#94a3b8', marginBottom: 8 }}>Entities Extracted</div>
              <div style={{ fontSize: 24, fontWeight: 700, color: '#a855f7' }}>
                {data.pipeline_stats.total_entities_extracted.toLocaleString()}
              </div>
            </div>
            <div style={{ padding: 16, background: 'rgba(15, 23, 42, 0.4)', borderRadius: 12 }}>
              <div style={{ fontSize: 12, color: '#94a3b8', marginBottom: 8 }}>Companies Enriched</div>
              <div style={{ fontSize: 24, fontWeight: 700, color: '#ec4899' }}>
                {data.pipeline_stats.total_companies_enriched.toLocaleString()}
              </div>
            </div>
          </div>
          {data.pipeline_stats.last_run && (
            <div style={{ 
              marginTop: 20, 
              padding: 16, 
              background: 'rgba(15, 23, 42, 0.6)', 
              borderRadius: 12,
              border: '1px solid rgba(249, 115, 22, 0.3)'
            }}>
              <div style={{ fontSize: 14, fontWeight: 600, color: '#f1f5f9', marginBottom: 12 }}>Last Run</div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: 12, fontSize: 13 }}>
                {data.pipeline_stats.last_run.articles_scraped !== undefined && (
                  <div>
                    <div style={{ color: '#94a3b8' }}>Articles Scraped</div>
                    <div style={{ color: '#f97316', fontWeight: 600 }}>
                      {data.pipeline_stats.last_run.articles_scraped}
                    </div>
                  </div>
                )}
                {data.pipeline_stats.last_run.articles_extracted !== undefined && (
                  <div>
                    <div style={{ color: '#94a3b8' }}>Articles Extracted</div>
                    <div style={{ color: '#ec4899', fontWeight: 600 }}>
                      {data.pipeline_stats.last_run.articles_extracted}
                    </div>
                  </div>
                )}
                {data.pipeline_stats.last_run.companies_enriched !== undefined && (
                  <div>
                    <div style={{ color: '#94a3b8' }}>Companies Enriched</div>
                    <div style={{ color: '#ec4899', fontWeight: 600 }}>
                      {data.pipeline_stats.last_run.companies_enriched}
                    </div>
                  </div>
                )}
                {data.pipeline_stats.last_run.timestamp && (
                  <div>
                    <div style={{ color: '#94a3b8' }}>Timestamp</div>
                    <div style={{ color: '#cbd5e1', fontSize: 12 }}>
                      {new Date(data.pipeline_stats.last_run.timestamp).toLocaleString()}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Breakdowns */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: 20 }}>
        <BreakdownCard
          title="Top Endpoints"
          icon="🔗"
          data={Object.entries(data.endpoints.counts)
            .sort(([, a], [, b]) => b - a)
            .slice(0, 10)
            .map(([name, count]) => ({ 
              name: name.length > 40 ? name.substring(0, 40) + '...' : name, 
              value: count,
              errorCount: data.endpoints.errors[name] || 0
            }))}
        />
        <BreakdownCard
          title="OpenAI Models"
          icon="🎯"
          data={Object.entries(data.openai_models.counts)
            .map(([name, count]) => ({
              name,
              value: count,
              subtitle: `$${data.openai_models.costs[name]?.toFixed(2) || '0.00'}`,
              tokens: data.openai_models.tokens[name] || 0
            }))}
        />
        <BreakdownCard
          title="OpenAI Operations"
          icon="⚙️"
          data={Object.entries(data.openai_operations.counts)
            .sort(([, a], [, b]) => b - a)
            .slice(0, 10)
            .map(([name, count]) => ({
              name,
              value: count,
              subtitle: `$${data.openai_operations.costs[name]?.toFixed(2) || '0.00'}`
            }))}
        />
      </div>

      {/* Recent Calls */}
      <div style={{
        padding: 24,
        background: 'rgba(30, 41, 59, 0.6)',
        borderRadius: 16,
        border: '1px solid rgba(59, 130, 246, 0.2)',
        boxShadow: '0 4px 20px rgba(0, 0, 0, 0.2)'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
          <div>
            <h3 style={{ margin: 0, fontSize: 20, fontWeight: 600, color: '#f1f5f9', marginBottom: 4 }}>
              📋 Recent Calls
            </h3>
            <p style={{ margin: 0, fontSize: 12, color: '#94a3b8' }}>
              Last {recentCalls.length} calls • Auto-refreshes every 30s
            </p>
          </div>
          <select
            value={selectedCallType}
            onChange={(e) => setSelectedCallType(e.target.value)}
            style={{
              padding: '8px 14px',
              background: 'rgba(15, 23, 42, 0.8)',
              border: '1px solid rgba(59, 130, 246, 0.3)',
              borderRadius: 8,
              color: '#f1f5f9',
              fontSize: 13,
              cursor: 'pointer',
              outline: 'none',
              transition: 'all 0.2s ease'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.borderColor = 'rgba(59, 130, 246, 0.5)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.borderColor = 'rgba(59, 130, 246, 0.3)';
            }}
          >
            <option value="all">All Types</option>
            <option value="api_call">API Calls</option>
            <option value="openai_call">OpenAI Calls</option>
            <option value="neo4j_query">Neo4j Queries</option>
            <option value="query_execution">Query Executions</option>
          </select>
        </div>
        <div style={{ display: 'grid', gap: 10, maxHeight: 500, overflowY: 'auto', paddingRight: 4 }}>
          {recentCalls.length === 0 ? (
            <div style={{ textAlign: 'center', padding: 40, color: '#94a3b8' }}>
              <div style={{ fontSize: 32, marginBottom: 12 }}>📭</div>
              <div>No calls recorded yet</div>
            </div>
          ) : (
            recentCalls.map((call, i) => (
              <CallCard key={i} call={call} />
            ))
          )}
        </div>
      </div>
    </div>
  );
}

function MetricCard({ title, value, subtitle, color, icon, trend }: {
  title: string;
  value: string | number;
  subtitle?: string;
  color: string;
  icon: string;
  trend?: 'up' | 'down' | 'neutral';
}) {
  return (
    <div className="metric-card" style={{
      padding: 24,
      background: `linear-gradient(135deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.6) 100%)`,
      borderRadius: 16,
      border: `1px solid ${color}40`,
      boxShadow: `0 4px 20px ${color}15`,
      position: 'relative',
      overflow: 'hidden'
    }}>
      {/* Background glow effect */}
      <div style={{
        position: 'absolute',
        top: -50,
        right: -50,
        width: 100,
        height: 100,
        background: `radial-gradient(circle, ${color}20 0%, transparent 70%)`,
        borderRadius: '50%'
      }} />
      
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 16, position: 'relative', zIndex: 1 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{
            width: 48,
            height: 48,
            borderRadius: 12,
            background: `${color}20`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: 24,
            border: `1px solid ${color}30`
          }}>
            {icon}
          </div>
          <div>
            <div style={{ fontSize: 11, color: '#94a3b8', fontWeight: 500, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
              {title}
            </div>
            {trend && (
              <div style={{ fontSize: 10, color: trend === 'up' ? '#10b981' : '#94a3b8', marginTop: 2 }}>
                {trend === 'up' && '↑ Active'}
              </div>
            )}
          </div>
        </div>
      </div>
      <div style={{ fontSize: 36, fontWeight: 700, color, marginBottom: 8, position: 'relative', zIndex: 1 }}>
        {value}
      </div>
      {subtitle && (
        <div style={{ fontSize: 12, color: '#64748b', position: 'relative', zIndex: 1 }}>
          {subtitle}
        </div>
      )}
    </div>
  );
}

function ChartCard({ title, icon, children }: { title: string; icon?: string; children: React.ReactNode }) {
  return (
    <div className="chart-card" style={{
      padding: 24,
      background: 'rgba(30, 41, 59, 0.6)',
      borderRadius: 16,
      border: '1px solid rgba(59, 130, 246, 0.2)',
      boxShadow: '0 4px 20px rgba(0, 0, 0, 0.2)'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 20 }}>
        {icon && <span style={{ fontSize: 20 }}>{icon}</span>}
        <h3 style={{ margin: 0, fontSize: 16, fontWeight: 600, color: '#cbd5e1' }}>{title}</h3>
      </div>
      {children}
    </div>
  );
}

function EnhancedLineChart({ data, dataKey, color, gradientColor, formatValue }: {
  data: Array<[string, any]>;
  dataKey: string;
  color: string;
  gradientColor: string;
  formatValue?: (v: number) => string;
}) {
  // Handle empty data
  if (!data || data.length === 0) {
    return (
      <div style={{ 
        height: 240, 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center',
        color: '#94a3b8',
        fontSize: 14
      }}>
        No data available
      </div>
    );
  }

  // Handle single data point
  if (data.length === 1) {
    const d = data[0][1];
    const value = (d && typeof d === 'object' ? d[dataKey] : 0) || 0;
    return (
      <div style={{ height: 240, position: 'relative' }}>
        <div style={{
          height: '100%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexDirection: 'column',
          gap: 8
        }}>
          <div style={{ fontSize: 32, fontWeight: 700, color }}>
            {formatValue ? formatValue(value) : value.toLocaleString()}
          </div>
          <div style={{ fontSize: 12, color: '#94a3b8' }}>
            Single data point
          </div>
        </div>
      </div>
    );
  }

  // Define chart constants before use to ensure they're always defined
  const chartHeight = 80; // Percentage of chart height to use for data

  // Extract values safely - convert all to valid numbers (0 for invalid)
  const values = data.map(([, d]) => {
    if (!d || typeof d !== 'object') return 0;
    const val = d[dataKey];
    return typeof val === 'number' && !isNaN(val) ? val : 0;
  });
  
  // Validate we have data points (defensive check - should never be empty after mapping)
  // This handles edge cases where data might be malformed
  if (values.length === 0) {
    return (
      <div style={{ 
        height: 240, 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center',
        color: '#94a3b8',
        fontSize: 14
      }}>
        No valid numeric data available
      </div>
    );
  }
  
  // Calculate min/max from actual data values (no hardcoded 0 to force range)
  // Values array is guaranteed to have at least one numeric value here
  const max = Math.max(...values);
  const min = Math.min(...values);
  const range = max - min || 1; // Prevent division by zero

  // Create path for area fill - ensure valid coordinates
  // Use the original data length for positioning, but validate values
  const areaPath = data.map(([, d], i) => {
    const value = (d && typeof d === 'object' ? d[dataKey] : 0) || 0;
    const normalizedValue = (typeof value === 'number' && !isNaN(value)) ? value : 0;
    const x = data.length > 1 ? (i / (data.length - 1)) * 100 : 50;
    const y = 100 - ((normalizedValue - min) / range) * chartHeight;
    // Clamp y to valid range [20, 100] to avoid overflow
    const clampedY = Math.max(20, Math.min(100, y));
    return `${i === 0 ? 'M' : 'L'} ${x}% ${clampedY}%`;
  }).join(' ') + ` L 100% 100% L 0% 100% Z`;

  return (
    <div style={{ height: 240, position: 'relative' }}>
      <svg width="100%" height="100%" style={{ overflow: 'visible' }}>
        <defs>
          <linearGradient id={`gradient-${dataKey}`} x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor={color} stopOpacity="0.3" />
            <stop offset="100%" stopColor={color} stopOpacity="0.05" />
          </linearGradient>
        </defs>
        
        {/* Area fill */}
        <path
          d={areaPath}
          fill={`url(#gradient-${dataKey})`}
        />
        
        {/* Line */}
        <polyline
          points={data.map(([, d], i) => {
            const value = (d && typeof d === 'object' ? d[dataKey] : 0) || 0;
            const normalizedValue = (typeof value === 'number' && !isNaN(value)) ? value : 0;
            const x = data.length > 1 ? (i / (data.length - 1)) * 100 : 50;
            const y = 100 - ((normalizedValue - min) / range) * chartHeight;
            const clampedY = Math.max(20, Math.min(100, y));
            return `${x}%,${clampedY}%`;
          }).join(' ')}
          fill="none"
          stroke={color}
          strokeWidth="3"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        
        {/* Data points */}
        {data.map(([, d], i) => {
          const value = (d && typeof d === 'object' ? d[dataKey] : 0) || 0;
          const normalizedValue = (typeof value === 'number' && !isNaN(value)) ? value : 0;
          const x = data.length > 1 ? (i / (data.length - 1)) * 100 : 50;
          const y = 100 - ((normalizedValue - min) / range) * chartHeight;
          const clampedY = Math.max(20, Math.min(100, y));
          return (
            <g key={i}>
              <circle
                cx={`${x}%`}
                cy={`${clampedY}%`}
                r="5"
                fill={color}
                stroke="#0f172a"
                strokeWidth="2"
              />
              <circle
                cx={`${x}%`}
                cy={`${clampedY}%`}
                r="8"
                fill={color}
                opacity="0.2"
              />
            </g>
          );
        })}
      </svg>
      
      {/* Min/Max labels */}
      <div style={{ 
        position: 'absolute', 
        bottom: 0, 
        left: 0, 
        right: 0, 
        display: 'flex', 
        justifyContent: 'space-between', 
        fontSize: 11, 
        color: '#64748b',
        paddingTop: 12,
        fontWeight: 500
      }}>
        <span>{formatValue ? formatValue(min) : min.toLocaleString()}</span>
        <span>{formatValue ? formatValue(max) : max.toLocaleString()}</span>
      </div>
    </div>
  );
}

function BreakdownCard({ title, icon, data }: { 
  title: string; 
  icon?: string;
  data: Array<{ 
    name: string; 
    value: number; 
    subtitle?: string;
    errorCount?: number;
    tokens?: number;
  }> 
}) {
  const max = Math.max(...data.map(d => d.value), 1);

  return (
    <div style={{
      padding: 24,
      background: 'rgba(30, 41, 59, 0.6)',
      borderRadius: 16,
      border: '1px solid rgba(59, 130, 246, 0.2)',
      boxShadow: '0 4px 20px rgba(0, 0, 0, 0.2)'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 20 }}>
        {icon && <span style={{ fontSize: 18 }}>{icon}</span>}
        <h3 style={{ margin: 0, fontSize: 16, fontWeight: 600, color: '#cbd5e1' }}>{title}</h3>
      </div>
      <div style={{ display: 'grid', gap: 12 }}>
        {data.map((item, i) => (
          <div key={i} style={{
            padding: 12,
            background: 'rgba(15, 23, 42, 0.4)',
            borderRadius: 10,
            border: '1px solid rgba(59, 130, 246, 0.1)',
            transition: 'all 0.2s ease'
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = 'rgba(15, 23, 42, 0.6)';
            e.currentTarget.style.borderColor = 'rgba(59, 130, 246, 0.3)';
            e.currentTarget.style.transform = 'translateX(4px)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = 'rgba(15, 23, 42, 0.4)';
            e.currentTarget.style.borderColor = 'rgba(59, 130, 246, 0.1)';
            e.currentTarget.style.transform = 'translateX(0)';
          }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
              <span style={{ color: '#cbd5e1', fontWeight: 500, fontSize: 13, flex: 1 }}>{item.name}</span>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                {item.errorCount !== undefined && item.errorCount > 0 && (
                  <span style={{ 
                    fontSize: 11, 
                    color: '#ef4444', 
                    background: 'rgba(239, 68, 68, 0.1)',
                    padding: '2px 6px',
                    borderRadius: 4
                  }}>
                    {item.errorCount} errors
                  </span>
                )}
                {item.tokens && (
                  <span style={{ fontSize: 11, color: '#94a3b8' }}>
                    {(item.tokens / 1000).toFixed(1)}K tokens
                  </span>
                )}
                <span style={{ color: '#94a3b8', fontWeight: 600, fontSize: 13, minWidth: 60, textAlign: 'right' }}>
                  {item.value.toLocaleString()}
                </span>
                {item.subtitle && (
                  <span style={{ 
                    fontSize: 11, 
                    color: '#f59e0b', 
                    background: 'rgba(245, 158, 11, 0.1)',
                    padding: '2px 8px',
                    borderRadius: 4,
                    fontWeight: 500
                  }}>
                    {item.subtitle}
                  </span>
                )}
              </div>
            </div>
            <div style={{
              height: 6,
              background: 'rgba(15, 23, 42, 0.8)',
              borderRadius: 3,
              overflow: 'hidden',
              position: 'relative'
            }}>
              <div style={{
                height: '100%',
                width: `${(item.value / max) * 100}%`,
                background: `linear-gradient(90deg, ${item.errorCount && item.errorCount > 0 ? '#ef4444' : '#3b82f6'}, ${item.errorCount && item.errorCount > 0 ? '#dc2626' : '#8b5cf6'})`,
                transition: 'width 0.5s ease',
                borderRadius: 3,
                boxShadow: `0 0 10px ${item.errorCount && item.errorCount > 0 ? 'rgba(239, 68, 68, 0.3)' : 'rgba(59, 130, 246, 0.3)'}`
              }} />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function CallCard({ call }: { call: RecentCall }) {
  const getCallIcon = () => {
    switch (call.type) {
      case 'api_call': return '📡';
      case 'openai_call': return '🤖';
      case 'neo4j_query': return '🗄️';
      case 'query_execution': return '🔍';
      default: return '📋';
    }
  };

  const getCallColor = () => {
    switch (call.type) {
      case 'api_call': return '#3b82f6';
      case 'openai_call': return '#10b981';
      case 'neo4j_query': return '#06b6d4';
      case 'query_execution': return '#8b5cf6';
      default: return '#94a3b8';
    }
  };

  const color = getCallColor();
  const isError = (call.type === 'api_call' && call.status_code >= 400) || 
                 (call.type === 'openai_call' && !call.success);

  return (
    <div style={{
      padding: 16,
      background: isError 
        ? 'rgba(239, 68, 68, 0.1)' 
        : 'rgba(15, 23, 42, 0.6)',
      borderRadius: 12,
      border: `1px solid ${isError ? 'rgba(239, 68, 68, 0.3)' : color + '20'}`,
      fontSize: 13,
      transition: 'all 0.2s ease'
    }}
    onMouseEnter={(e) => {
      e.currentTarget.style.transform = 'translateX(4px)';
      e.currentTarget.style.borderColor = isError ? 'rgba(239, 68, 68, 0.5)' : color + '40';
    }}
    onMouseLeave={(e) => {
      e.currentTarget.style.transform = 'translateX(0)';
      e.currentTarget.style.borderColor = isError ? 'rgba(239, 68, 68, 0.3)' : color + '20';
    }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span style={{ fontSize: 18 }}>{getCallIcon()}</span>
          <span style={{ 
            color: isError ? '#ef4444' : '#cbd5e1', 
            fontWeight: 600,
            fontSize: 13,
            textTransform: 'capitalize'
          }}>
            {call.type.replace('_', ' ')}
          </span>
          {isError && (
            <span style={{
              fontSize: 10,
              color: '#ef4444',
              background: 'rgba(239, 68, 68, 0.2)',
              padding: '2px 6px',
              borderRadius: 4,
              fontWeight: 500
            }}>
              ERROR
            </span>
          )}
        </div>
        <span style={{ color: '#94a3b8', fontSize: 11 }}>
          {new Date(call.timestamp).toLocaleTimeString()}
        </span>
      </div>
      
      {call.type === 'api_call' && (
        <div style={{ color: '#94a3b8', fontSize: 12, lineHeight: 1.6 }}>
          <span style={{ 
            color: call.status_code >= 400 ? '#ef4444' : call.status_code >= 300 ? '#f59e0b' : '#10b981',
            fontWeight: 600,
            marginRight: 8
          }}>
            {call.method}
          </span>
          <span style={{ color: '#cbd5e1' }}>{call.endpoint}</span>
          <span style={{ margin: '0 8px', color: '#64748b' }}>•</span>
          <span style={{ color: call.status_code >= 400 ? '#ef4444' : '#94a3b8' }}>
            {call.status_code}
          </span>
          <span style={{ margin: '0 8px', color: '#64748b' }}>•</span>
          <span>{call.duration_ms?.toFixed(0)}ms</span>
        </div>
      )}
      
      {call.type === 'openai_call' && (
        <div style={{ color: '#94a3b8', fontSize: 12, lineHeight: 1.6 }}>
          <span style={{ color: '#cbd5e1', fontWeight: 500 }}>{call.model}</span>
          <span style={{ margin: '0 8px', color: '#64748b' }}>•</span>
          <span>{call.operation}</span>
          <span style={{ margin: '0 8px', color: '#64748b' }}>•</span>
          <span style={{ color: '#f59e0b' }}>{call.total_tokens?.toLocaleString()} tokens</span>
          <span style={{ margin: '0 8px', color: '#64748b' }}>•</span>
          <span style={{ color: '#ef4444', fontWeight: 500 }}>${call.cost_usd?.toFixed(4)}</span>
          <span style={{ margin: '0 8px', color: '#64748b' }}>•</span>
          <span>{call.duration_ms?.toFixed(0)}ms</span>
        </div>
      )}
      
      {call.type === 'query_execution' && (
        <div style={{ color: '#94a3b8', fontSize: 12, lineHeight: 1.6 }}>
          <div style={{ 
            color: '#cbd5e1', 
            marginBottom: 4,
            fontStyle: 'italic',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap'
          }}>
            "{call.query_text}"
          </div>
          <div>
            <span>{call.duration_ms?.toFixed(0)}ms</span>
            {call.cache_hit && (
              <>
                <span style={{ margin: '0 8px', color: '#64748b' }}>•</span>
                <span style={{ color: '#10b981', fontWeight: 500 }}>Cached</span>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
