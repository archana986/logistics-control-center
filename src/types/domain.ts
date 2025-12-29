export type Center = {
  id: string;
  name: string;
  lat: number;
  lng: number;
  type: "dc" | "air_hub" | "sort";
};

export type Lane = {
  id: string;
  origin: string;
  dest: string;
  mode: "air" | "ground";
  avgDailyVolume: number;
  onTimePct: number;
  delayMinutes: number;
  slaRiskPct: number;
};

export type Incident = {
  laneId: string;
  timestamp: string;
  type: 
    | "flight_delay" 
    | "highway_closure" 
    | "maintenance_check" 
    | "equipment_issue"
    | "highway_delay"
    | "vehicle_breakdown"
    | "traffic_congestion"
    | "weather"
    | "air_traffic_control"
    | "air_space_restriction"
    | "security_delay";
  ref: string;
  cause: string;
  impactMinutes?: number;
  impactThroughputPct?: number;
  confidence: number;
};

export type Shipment = {
  trackingId: string;
  customerId: string;
  priority: "LOW" | "MED" | "HIGH";
  laneId: string;
  promisedETA: string;
  currentETA: string;
  packageCount?: number;
};

export type RerouteSuggestion = {
  laneId: string;
  strategy: string;
  deltaETAminutes: number;
  addedCostUSD: number;
  capacityUsedPct: number;
  notes: string;
};

export type CustomerInteraction = {
  date: string;
  type: "email" | "call" | "meeting" | "chat";
  summary: string;
  sentiment?: "positive" | "neutral" | "concerned";
  tags?: string[];
};

export type Customer = {
  id: string;
  name: string;
  contact: string;
  tier: string;
  preferredCommunication?: "email" | "phone" | "both";
  recentInteractions?: CustomerInteraction[];
  shippingHistory?: Record<string, {
    last90Days: number;
    avgPrice: number;
  }>;
};

export type CapacityLane = Lane & {
  maxCapacity: number;
  utilizationPct: number;
  availableCapacity: number;
  optimalUtilization: number;
};

export type CapacityAction = {
  type: "pull_forward" | "hold_back";
  volumeChange: number;
  npsImpact: number;
  costImpact: number;
  efficiencyImpact: number;
  notes: string;
};

export type SpotPriceQuote = {
  laneId: string;
  availableCapacity: number;
  pricePerPackage: number;
  totalPrice: number;
  deliveryCommitment: string;
  validUntil: string;
  terms: string[];
};

export type AgentActivity = {
  id: string;
  laneId: string;
  timestamp: string;
  agentType: "capacity" | "pricing" | "sales";
  situation: string;
  action: string;
  result: string;
  status: "completed" | "pending" | "awaiting_response";
  metadata?: {
    customerId?: string;
    volumeChange?: number;
    revenueOpportunity?: number;
    pricing?: {
      historical: number;
      recommended: number;
    };
  };
};

export type SalesOpportunity = {
  laneId: string;
  activityId: string;
  availableCapacity: number;
  forecastDate: string;
  targetCustomers: Array<{
    id: string;
    name: string;
    reason: string;
  }>;
  pricing: {
    historical: number;
    recommended: number;
    discount: number;
  };
  projectedImpact: {
    revenue: number;
    utilizationBefore: number;
    utilizationAfter: number;
    margin: number;
  };
};

