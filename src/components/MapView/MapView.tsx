import { Map } from "react-map-gl/maplibre";
import DeckGL from "@deck.gl/react";
import { useMemo, useState, useEffect, useRef } from "react";
import { hubsLayer, flowsLayer } from "./layers";
import type { Center, Lane } from "../../types/domain";
import "maplibre-gl/dist/maplibre-gl.css";

const INITIAL_VIEW_STATE = {
  longitude: -88,
  latitude: 38.5,
  zoom: 4.2,
  bearing: 0,
  pitch: 30,
};

interface MapViewProps {
  centers: Center[];
  lanes: Lane[];
  selectedLaneId?: string | null;
  onLaneClick?: (laneId: string) => void;
  viewMode?: 'congestion' | 'capacity';
  autoZoomToLanes?: boolean;
}

function calculateBounds(lanes: Lane[], centersById: Record<string, Center>) {
  if (lanes.length === 0) return null;

  let minLng = Infinity;
  let maxLng = -Infinity;
  let minLat = Infinity;
  let maxLat = -Infinity;

  lanes.forEach(lane => {
    const origin = centersById[lane.origin];
    const dest = centersById[lane.dest];
    
    if (origin) {
      minLng = Math.min(minLng, origin.lng);
      maxLng = Math.max(maxLng, origin.lng);
      minLat = Math.min(minLat, origin.lat);
      maxLat = Math.max(maxLat, origin.lat);
    }
    
    if (dest) {
      minLng = Math.min(minLng, dest.lng);
      maxLng = Math.max(maxLng, dest.lng);
      minLat = Math.min(minLat, dest.lat);
      maxLat = Math.max(maxLat, dest.lat);
    }
  });

  if (minLng === Infinity) return null;

  // Add padding
  const padding = 0.1;
  const lngRange = maxLng - minLng;
  const latRange = maxLat - minLat;
  
  return {
    minLng: minLng - lngRange * padding,
    maxLng: maxLng + lngRange * padding,
    minLat: minLat - latRange * padding,
    maxLat: maxLat + latRange * padding,
  };
}

function calculateZoomFromBounds(bounds: { minLng: number; maxLng: number; minLat: number; maxLat: number }) {
  const lngRange = bounds.maxLng - bounds.minLng;
  const latRange = bounds.maxLat - bounds.minLat;
  
  // Calculate center
  const centerLng = (bounds.minLng + bounds.maxLng) / 2;
  const centerLat = (bounds.minLat + bounds.maxLat) / 2;
  
  // Estimate zoom level based on the larger range
  // This is a simplified calculation - you may need to adjust based on your map projection
  const maxRange = Math.max(lngRange, latRange);
  let zoom = 4.2;
  
  if (maxRange < 5) zoom = 6;
  else if (maxRange < 10) zoom = 5;
  else if (maxRange < 20) zoom = 4.5;
  else if (maxRange < 40) zoom = 4;
  else zoom = 3.5;
  
  return {
    longitude: centerLng,
    latitude: centerLat,
    zoom: Math.max(3, Math.min(7, zoom)),
    bearing: 0,
    pitch: 30,
  };
}

