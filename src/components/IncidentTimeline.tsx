import type { Incident } from "@/types/domain";
import { formatDate } from "@/lib/format";
import { Plane, Truck, AlertTriangle, Wrench, Cloud, Radio, Shield, Clock } from "lucide-react";

interface IncidentTimelineProps {
  incidents: Incident[];
}

function getIncidentDisplay(type: string) {
  const typeMap: Record<string, { icon: any; label: string; color: string; bgColor: string }> = {
    flight_delay: { icon: Plane, label: 'Flight Delay', color: 'text-orange-500', bgColor: 'bg-orange-500/20' },
    maintenance_check: { icon: Wrench, label: 'Maintenance Check', color: 'text-blue-500', bgColor: 'bg-blue-500/20' },
    equipment_issue: { icon: Wrench, label: 'Equipment Issue', color: 'text-amber-500', bgColor: 'bg-amber-500/20' },
    highway_closure: { icon: Truck, label: 'Highway Closure', color: 'text-red-500', bgColor: 'bg-red-500/20' },
    highway_delay: { icon: Truck, label: 'Highway Delay', color: 'text-orange-500', bgColor: 'bg-orange-500/20' },
    vehicle_breakdown: { icon: Truck, label: 'Vehicle Breakdown', color: 'text-red-500', bgColor: 'bg-red-500/20' },
    traffic_congestion: { icon: Truck, label: 'Traffic Congestion', color: 'text-yellow-500', bgColor: 'bg-yellow-500/20' },
    weather: { icon: Cloud, label: 'Weather Event', color: 'text-purple-500', bgColor: 'bg-purple-500/20' },
    air_traffic_control: { icon: Radio, label: 'Air Traffic Control', color: 'text-cyan-500', bgColor: 'bg-cyan-500/20' },
    air_space_restriction: { icon: Shield, label: 'Airspace Restriction', color: 'text-red-500', bgColor: 'bg-red-500/20' },
    security_delay: { icon: Shield, label: 'Security Delay', color: 'text-orange-500', bgColor: 'bg-orange-500/20' },
  };
  
  return typeMap[type] || { icon: Clock, label: 'Delay', color: 'text-gray-500', bgColor: 'bg-gray-500/20' };
}

export default function IncidentTimeline({ incidents }: IncidentTimelineProps) {
  return (
    <div className="space-y-3">
      {incidents.map((incident, idx) => {
        const display = getIncidentDisplay(incident.type);
        const Icon = display.icon;
        
        return (
          <div key={idx} className="flex gap-3">
            <div className="flex flex-col items-center">
              <div className={`rounded-full p-2 ${display.bgColor}`}>
                <Icon className={`h-4 w-4 ${display.color}`} />
              </div>
              {idx < incidents.length - 1 && (
                <div className="w-0.5 flex-1 bg-border my-1 min-h-4" />
              )}
            </div>
            <div className="flex-1 pb-3">
              <div className="flex items-start justify-between gap-2">
                <div>
                  <div className="font-medium text-sm">
                    {display.label}
                  </div>
                  <div className="text-sm text-muted-foreground">{incident.ref}</div>
                </div>
              <div className="flex items-center gap-1 text-xs">
                <AlertTriangle className="h-3 w-3" />
                {(incident.confidence * 100).toFixed(0)}% conf.
              </div>
            </div>
            <div className="text-sm mt-1">{incident.cause}</div>
            {incident.impactMinutes && (
              <div className="text-xs text-orange-500 mt-1">
                Impact: +{incident.impactMinutes}m delay
              </div>
            )}
            {incident.impactThroughputPct && (
              <div className="text-xs text-red-500 mt-1">
                Impact: {incident.impactThroughputPct}% throughput
              </div>
            )}
            <div className="text-xs text-muted-foreground mt-1">
              {formatDate(incident.timestamp)}
            </div>
          </div>
        </div>
        );
      })}
    </div>
  );
}

