/**
 * Manual API client functions for the Staffing Optimization app.
 * These complement the auto-generated functions from orval.
 */
import axios from "axios";

const api = axios.create({
  baseURL: "/api",
});

// ============== Workspace Info ==============

export interface WorkspaceInfo {
  host?: string | null;
  databricks_job_id?: number | null;
}

export async function getWorkspaceInfo(): Promise<WorkspaceInfo> {
  const { data } = await api.get<WorkspaceInfo>("/workspace-info");
  return data;
}

// ============== Types ==============

export interface CatalogInfo {
  name: string;
  comment?: string | null;
}

export interface SchemaInfo {
  name: string;
  catalog_name: string;
  comment?: string | null;
}

export interface TableInfo {
  name: string;
  catalog_name: string;
  schema_name: string;
  table_type: string;
  comment?: string | null;
}

export interface ColumnInfo {
  name: string;
  type_name: string;
  comment?: string | null;
}

export interface TableColumnsOut {
  table: TableInfo;
  columns: ColumnInfo[];
}

export interface OptimizationConfig {
  id: string;
  name: string;
  description?: string | null;
  owner_user?: string | null;
  source_catalog: string;
  source_schema: string;
  workers_table: string;
  shifts_table: string;
  availability_table: string;
  worker_name_col: string;
  worker_pay_col: string;
  shift_name_col: string;
  shift_required_col: string;
  availability_worker_col: string;
  availability_shift_col: string;
  max_shifts_per_worker?: number | null;
  time_limit_seconds: number;
  target_catalog?: string | null;
  target_schema?: string | null;
  results_table?: string | null;
  databricks_job_id?: number | null;
  created_at: string;
  updated_at: string;
}

export interface OptimizationConfigCreate {
  name: string;
  description?: string;
  source_catalog: string;
  source_schema: string;
  workers_table: string;
  shifts_table: string;
  availability_table: string;
  worker_name_col?: string;
  worker_pay_col?: string;
  shift_name_col?: string;
  shift_required_col?: string;
  availability_worker_col?: string;
  availability_shift_col?: string;
  max_shifts_per_worker?: number;
  time_limit_seconds?: number;
  target_catalog?: string;
  target_schema?: string;
  results_table?: string;
}

export type RunStatus = "PENDING" | "RUNNING" | "COMPLETED" | "FAILED" | "CANCELLED";

export interface OptimizationRun {
  id: string;
  config_id: string;
  run_name?: string | null;
  owner_user?: string | null;
  status: RunStatus;
  databricks_run_id?: number | null;
  total_cost?: number | null;
  solve_time_seconds?: number | null;
  num_workers_assigned?: number | null;
  num_shifts_covered?: number | null;
  error_message?: string | null;
  created_at: string;
  updated_at: string;
  completed_at?: string | null;
}

export interface OptimizationRunCreate {
  config_id: string;
  run_name?: string;
}

export interface AssignmentResult {
  worker_name: string;
  shift_name: string;
  cost: number;
}

export interface OptimizationResult {
  run_id: string;
  status: RunStatus;
  total_cost?: number | null;
  solve_time_seconds?: number | null;
  assignments: AssignmentResult[];
  worker_summary: Record<string, { shifts: string[]; total_cost: number }>;
  shift_summary: Record<string, { workers: string[]; assigned: number }>;
}

export interface GenerateSampleDataRequest {
  catalog: string;
  schema: string;
  num_workers?: number;
  num_shifts?: number;
  min_pay?: number;
  max_pay?: number;
  avg_availability_pct?: number;
  dataset_label?: string;
}

export interface GenerateSampleDataResponse {
  dataset_label?: string | null;
  workers_table: string;
  shifts_table: string;
  availability_table: string;
  num_workers: number;
  num_shifts: number;
  num_availability_records: number;
}

// ============== Unity Catalog ==============

export async function listCatalogs(): Promise<CatalogInfo[]> {
  const { data } = await api.get<CatalogInfo[]>("/catalogs");
  return data;
}

export async function listSchemas(catalogName: string): Promise<SchemaInfo[]> {
  const { data } = await api.get<SchemaInfo[]>(`/catalogs/${catalogName}/schemas`);
  return data;
}

export async function listTables(catalogName: string, schemaName: string): Promise<TableInfo[]> {
  const { data } = await api.get<TableInfo[]>(
    `/catalogs/${catalogName}/schemas/${schemaName}/tables`
  );
  return data;
}

export async function getTableColumns(
  catalogName: string,
  schemaName: string,
  tableName: string
): Promise<TableColumnsOut> {
  const { data } = await api.get<TableColumnsOut>(
    `/catalogs/${catalogName}/schemas/${schemaName}/tables/${tableName}/columns`
  );
  return data;
}

// ============== Sample Data ==============

export async function generateSampleData(
  request: GenerateSampleDataRequest
): Promise<GenerateSampleDataResponse> {
  const { data } = await api.post<GenerateSampleDataResponse>("/generate-sample-data", request);
  return data;
}

// ============== Configurations ==============

export async function listConfigs(): Promise<OptimizationConfig[]> {
  const { data } = await api.get<OptimizationConfig[]>("/configs");
  return data;
}

export async function getConfig(configId: string): Promise<OptimizationConfig> {
  const { data } = await api.get<OptimizationConfig>(`/configs/${configId}`);
  return data;
}

export async function createConfig(config: OptimizationConfigCreate): Promise<OptimizationConfig> {
  const { data } = await api.post<OptimizationConfig>("/configs", config);
  return data;
}

