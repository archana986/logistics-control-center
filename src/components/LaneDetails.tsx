import { useMemo } from "react";
import { Package, Clock, MapPin, AlertCircle, TrendingUp, BoxIcon, Loader2 } from "lucide-react";
import type { Lane, Incident, Shipment } from "@/types/domain";
import IncidentTimeline from "./IncidentTimeline";
import RootCauseAnalysis from "./RootCauseAnalysis";

interface LaneDetailsProps {
  lane: Lane;
  incidents: Incident[];
  shipments?: Shipment[];
  triggerAnalysis?: boolean;
  loadingIncidents?: boolean;
}

export default function LaneDetails({ lane, incidents, shipments = [], triggerAnalysis = false, loadingIncidents = false }: LaneDetailsProps) {
  const laneShipments = useMemo(() => {
    return shipments.filter(s => s.laneId === lane.id);
  }, [shipments, lane.id]);

  const urgentShipments = useMemo(() => {
    return laneShipments.filter(s => s.priority === "HIGH");
  }, [laneShipments]);

  const urgentIncidents = useMemo(() => {
    return incidents.filter(i => (i.impactMinutes || 0) > 60 || (i.confidence || 1) < 0.8);
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
          <span className="font-medium">{lane.dest}</span>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 gap-3">
        <div className="bg-card border rounded-lg p-3">
          <div className="flex items-center gap-2 text-muted-foreground text-xs mb-1">
            <BoxIcon className="h-3 w-3" />
            <span>Shipments</span>
          </div>
          <div className="text-2xl font-bold">{laneShipments.length}</div>
          {urgentShipments.length > 0 && (
            <div className="text-xs text-red-600 font-medium mt-1">
              {urgentShipments.length} urgent (HIGH)
            </div>
          )}
        </div>

        <div className="bg-card border rounded-lg p-3">
          <div className="flex items-center gap-2 text-muted-foreground text-xs mb-1">
            <Package className="h-3 w-3" />
            <span>Daily Volume</span>
          </div>
          <div className="text-2xl font-bold">{Number(lane.avgDailyVolume).toLocaleString()}</div>
          <div className="text-xs text-muted-foreground mt-1">
            {(Number(lane.onTimePct) * 100).toFixed(0)}% on-time
          </div>
        </div>

        <div className="bg-card border rounded-lg p-3">
          <div className="flex items-center gap-2 text-muted-foreground text-xs mb-1">
            <Clock className="h-3 w-3" />
            <span>Avg Delay</span>
          </div>
          <div className={`text-2xl font-bold ${getRiskColor(Number(lane.delayMinutes)).split(' ')[0]}`}>
            {lane.delayMinutes}m
          </div>
          {Number(lane.delayMinutes) > 0 && (
            <div className="flex items-center gap-1 text-xs text-red-600 mt-1">
              <TrendingUp className="h-3 w-3" />
              <span>+{Math.round(Number(lane.delayMinutes) * 0.2)}m in 1hr</span>
            </div>
          )}
        </div>

        <div className="bg-card border rounded-lg p-3">
          <div className="flex items-center gap-2 text-muted-foreground text-xs mb-1">
            <AlertCircle className="h-3 w-3" />
            <span>Incidents</span>
          </div>
          {loadingIncidents ? (
            <div className="flex items-center gap-2">
              <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
              <span className="text-sm text-muted-foreground">Loading...</span>
            </div>
          ) : (
            <>
              <div className="text-2xl font-bold">{incidents.length}</div>
              {urgentIncidents.length > 0 && (
                <div className="text-xs text-orange-600 font-medium mt-1">
                  {urgentIncidents.length} high-impact
                </div>
              )}
            </>
          )}
        </div>
      </div>

      {/* Incidents */}
      {loadingIncidents ? (
        <div className="bg-card border rounded-lg p-4">
          <h4 className="font-semibold mb-3 flex items-center gap-2">
            <AlertCircle className="h-4 w-4 text-orange-600" />
            Active Incidents
          </h4>
          <div className="flex items-center justify-center gap-2 py-8 text-muted-foreground">
            <Loader2 className="h-5 w-5 animate-spin" />
            <span className="text-sm">Loading incidents...</span>
          </div>
        </div>
      ) : incidents.length > 0 ? (
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
      {triggerAnalysis && incidents.length > 0 && (
        <RootCauseAnalysis laneId={lane.id} incidents={incidents} triggerAnalysis={triggerAnalysis} />
      )}
    </div>
  );
}

