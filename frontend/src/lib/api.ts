export const API_BASE_URL: string = (import.meta as any).env?.VITE_API_BASE_URL || 'http://localhost:8000';

export type QueryRequest = {
  question: string;
  return_context?: boolean;
  use_llm?: boolean;
};

export type QueryResponse = {
  question: string;
  intent: Record<string, unknown>;
  answer?: string | null;
  context?: unknown;
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
    throw new Error(text || `HTTP ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export async function postJson<TReq, TRes>(path: string, body: TReq): Promise<TRes> {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  });
  return handleResponse<TRes>(res);
}

export async function getJson<TRes>(path: string): Promise<TRes> {
  const res = await fetch(`${API_BASE_URL}${path}`);
  return handleResponse<TRes>(res);
}

export async function getText(path: string): Promise<string> {
  const res = await fetch(`${API_BASE_URL}${path}`);
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

export async function fetchPipelineLogs(tail = 200): Promise<string> {
  const res = await getJson<{ log: string }>(`/admin/pipeline/logs?tail=${tail}`);
  return res.log || '';
}


