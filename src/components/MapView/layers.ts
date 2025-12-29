import { ArcLayer, ScatterplotLayer, PathLayer } from "@deck.gl/layers";
import type { Center, Lane, CapacityLane } from "../../types/domain";

function getCapacityColor(lane: CapacityLane | Lane, isTarget: boolean = false): [number, number, number, number] {
  // Check if lane has capacity data
  const capacityLane = lane as CapacityLane;
  if (!capacityLane.utilizationPct) {
    // Fallback to delay-based coloring
    const delayRatio = Math.min(1, lane.delayMinutes / 150);
    const alpha = isTarget ? 120 : 200;
    if (delayRatio < 0.3) return [34, 197, 94, alpha]; // green
    if (delayRatio < 0.6) return [250, 204, 21, alpha]; // yellow
    return [239, 68, 68, alpha]; // red
  }
  
  const util = capacityLane.utilizationPct;
  const alpha = isTarget ? 120 : 200;
  
  // Color by utilization
  if (util < 0.70) return [34, 197, 94, alpha];      // Green - underutilized
  if (util < 0.85) return [59, 130, 246, alpha];     // Blue - optimal
  if (util < 0.95) return [250, 204, 21, alpha];     // Yellow - approaching capacity
  return [239, 68, 68, alpha];                        // Red - overcapacity
}

function getDelayColor(lane: Lane, isTarget: boolean = false): [number, number, number, number] {
  const delayRatio = Math.min(1, lane.delayMinutes / 150);
  const alpha = isTarget ? 100 : 180;
  if (delayRatio < 0.3) return [34, 197, 94, alpha]; // green
  if (delayRatio < 0.6) return [250, 204, 21, alpha]; // yellow
  return [239, 68, 68, alpha]; // red
}

export function hubsLayer(centers: Center[]) {
  return new ScatterplotLayer({
    id: "hubs",
    data: centers,
    visible: true,
    getPosition: (d: Center) => [d.lng, d.lat],
    getRadius: () => 26000,
    radiusUnits: "meters",
    getFillColor: (d: Center) => {
      // Color by hub type
      if (d.type === "air_hub") return [147, 51, 234, 200]; // purple
      if (d.type === "dc") return [59, 130, 246, 200]; // blue
      return [16, 185, 129, 200]; // green
    },
    pickable: false,
    stroked: true,
    lineWidthMinPixels: 2,
    getLineColor: [255, 255, 255, 150],
    updateTriggers: {
      getPosition: [centers],
      getFillColor: [centers],
    },
  });
}

export function flowsLayer(
  lanes: Lane[], 
  centersById: Record<string, Center>, 
  selectedLaneId?: string | null,
  viewMode: 'congestion' | 'capacity' = 'congestion'
) {
  // Filter out lanes where centers don't exist to prevent [0,0] coordinates
  const validLanes = lanes.filter(lane => {
    const hasOrigin = centersById[lane.origin];
    const hasDest = centersById[lane.dest];
    if (!hasOrigin || !hasDest) {
      console.warn(`Lane ${lane.id} has missing center(s): origin=${lane.origin} (${!!hasOrigin}), dest=${lane.dest} (${!!hasDest})`);
      return false;
    }
    return true;
  });

  // Separate air and ground lanes (from valid lanes only)
  const airLanes = validLanes.filter(lane => lane.mode === "air");
  const groundLanes = validLanes.filter(lane => lane.mode !== "air");

  const layers = [];

  // Ground routes - using PathLayer for flat, thicker lines
  if (groundLanes.length > 0) {
    layers.push(
      new PathLayer({
        id: "flows-ground",
        data: groundLanes,
        visible: true,
        getPath: (d: Lane) => {
          const origin = centersById[d.origin];
          const dest = centersById[d.dest];
          // Should always exist due to filtering above, but keep safety check
          return origin && dest ? [[origin.lng, origin.lat], [dest.lng, dest.lat]] : [];
        },
        // Ground routes are thicker
        getWidth: (d: Lane) => {
          const base = Math.max(4, Math.min(16, d.avgDailyVolume / 320));
          return d.id === selectedLaneId ? base * 1.2 : base;
        },
        // Color based on view mode
        getColor: (d: Lane) => {
          return viewMode === 'capacity' ? getCapacityColor(d, false) : getDelayColor(d, false);
        },
        widthUnits: 'pixels',
        widthMinPixels: 3,
        pickable: true,
        autoHighlight: false,
        capRounded: true,
        jointRounded: true,
        updateTriggers: {
          getPath: [centersById],
          getWidth: [selectedLaneId],
          getColor: [viewMode],
        },
      })
    );
  }

  // Air routes - using ArcLayer for curved, elevated lines
  if (airLanes.length > 0) {
    layers.push(
      new ArcLayer({
        id: "flows-air",
        data: airLanes,
        visible: true,
        getSourcePosition: (d: Lane) => {
          const c = centersById[d.origin];
          // Should always exist due to filtering above, but keep safety check
          return c ? [c.lng, c.lat] : [0, 0];
        },
        getTargetPosition: (d: Lane) => {
          const c = centersById[d.dest];
          // Should always exist due to filtering above, but keep safety check
          return c ? [c.lng, c.lat] : [0, 0];
        },
        // Air routes are slightly thinner
        getWidth: (d: Lane) => {
          const base = Math.max(2, Math.min(10, d.avgDailyVolume / 450));
          return d.id === selectedLaneId ? base * 1.2 : base;
        },
        // Higher arcs for air routes
        getHeight: (d: Lane) => {
          const volumeFactor = Math.min(1, d.avgDailyVolume / 5000);
          return 0.3 + (volumeFactor * 0.3); // Range: 0.3 to 0.6
        },
        getTilt: 15,
        // Color based on view mode
        getSourceColor: (d: Lane) => {
          return viewMode === 'capacity' ? getCapacityColor(d, false) : getDelayColor(d, false);
        },
        getTargetColor: (d: Lane) => {
          return viewMode === 'capacity' ? getCapacityColor(d, true) : getDelayColor(d, true);
        },
        pickable: true,
        autoHighlight: false,
        greatCircle: true,
        updateTriggers: {
          getSourcePosition: [centersById],
          getTargetPosition: [centersById],
          getWidth: [selectedLaneId],
          getHeight: [],
          getSourceColor: [viewMode],
          getTargetColor: [viewMode],
        },
      })
    );
  }

  return layers;
}