export async function updateConfig(
  configId: string,
  config: OptimizationConfigCreate
): Promise<OptimizationConfig> {
  const { data } = await api.put<OptimizationConfig>(`/configs/${configId}`, config);
  return data;
}

export async function deleteConfig(configId: string): Promise<void> {
  await api.delete(`/configs/${configId}`);
}

// ============== Runs ==============

export async function listRuns(configId?: string): Promise<OptimizationRun[]> {
  const params = configId ? { config_id: configId } : {};
  const { data } = await api.get<OptimizationRun[]>("/runs", { params });
  return data;
}

export async function getRun(runId: string): Promise<OptimizationRun> {
  const { data } = await api.get<OptimizationRun>(`/runs/${runId}`);
  return data;
}

export async function createRun(run: OptimizationRunCreate): Promise<OptimizationRun> {
  const { data } = await api.post<OptimizationRun>("/runs", run);
  return data;
}

export async function cancelRun(runId: string): Promise<void> {
  await api.post(`/runs/${runId}/cancel`);
}

export async function refreshRunStatus(runId: string): Promise<OptimizationRun> {
  const { data } = await api.post<OptimizationRun>(`/runs/${runId}/refresh`);
  return data;
}

// ============== Results (legacy full-payload, kept for small datasets) ==============

export async function getRunResults(runId: string): Promise<OptimizationResult> {
  const { data } = await api.get<OptimizationResult>(`/runs/${runId}/results`);
  return data;
}

export async function exportRunResults(runId: string, format: "csv" | "json"): Promise<Blob> {
  const { data } = await api.get(`/runs/${runId}/export`, {
    params: { format },
    responseType: "blob",
  });
  return data;
}

export async function saveResultsToTable(
  runId: string,
  catalog: string,
  schemaName: string,
  tableName: string
): Promise<{ status: string; table: string; rows: number }> {
  const { data } = await api.post(`/runs/${runId}/save-to-table`, null, {
    params: { catalog, schema_name: schemaName, table_name: tableName },
  });
  return data;
}

// ============== Scalable / Paginated Results ==============

export interface PaginationMeta {
  offset: number;
  limit: number;
  total: number;
  has_more: boolean;
}

export interface RunResultsSummary {
  run_id: string;
  status: RunStatus;
  total_cost?: number | null;
  solve_time_seconds?: number | null;
  num_workers_assigned?: number | null;
  num_shifts_covered?: number | null;
  total_assignments: number;
  avg_cost_per_assignment?: number | null;
  min_assignment_cost?: number | null;
  max_assignment_cost?: number | null;
}

export interface PagedAssignments {
  run_id: string;
  assignments: AssignmentResult[];
  pagination: PaginationMeta;
}

export interface ShiftAggregate {
  shift_name: string;
  assigned_count: number;
  total_cost: number;
}

export interface PagedShiftAggregates {
  run_id: string;
  shifts: ShiftAggregate[];
  pagination: PaginationMeta;
}

export interface WorkerAggregate {
  worker_name: string;
  shift_count: number;
  total_cost: number;
}

export interface PagedWorkerAggregates {
  run_id: string;
  workers: WorkerAggregate[];
  pagination: PaginationMeta;
}

export interface GraphNode {
  id: string;
  kind: "worker" | "shift";
  label: string;
  totalCost?: number;
  assignedCount?: number;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  cost: number;
  workerName: string;
  shiftName: string;
}

export interface GraphSubset {
  run_id: string;
  focus_entity?: string | null;
  focus_type?: string | null;
  nodes: GraphNode[];
  edges: GraphEdge[];
  total_nodes: number;
  total_edges: number;
  is_complete: boolean;
}

export async function getRunResultsSummary(runId: string): Promise<RunResultsSummary> {
  const { data } = await api.get<RunResultsSummary>(`/runs/${runId}/results/summary`);
  return data;
}

export async function getPagedAssignments(
  runId: string,
  params: { limit?: number; offset?: number; sort?: string; sort_dir?: string } = {},
): Promise<PagedAssignments> {
  const { data } = await api.get<PagedAssignments>(`/runs/${runId}/results/assignments`, { params });
  return data;
}

export async function getShiftAggregates(
  runId: string,
  params: { limit?: number; offset?: number; sort?: string; sort_dir?: string } = {},
): Promise<PagedShiftAggregates> {
  const { data } = await api.get<PagedShiftAggregates>(`/runs/${runId}/results/by-shift`, { params });
  return data;
}

export async function getShiftAssignments(
  runId: string,
  shiftName: string,
  params: { limit?: number; offset?: number } = {},
): Promise<PagedAssignments> {
  const { data } = await api.get<PagedAssignments>(
    `/runs/${runId}/results/by-shift/${encodeURIComponent(shiftName)}/assignments`,
    { params },
  );
  return data;
}

export async function getWorkerAggregates(
  runId: string,
  params: { limit?: number; offset?: number; sort?: string; sort_dir?: string } = {},
): Promise<PagedWorkerAggregates> {
  const { data } = await api.get<PagedWorkerAggregates>(`/runs/${runId}/results/by-worker`, { params });
  return data;
}

export async function getWorkerAssignments(
  runId: string,
  workerName: string,
  params: { limit?: number; offset?: number } = {},
): Promise<PagedAssignments> {
  const { data } = await api.get<PagedAssignments>(
    `/runs/${runId}/results/by-worker/${encodeURIComponent(workerName)}/assignments`,
    { params },
  );
  return data;
}

export async function getFocusedGraph(
  runId: string,
  params: { shift_name?: string; worker_name?: string; limit?: number } = {},
): Promise<GraphSubset> {
  const { data } = await api.get<GraphSubset>(`/runs/${runId}/graph/focused`, { params });
  return data;
}
