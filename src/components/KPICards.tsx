import { formatPercent } from "@/lib/format";
import type { Lane, CapacityLane } from "@/types/domain";
import { TrendingUp, Package, AlertTriangle, Clock, Activity, TrendingDown } from "lucide-react";

interface KPICardsProps {
  lanes: Lane[];
  viewMode?: 'congestion' | 'capacity';
}

export default function KPICards({ lanes, viewMode = 'congestion' }: KPICardsProps) {
  // Check if lanes have capacity data
  const hasCapacityData = lanes.length > 0 && 'utilizationPct' in lanes[0];
  const capacityLanes = hasCapacityData ? lanes as CapacityLane[] : [];
  
  // Congestion mode metrics
  const laneCount = Math.max(1, lanes.length);
  const totalVolume = lanes.reduce((sum, lane) => sum + (Number.isFinite(Number(lane.avgDailyVolume)) ? Number(lane.avgDailyVolume) : 0), 0);
  const avgOnTime = lanes.reduce((sum, lane) => sum + (Number.isFinite(Number(lane.onTimePct)) ? Number(lane.onTimePct) : 0), 0) / laneCount;
  const atRiskCount = lanes.filter(lane => lane.slaRiskPct > 0.1).length;
  const avgDelay = lanes.reduce((sum, lane) => sum + (Number.isFinite(Number(lane.delayMinutes)) ? Number(lane.delayMinutes) : 0), 0) / laneCount;
  
  // Capacity mode metrics
  const avgUtilization = hasCapacityData 
    ? capacityLanes.reduce((sum, lane) => sum + (Number.isFinite(Number(lane.utilizationPct)) ? Number(lane.utilizationPct) : 0), 0) / Math.max(1, capacityLanes.length)
    : 0;
  const underutilizedCount = hasCapacityData 
    ? capacityLanes.filter(lane => lane.utilizationPct < 0.70).length
    : 0;
  const overcapacityCount = hasCapacityData 
    ? capacityLanes.filter(lane => lane.utilizationPct > 0.95).length
    : 0;
  const totalBuffer = hasCapacityData 
    ? capacityLanes.reduce((sum, lane) => sum + lane.availableCapacity, 0)
    : 0;

  if (viewMode === 'capacity' && hasCapacityData) {
    return (
      <div className="grid grid-cols-2 gap-4 p-4">
        <div className="bg-card border rounded-lg p-4 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold">{formatPercent(avgUtilization, 0)}</div>
              <div className="text-sm text-muted-foreground">Network Utilization</div>
            </div>
            <Activity className="h-8 w-8 text-primary opacity-70" />
          </div>
        </div>

        <div className="bg-card border rounded-lg p-4 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold text-green-500">{underutilizedCount}</div>
              <div className="text-sm text-muted-foreground">Underutilized</div>
            </div>
            <TrendingDown className="h-8 w-8 text-green-500 opacity-70" />
          </div>
        </div>

        <div className="bg-card border rounded-lg p-4 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold text-red-500">{overcapacityCount}</div>
              <div className="text-sm text-muted-foreground">Overcapacity</div>
            </div>
            <AlertTriangle className="h-8 w-8 text-red-500 opacity-70" />
          </div>
        </div>

        <div className="bg-card border rounded-lg p-4 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold">{(totalBuffer / 1000).toFixed(0)}K</div>
              <div className="text-sm text-muted-foreground">Available Buffer</div>
            </div>
            <Package className="h-8 w-8 text-blue-500 opacity-70" />
          </div>
        </div>
      </div>
    );
  }

  // Congestion mode (default)
  return (
    <div className="grid grid-cols-2 gap-4 p-4">
      <div className="bg-card border rounded-lg p-4 shadow-sm">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-2xl font-bold">{(totalVolume / 1000).toFixed(1)}K</div>
            <div className="text-sm text-muted-foreground">Daily Volume</div>
          </div>
          <Package className="h-8 w-8 text-primary opacity-70" />
        </div>
      </div>

      <div className="bg-card border rounded-lg p-4 shadow-sm">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-2xl font-bold">{formatPercent(avgOnTime, 0)}</div>
            <div className="text-sm text-muted-foreground">On-Time Avg</div>
          </div>
          <TrendingUp className="h-8 w-8 text-green-500 opacity-70" />
        </div>
      </div>

      <div className="bg-card border rounded-lg p-4 shadow-sm">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-2xl font-bold text-orange-500">{atRiskCount}</div>
            <div className="text-sm text-muted-foreground">At-Risk Lanes</div>
          </div>
          <AlertTriangle className="h-8 w-8 text-orange-500 opacity-70" />
        </div>
      </div>

      <div className="bg-card border rounded-lg p-4 shadow-sm">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-2xl font-bold">{Math.round(avgDelay)}m</div>
            <div className="text-sm text-muted-foreground">Avg Delay</div>
          </div>
          <Clock className="h-8 w-8 text-blue-500 opacity-70" />
        </div>
      </div>
    </div>
  );
}

