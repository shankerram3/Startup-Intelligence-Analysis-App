// Runtime-configurable API base URL
// Priority: window.__API_BASE_URL__ > VITE_API_BASE_URL > localhost (for dev)
// For Vercel deployment, set VITE_API_BASE_URL environment variable
function getApiBaseUrl(): string {
  // 1. Check for runtime config (injected via script tag in index.html)
  if (typeof window !== 'undefined' && (window as any).__API_BASE_URL__) {
    return (window as any).__API_BASE_URL__;
  }
  
  // 2. Check for build-time env var (REQUIRED for Vercel/production)
  const envUrl = (import.meta as any).env?.VITE_API_BASE_URL;
  if (envUrl) {
    return envUrl;
  }
  
  // 3. Default to localhost for local development
  // In production (Vercel), VITE_API_BASE_URL must be set
  if (typeof window !== 'undefined') {
    const origin = window.location.origin;
    // If on localhost, use localhost backend
    if (origin.includes('localhost') || origin.includes('127.0.0.1')) {
      return 'http://localhost:8000';
    }
    // If in production but no env var set, warn and use localhost (will fail)
    console.warn('VITE_API_BASE_URL not set. API calls will fail in production.');
    return 'http://localhost:8000';
  }
  
  // 4. Fallback to localhost
  return 'http://localhost:8000';
}

export const API_BASE_URL: string = getApiBaseUrl();

// Runtime-configurable API key
// Priority: window.__API_KEY__ > VITE_API_KEY > none (optional)
// For Vercel deployment, set VITE_API_KEY environment variable
function getApiKey(): string | undefined {
  // 1. Check for runtime config (injected via script tag in index.html)
  if (typeof window !== 'undefined' && (window as any).__API_KEY__) {
    return (window as any).__API_KEY__;
  }
  
  // 2. Check for build-time env var (for Vercel/production)
  const envKey = (import.meta as any).env?.VITE_API_KEY;
  if (envKey) {
    return envKey;
  }
  
  // 3. No API key (optional - only needed if backend requires it)
  return undefined;
}

export const API_KEY: string | undefined = getApiKey();

// Helper function to get default headers with API key
function getDefaultHeaders(): Record<string, string> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  
  // Add API key if configured
  if (API_KEY) {
    headers['X-API-Key'] = API_KEY;
  }
  
  return headers;
}

export type QueryRequest = {
  question: string;
  return_context?: boolean;
  use_llm?: boolean;
  return_traversal?: boolean;
};

export type TraversalNode = {
  id: string;
  label: string;
  type: string;
  description?: string;
};

export type TraversalEdge = {
  id: string;
  from: string;
  to: string;
  type: string;
  label: string;
};

export type TraversalData = {
  nodes: TraversalNode[];
  edges: TraversalEdge[];
  node_order: string[];
  edge_order: string[];
};

export type QueryResponse = {
  question: string;
  intent: Record<string, unknown>;
  answer?: string | null;
  context?: unknown;
  traversal?: TraversalData;
};

export type SemanticSearchRequest = {
  query: string;
  top_k?: number;
  entity_type?: string | null;
};

export type SemanticSearchResponse = {
  results: unknown[];
  count: number;
};

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    
    // Check for server errors (503/504) - these are often temporary
    if (res.status === 503 || res.status === 504) {
      // Check if it's an HTML error page (like DigitalOcean App Platform errors)
      if (text.includes('no_healthy_upstream') || text.includes('connection_timed_out') || text.includes('<!DOCTYPE html>')) {
        const error = new Error(`Server temporarily unavailable (${res.status})`);
        (error as any).status = res.status;
        (error as any).isServerError = true;
        throw error;
      }
    }
    
    // Try to parse JSON error response (FastAPI format)
    try {
      const json = JSON.parse(text);
      if (json.detail) {
        throw new Error(JSON.stringify({ detail: json.detail }));
      }
    } catch {
      // Not JSON or no detail field, use text as-is
    }
    throw new Error(text || `HTTP ${res.status}: ${res.statusText}`);
  }
  return res.json() as Promise<T>;
}

export async function postJson<TReq, TRes>(path: string, body: TReq): Promise<TRes> {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    method: 'POST',
    headers: getDefaultHeaders(),
    body: JSON.stringify(body)
  });
  return handleResponse<TRes>(res);
}

