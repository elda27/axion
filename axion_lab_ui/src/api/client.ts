import type {
  CursorPaginatedResponse,
  OrgResponse,
  OrgCreate,
  ProjectResponse,
  ProjectCreate,
  BatchResponse,
  BatchCreate,
  RunResponse,
  RunCreate,
  RunUpdate,
  RunSummaryResponse,
  ArtifactResponse,
  ArtifactCreate,
  PinResponse,
  PinCreate,
  PinType,
  RunMetricResponse,
  ComparisonIndicatorResponse,
  DPJobResponse,
  DPJobCreate,
  AggregationResponse,
  AggregationCreate,
  AggregationMemberResponse,
  AggregationMemberAdd,
} from "../types";

const BASE = "/api/v1";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...init?.headers },
    ...init,
  });
  if (res.status === 204) return undefined as T;
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`API ${res.status}: ${text}`);
  }
  return res.json() as Promise<T>;
}

// ── Orgs ──

export function createOrg(data: OrgCreate) {
  return request<OrgResponse>("/orgs", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function listOrgs(limit = 20, cursor?: string) {
  const params = new URLSearchParams({ limit: String(limit) });
  if (cursor) params.set("cursor", cursor);
  return request<CursorPaginatedResponse<OrgResponse>>(`/orgs?${params}`);
}

export function getOrg(orgId: string) {
  return request<OrgResponse>(`/orgs/${orgId}`);
}

// ── Projects ──

export function createProject(orgId: string, data: ProjectCreate) {
  return request<ProjectResponse>(`/orgs/${orgId}/projects`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function listProjects(orgId: string, limit = 20, cursor?: string) {
  const params = new URLSearchParams({ limit: String(limit) });
  if (cursor) params.set("cursor", cursor);
  return request<CursorPaginatedResponse<ProjectResponse>>(
    `/orgs/${orgId}/projects?${params}`,
  );
}

export function getProject(projectId: string) {
  return request<ProjectResponse>(`/projects/${projectId}`);
}

// ── Batches ──

export function createBatch(projectId: string, data: BatchCreate) {
  return request<BatchResponse>(`/projects/${projectId}/batches`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function listBatches(projectId: string, limit = 20, cursor?: string) {
  const params = new URLSearchParams({ limit: String(limit) });
  if (cursor) params.set("cursor", cursor);
  return request<CursorPaginatedResponse<BatchResponse>>(
    `/projects/${projectId}/batches?${params}`,
  );
}

export function getBatch(batchId: string) {
  return request<BatchResponse>(`/batches/${batchId}`);
}

// ── Runs ──

export function createRun(batchId: string, data: RunCreate) {
  return request<RunResponse>(`/batches/${batchId}/runs`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function listRuns(
  batchId: string,
  opts: {
    status?: string;
    includeGarbage?: boolean;
    tag?: string;
    q?: string;
    limit?: number;
    cursor?: string;
  } = {},
) {
  const params = new URLSearchParams();
  if (opts.limit) params.set("limit", String(opts.limit));
  if (opts.cursor) params.set("cursor", opts.cursor);
  if (opts.status) params.set("status", opts.status);
  if (opts.includeGarbage) params.set("include_garbage", "true");
  if (opts.tag) params.set("tag", opts.tag);
  if (opts.q) params.set("q", opts.q);
  return request<CursorPaginatedResponse<RunResponse>>(
    `/batches/${batchId}/runs?${params}`,
  );
}

export function getRunSummary(batchId: string, includeGarbage = false) {
  const params = new URLSearchParams();
  if (includeGarbage) params.set("include_garbage", "true");
  return request<RunSummaryResponse>(
    `/batches/${batchId}/runs/summary?${params}`,
  );
}

export function getRun(runId: string) {
  return request<RunResponse>(`/runs/${runId}`);
}

export function updateRun(runId: string, data: RunUpdate) {
  return request<RunResponse>(`/runs/${runId}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

// ── Artifacts ──

export function createArtifact(runId: string, data: ArtifactCreate) {
  return request<ArtifactResponse>(`/runs/${runId}/artifacts`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function listArtifacts(runId: string, limit = 100, cursor?: string) {
  const params = new URLSearchParams({ limit: String(limit) });
  if (cursor) params.set("cursor", cursor);
  return request<CursorPaginatedResponse<ArtifactResponse>>(
    `/runs/${runId}/artifacts?${params}`,
  );
}

export function deleteArtifact(artifactId: string) {
  return request<void>(`/artifacts/${artifactId}`, { method: "DELETE" });
}

// ── Pins ──

export function createPin(runId: string, data: PinCreate) {
  return request<PinResponse>(`/runs/${runId}/pins`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function deletePin(runId: string, pinType: PinType) {
  return request<void>(`/runs/${runId}/pins/${pinType}`, {
    method: "DELETE",
  });
}

// ── Run Metrics ──

export function getRunMetrics(runId: string) {
  return request<RunMetricResponse[]>(`/runs/${runId}/run-metrics`);
}

export function getBatchRunMetrics(
  batchId: string,
  key?: string,
  limit = 100,
  cursor?: string,
) {
  const params = new URLSearchParams({ limit: String(limit) });
  if (key) params.set("key", key);
  if (cursor) params.set("cursor", cursor);
  return request<CursorPaginatedResponse<RunMetricResponse>>(
    `/batches/${batchId}/run-metrics?${params}`,
  );
}

// ── Comparison Indicators ──

export function getRunComparisonIndicators(runId: string) {
  return request<ComparisonIndicatorResponse[]>(
    `/runs/${runId}/comparison-indicators`,
  );
}

export function getBatchComparisonIndicators(
  batchId: string,
  key?: string,
  limit = 100,
  cursor?: string,
) {
  const params = new URLSearchParams({ limit: String(limit) });
  if (key) params.set("key", key);
  if (cursor) params.set("cursor", cursor);
  return request<CursorPaginatedResponse<ComparisonIndicatorResponse>>(
    `/batches/${batchId}/comparison-indicators?${params}`,
  );
}

// ── DP Jobs ──

export function triggerDPCompute(batchId: string, data: DPJobCreate = {}) {
  return request<DPJobResponse>(`/batches/${batchId}/dp/compute`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function getDPJob(jobId: string) {
  return request<DPJobResponse>(`/dp/jobs/${jobId}`);
}

// ── Aggregations ──

export function createAggregation(projectId: string, data: AggregationCreate) {
  return request<AggregationResponse>(`/projects/${projectId}/aggregations`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function listAggregations(
  projectId: string,
  limit = 20,
  cursor?: string,
) {
  const params = new URLSearchParams({ limit: String(limit) });
  if (cursor) params.set("cursor", cursor);
  return request<CursorPaginatedResponse<AggregationResponse>>(
    `/projects/${projectId}/aggregations?${params}`,
  );
}

export function getAggregation(aggregationId: string) {
  return request<AggregationResponse>(`/aggregations/${aggregationId}`);
}

export function deleteAggregation(aggregationId: string) {
  return request<void>(`/aggregations/${aggregationId}`, {
    method: "DELETE",
  });
}

export function addAggregationMember(
  aggregationId: string,
  data: AggregationMemberAdd,
) {
  return request<AggregationMemberResponse>(
    `/aggregations/${aggregationId}/members`,
    {
      method: "POST",
      body: JSON.stringify(data),
    },
  );
}

export function listAggregationMembers(
  aggregationId: string,
  limit = 100,
  cursor?: string,
) {
  const params = new URLSearchParams({ limit: String(limit) });
  if (cursor) params.set("cursor", cursor);
  return request<CursorPaginatedResponse<AggregationMemberResponse>>(
    `/aggregations/${aggregationId}/members?${params}`,
  );
}

export function removeAggregationMember(aggregationId: string, runId: string) {
  return request<void>(`/aggregations/${aggregationId}/members/${runId}`, {
    method: "DELETE",
  });
}

export function getAggregationRunMetrics(
  aggregationId: string,
  key?: string,
  limit = 100,
  cursor?: string,
) {
  const params = new URLSearchParams({ limit: String(limit) });
  if (key) params.set("key", key);
  if (cursor) params.set("cursor", cursor);
  return request<CursorPaginatedResponse<RunMetricResponse>>(
    `/aggregations/${aggregationId}/run-metrics?${params}`,
  );
}

export function getAggregationComparisonIndicators(
  aggregationId: string,
  key?: string,
  limit = 100,
  cursor?: string,
) {
  const params = new URLSearchParams({ limit: String(limit) });
  if (key) params.set("key", key);
  if (cursor) params.set("cursor", cursor);
  return request<CursorPaginatedResponse<ComparisonIndicatorResponse>>(
    `/aggregations/${aggregationId}/comparison-indicators?${params}`,
  );
}
