// Session-based state management for user actions
// This state is unique to the user's session and purged when the browser is closed

const SESSION_KEYS = {
  APPROVED_EVENTS: 'approved_events',
  REJECTED_EVENTS: 'rejected_events',
  APPROVED_QUOTES: 'approved_quotes',
  REJECTED_QUOTES: 'rejected_quotes',
};

// Custom event for state changes
export const EVENT_STATE_CHANGED = 'eventStateChanged';
export const QUOTE_STATE_CHANGED = 'quoteStateChanged';

// Event Actions
export function approveEvent(eventId: string): void {
  const approved = getApprovedEvents();
  if (!approved.includes(eventId)) {
    approved.push(eventId);
    sessionStorage.setItem(SESSION_KEYS.APPROVED_EVENTS, JSON.stringify(approved));
  }
  
  // Remove from rejected if it was there
  const rejected = getRejectedEvents().filter(id => id !== eventId);
  sessionStorage.setItem(SESSION_KEYS.REJECTED_EVENTS, JSON.stringify(rejected));
  
  // Dispatch custom event to notify other components
  window.dispatchEvent(new CustomEvent(EVENT_STATE_CHANGED, { detail: { eventId, approved: true } }));
}

export function rejectEvent(eventId: string): void {
  const rejected = getRejectedEvents();
  if (!rejected.includes(eventId)) {
    rejected.push(eventId);
    sessionStorage.setItem(SESSION_KEYS.REJECTED_EVENTS, JSON.stringify(rejected));
  }
  
  // Remove from approved if it was there
  const approved = getApprovedEvents().filter(id => id !== eventId);
  sessionStorage.setItem(SESSION_KEYS.APPROVED_EVENTS, JSON.stringify(approved));
  
  // Dispatch custom event to notify other components
  window.dispatchEvent(new CustomEvent(EVENT_STATE_CHANGED, { detail: { eventId, rejected: true } }));
}

export function isEventApproved(eventId: string): boolean {
  return getApprovedEvents().includes(eventId);
}

export function isEventRejected(eventId: string): boolean {
  return getRejectedEvents().includes(eventId);
}

export function getApprovedEvents(): string[] {
  const stored = sessionStorage.getItem(SESSION_KEYS.APPROVED_EVENTS);
  return stored ? JSON.parse(stored) : [];
}

export function getRejectedEvents(): string[] {
  const stored = sessionStorage.getItem(SESSION_KEYS.REJECTED_EVENTS);
  return stored ? JSON.parse(stored) : [];
}

// Quote Actions
export function approveQuote(quoteId: string): void {
  const approved = getApprovedQuotes();
  if (!approved.includes(quoteId)) {
    approved.push(quoteId);
    sessionStorage.setItem(SESSION_KEYS.APPROVED_QUOTES, JSON.stringify(approved));
  }
  
  // Remove from rejected if it was there
  const rejected = getRejectedQuotes().filter(id => id !== quoteId);
  sessionStorage.setItem(SESSION_KEYS.REJECTED_QUOTES, JSON.stringify(rejected));
  
  // Dispatch custom event to notify other components
  window.dispatchEvent(new CustomEvent(QUOTE_STATE_CHANGED, { detail: { quoteId, approved: true } }));
}

export function rejectQuote(quoteId: string): void {
  const rejected = getRejectedQuotes();
  if (!rejected.includes(quoteId)) {
    rejected.push(quoteId);
    sessionStorage.setItem(SESSION_KEYS.REJECTED_QUOTES, JSON.stringify(rejected));
  }
  
  // Remove from approved if it was there
  const approved = getApprovedQuotes().filter(id => id !== quoteId);
  sessionStorage.setItem(SESSION_KEYS.APPROVED_QUOTES, JSON.stringify(approved));
  
  // Dispatch custom event to notify other components
  window.dispatchEvent(new CustomEvent(QUOTE_STATE_CHANGED, { detail: { quoteId, rejected: true } }));
}

export function isQuoteApproved(quoteId: string): boolean {
  return getApprovedQuotes().includes(quoteId);
}

export function isQuoteRejected(quoteId: string): boolean {
  return getRejectedQuotes().includes(quoteId);
}

export function getApprovedQuotes(): string[] {
  const stored = sessionStorage.getItem(SESSION_KEYS.APPROVED_QUOTES);
  return stored ? JSON.parse(stored) : [];
}

export function getRejectedQuotes(): string[] {
  const stored = sessionStorage.getItem(SESSION_KEYS.REJECTED_QUOTES);
  return stored ? JSON.parse(stored) : [];
}

// Clear all session state (useful for testing)
export function clearAllSessionState(): void {
  Object.values(SESSION_KEYS).forEach(key => {
    sessionStorage.removeItem(key);
  });
}



