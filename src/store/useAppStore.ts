import { create } from "zustand";
import type { Incident, Shipment, RerouteSuggestion } from "../types/domain";

interface AppState {
  incidents: Incident[];
  urgentShipments: Shipment[];
  rerouteSuggestions: RerouteSuggestion[];
  openReroute: boolean;
  openGenAI: boolean;
  genPayload: any | null;
  
  setIncidents: (incidents: Incident[]) => void;
  setUrgentShipments: (shipments: Shipment[]) => void;
  setRerouteSuggestions: (suggestions: RerouteSuggestion[]) => void;
  setOpenReroute: (open: boolean) => void;
  setOpenGenAI: (open: boolean) => void;
  setGenPayload: (payload: any | null) => void;
}

export const useAppStore = create<AppState>((set) => ({
  incidents: [],
  urgentShipments: [],
  rerouteSuggestions: [],
  openReroute: false,
  openGenAI: false,
  genPayload: null,
  
  setIncidents: (incidents) => set({ incidents }),
  setUrgentShipments: (urgentShipments) => set({ urgentShipments }),
  setRerouteSuggestions: (rerouteSuggestions) => set({ rerouteSuggestions }),
  setOpenReroute: (openReroute) => set({ openReroute }),
  setOpenGenAI: (openGenAI) => set({ openGenAI }),
  setGenPayload: (genPayload) => set({ genPayload }),
}));