export async function getJson<TRes>(path: string, timeout: number = 10000): Promise<TRes> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);
  
  try {
    const res = await fetch(`${API_BASE_URL}${path}`, {
      signal: controller.signal,
      headers: getDefaultHeaders()
    });
    clearTimeout(timeoutId);
    return handleResponse<TRes>(res);
  } catch (err: any) {
    clearTimeout(timeoutId);
    if (err.name === 'AbortError') {
      const error = new Error(`Request timeout after ${timeout}ms`);
      (error as any).isTimeout = true;
      throw error;
    }
    throw err;
  }
}

// Neo4j/AuraDB admin
export type Neo4jOverview = {
  status: string;
  db_info: { components: Array<{ name?: string; versions?: string[]; edition?: string }> };
  labels: string[];
  relationship_types: string[];
  graph_stats: {
    node_counts: Array<{ label: string; count: number }>;
    relationship_counts: Array<{ type: string; count: number }>;
    community_count: number;
  };
  top_connected_entities: Array<{ id: string; name: string; type: string; degree: number }>;
  top_important_entities: Array<{ id: string; name: string; type: string; importance_score: number }>;
};

export async function fetchNeo4jOverview(): Promise<Neo4jOverview> {
  return getJson<Neo4jOverview>('/admin/neo4j/overview');
}

export async function getText(path: string): Promise<string> {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    headers: getDefaultHeaders()
  });
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(text || `HTTP ${res.status}`);
  }
  return res.text();
}

// Admin API types
export type PipelineStartRequest = {
  scrape_category?: string;
  scrape_max_pages?: number;
  max_articles?: number;
  skip_scraping?: boolean;
  skip_extraction?: boolean;
  skip_enrichment?: boolean;
  skip_graph?: boolean;
  skip_post_processing?: boolean;
  max_companies_per_article?: number;
  no_resume?: boolean;
  no_validation?: boolean;
  no_cleanup?: boolean;
  enable_debug_logs?: boolean;
};

export type PipelineStartResponse = {
  status: string;
  pid: number;
  args: string[];
  log: string;
};

export type PipelineStatus = {
  running: boolean;
  pid?: number;
  returncode?: number | null;
};

export function startPipeline(body: PipelineStartRequest) {
  return postJson<PipelineStartRequest, PipelineStartResponse>(`/admin/pipeline/start`, body);
}

export function stopPipeline() {
  return postJson<{}, { status: string }>(`/admin/pipeline/stop`, {} as any);
}

export function fetchPipelineStatus() {
  return getJson<PipelineStatus>(`/admin/pipeline/status`);
}

export async function fetchPipelineLogs(tail = 200, timeout?: number): Promise<string> {
  // Use longer timeout for large log fetches (5000 lines can take time)
  const logTimeout = timeout || (tail > 2000 ? 30000 : 10000);
  const res = await getJson<{ log: string }>(`/admin/pipeline/logs?tail=${tail}`, logTimeout);
  return res.log || '';
}

export function clearPipelineLogs() {
  return postJson<{}, { status: string; message: string }>(`/admin/pipeline/logs/clear`, {} as any);
}

// Aura Graph Analytics API types
export type AuraCommunityDetectionRequest = {
  algorithm?: string;
  min_community_size?: number;
  graph_name?: string;
};

export type AuraCommunityDetectionResponse = {
  algorithm: string;
  total_communities: number;
  communities: Record<number, string[]>;
  node_count: number;
  relationship_count: number;
  method: string;
  write_back_failed?: boolean;
};

export type AuraCommunitiesResponse = {
  communities: Array<{
    community_id: number;
    size: number;
    members: Array<{ name: string; type: string }>;
  }>;
  count: number;
};

export type AuraCommunityStats = {
  total_communities: number;
  total_entities: number;
  entities_in_communities: number;
  coverage_percentage: number;
  size_distribution: {
    min: number;
    max: number;
    avg: number;
    median: number;
  };
};

export type AuraAnalyticsResponse = {
  most_connected?: Array<{ id: string; name: string; type: string; degree: number }>;
  importance?: Array<{ id: string; name: string; type: string; importance_score: number }>;
};

export type AuraCommunityGraphResponse = {
  nodes: Array<{
    id: string;
    label: string;
    type: string;
    community_id: number | null;
    title?: string;
  }>;
  edges: Array<{
    from: string;
    to: string;
    type: string;
    label?: string;
  }>;
  communities: number[];
  node_count: number;
  edge_count: number;
};

