import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription } from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { useEffect, useState } from "react";
import { getRerouteSuggestions, getUrgentShipments, getIncidents } from "@/lib/mockApi";
import { formatCurrency, formatDuration } from "@/lib/format";
import type { RerouteSuggestion, Shipment, Incident } from "@/types/domain";
import { ArrowRight, CheckCircle2, DollarSign, Clock, Package, PartyPopper } from "lucide-react";

interface ReroutePanelProps {
  laneId: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onComplete?: () => void;
}

export default function ReroutePanel({ laneId, open, onOpenChange, onComplete }: ReroutePanelProps) {
  const [suggestions, setSuggestions] = useState<RerouteSuggestion[]>([]);
  const [shipments, setShipments] = useState<Shipment[]>([]);
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedSuggestion, setSelectedSuggestion] = useState<RerouteSuggestion | null>(null);
  const [showSuccess, setShowSuccess] = useState(false);

  useEffect(() => {
    if (!open || !laneId) return;
    
    // Reset state when opening
    setShowSuccess(false);
    setSelectedSuggestion(null);
    
    setLoading(true);
    Promise.all([
      getRerouteSuggestions(laneId),
      getUrgentShipments(laneId),
      getIncidents(laneId)
    ]).then(([sugs, ships, incs]) => {
      setSuggestions(sugs);
      setShipments(ships);
      setIncidents(incs);
      setLoading(false);
    });
  }, [laneId, open]);
  
  const handleSelectReroute = (suggestion: RerouteSuggestion) => {
    setSelectedSuggestion(suggestion);
    setShowSuccess(true);
  };
  
  // Calculate total packages affected
  const totalPackages = shipments.reduce((sum, shipment) => sum + (shipment.packageCount || 1), 0);
  
  // Calculate scaled cost (the base cost is for a typical shipment batch, scale it to actual package count)
  const getScaledCost = (baseCost: number) => {
    // Assume base cost in mock data is for ~100 packages, scale proportionally
    const basePackageCount = 100;
    return Math.round((baseCost / basePackageCount) * totalPackages);
  };
  
  const parseRouteDescription = (laneId: string, strategy: string) => {
    // Parse the lane ID (e.g., "BNA-STL-AIR")
    const parts = laneId.split('-');
    const origin = parts[0];
    const dest = parts[1];
    const originalMode = parts[2]?.toLowerCase();
    
    // Format the original route
    const fromRoute = `${originalMode === 'air' ? 'air' : 'truck'} from ${origin}→${dest}`;
    
    // Parse the strategy (e.g., "TRUCK-VIA-ORD", "AIR-VIA-ATL", "GROUND-EXPEDITED")
    const strategyLower = strategy.toLowerCase();
    
    if (strategyLower.includes('via')) {
      const viaMatch = strategy.match(/VIA-(\w+)/);
      const hub = viaMatch ? viaMatch[1] : '';
      
      // Map known routes to their actual modes based on lanes.json
      if (strategyLower.startsWith('truck')) {
        // TRUCK-VIA-ORD: typically air to hub, then ground to destination
        return {
          from: fromRoute,
          to: `air from ${origin}→${hub}, then truck from ${hub}→${dest}`,
          mode: 'mixed'
        };
      } else if (strategyLower.startsWith('ground')) {
        // GROUND-VIA-XXX: ground routing through hub
        return {
          from: fromRoute,
          to: `truck from ${origin}→${hub}, then truck from ${hub}→${dest}`,
          mode: 'ground'
        };
      } else if (strategyLower.startsWith('air')) {
        // AIR-VIA-XXX: air connections throughout
        return {
          from: fromRoute,
          to: `air from ${origin}→${hub}, then air from ${hub}→${dest}`,
          mode: 'air'
        };
      }
    } else if (strategyLower.includes('expedited')) {
      if (strategyLower.startsWith('ground')) {
        return {
          from: fromRoute,
          to: `expedited truck service from ${origin}→${dest}`,
          mode: 'ground'
        };
      }
    } else if (strategyLower.includes('direct')) {
      if (strategyLower.startsWith('air')) {
        return {
          from: fromRoute,
          to: `direct air freight from ${origin}→${dest}`,
          mode: 'air'
        };
      }
    } else if (strategyLower.includes('delay')) {
      return {
        from: fromRoute,
        to: `same route (delayed 24 hours for weather clearance)`,
        mode: originalMode || 'air'
      };
    }
    
    // Default fallback
    return {
      from: fromRoute,
      to: `${strategy.toLowerCase().replace(/-/g, ' ')} routing from ${origin}→${dest}`,
      mode: originalMode || 'ground'
    };
  };

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="w-[520px] overflow-y-auto">
        {showSuccess && selectedSuggestion ? (
          // Success View
          <>
            <SheetHeader>
              <SheetTitle className="flex items-center gap-2">
                <CheckCircle2 className="h-6 w-6 text-green-600" />
                Reroute Successful
              </SheetTitle>
              <SheetDescription>
                Packages successfully rerouted on lane {laneId}
              </SheetDescription>
            </SheetHeader>

            <div className="mt-6 space-y-6">
              {/* Success Banner */}
              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <div className="flex items-start gap-3">
                  <PartyPopper className="h-5 w-5 text-green-600 mt-0.5 flex-shrink-0" />
                  <div className="flex-1">
                    <div className="font-semibold text-green-900 mb-1">
                      Successfully rerouted {totalPackages.toLocaleString()} urgent packages
                    </div>
                    <div className="text-sm text-green-700">
                      {incidents.length > 0 ? (
                        <>Packages impacted by {incidents[0].cause.toLowerCase()} have been reassigned to an alternate route.</>
                      ) : (
                        <>All affected shipments have been automatically reassigned to the new route.</>
                      )}
                    </div>
                  </div>
                </div>
              </div>

              {/* Route Change Details */}
              <div className="border rounded-lg p-4 space-y-3">
                <div className="font-semibold text-base">Route Change Summary</div>
                
                <div className="space-y-2 text-sm">
                  <div className="flex items-start gap-2">
                    <div className="text-muted-foreground min-w-[80px]">Previous:</div>
                    <div className="font-medium">
                      {parseRouteDescription(laneId, selectedSuggestion.strategy).from}
                    </div>
                  </div>
                  <div className="flex items-center justify-center py-1">
                    <ArrowRight className="h-4 w-4 text-muted-foreground" />
                  </div>
                  <div className="flex items-start gap-2">
                    <div className="text-muted-foreground min-w-[80px]">New route:</div>
                    <div className="font-medium text-green-700">
                      {parseRouteDescription(laneId, selectedSuggestion.strategy).to}
                    </div>
                  </div>
                </div>
              </div>

              {/* Impact Metrics */}
              <div className="grid grid-cols-2 gap-4">
                <div className="border rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <Clock className="h-4 w-4 text-muted-foreground" />
                    <span className="text-xs text-muted-foreground">Time Impact</span>
                  </div>
                  <div className={`text-2xl font-bold ${
                    selectedSuggestion.deltaETAminutes < 0 ? 'text-green-600' : 'text-orange-600'
                  }`}>
                    {selectedSuggestion.deltaETAminutes < 0 ? '-' : '+'}
                    {formatDuration(Math.abs(selectedSuggestion.deltaETAminutes))}
                  </div>
                  <div className="text-xs text-muted-foreground mt-1">
                    {selectedSuggestion.deltaETAminutes < 0 ? 'Faster delivery' : 'Delay added'}
                  </div>
                </div>

                <div className="border rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <DollarSign className="h-4 w-4 text-muted-foreground" />
                    <span className="text-xs text-muted-foreground">Added Cost</span>
                  </div>
                  <div className="text-2xl font-bold">
                    {formatCurrency(getScaledCost(selectedSuggestion.addedCostUSD))}
                  </div>
                  <div className="text-xs text-muted-foreground mt-1">
                    For {totalPackages.toLocaleString()} packages
                  </div>
                </div>
              </div>

              {/* Additional Details */}
              <div className="bg-muted/50 rounded-lg p-4">
                <div className="text-sm font-medium mb-2">Route Details</div>
                <div className="text-sm text-muted-foreground">
                  {parseRouteDescription(laneId, selectedSuggestion.strategy).to}
                </div>
              </div>

              {/* Capacity Usage */}
              <div className="border rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium">Route Capacity</span>
                  <span className="text-sm font-bold">{selectedSuggestion.capacityUsedPct}%</span>
                </div>
                <div className="w-full bg-muted rounded-full h-2">
                  <div 
                    className="bg-primary h-2 rounded-full transition-all"
                    style={{ width: `${selectedSuggestion.capacityUsedPct}%` }}
                  />
                </div>
                <div className="text-xs text-muted-foreground mt-1">
                  Sufficient capacity available for this reroute
                </div>
              </div>

              {/* Action Button */}
              <Button
                className="w-full"
                size="lg"
                onClick={() => {
                  onOpenChange(false);
                  onComplete?.();
                }}
              >
                Done
              </Button>
            </div>
          </>
        ) : (
          // Selection View
          <>
            <SheetHeader>
              <SheetTitle>Reroute Urgent Packages</SheetTitle>
              <SheetDescription>
                Lane: {laneId}
              </SheetDescription>
            </SheetHeader>

            <div className="mt-6 space-y-4">
              {/* Affected Shipments */}
              <div className="bg-muted/50 rounded-lg p-4">
                <div className="flex items-center gap-2 mb-2">
                  <Package className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm font-medium">Affected Packages</span>
                </div>
                <div className="text-2xl font-bold">{totalPackages.toLocaleString()}</div>
                <div className="text-xs text-muted-foreground">Across {shipments.length} shipment{shipments.length !== 1 ? 's' : ''}</div>
              </div>

              {/* Reroute Options */}
              {loading ? (
                <div className="text-center py-8 text-muted-foreground">Loading options...</div>
              ) : suggestions.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">No reroute options available</div>
              ) : (
                <div className="space-y-3">
                  <div className="font-medium text-sm">Available Reroute Options</div>
                  {suggestions.map((suggestion, idx) => {
                    const routeDesc = parseRouteDescription(laneId, suggestion.strategy);
                    return (
                      <div key={idx} className="border rounded-lg p-4 space-y-3 hover:border-primary transition-colors">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="font-semibold">{suggestion.strategy}</div>
                            <div className="text-xs text-muted-foreground mt-1">
                              Capacity: {suggestion.capacityUsedPct}% utilized
                            </div>
                          </div>
                          {suggestion.deltaETAminutes < 0 && (
                            <div className="flex items-center gap-1 text-green-600 text-sm flex-shrink-0 ml-2">
                              <CheckCircle2 className="h-4 w-4" />
                              Faster
                            </div>
                          )}
                        </div>

                        <div className="grid grid-cols-2 gap-3">
                          <div className="flex items-center gap-2">
                            <Clock className="h-4 w-4 text-muted-foreground" />
                            <div>
                              <div className="text-xs text-muted-foreground">ETA Change</div>
                              <div className={`text-sm font-medium ${
                                suggestion.deltaETAminutes < 0 ? 'text-green-600' : 'text-orange-600'
                              }`}>
                                {suggestion.deltaETAminutes > 0 ? '+' : ''}
                                {formatDuration(Math.abs(suggestion.deltaETAminutes))}
                              </div>
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            <DollarSign className="h-4 w-4 text-muted-foreground" />
                            <div>
                              <div className="text-xs text-muted-foreground">Added Cost</div>
                              <div className="text-sm font-medium">{formatCurrency(getScaledCost(suggestion.addedCostUSD))}</div>
                            </div>
                          </div>
                        </div>

                        <div className="text-xs text-muted-foreground bg-muted/50 rounded p-2">
                          {routeDesc.to}
                        </div>

                        <Button
                          className="w-full"
                          onClick={() => handleSelectReroute(suggestion)}
                        >
                          Choose this reroute
                          <ArrowRight className="ml-2 h-4 w-4" />
                        </Button>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </>
        )}
      </SheetContent>
    </Sheet>
  );
}