export default function MapView({ centers, lanes, selectedLaneId, onLaneClick, viewMode = 'congestion', autoZoomToLanes = false }: MapViewProps) {
  const [viewState, setViewState] = useState(INITIAL_VIEW_STATE);
  const isInitialMount = useRef(true);
  const previousLanesRef = useRef<string>('');

  const centersById = useMemo(
    () => Object.fromEntries(centers.map((c) => [c.id, c])),
    [centers]
  );

  const layers = useMemo(
    () => [
      ...flowsLayer(lanes, centersById, selectedLaneId, viewMode),
      hubsLayer(centers),
    ],
    [lanes, centersById, selectedLaneId, viewMode, centers]
  );

  // Auto-zoom to filtered lanes when filters change
  useEffect(() => {
    // Skip if auto-zoom is disabled or data isn't ready
    if (!autoZoomToLanes || centers.length === 0) {
      if (isInitialMount.current) {
        isInitialMount.current = false;
      }
      return;
    }

    // Skip zoom on very first mount
    if (isInitialMount.current) {
      isInitialMount.current = false;
      previousLanesRef.current = lanes.map(l => l.id).sort().join(',');
      return;
    }

    // If no lanes after filtering, reset to initial view
    if (lanes.length === 0) {
      setViewState(INITIAL_VIEW_STATE);
      previousLanesRef.current = '';
      return;
    }

    // Create a signature of the current lanes to detect changes
    const lanesSignature = lanes.map(l => l.id).sort().join(',');
    
    // Only zoom if lanes actually changed (not just on every render)
    if (lanesSignature === previousLanesRef.current) {
      return;
    }
    
    previousLanesRef.current = lanesSignature;

    // Calculate bounds and zoom to filtered lanes
    const bounds = calculateBounds(lanes, centersById);
    if (bounds) {
      const newViewState = calculateZoomFromBounds(bounds);
      setViewState(newViewState);
    }
  }, [lanes, centersById, autoZoomToLanes, centers.length]);

  // Don't render the map if centers haven't loaded yet
  if (!centers || centers.length === 0) {
    return (
      <div className="h-full w-full relative flex items-center justify-center bg-slate-900">
        <div className="text-center">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-white border-r-transparent"></div>
          <div className="mt-4 text-white">Loading map...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full w-full relative">
      <DeckGL
        viewState={viewState}
        onViewStateChange={({ viewState: newViewState }) => {
          if (newViewState && typeof newViewState === 'object' && 'longitude' in newViewState && 'latitude' in newViewState && 'zoom' in newViewState) {
            setViewState({
              longitude: Number(newViewState.longitude),
              latitude: Number(newViewState.latitude),
              zoom: Number(newViewState.zoom),
              bearing: newViewState.bearing != null ? Number(newViewState.bearing) : 0,
              pitch: newViewState.pitch != null ? Number(newViewState.pitch) : 30,
            });
          }
        }}
        layers={layers}
        controller={true}
        getTooltip={({ object }) => {
          if (!object) return null;
          if (object.id) {
            // Lane tooltip only
            const modeIcon = object.mode === 'air' ? '✈️' : '🚚';
            
            // Different tooltip for capacity vs congestion view
            if (viewMode === 'capacity') {
              const capacityPct = object.utilizationPct ? (object.utilizationPct * 100).toFixed(1) : '0';
              return {
                html: `<div class="deck-tooltip">
                  <div style="font-weight: 600; margin-bottom: 4px;">${modeIcon} ${object.id}</div>
                  <div style="font-size: 11px; opacity: 0.8; text-transform: capitalize;">${object.mode} Route</div>
                  <div style="margin-top: 4px;">Volume: ${object.avgDailyVolume.toLocaleString()} pkgs/day</div>
                  <div>Capacity: ${capacityPct}%</div>
                  <div>Available: ${object.availableCapacity ? object.availableCapacity.toLocaleString() : '0'} pkgs</div>
                </div>`,
                style: {
                  backgroundColor: 'transparent',
                  padding: '0',
                }
              };
            } else {
              return {
                html: `<div class="deck-tooltip">
                  <div style="font-weight: 600; margin-bottom: 4px;">${modeIcon} ${object.id}</div>
                  <div style="font-size: 11px; opacity: 0.8; text-transform: capitalize;">${object.mode} Route</div>
                  <div style="margin-top: 4px;">Volume: ${object.avgDailyVolume.toLocaleString()} pkgs/day</div>
                  <div>On-time: ${(object.onTimePct * 100).toFixed(1)}%</div>
                  <div>Avg delay: ${object.delayMinutes}m</div>
                </div>`,
                style: {
                  backgroundColor: 'transparent',
                  padding: '0',
                }
              };
            }
          }
          return null;
        }}
        onClick={({ object }) => {
          if (object?.origin && onLaneClick) {
            onLaneClick(object.id);
          }
        }}
      >
        <Map
          reuseMaps
          mapStyle="https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json"
        />
      </DeckGL>
    </div>
  );
}