export async function runAuraCommunityDetection(
  params: AuraCommunityDetectionRequest
): Promise<AuraCommunityDetectionResponse> {
  return postJson<AuraCommunityDetectionRequest, AuraCommunityDetectionResponse>(
    '/aura/community-detection',
    params
  );
}

export async function fetchAuraCommunities(
  min_size: number = 3,
  limit: number = 50
): Promise<AuraCommunitiesResponse> {
  return getJson<AuraCommunitiesResponse>(`/aura/communities?min_size=${min_size}&limit=${limit}`);
}

export async function fetchAuraCommunityStats(): Promise<AuraCommunityStats> {
  return getJson<AuraCommunityStats>('/aura/community-stats');
}

export async function fetchAuraAnalytics(): Promise<AuraAnalyticsResponse> {
  try {
    const [mostConnected, importance] = await Promise.all([
      getJson<{ results: any[]; count: number }>('/analytics/most-connected?limit=20').catch(() => ({ results: [], count: 0 })),
      getJson<{ results: any[]; count: number }>('/analytics/importance?limit=20').catch(() => ({ results: [], count: 0 }))
    ]);
    return {
      most_connected: mostConnected.results || [],
      importance: importance.results || []
    };
  } catch (e) {
    return { most_connected: [], importance: [] };
  }
}

export async function fetchAuraCommunityGraph(
  communityId?: number,
  maxNodes: number = 200,
  maxCommunities: number = 10
): Promise<AuraCommunityGraphResponse> {
  const params = new URLSearchParams({
    max_nodes: maxNodes.toString(),
    max_communities: maxCommunities.toString()
  });
  if (communityId !== undefined && communityId !== null) {
    params.append('community_id', communityId.toString());
  }
  return getJson<AuraCommunityGraphResponse>(`/aura/community-graph?${params.toString()}`);
}

// Theme extraction API types
export type RecurringTheme = {
  theme: string;
  type: 'technology_trend' | 'funding_pattern' | 'partnership_pattern' | 'industry_cluster';
  frequency: number;
  description: string;
  entities: string[];
  strength: number;
};

export type RecurringThemesResponse = {
  themes: RecurringTheme[];
  count: number;
};

export type ThemeDetailsResponse = {
  // Theme metadata
  theme_name?: string;
  theme_type?: string;
  description?: string;
  error?: string;
  
  // Technology theme fields
  technology?: string;
  
  // Investor theme fields
  investor?: string;
  
  // Entity theme fields
  entity?: string;
  mention_count?: number;
  
  // Partnership theme fields
  partnerships?: Array<{
    from: string;
    to: string;
    type: string;
  }>;
  total_partnerships?: number;
  
  // Relationship fields
  relationships?: Array<{
    name: string;
    relationship: string;
  }>;
  
  // Keyword/Industry fields
  keyword?: string;
  
  // Common fields
  companies?: Array<{
    name: string;
    description?: string;
    investors?: string[];
  }>;
  total_companies?: number;
  
  // Related entities
  entities?: string[];
  
  // Community theme fields
  community_id?: number;
  total_entities?: number;
};

export async function fetchRecurringThemes(
  minFrequency: number = 3,
  limit: number = 20,
  timeWindowDays?: number
): Promise<RecurringThemesResponse> {
  const params = new URLSearchParams({
    min_frequency: minFrequency.toString(),
    limit: limit.toString()
  });
  if (timeWindowDays !== undefined) {
    params.append('time_window_days', timeWindowDays.toString());
  }
  return getJson<RecurringThemesResponse>(`/analytics/recurring-themes?${params.toString()}`);
}

export async function fetchThemeDetails(
  themeName: string,
  themeType: string
): Promise<ThemeDetailsResponse> {
  const params = new URLSearchParams({
    theme_type: themeType
  });
  // URL encode the theme name
  const encodedName = encodeURIComponent(themeName);
  return getJson<ThemeDetailsResponse>(`/analytics/theme/${encodedName}?${params.toString()}`);
}

export type ThemeSummaryResponse = {
  summary: string;
  theme_name?: string;
  theme_type?: string;
};

export async function generateThemeSummary(
  themeData: any
): Promise<ThemeSummaryResponse> {
  return postJson<any, ThemeSummaryResponse>('/analytics/theme/summary', themeData);
}

