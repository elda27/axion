// ── Pagination ──
export interface CursorPaginatedResponse<T> {
  items: T[];
  next_cursor: string | null;
  has_more: boolean;
}

// ── Org ──
export interface OrgResponse {
  orgId: string;
  name: string;
  createdAt: string;
}

export interface OrgCreate {
  name: string;
}

// ── Project ──
export interface ProjectResponse {
  projectId: string;
  orgId: string;
  name: string;
  createdAt: string;
}

export interface ProjectCreate {
  name: string;
}

// ── Batch ──
export interface BatchResponse {
  batchId: string;
  projectId: string;
  name: string;
  createdAt: string;
}

export interface BatchCreate {
  name: string;
}

// ── Run ──
export type RunStatus = "active" | "garbage" | "archived";

export interface RunResponse {
  runId: string;
  batchId: string;
  name: string;
  status: RunStatus;
  tags: string[];
  note: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface RunCreate {
  name: string;
  status?: RunStatus;
  tags?: string[];
  note?: string;
}

export interface RunUpdate {
  name?: string;
  status?: RunStatus;
  tags?: string[];
  note?: string;
}

export interface RunBriefResponse {
  runId: string;
  name: string;
}

export interface RunSummaryResponse {
  champion: RunBriefResponse | null;
  recentCollapsed: {
    defaultOpen: boolean;
    runs: RunBriefResponse[];
  };
  userSelected: RunBriefResponse[];
  others: {
    cursor: string | null;
    runs: RunBriefResponse[];
  };
}

// ── Artifact ──
export type ArtifactKind =
  | "url"
  | "local"
  | "inline_text"
  | "inline_number"
  | "inline_json";

export type ArtifactType =
  | "langfuse_trace"
  | "object_storage"
  | "note"
  | "dashboard"
  | "git_commit"
  | "file"
  | "evaluation"
  | "latency_p95_ms"
  | "cost_usd"
  | "other";

export interface ArtifactResponse {
  artifactId: string;
  runId: string;
  kind: ArtifactKind;
  type: ArtifactType;
  label: string;
  payload: unknown;
  meta: Record<string, unknown>;
  createdAt: string;
}

export interface ArtifactCreate {
  kind: ArtifactKind;
  type: ArtifactType;
  label: string;
  payload: unknown;
  meta?: Record<string, unknown>;
}

// ── Pin ──
export type PinType = "champion" | "user_selected";

export interface PinResponse {
  pinId: string;
  runId: string;
  batchId: string;
  pinType: PinType;
  pinnedBy: string | null;
  pinnedAt: string;
}

export interface PinCreate {
  pinType: PinType;
}

// ── Quality Metric ──
export type QualityMetricSource = "raw" | "derived" | "manual";

export interface QualityMetricResponse {
  qmId: string;
  runId: string;
  key: string;
  value: unknown;
  source: QualityMetricSource;
  computedAt: string;
  version: number;
}

// ── Comparison Indicator ──
export interface ComparisonIndicatorResponse {
  ciId: string;
  runId: string;
  key: string;
  value: unknown;
  baselineRef: string | null;
  computedAt: string;
  version: number;
}

// ── DP Job ──
export type DPJobMode = "active_only" | "include_garbage";
export type DPJobStatus =
  | "queued"
  | "running"
  | "succeeded"
  | "failed"
  | "canceled";

export interface DPJobCreate {
  mode?: DPJobMode;
  recompute?: boolean;
}

export interface DPJobResponse {
  jobId: string;
  batchId: string;
  mode: DPJobMode;
  recompute: boolean;
  status: DPJobStatus;
  requestedBy: string | null;
  createdAt: string;
  startedAt: string | null;
  finishedAt: string | null;
  errorText: string | null;
}

// ── Aggregation ──
export interface AggregationResponse {
  aggregationId: string;
  projectId: string;
  name: string;
  description: string | null;
  groupByKeys: string[];
  filter: Record<string, unknown>;
  createdAt: string;
  memberCount: number;
}

export interface AggregationCreate {
  name: string;
  description?: string;
  groupByKeys?: string[];
  filter?: Record<string, unknown>;
}

export interface AggregationMemberResponse {
  memberId: string;
  aggregationId: string;
  runId: string;
  metadata: Record<string, unknown>;
  addedAt: string;
}

export interface AggregationMemberAdd {
  runId: string;
  metadata?: Record<string, unknown>;
}
