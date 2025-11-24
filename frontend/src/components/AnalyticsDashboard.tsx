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

  async function loadData() {
    setLoading(true);
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
          <div style={{ fontSize: 24, marginBottom: 12 }}>⏳</div>
          <div>Loading analytics...</div>
        </div>
      </div>
    );
  }

  if (error && !data) {
    return (
      <div style={{ padding: 24, background: 'rgba(239, 68, 68, 0.1)', borderRadius: 8, color: '#fca5a5' }}>
        ⚠️ {error}
      </div>
    );
  }

  if (!data) return null;

  const summary = data.summary;
  const timeSeriesEntries = Object.entries(data.time_series).slice(-20); // Last 20 data points

  return (
    <div style={{ display: 'grid', gap: 24, minHeight: 0 }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 16 }}>
        <div>
          <h1 style={{ margin: 0, fontSize: 28, fontWeight: 700, background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
            Analytics Dashboard
          </h1>
          <p style={{ margin: '8px 0 0', color: '#94a3b8', fontSize: 14 }}>
            Monitor API calls, OpenAI usage, and system performance
          </p>
        </div>
        <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
          <select
            value={timePeriod}
            onChange={(e) => setTimePeriod(parseInt(e.target.value))}
            style={{
              padding: '8px 12px',
              background: 'rgba(15, 23, 42, 0.8)',
              border: '1px solid rgba(59, 130, 246, 0.3)',
              borderRadius: 6,
              color: '#f1f5f9',
              fontSize: 14
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
              padding: '8px 12px',
              background: 'rgba(15, 23, 42, 0.8)',
              border: '1px solid rgba(59, 130, 246, 0.3)',
              borderRadius: 6,
              color: '#f1f5f9',
              fontSize: 14
            }}
          >
            <option value="minute">By Minute</option>
            <option value="hour">By Hour</option>
            <option value="day">By Day</option>
          </select>
          <button
            onClick={loadData}
            style={{
              padding: '8px 16px',
              background: 'rgba(59, 130, 246, 0.2)',
              border: '1px solid rgba(59, 130, 246, 0.3)',
              borderRadius: 6,
              color: '#60a5fa',
              cursor: 'pointer',
              fontSize: 14,
              fontWeight: 500
            }}
          >
            🔄 Refresh
          </button>
        </div>
      </div>

      {/* Summary Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 16 }}>
        <MetricCard
          title="API Calls"
          value={summary.total_api_calls.toLocaleString()}
          subtitle={`${summary.total_api_errors} errors`}
          color="#3b82f6"
          icon="📡"
        />
        <MetricCard
          title="OpenAI Calls"
          value={summary.total_openai_calls.toLocaleString()}
          subtitle={`${summary.total_openai_errors} errors`}
          color="#10b981"
          icon="🤖"
        />
        <MetricCard
          title="OpenAI Tokens"
          value={summary.total_openai_tokens.toLocaleString()}
          subtitle={`${(summary.total_openai_tokens / 1000).toFixed(1)}K`}
          color="#f59e0b"
          icon="🔢"
        />
        <MetricCard
          title="OpenAI Cost"
          value={`$${summary.total_openai_cost.toFixed(2)}`}
          subtitle={`${timePeriod}h period`}
          color="#ef4444"
          icon="💰"
        />
        <MetricCard
          title="Queries"
          value={summary.total_query_executions.toLocaleString()}
          subtitle="GraphRAG queries"
          color="#8b5cf6"
          icon="🔍"
        />
        <MetricCard
          title="Neo4j Queries"
          value={summary.total_neo4j_queries.toLocaleString()}
          subtitle="Database queries"
          color="#06b6d4"
          icon="🗄️"
        />
      </div>

      {/* Time Series Charts */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: 16 }}>
        <ChartCard title="API Calls Over Time">
          <SimpleLineChart
            data={timeSeriesEntries}
            dataKey="api_calls"
            color="#3b82f6"
          />
        </ChartCard>
        <ChartCard title="OpenAI Calls Over Time">
          <SimpleLineChart
            data={timeSeriesEntries}
            dataKey="openai_calls"
            color="#10b981"
          />
        </ChartCard>
        <ChartCard title="OpenAI Cost Over Time">
          <SimpleLineChart
            data={timeSeriesEntries}
            dataKey="openai_cost"
            color="#ef4444"
            formatValue={(v) => `$${v.toFixed(2)}`}
          />
        </ChartCard>
        <ChartCard title="OpenAI Tokens Over Time">
          <SimpleLineChart
            data={timeSeriesEntries}
            dataKey="openai_tokens"
            color="#f59e0b"
            formatValue={(v) => `${(v / 1000).toFixed(1)}K`}
          />
        </ChartCard>
      </div>

      {/* Breakdowns */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 16 }}>
        <BreakdownCard
          title="Top Endpoints"
          data={Object.entries(data.endpoints.counts)
            .sort(([, a], [, b]) => b - a)
            .slice(0, 10)
            .map(([name, count]) => ({ name, value: count }))}
        />
        <BreakdownCard
          title="OpenAI Models"
          data={Object.entries(data.openai_models.counts)
            .map(([name, count]) => ({
              name,
              value: count,
              subtitle: `$${data.openai_models.costs[name]?.toFixed(2) || '0.00'}`
            }))}
        />
        <BreakdownCard
          title="OpenAI Operations"
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
        padding: 20,
        background: 'rgba(30, 41, 59, 0.6)',
        borderRadius: 12,
        border: '1px solid rgba(59, 130, 246, 0.2)'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <h3 style={{ margin: 0, fontSize: 18, fontWeight: 600, color: '#f1f5f9' }}>
            Recent Calls
          </h3>
          <select
            value={selectedCallType}
            onChange={(e) => setSelectedCallType(e.target.value)}
            style={{
              padding: '6px 12px',
              background: 'rgba(15, 23, 42, 0.8)',
              border: '1px solid rgba(59, 130, 246, 0.3)',
              borderRadius: 6,
              color: '#f1f5f9',
              fontSize: 13
            }}
          >
            <option value="all">All Types</option>
            <option value="api_call">API Calls</option>
            <option value="openai_call">OpenAI Calls</option>
            <option value="neo4j_query">Neo4j Queries</option>
            <option value="query_execution">Query Executions</option>
          </select>
        </div>
        <div style={{ display: 'grid', gap: 8, maxHeight: 400, overflowY: 'auto' }}>
          {recentCalls.map((call, i) => (
            <div
              key={i}
              style={{
                padding: 12,
                background: 'rgba(15, 23, 42, 0.6)',
                borderRadius: 8,
                border: '1px solid rgba(59, 130, 246, 0.1)',
                fontSize: 12
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                <span style={{ color: '#cbd5e1', fontWeight: 600 }}>
                  {call.type === 'api_call' && '📡'}
                  {call.type === 'openai_call' && '🤖'}
                  {call.type === 'neo4j_query' && '🗄️'}
                  {call.type === 'query_execution' && '🔍'}
                  {' '}
                  {call.type.replace('_', ' ').toUpperCase()}
                </span>
                <span style={{ color: '#94a3b8' }}>
                  {new Date(call.timestamp).toLocaleString()}
                </span>
              </div>
              {call.type === 'api_call' && (
                <div style={{ color: '#94a3b8', fontSize: 11 }}>
                  {call.method} {call.endpoint} • {call.status_code} • {call.duration_ms?.toFixed(0)}ms
                </div>
              )}
              {call.type === 'openai_call' && (
                <div style={{ color: '#94a3b8', fontSize: 11 }}>
                  {call.model} • {call.operation} • {call.total_tokens} tokens • ${call.cost_usd?.toFixed(4)} • {call.duration_ms?.toFixed(0)}ms
                </div>
              )}
              {call.type === 'query_execution' && (
                <div style={{ color: '#94a3b8', fontSize: 11 }}>
                  {call.query_text} • {call.duration_ms?.toFixed(0)}ms {call.cache_hit && '• Cached'}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function MetricCard({ title, value, subtitle, color, icon }: {
  title: string;
  value: string | number;
  subtitle?: string;
  color: string;
  icon: string;
}) {
  return (
    <div style={{
      padding: 20,
      background: 'rgba(30, 41, 59, 0.6)',
      borderRadius: 12,
      border: `1px solid ${color}40`,
      boxShadow: `0 4px 12px ${color}20`
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 8 }}>
        <span style={{ fontSize: 24 }}>{icon}</span>
        <div style={{ fontSize: 12, color: '#94a3b8', fontWeight: 500 }}>{title}</div>
      </div>
      <div style={{ fontSize: 28, fontWeight: 700, color, marginBottom: 4 }}>{value}</div>
      {subtitle && <div style={{ fontSize: 12, color: '#64748b' }}>{subtitle}</div>}
    </div>
  );
}

function ChartCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div style={{
      padding: 20,
      background: 'rgba(30, 41, 59, 0.6)',
      borderRadius: 12,
      border: '1px solid rgba(59, 130, 246, 0.2)'
    }}>
      <h3 style={{ margin: '0 0 16px', fontSize: 14, fontWeight: 600, color: '#cbd5e1' }}>{title}</h3>
      {children}
    </div>
  );
}

function SimpleLineChart({ data, dataKey, color, formatValue }: {
  data: Array<[string, any]>;
  dataKey: string;
  color: string;
  formatValue?: (v: number) => string;
}) {
  const values = data.map(([, d]) => d[dataKey] || 0);
  const max = Math.max(...values, 1);
  const min = Math.min(...values);

  return (
    <div style={{ height: 200, position: 'relative' }}>
      <svg width="100%" height="100%" style={{ overflow: 'visible' }}>
        <polyline
          points={data.map(([, d], i) => {
            const value = d[dataKey] || 0;
            const x = (i / (data.length - 1 || 1)) * 100;
            const y = 100 - ((value - min) / (max - min || 1)) * 80;
            return `${x}%,${y}%`;
          }).join(' ')}
          fill="none"
          stroke={color}
          strokeWidth="2"
          opacity={0.8}
        />
        {data.map(([, d], i) => {
          const value = d[dataKey] || 0;
          const x = (i / (data.length - 1 || 1)) * 100;
          const y = 100 - ((value - min) / (max - min || 1)) * 80;
          return (
            <circle
              key={i}
              cx={`${x}%`}
              cy={`${y}%`}
              r="3"
              fill={color}
            />
          );
        })}
      </svg>
      <div style={{ position: 'absolute', bottom: 0, left: 0, right: 0, display: 'flex', justifyContent: 'space-between', fontSize: 10, color: '#64748b', paddingTop: 8 }}>
        <span>{formatValue ? formatValue(min) : min.toLocaleString()}</span>
        <span>{formatValue ? formatValue(max) : max.toLocaleString()}</span>
      </div>
    </div>
  );
}

function BreakdownCard({ title, data }: { title: string; data: Array<{ name: string; value: number; subtitle?: string }> }) {
  const max = Math.max(...data.map(d => d.value), 1);

  return (
    <div style={{
      padding: 20,
      background: 'rgba(30, 41, 59, 0.6)',
      borderRadius: 12,
      border: '1px solid rgba(59, 130, 246, 0.2)'
    }}>
      <h3 style={{ margin: '0 0 16px', fontSize: 14, fontWeight: 600, color: '#cbd5e1' }}>{title}</h3>
      <div style={{ display: 'grid', gap: 8 }}>
        {data.map((item, i) => (
          <div key={i}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4, fontSize: 12 }}>
              <span style={{ color: '#cbd5e1' }}>{item.name}</span>
              <span style={{ color: '#94a3b8' }}>
                {item.value.toLocaleString()}
                {item.subtitle && <span style={{ marginLeft: 8, color: '#64748b' }}>{item.subtitle}</span>}
              </span>
            </div>
            <div style={{
              height: 4,
              background: 'rgba(15, 23, 42, 0.8)',
              borderRadius: 2,
              overflow: 'hidden'
            }}>
              <div style={{
                height: '100%',
                width: `${(item.value / max) * 100}%`,
                background: 'linear-gradient(90deg, #3b82f6, #8b5cf6)',
                transition: 'width 0.3s ease'
              }} />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

