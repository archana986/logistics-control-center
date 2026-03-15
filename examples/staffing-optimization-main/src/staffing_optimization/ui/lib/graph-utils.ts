/**
 * Graph utilities for transforming optimization results to Cytoscape format
 */
import type { OptimizationResult } from "./api-client";

export type NodeKind = "worker" | "shift";

export interface GraphNodeData {
  id: string;
  kind: NodeKind;
  label: string;
  shiftCount?: number;
  assignedCount?: number;
  totalCost?: number;
}

export interface GraphEdgeData {
  id: string;
  source: string;
  target: string;
  cost: number;
  workerName: string;
  shiftName: string;
}

export interface GraphNode {
  data: GraphNodeData;
}

export interface GraphEdge {
  data: GraphEdgeData;
}

export interface GraphElements {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface GraphStats {
  workerCount: number;
  shiftCount: number;
  assignmentCount: number;
  totalCost: number;
  avgCostPerAssignment: number;
  minCost: number;
  maxCost: number;
}

/**
 * Transform optimization results into Cytoscape graph elements
 */
export function transformResultsToGraph(results: OptimizationResult): GraphElements {
  const nodes: GraphNode[] = [];
  const edges: GraphEdge[] = [];

  // Create worker nodes from worker_summary
  for (const [workerName, summary] of Object.entries(results.worker_summary)) {
    nodes.push({
      data: {
        id: `worker-${workerName}`,
        kind: "worker",
        label: workerName,
        shiftCount: summary.shifts?.length ?? 0,
        totalCost: summary.total_cost ?? 0,
      },
    });
  }

  // Create shift nodes from shift_summary
  for (const [shiftName, summary] of Object.entries(results.shift_summary)) {
    nodes.push({
      data: {
        id: `shift-${shiftName}`,
        kind: "shift",
        label: shiftName,
        assignedCount: summary.assigned ?? 0,
      },
    });
  }

  // Create edges from assignments
  for (const assignment of results.assignments) {
    edges.push({
      data: {
        id: `edge-${assignment.worker_name}-${assignment.shift_name}`,
        source: `worker-${assignment.worker_name}`,
        target: `shift-${assignment.shift_name}`,
        cost: assignment.cost,
        workerName: assignment.worker_name,
        shiftName: assignment.shift_name,
      },
    });
  }

  return { nodes, edges };
}

/**
 * Calculate statistics from graph elements
 */
export function calculateGraphStats(elements: GraphElements): GraphStats {
  const workerCount = elements.nodes.filter((n) => n.data.kind === "worker").length;
  const shiftCount = elements.nodes.filter((n) => n.data.kind === "shift").length;
  const assignmentCount = elements.edges.length;

  const costs = elements.edges.map((e) => e.data.cost);
  const totalCost = costs.reduce((sum, c) => sum + c, 0);
  const minCost = costs.length > 0 ? Math.min(...costs) : 0;
  const maxCost = costs.length > 0 ? Math.max(...costs) : 0;
  const avgCostPerAssignment = assignmentCount > 0 ? totalCost / assignmentCount : 0;

  return {
    workerCount,
    shiftCount,
    assignmentCount,
    totalCost,
    avgCostPerAssignment,
    minCost,
    maxCost,
  };
}

export interface FilterState {
  search: string;
  costRange: [number, number];
  showWorkers: boolean;
  showShifts: boolean;
}

export const defaultFilterState: FilterState = {
  search: "",
  costRange: [0, Infinity],
  showWorkers: true,
  showShifts: true,
};

/**
 * Apply filters to graph elements
 */
export function applyFilters(
  elements: GraphElements,
  filters: FilterState
): GraphElements {
  const searchLower = filters.search.toLowerCase();

  // First pass: find nodes that match the search term
  const matchingNodeIds = new Set<string>();
  
  if (searchLower) {
    for (const node of elements.nodes) {
      if (node.data.label.toLowerCase().includes(searchLower)) {
        matchingNodeIds.add(node.data.id);
      }
    }
  }

  // Find connected nodes (neighbors of matching nodes via edges)
  const connectedNodeIds = new Set<string>();
  if (searchLower && matchingNodeIds.size > 0) {
    for (const edge of elements.edges) {
      if (matchingNodeIds.has(edge.data.source)) {
        connectedNodeIds.add(edge.data.target);
      }
      if (matchingNodeIds.has(edge.data.target)) {
        connectedNodeIds.add(edge.data.source);
      }
    }
  }

  // Filter nodes
  const filteredNodes = elements.nodes.filter((node) => {
    // Kind filter (only apply when not searching, or node is a match/connected)
    if (node.data.kind === "worker" && !filters.showWorkers) return false;
    if (node.data.kind === "shift" && !filters.showShifts) return false;

    // Search filter: include if matches OR is connected to a match
    if (searchLower) {
      const isMatch = matchingNodeIds.has(node.data.id);
      const isConnected = connectedNodeIds.has(node.data.id);
      if (!isMatch && !isConnected) {
        return false;
      }
    }

    return true;
  });

  const candidateNodeIds = new Set(filteredNodes.map((n) => n.data.id));

  // Filter edges - only show edges where both endpoints are visible
  // and cost is within range.
  const filteredEdges = elements.edges.filter((edge) => {
    if (!candidateNodeIds.has(edge.data.source)) return false;
    if (!candidateNodeIds.has(edge.data.target)) return false;

    const [minCost, maxCost] = filters.costRange;
    if (edge.data.cost < minCost || edge.data.cost > maxCost) return false;

    return true;
  });

  // Keep only nodes that still participate in at least one visible edge.
  // This makes cost filtering remove disconnected nodes and automatically
  // add them back when the range changes to include them.
  const visibleNodeIds = new Set<string>();
  for (const edge of filteredEdges) {
    visibleNodeIds.add(edge.data.source);
    visibleNodeIds.add(edge.data.target);
  }

  const finalNodes = filteredNodes.filter((node) => visibleNodeIds.has(node.data.id));

  return {
    nodes: finalNodes,
    edges: filteredEdges,
  };
}

/**
 * Get Cytoscape-compatible elements array
 */
export function toCytoscapeElements(
  elements: GraphElements
): cytoscape.ElementDefinition[] {
  return [
    ...elements.nodes.map((n) => ({ data: n.data, group: "nodes" as const })),
    ...elements.edges.map((e) => ({ data: e.data, group: "edges" as const })),
  ];
}
