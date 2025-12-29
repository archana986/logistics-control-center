import type { Customer, Incident, CustomerInteraction, CapacityAction, CapacityLane } from "@/types/domain";

// Get backend URL from environment variable
// In production (Databricks Apps), this will be "/api"
// In development, use full URL to the backend server
const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || "http://localhost:8001/api";

/**
 * Call the backend API to generate a customer update using Databricks model
 */
export async function generateCustomerUpdateWithAI({
  customerName,
  laneId,
  strategy,
  incidentSummary,
  customer,
  incident,
}: {
  customerName: string;
  laneId: string;
  strategy: any;
  incidentSummary: string;
  customer?: Customer;
  incident?: Incident;
}): Promise<{ message: string; source: string }> {
  try {
    const response = await fetch(`${BACKEND_URL}/generate-customer-update`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        customerName,
        laneId,
        strategy,
        incidentSummary,
        customer,
        incident,
      }),
    });

    if (!response.ok) {
      throw new Error(`Backend API error: ${response.status}`);
    }

    const data = await response.json();
    return {
      message: data.message,
      source: data.source,
    };
  } catch (error) {
    console.error("Error calling backend API:", error);
    // Fallback to local generation
    const message = draftCustomerUpdate({
      customerName,
      laneId,
      strategy,
      etaDeltaMinutes: strategy.deltaETAminutes,
      incidentSummary,
      customer,
      incident,
    });
    return {
      message,
      source: "fallback-local",
    };
  }
}

export function draftCustomerUpdate({
  customerName,
  laneId,
  strategy,
  etaDeltaMinutes,
  incidentSummary,
  customer,
  incident,
}: {
  customerName: string;
  laneId: string;
  strategy: string;
  etaDeltaMinutes: number;
  incidentSummary: string;
  customer?: Customer;
  incident?: Incident;
}) {
  const improved = etaDeltaMinutes < 0;
  const impactText = improved
    ? `improved ETA by ${Math.abs(etaDeltaMinutes)} minutes`
    : `+${etaDeltaMinutes} minutes`;

  // Get relevant past interactions to personalize message
  const relevantInteractions = customer?.recentInteractions?.slice(0, 2) || [];
  
  // Build personalized context based on past interactions
  let personalizedContext = "";
  if (relevantInteractions.length > 0) {
    const hasProactiveCommunicationPreference = relevantInteractions.some(
      i => i.tags?.includes("proactive-communication") || i.tags?.includes("proactive")
    );
    const needsPhoneForCritical = relevantInteractions.some(
      i => i.tags?.includes("phone-preferred") || i.tags?.includes("critical-issues")
    );
    
    if (hasProactiveCommunicationPreference) {
      personalizedContext = "\nConsistent with your preference for proactive alerts, we're reaching out immediately to keep you informed.";
    }
    
    if (needsPhoneForCritical && !improved) {
      personalizedContext += "\nGiven the time-sensitive nature, our team is standing by for a call if you need one.";
    }
  }

  // Build incident context section
  let incidentContext = "";
  if (incident) {
    incidentContext = [
      ``,
      `Incident Details:`,
      `• Type: ${incident.type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}`,
      `• Reference: ${incident.ref}`,
      `• Root Cause: ${incident.cause}`,
      incident.impactMinutes ? `• Original Impact: ${incident.impactMinutes} minutes` : "",
      `• Detection Confidence: ${Math.round(incident.confidence * 100)}%`,
    ].filter(line => line).join("\n");
  }

  // Build citations section
  let citationsSection = "";
  if (relevantInteractions.length > 0) {
    const citations = relevantInteractions.map((interaction: CustomerInteraction, idx: number) => {
      const date = new Date(interaction.date).toLocaleDateString('en-US', { 
        month: 'short', 
        day: 'numeric',
        year: 'numeric'
      });
      return `[${idx + 1}] ${interaction.type.charAt(0).toUpperCase() + interaction.type.slice(1)} on ${date}: ${interaction.summary}`;
    });

    citationsSection = [
      ``,
      `---`,
      ``,
      `Context from Recent Interactions:`,
      ...citations,
    ].join("\n");
  }

  return [
    `Subject: Proactive update on your priority shipments (${laneId})`,
    ``,
    `Hi ${customerName},`,
    ``,
    `We detected a disruption on ${laneId} (${incidentSummary}). To protect your urgent deliveries,`,
    `we've proactively re-routed via ${strategy}.${personalizedContext}`,
    ``,
    `• Estimated impact: ${impactText}`,
    `• Your shipments remain prioritized end-to-end`,
    `• Reroute automatically triggered by our network AI`,
    incidentContext,
    ``,
    `We'll continue to monitor until delivery is complete. If you'd like a live view or a call,`,
    `reply here and we'll set it up immediately.`,
    citationsSection,
    ``,
    `Thank you for your partnership,`,
    `Network Operations Center`,
  ].join("\n");
}

