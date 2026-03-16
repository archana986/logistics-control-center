import { useEffect, useState, useMemo } from "react";
import MapView from "@/components/MapView/MapView";
import Legend from "@/components/MapView/Legend";
import KPICards from "@/components/KPICards";
import LaneDetails from "@/components/LaneDetails";
import ReroutePanel from "@/components/ReroutePanel";
import GenAIDrawer from "@/components/GenAIDrawer";
import { getCenters, getLanes, getIncidents, getShipmentMetrics } from "@/lib/mockApi";
import { Button } from "@/components/ui/button";
import type { Center, Lane, Incident, ShipmentLaneMetric } from "@/types/domain";
import { Sparkles, Filter, Brain, CheckCircle } from "lucide-react";
import databricksLogo from "@/assets/databricks_logo.svg";
import { clearAllSessionState } from "@/lib/sessionState";

export default function IncidentResponseView() {
  const [centers, setCenters] = useState<Center[]>([]);
  const [lanes, setLanes] = useState<Lane[]>([]);
  const [selectedLaneId, setSelectedLaneId] = useState<string | null>(null);
  const [selectedLane, setSelectedLane] = useState<Lane | null>(null);
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [openReroute, setOpenReroute] = useState(false);
  const [openGenAI, setOpenGenAI] = useState(false);
  const [genPayload] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [riskFilter, setRiskFilter] = useState<string>("");
  const [customerFilter, setCustomerFilter] = useState<string>("");
  const [shipmentMetrics, setShipmentMetrics] = useState<ShipmentLaneMetric[]>([]);
  const [triggerAnalysis, setTriggerAnalysis] = useState(false);
  const [showResetConfirm, setShowResetConfirm] = useState(false);
  const [loadingIncidents, setLoadingIncidents] = useState(false);

  // Keyboard shortcut for demo reset (Cmd+Shift+R or Ctrl+Shift+R)
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.shiftKey && e.key === 'R') {
        e.preventDefault();
        handleDemoReset();
      }
    };
    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, []);

  const handleDemoReset = () => {
    clearAllSessionState();
    setShowResetConfirm(true);
    setTimeout(() => setShowResetConfirm(false), 2000);
    // Refresh the page to reset UI
    window.location.reload();
  };

  // Load initial data
  useEffect(() => {
    Promise.all([
      getCenters(), 
      getLanes(),
      getShipmentMetrics()
    ]).then(([centersData, lanesData, shipmentMetricsData]) => {
      setCenters(centersData);
      setLanes(lanesData);
      setShipmentMetrics(shipmentMetricsData);
      setLoading(false);
    });
  }, []);

  // Format customer ID into user-friendly display name
  const formatCustomerName = (customerId: string): string => {
    // Convert to lowercase first for consistent processing
    const normalized = customerId.toLowerCase();
    
    // Split by dash or keep as single word
    const parts = normalized.split('-');
    
    // Capitalize each word
    const formatted = parts.map(word => {
      // Special handling for common abbreviations
      if (word === 'techcorp') return 'TechCorp';
      if (word === 'bestbuy') return 'Best Buy';
      return word.charAt(0).toUpperCase() + word.slice(1);
    }).join(' ');
    
    return formatted;
  };

  // Get unique customers from shipments
  const uniqueCustomers = useMemo(() => {
    const customerSet = new Set<string>();
    shipmentMetrics.forEach(metric => {
      if (metric.customerId) {
        customerSet.add(metric.customerId);
      }
    });
    return Array.from(customerSet).sort();
  }, [shipmentMetrics]);

  // Filter lanes based on risk level and customer
  const filteredLanes = useMemo(() => {
    let filtered = lanes;
    
    // Apply risk filter based on delay minutes
    if (riskFilter) {
      filtered = filtered.filter(lane => {
        const delayMinutes = lane.delayMinutes;
        switch (riskFilter) {
          case "low":
            return delayMinutes < 45;
          case "medium":
            return delayMinutes >= 45 && delayMinutes < 90;
          case "high":
            return delayMinutes >= 90;
          default:
            return true;
        }
      });
    }
    
    // Apply customer filter
    if (customerFilter) {
      const customerLaneIds = new Set(
        shipmentMetrics
          .filter(m => m.customerId === customerFilter && m.shipmentCount > 0)
          .map(m => m.laneId)
      );
      filtered = filtered.filter(lane => customerLaneIds.has(lane.id));
    }
    
    return filtered;
  }, [lanes, riskFilter, customerFilter, shipmentMetrics]);

  // Load incidents when lane is selected
  useEffect(() => {
    if (selectedLaneId) {
      setLoadingIncidents(true);
      getIncidents(selectedLaneId)
        .then(setIncidents)
        .finally(() => setLoadingIncidents(false));
      const lane = filteredLanes.find(l => l.id === selectedLaneId) as Lane;
      setSelectedLane(lane || null);
    } else {
      setIncidents([]);
      setSelectedLane(null);
      setLoadingIncidents(false);
    }
    setTriggerAnalysis(false);
  }, [selectedLaneId, filteredLanes]);

  const handleLaneClick = (laneId: string) => {
    setSelectedLaneId(laneId);
  };

  if (loading) {
    return (
      <div className="h-full w-full flex items-center justify-center bg-background">
        <div className="text-center">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-primary border-r-transparent"></div>
          <div className="mt-4 text-muted-foreground">Loading network...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full w-full flex flex-col bg-background">
      {/* Reset Confirmation Toast */}
      {showResetConfirm && (
        <div className="fixed top-4 right-4 z-50 bg-green-600 text-white px-6 py-3 rounded-lg shadow-lg flex items-center gap-2 animate-fade-in">
          <CheckCircle className="w-5 h-5" />
          <span className="font-medium">Demo state cleared!</span>
        </div>
      )}

      {/* Header */}
      <div className="border-b px-6 py-3 flex items-center justify-between" style={{ backgroundColor: '#1B3139' }}>
        {/* Left: Logo and Live Ticker */}
        <div className="flex items-center gap-4 flex-1">
          <img src={databricksLogo} alt="Databricks" className="h-12" />
          <div className="border-l border-white/20 pl-4 ml-2">
            <button 
              onClick={handleDemoReset}
              className="flex items-center gap-2 text-sm px-3 py-1.5 rounded-lg hover:bg-white/10 transition-colors cursor-pointer group"
              title="Click to reset demo state (or use Cmd/Ctrl+Shift+R)"
            >
              <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse group-hover:bg-green-300"></div>
              <span className="text-white/80 group-hover:text-white">Live</span>
            </button>
          </div>
        </div>
        
        {/* Center: Title with Subtitle */}
        <div className="flex flex-col items-center justify-center flex-1">
          <h2 className="text-3xl font-semibold text-white">Network Control Center</h2>
          <p className="text-xs text-white/70 mt-1">Incident Response & Network Operations</p>
        </div>
        
        {/* Right: Filters */}
        <div className="flex items-center gap-4 flex-1 justify-end">
          <div className="flex items-center gap-2">
            <Filter className="h-4 w-4 text-white/70" />
            <select 
              value={riskFilter}
              onChange={(e) => {
                setRiskFilter(e.target.value);
                setSelectedLaneId(null);
              }}
              className="bg-white/10 border border-white/20 text-white rounded-md px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-white/50"
              style={{ color: 'white' }}
            >
              <option value="" style={{ backgroundColor: '#1B3139', color: 'white' }}>All Risk Levels</option>
              <option value="low" style={{ backgroundColor: '#1B3139', color: 'white' }}>🟢 On-time (&lt; 45m delay)</option>
              <option value="medium" style={{ backgroundColor: '#1B3139', color: 'white' }}>🟡 Caution (45-90m delay)</option>
              <option value="high" style={{ backgroundColor: '#1B3139', color: 'white' }}>🔴 At-risk (&gt; 90m delay)</option>
            </select>
          </div>
          
          <div className="flex items-center gap-2">
            <select 
              value={customerFilter}
              onChange={(e) => {
                setCustomerFilter(e.target.value);
                setSelectedLaneId(null);
              }}
              className="bg-white/10 border border-white/20 text-white rounded-md px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-white/50"
              style={{ color: 'white' }}
            >
              <option value="" style={{ backgroundColor: '#1B3139', color: 'white' }}>All Customers</option>
              {uniqueCustomers.map(customerId => (
                <option key={customerId} value={customerId} style={{ backgroundColor: '#1B3139', color: 'white' }}>
                  {formatCustomerName(customerId)}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Map Section */}
        <div className="flex-1 relative">
          <MapView
            centers={centers}
            lanes={filteredLanes}
            selectedLaneId={selectedLaneId}
            onLaneClick={handleLaneClick}
            viewMode="congestion"
            autoZoomToLanes={true}
          />
          <Legend viewMode="congestion" />
          
          {/* Filter Badges */}
          {(riskFilter || customerFilter) && (
            <div className="absolute top-4 left-4 flex flex-col gap-2">
              {riskFilter && (
                <div 
                  className="px-4 py-2 rounded-lg shadow-lg text-sm font-medium"
                  style={{
                    backgroundColor: riskFilter === "low" 
                      ? "rgb(34, 197, 94)" 
                      : riskFilter === "medium" 
                      ? "rgb(250, 204, 21)" 
                      : "rgb(239, 68, 68)",
                    color: riskFilter === "medium" ? "rgb(0, 0, 0)" : "rgb(255, 255, 255)"
                  }}
                >
                  {riskFilter === "low" ? "🟢 On-time" : riskFilter === "medium" ? "🟡 Caution" : "🔴 At-risk"}
                </div>
              )}
              {customerFilter && (
                <div 
                  className="px-4 py-2 rounded-lg shadow-lg text-sm font-medium bg-blue-600 text-white"
                >
                  👤 {formatCustomerName(customerFilter)}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Right Panel */}
        <div className="w-[420px] border-l bg-card/30 backdrop-blur-sm flex flex-col overflow-hidden">
          {/* KPIs at top */}
          <div className="border-b">
            <KPICards lanes={filteredLanes} viewMode="congestion" />
          </div>

          {/* Lane Details or Placeholder */}
          <div className="flex-1 overflow-y-auto p-4">
            {selectedLane ? (
              <div className="space-y-4">
                <LaneDetails lane={selectedLane} incidents={incidents} shipmentMetrics={shipmentMetrics} triggerAnalysis={triggerAnalysis} loadingIncidents={loadingIncidents} />
                
                {/* Action Buttons */}
                <div className="space-y-2">
                  <Button
                    className="w-full"
                    size="lg"
                    onClick={() => setOpenReroute(true)}
                    disabled={incidents.length === 0}
                  >
                    <Sparkles className="mr-2 h-5 w-5" />
                    Reroute Urgent Packages
                  </Button>
                  
                  {/* AI Root Cause Analysis Button */}
                  {incidents.length > 0 && !triggerAnalysis && (
                    <Button
                      className="w-full"
                      variant="outline"
                      size="lg"
                      onClick={() => setTriggerAnalysis(true)}
                    >
                      <Brain className="mr-2 h-5 w-5" />
                      Run AirOps AI Root Cause Analysis
                    </Button>
                  )}
                  
                  {incidents.length === 0 && (
                    <p className="text-xs text-center text-muted-foreground">
                      No active incidents on this lane
                    </p>
                  )}
                </div>
              </div>
            ) : (
              <div className="h-full flex items-center justify-center text-center p-8">
                <div>
                  <div className="text-6xl mb-4 opacity-20">🗺️</div>
                  <h3 className="font-semibold mb-2">Select a Lane</h3>
                  <p className="text-sm text-muted-foreground">
                    Click on any lane (arc) on the map to view details, incidents, and take action
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Panels */}
      {selectedLaneId && (
        <ReroutePanel
          laneId={selectedLaneId}
          open={openReroute}
          onOpenChange={setOpenReroute}
          onComplete={() => {
            setSelectedLaneId(null);
            setRiskFilter("");
            setCustomerFilter("");
          }}
        />
      )}

      <GenAIDrawer
        open={openGenAI}
        onOpenChange={setOpenGenAI}
        payload={genPayload}
        onApprove={() => {}}
      />
    </div>
  );
}