// Analytics Dashboard Types
export type AnalyticsTimeSeries = Record<string, {
  api_calls: number;
  openai_calls: number;
  neo4j_queries: number;
  query_executions: number;
  pipeline_events?: number;
  articles_scraped?: number;
  articles_extracted?: number;
  entities_extracted?: number;
  relationships_created?: number;
  openai_tokens: number;
  openai_cost: number;
  api_errors: number;
  openai_errors: number;
  avg_api_duration: number;
  avg_openai_duration: number;
}>;

export type AnalyticsDashboardResponse = {
  time_period_hours: number;
  total_records: number;
  time_series: AnalyticsTimeSeries;
  endpoints: {
    counts: Record<string, number>;
    errors: Record<string, number>;
  };
  openai_models: {
    counts: Record<string, number>;
    tokens: Record<string, number>;
    costs: Record<string, number>;
  };
  openai_operations: {
    counts: Record<string, number>;
    costs: Record<string, number>;
  };
  summary: {
    total_api_calls: number;
    total_openai_calls: number;
    total_neo4j_queries: number;
    total_query_executions: number;
    total_pipeline_events?: number;
    total_articles_scraped?: number;
    total_articles_extracted?: number;
    total_entities_extracted?: number;
    total_relationships_created?: number;
    total_openai_tokens: number;
    total_openai_cost: number;
    total_api_errors: number;
    total_openai_errors: number;
  };
  pipeline_stats?: {
    total_runs: number;
    total_articles_scraped: number;
    total_articles_extracted: number;
    total_entities_extracted: number;
    total_relationships_created: number;
    total_companies_enriched: number;
    runs_by_phase: Record<string, number>;
    last_run: {
      timestamp?: string;
      phase?: string;
      articles_scraped?: number;
      articles_extracted?: number;
      companies_enriched?: number;
    } | null;
  };
};

export type RecentCall = {
  type: 'api_call' | 'openai_call' | 'neo4j_query' | 'query_execution';
  timestamp: string;
  [key: string]: any;
};

export type RecentCallsResponse = {
  calls: RecentCall[];
  count: number;
};

export async function fetchAnalyticsDashboard(
  hours: number = 24,
  groupBy: string = 'hour'
): Promise<AnalyticsDashboardResponse> {
  return getJson<AnalyticsDashboardResponse>(
    `/analytics/dashboard?hours=${hours}&group_by=${groupBy}`
  );
}

export async function fetchRecentCalls(
  limit: number = 100,
  callType?: string
): Promise<RecentCallsResponse> {
  const params = new URLSearchParams({ limit: limit.toString() });
  if (callType) {
    params.append('call_type', callType);
  }
  return getJson<RecentCallsResponse>(`/analytics/recent-calls?${params.toString()}`);
}

// Evaluation Types
export type EvaluationQuery = {
  query: string;
  expected_answer?: string;
};

export type EvaluationResult = {
  query: string;
  expected_answer?: string;
  actual_answer?: string;
  latency_ms: number;
  tokens_used: number;
  cost_usd: number;
  relevance_score: number;
  accuracy_score: number;
  completeness_score: number;
  coherence_score: number;
  context_relevance: number;
  answer_faithfulness: number;
  answer_relevancy: number;
  cache_hit: boolean;
  success: boolean;
  error?: string;
  timestamp: string;
  logs?: string[];
  calculation_details?: Record<string, any>;
  intent_classified?: string;
  context_size?: number;
  context_entities?: string[];
};

export type EvaluationSummary = {
  total_queries: number;
  successful_queries: number;
  failed_queries: number;
  avg_latency_ms: number;
  p50_latency_ms: number;
  p95_latency_ms: number;
  p99_latency_ms: number;
  total_tokens: number;
  total_cost_usd: number;
  avg_relevance: number;
  avg_accuracy: number;
  avg_completeness: number;
  avg_coherence: number;
  avg_context_relevance: number;
  avg_answer_faithfulness: number;
  avg_answer_relevancy: number;
  cache_hit_rate: number;
  error_rate: number;
};

export type EvaluationResponse = {
  summary: EvaluationSummary;
  results: EvaluationResult[];
};

export type EvaluationRequest = {
  queries: EvaluationQuery[];
  use_llm?: boolean;
  use_sample_dataset?: boolean;
};

export async function runEvaluation(
  request: EvaluationRequest
): Promise<EvaluationResponse> {
  return postJson<EvaluationRequest, EvaluationResponse>('/evaluation/run', request);
}

export async function getSampleEvaluationDataset(): Promise<{ queries: EvaluationQuery[] }> {
  return getJson<{ queries: EvaluationQuery[] }>('/evaluation/sample-dataset');
}