/**
 * Call the backend API to generate a spot pricing quote using Databricks model
 */
export async function generateSpotQuoteWithAI({
  laneId,
  action,
  lane,
  volumeChange,
}: {
  laneId: string;
  action: CapacityAction;
  lane: CapacityLane;
  volumeChange: number;
}): Promise<{ quote: string; source: string }> {
  try {
    const response = await fetch(`${BACKEND_URL}/capacity/spot-quote`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        laneId,
        action,
        lane,
        volumeChange,
      }),
    });

    if (!response.ok) {
      throw new Error(`Backend API error: ${response.status}`);
    }

    const data = await response.json();
    return {
      quote: data.quote,
      source: data.source,
    };
  } catch (error) {
    console.error("Error calling backend API for spot quote:", error);
    // Fallback to local generation
    const quote = draftSpotQuote({ laneId, action, lane, volumeChange });
    return {
      quote,
      source: "fallback-local",
    };
  }
}

export function draftSpotQuote({
  laneId,
  action,
  lane,
  volumeChange,
}: {
  laneId: string;
  action: CapacityAction;
  lane: CapacityLane;
  volumeChange: number;
}) {
  const actionVerb = action.type === "pull_forward" ? "Pull Forward" : "Hold Back";
  const deliveryCommit = action.type === "pull_forward" ? "Next-Day Delivery" : "2-Day Standard Service";
  
  const currentUtil = lane.utilizationPct * 100;
  const newVolume = lane.avgDailyVolume + volumeChange;
  const newUtil = (newVolume / lane.maxCapacity) * 100;
  
  const pricePerPkg = Math.abs(action.costImpact) / Math.abs(volumeChange);
  
  return [
    `SPOT CAPACITY QUOTE`,
    `Lane: ${laneId}`,
    `Quote ID: SQ-${laneId.replace(/-/g, '')}-${action.type.toUpperCase().substring(0, 4)}-001`,
    ``,
    `━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`,
    ``,
    `CAPACITY OPTIMIZATION OPPORTUNITY`,
    ``,
    `Action: ${actionVerb} ${Math.abs(volumeChange).toLocaleString()} Packages`,
    `Current Lane Utilization: ${currentUtil.toFixed(0)}%`,
    `Projected Utilization: ${newUtil.toFixed(0)}%`,
    `Available Buffer: ${lane.availableCapacity.toLocaleString()} packages`,
    ``,
    `━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`,
    ``,
    `PRICING`,
    ``,
    `Volume: ${Math.abs(volumeChange).toLocaleString()} packages`,
    `Rate: $${pricePerPkg.toFixed(2)} per package`,
    `Total: $${Math.abs(action.costImpact).toLocaleString()}`,
    ``,
    `Service Level: ${deliveryCommit}`,
    action.type === "pull_forward" ? `Premium handling included` : `Standard processing`,
    ``,
    `━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`,
    ``,
    `BUSINESS IMPACT ANALYSIS`,
    ``,
    `Customer Satisfaction (NPS): ${action.npsImpact >= 0 ? '+' : ''}${action.npsImpact} points`,
    `Operational Efficiency: ${action.efficiencyImpact >= 0 ? '+' : ''}${(action.efficiencyImpact * 100).toFixed(1)}%`,
    `Network Optimization: ${action.type === "hold_back" ? "Reduced congestion" : "Maximized throughput"}`,
    ``,
    action.npsImpact > 0 ? `✓ Recommended: Improves customer experience` : `⚠ Note: May impact customer satisfaction`,
    action.efficiencyImpact > 0 ? `✓ Improves operational efficiency` : `⚠ Reduces operational efficiency`,
    ``,
    `━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`,
    ``,
    `TERMS & CONDITIONS`,
    ``,
    `• Quote valid for: 24 hours`,
    `• Subject to: Real-time capacity availability`,
    `• Commitment required: 4 hours advance notice`,
    `• Cancellation policy: Up to 2 hours before scheduled pickup`,
    `• Payment terms: Net 30 days`,
    ``,
    `━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`,
    ``,
    `For approval or questions, contact:`,
    `Network Capacity Planning Team`,
    `Email: capacity@databricks.com | Phone: 1-800-DATABRICKS`,
    ``,
    `This quote represents an optimal balance between customer satisfaction`,
    `and operational efficiency based on current network conditions.`,
  ].join("\n");
}

