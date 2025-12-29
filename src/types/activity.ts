export type EventStatus = 'completed' | 'pending' | 'requires-approval';
export type EventCategory = 'revenue-margin' | 'customer-retention';
export type EventTag = 'Revenue' | 'Efficiency' | 'NPS' | 'SLA Risk' | 'Forecast' | 'Anomaly' | 'Quote' | 'External';

export interface LogisticsEvent {
  id: string;
  title: string;
  summary: string;
  situation: string;
  action: string;
  expectedOutcome: string;
  tags: EventTag[];
  status: EventStatus;
  timestamp: string;
  agentName: string;
  category: EventCategory;
  
  // Detail view data
  overview: {
    fullNarrative: string;
  };
  
  visualData: {
    capacityData: { date: string; capacity: number; demand: number }[];
    costDeviationData: { date: string; cost: number; baseline: number }[];
    metrics: {
      capacityRemaining: string;
      riskLevel: string;
      forecastConfidence: string;
      revenueImpact: string;
    };
    benchmark: string;
  };
  
  explainability: {
    keySignals: string[];
    confidenceScore: number;
    tradeoffs: { factor1: string; factor2: string; chosen: string }[];
    rationale: string;
    operationalContext: string[];
  };
}

export interface CustomerAccount {
  id: string;
  name: string;
  status: 'active' | 'at-risk' | 'inactive';
  tier: 'platinum' | 'gold' | 'silver' | 'bronze';
  revenue: {
    next7Days: number;
    monthly: number;
    annual: number;
  };
  slaRisk: {
    score: number;
    flaggedShipments: number;
  };
  nps: {
    current: number;
    trend: 'up' | 'down' | 'stable';
  };
  volume: {
    forecasted30Days: number;
    trend: number; // percentage
  };
  topLanes: Array<{
    lane: string;
    volume: number;
    trend: string;
  }>;
  churnRisk: {
    level: 'low' | 'medium' | 'high';
    percentage: number;
    reasons: string[];
  };
  pricingSensitivity: {
    elasticity: number;
    discountTolerance: string;
    priority: 'price' | 'sla' | 'balanced';
  };
  quoteAcceptanceRate: {
    rate: number;
    trend: string;
  };
  operationalConstraints: Array<{
    label: string;
    value: string;
  }>;
  recentAnomalies: string[];
}








