import { useMemo } from "react";
import { Package, Clock, MapPin, AlertCircle, TrendingUp } from "lucide-react";
import type { Lane, Incident } from "@/types/domain";
import IncidentTimeline from "./IncidentTimeline";
import RootCauseAnalysis from "./RootCauseAnalysis";

interface LaneDetailsProps {
  lane: Lane;
  incidents: Incident[];
  triggerAnalysis?: boolean;
}

export default function LaneDetails({ lane, incidents, triggerAnalysis = false }: LaneDetailsProps) {
  const urgentIncidents = useMemo(() => {
    return incidents.filter(i => i.severity === "high" || i.severity === "critical");
  }, [incidents]);

  const getRiskColor = (delayMinutes: number) => {
    if (delayMinutes < 45) return "text-green-600 bg-green-50";
    if (delayMinutes < 90) return "text-yellow-600 bg-yellow-50";
    return "text-red-600 bg-red-50";
  };

  const getRiskLabel = (delayMinutes: number) => {
    if (delayMinutes < 45) return "On-time";
    if (delayMinutes < 90) return "Caution";
    return "At-risk";
  };

  return (
    <div className="space-y-4">
      {/* Lane Header */}
      <div className="border-b pb-3">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-lg font-semibold">Lane Details</h3>
          <span className={`px-3 py-1 rounded-full text-xs font-medium ${getRiskColor(lane.delayMinutes)}`}>
            {getRiskLabel(lane.delayMinutes)}
          </span>
        </div>
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <MapPin className="h-4 w-4" />
          <span className="font-medium">{lane.origin}</span>
          <span>→</span>
          <span className="font-medium">{lane.destination}</span>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 gap-3">
        <div className="bg-card border rounded-lg p-3">
          <div className="flex items-center gap-2 text-muted-foreground text-xs mb-1">
            <Package className="h-3 w-3" />
            <span>Shipments</span>
          </div>
          <div className="text-2xl font-bold">{lane.shipmentCount}</div>
          {lane.urgentShipments > 0 && (
            <div className="text-xs text-red-600 font-medium mt-1">
              {lane.urgentShipments} urgent
            </div>
          )}
        </div>

        <div className="bg-card border rounded-lg p-3">
          <div className="flex items-center gap-2 text-muted-foreground text-xs mb-1">
            <Clock className="h-3 w-3" />
            <span>Avg Delay</span>
          </div>
          <div className={`text-2xl font-bold ${getRiskColor(lane.delayMinutes).split(' ')[0]}`}>
            {lane.delayMinutes}m
          </div>
          {lane.delayMinutes > 0 && (
            <div className="flex items-center gap-1 text-xs text-red-600 mt-1">
              <TrendingUp className="h-3 w-3" />
              <span>+{Math.round(lane.delayMinutes * 0.2)}m in 1hr</span>
            </div>
          )}
        </div>

        <div className="bg-card border rounded-lg p-3">
          <div className="flex items-center gap-2 text-muted-foreground text-xs mb-1">
            <AlertCircle className="h-3 w-3" />
            <span>Incidents</span>
          </div>
          <div className="text-2xl font-bold">{incidents.length}</div>
          {urgentIncidents.length > 0 && (
            <div className="text-xs text-orange-600 font-medium mt-1">
              {urgentIncidents.length} urgent
            </div>
          )}
        </div>

        <div className="bg-card border rounded-lg p-3">
          <div className="flex items-center gap-2 text-muted-foreground text-xs mb-1">
            <MapPin className="h-3 w-3" />
            <span>Mode</span>
          </div>
          <div className="text-lg font-bold capitalize">
            {lane.mode === "air" ? "✈️ Air" : lane.mode === "ground" ? "🚛 Ground" : "🚢 Ocean"}
          </div>
        </div>
      </div>

      {/* Incidents */}
      {incidents.length > 0 ? (
        <div>
          <h4 className="font-semibold mb-3 flex items-center gap-2">
            <AlertCircle className="h-4 w-4 text-orange-600" />
            Active Incidents ({incidents.length})
          </h4>
          <IncidentTimeline incidents={incidents} />
        </div>
      ) : (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4 text-center">
          <div className="text-green-600 font-medium">✓ No Active Incidents</div>
          <div className="text-xs text-green-600 mt-1">This lane is operating normally</div>
        </div>
      )}

      {/* Root Cause Analysis */}
      {triggerAnalysis && lane.mode === "air" && incidents.length > 0 && (
        <RootCauseAnalysis lane={lane} incidents={incidents} />
      )}
    </div>
  );
}

