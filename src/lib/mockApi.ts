import type {
  Center,
  Lane,
  Incident,
  ShipmentLaneMetric,
  RerouteSuggestion,
  Customer,
  CapacityLane,
  CapacityAction,
  AgentActivity,
  SalesOpportunity,
} from "../types/domain";

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
    console.error('Backend unavailable for centers:', error);
    return [];
  }
}

export async function getLanes(): Promise<Lane[]> {
  await sleep(350);
  try {
    const response = await fetch(`${BACKEND_URL}/lanes`);
    if (!response.ok) throw new Error('Backend unavailable');
    return response.json();
  } catch (error) {
    console.error('Backend unavailable for lanes:', error);
    return [];
  }
}

export async function getIncidents(laneId?: string): Promise<Incident[]> {
  await sleep(300);
  try {
    const url = laneId ? `${BACKEND_URL}/incidents?laneId=${laneId}` : `${BACKEND_URL}/incidents`;
    const response = await fetch(url);
    if (!response.ok) throw new Error('Backend unavailable');
    return response.json();
  } catch (error) {
    console.error('Backend unavailable for incidents:', error);
    return [];
  }
}

export async function getRerouteSuggestions(laneId: string): Promise<RerouteSuggestion[]> {
  await sleep(400);
  try {
    const response = await fetch(`${BACKEND_URL}/reroute-suggestions?laneId=${laneId}`);
    if (!response.ok) throw new Error('Backend unavailable');
    return response.json();
  } catch (error) {
    console.error('Backend unavailable for reroute suggestions:', error);
    return [];
  }
}

export async function getCustomers(ids?: string[]): Promise<Customer[]> {
  await sleep(200);
  try {
    const url = ids ? `${BACKEND_URL}/customers?ids=${ids.join(',')}` : `${BACKEND_URL}/customers`;
    const response = await fetch(url);
    if (!response.ok) throw new Error('Backend unavailable');
    return response.json();
  } catch (error) {
    console.error('Backend unavailable for customers:', error);
    return [];
  }
}

export async function getShipmentMetrics(laneId?: string, customerId?: string): Promise<ShipmentLaneMetric[]> {
  await sleep(220);
  try {
    const params = new URLSearchParams();
    if (laneId) params.set("laneId", laneId);
    if (customerId) params.set("customerId", customerId);
    const qs = params.toString();
    const url = qs ? `${BACKEND_URL}/shipments/metrics?${qs}` : `${BACKEND_URL}/shipments/metrics`;
    const response = await fetch(url);
    if (!response.ok) throw new Error("Backend unavailable");
    return response.json();
  } catch (error) {
    console.error("Backend unavailable for shipment metrics:", error);
    return [];
  }
}

export async function getCapacityLanes(): Promise<CapacityLane[]> {
  await sleep(350);
  try {
    const response = await fetch(`${BACKEND_URL}/capacity/lanes`);
    if (!response.ok) throw new Error('Backend unavailable');
    return response.json();
  } catch (error) {
    console.error('Backend unavailable for capacity lanes:', error);
    return [];
  }
}

export async function getCapacityActions(laneId: string): Promise<CapacityAction[]> {
  await sleep(300);
  try {
    const response = await fetch(`${BACKEND_URL}/capacity/actions/${laneId}`);
    if (!response.ok) throw new Error('Backend unavailable');
    return response.json();
  } catch (error) {
    console.error('Backend unavailable for capacity actions:', error);
    return [];
  }
}

export async function getAgentActivities(laneId?: string): Promise<AgentActivity[]> {
  await sleep(250);
  try {
    const url = laneId ? `${BACKEND_URL}/agent-activities?laneId=${laneId}` : `${BACKEND_URL}/agent-activities`;
    const response = await fetch(url);
    if (!response.ok) throw new Error('Backend unavailable');
    return response.json();
  } catch (error) {
    console.error('Backend unavailable for agent activities:', error);
    return [];
  }
}

export async function getSalesOpportunity(laneId: string, activityId: string): Promise<SalesOpportunity | null> {
  await sleep(300);
  try {
    const response = await fetch(`${BACKEND_URL}/sales-opportunities?laneId=${laneId}&activityId=${activityId}`);
    if (!response.ok) throw new Error('Backend unavailable');
    const data = await response.json();
    return data && Object.keys(data).length > 0 ? data as SalesOpportunity : null;
  } catch (error) {
    console.error('Backend unavailable for sales opportunities:', error);
    return null;
  }
}

// Agent query functions
export async function queryGenie(question: string): Promise<{ answer: string; sql?: string; data?: any[]; source: string }> {
  try {
    const response = await fetch(`${BACKEND_URL}/genie/query`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ question }),
    });
    if (!response.ok) throw new Error('Backend unavailable');
    return response.json();
  } catch (error) {
    console.error("Error querying Genie:", error);
    return {
      answer: "Unable to query Genie. Please try again later.",
      source: "error"
    };
  }
}

export async function queryKnowledge(question: string, context?: Record<string, any>): Promise<{ answer: string; citations?: string[]; source: string }> {
  try {
    const response = await fetch(`${BACKEND_URL}/knowledge/query`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ question, context }),
    });
    if (!response.ok) throw new Error('Backend unavailable');
    return response.json();
  } catch (error) {
    console.error("Error querying Knowledge Assistant:", error);
    return {
      answer: "Unable to query Knowledge Assistant. Please try again later.",
      source: "error"
    };
  }
}

export async function querySupervisor(message: string, context?: Record<string, any>): Promise<{ message: string; source: string }> {
  try {
    const response = await fetch(`${BACKEND_URL}/supervisor/query`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ message, context }),
    });
    if (!response.ok) throw new Error('Backend unavailable');
    return response.json();
  } catch (error) {
    console.error("Error querying Supervisor:", error);
    return {
      message: "Unable to query Multi-Agent Supervisor. Please try again later.",
      source: "error"
    };
  }
}

