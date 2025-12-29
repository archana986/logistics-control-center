import type { Center, Lane, Incident, Shipment, RerouteSuggestion, Customer, CapacityLane, CapacityAction, AgentActivity, SalesOpportunity } from "../types/domain";

// Get backend URL from environment variable
// In production (Databricks Apps), this will be "/api"
// In development, use full URL to the backend server
const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || "http://localhost:8001/api";

const sleep = (ms: number) => new Promise(r => setTimeout(r, ms));

export async function getCenters(): Promise<Center[]> {
  await sleep(250);
  try {
    const response = await fetch(`${BACKEND_URL}/centers`);
    if (!response.ok) throw new Error('Backend unavailable');
    return response.json();
  } catch (error) {
    // Fallback to local mock data if backend is unavailable
    console.warn('Backend unavailable, using local mock data:', error);
    const response = await fetch("/mock/centers.json");
    return response.json();
  }
}

export async function getLanes(): Promise<Lane[]> {
  await sleep(350);
  const response = await fetch("/mock/lanes.json");
  return response.json();
}

export async function getIncidents(laneId?: string): Promise<Incident[]> {
  await sleep(300);
  const response = await fetch("/mock/incidents.json");
  const all: Incident[] = await response.json();
  return laneId ? all.filter((i) => i.laneId === laneId) : all;
}

export async function getUrgentShipments(laneId: string): Promise<Shipment[]> {
  await sleep(300);
  try {
    const response = await fetch(`${BACKEND_URL}/shipments`);
    if (!response.ok) throw new Error('Backend unavailable');
    const all: Shipment[] = await response.json();
    return all.filter((s) => s.laneId === laneId && s.priority === "HIGH");
  } catch (error) {
    // Fallback to local mock data
    console.warn('Backend unavailable, using local mock data:', error);
    const response = await fetch("/mock/shipments.json");
    const all: Shipment[] = await response.json();
    return all.filter((s) => s.laneId === laneId && s.priority === "HIGH");
  }
}

export async function getRerouteSuggestions(laneId: string): Promise<RerouteSuggestion[]> {
  await sleep(400);
  const response = await fetch("/mock/reroute_solutions.json");
  const all: RerouteSuggestion[] = await response.json();
  return all.filter((r) => r.laneId === laneId);
}

export async function getCustomers(ids?: string[]): Promise<Customer[]> {
  await sleep(200);
  try {
    const response = await fetch(`${BACKEND_URL}/customers`);
    if (!response.ok) throw new Error('Backend unavailable');
    const all: Customer[] = await response.json();
    return ids ? all.filter((c) => ids.includes(c.id)) : all;
  } catch (error) {
    // Fallback to local mock data
    console.warn('Backend unavailable, using local mock data:', error);
    const response = await fetch("/mock/customers.json");
    const all: Customer[] = await response.json();
    return ids ? all.filter((c) => ids.includes(c.id)) : all;
  }
}

export async function getAllShipments(): Promise<Shipment[]> {
  await sleep(200);
  try {
    const response = await fetch(`${BACKEND_URL}/shipments`);
    if (!response.ok) throw new Error('Backend unavailable');
    return response.json();
  } catch (error) {
    // Fallback to local mock data
    console.warn('Backend unavailable, using local mock data:', error);
    const response = await fetch("/mock/shipments.json");
    return response.json();
  }
}

export async function getCapacityLanes(): Promise<CapacityLane[]> {
  await sleep(350);
  try {
    const response = await fetch(`${BACKEND_URL}/capacity/lanes`);
    if (!response.ok) throw new Error('Backend unavailable');
    return response.json();
  } catch (error) {
    // Fallback to local mock data
    console.warn('Backend unavailable, using local mock data:', error);
    const response = await fetch("/mock/capacity_lanes.json");
    return response.json();
  }
}

export async function getCapacityActions(laneId: string): Promise<CapacityAction[]> {
  await sleep(300);
  try {
    const response = await fetch(`${BACKEND_URL}/capacity/actions/${laneId}`);
    if (!response.ok) throw new Error('Backend unavailable');
    return response.json();
  } catch (error) {
    // Fallback to local mock data
    console.warn('Backend unavailable, using local mock data:', error);
    const response = await fetch("/mock/capacity_actions.json");
    const all: Record<string, CapacityAction[]> = await response.json();
    return all[laneId] || [];
  }
}

export async function getAgentActivities(laneId?: string): Promise<AgentActivity[]> {
  await sleep(250);
  const response = await fetch("/mock/agent_activities.json");
  const all: AgentActivity[] = await response.json();
  return laneId ? all.filter((a) => a.laneId === laneId) : all;
}

export async function getSalesOpportunity(laneId: string, activityId: string): Promise<SalesOpportunity | null> {
  await sleep(300);
  const response = await fetch("/mock/sales_opportunities.json");
  const all: SalesOpportunity[] = await response.json();
  return all.find((o) => o.laneId === laneId && o.activityId === activityId) || null;
}

