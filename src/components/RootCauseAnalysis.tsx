import { useEffect, useState, useRef } from "react";
import type { JSX } from "react";
import { Brain, CheckCircle2, Send, Loader2 } from "lucide-react";
import type { Incident } from "@/types/domain";
import { Button } from "@/components/ui/button";

// Get backend URL from environment variable
const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || "http://localhost:8001/api";

interface RootCauseAnalysisProps {
  incidents: Incident[];
  triggerAnalysis?: boolean;
  laneId?: string;
}

interface ChatMessage {
  role: "system" | "assistant" | "user";
  content: string;
  isTyping?: boolean;
  source?: string;
}

// Helper function to normalize special unicode characters for better display
const normalizeText = (text: string): string => {
  return text
    .replace(/‑/g, '-')
    .replace(/–/g, '-')
    .replace(/—/g, '-')
    .replace(/'/g, "'")
    .replace(/'/g, "'")
    .replace(/"/g, '"')
    .replace(/"/g, '"')
    .replace(/…/g, '...');
};

/** Build a rich boilerplate analysis from the incidents data for a lane. */
function buildBoilerplateAnalysis(incidents: Incident[], laneId: string): string {
  const primary = incidents[0];
  const incidentType = (primary.type || "unknown").replace(/_/g, " ");
  const cause = primary.cause || "Unknown cause";
  const ref = primary.ref || "N/A";
  const impact = primary.impactMinutes || 0;
  const confidence = ((primary.confidence || 0) * 100).toFixed(0);

  const otherIncidents = incidents.slice(1);
  const otherSummary = otherIncidents.length > 0
    ? `\n\n**Additional Active Incidents (${otherIncidents.length}):**\n` +
      otherIncidents.map(inc => `- **${(inc.type || "").replace(/_/g, " ")}** (${inc.ref}): ${inc.cause} - +${inc.impactMinutes || 0}m delay`).join("\n")
    : "";

  return `## Root Cause Analysis - ${laneId}

**Primary Incident:** ${incidentType} (${ref})
**Cause:** ${cause}
**Impact:** +${impact} minutes delay | ${confidence}% detection confidence

---

### Assessment

The ${incidentType} on lane ${laneId} has been identified with ${confidence}% confidence. The root cause is: **${cause}**.

### Current Impact
- Estimated delay: **+${impact} minutes**
${primary.impactThroughputPct ? `- Throughput impact: **${primary.impactThroughputPct}%**` : ""}
- Active incidents on this lane: **${incidents.length}**

### Recommended Actions
1. Monitor lane status for further developments
2. Consider rerouting urgent shipments through alternative lanes
3. Notify affected customers proactively
4. Review historical patterns for similar incidents on this lane
${otherSummary}

---
*Querying Knowledge Assistant for deeper analysis...*`;
}

export default function RootCauseAnalysis({ incidents, triggerAnalysis = false, laneId }: RootCauseAnalysisProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [chatInput, setChatInput] = useState("");
  const [isSendingChat, setIsSendingChat] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  // Use the first incident as the primary one for analysis context
  const primaryIncident = incidents[0] || null;

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Function to send chat message to backend
  const sendChatMessage = async () => {
    if (!chatInput.trim() || isSendingChat) return;

    const userMessage = chatInput.trim();
    setChatInput("");
    setIsSendingChat(true);

    // Add user message to chat
    setMessages(prev => [...prev, { role: "user", content: userMessage }]);

    try {
      const response = await fetch(`${BACKEND_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: userMessage,
          context: {
            incident: primaryIncident,
            lane: { id: laneId }
          }
        }),
      });

      if (!response.ok) throw new Error(`API error: ${response.status}`);

      const data = await response.json();
      setMessages(prev => [...prev, {
        role: "assistant",
        content: data.message,
        source: data.source
      }]);
    } catch (error) {
      console.error("Error sending chat message:", error);
      setMessages(prev => [...prev, {
        role: "assistant",
        content: "I'm having trouble connecting right now. Please try again in a moment.",
        source: "error"
      }]);
    } finally {
      setIsSendingChat(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendChatMessage();
    }
  };

  // Create a stable identifier for the current set of incidents
  const incidentsKey = incidents.map(i => i.ref).join(',');

  useEffect(() => {
    if (!triggerAnalysis || incidents.length === 0) return;

    setIsAnalyzing(true);
    setMessages([]);

    // Step 1: Show system init message
    setMessages([{
      role: "system",
      content: "Initiating automated root cause analysis...",
      source: "system"
    }]);

    // Step 2: Show boilerplate analysis immediately
    const boilerplate = buildBoilerplateAnalysis(incidents, laneId || "unknown");
    setTimeout(() => {
      setMessages(prev => [
        ...prev,
        {
          role: "assistant",
          content: boilerplate,
          source: "analysis"
        }
      ]);
    }, 600);

    // Step 3: Call Knowledge Assistant for deeper analysis
    const incidentRef = primaryIncident?.ref || "Unknown";
    const incidentType = (primaryIncident?.type || "").replace(/_/g, ' ');
    const question = `Analyze incident ${incidentRef} on lane ${laneId || 'unknown'}. This is a ${incidentType} with cause: ${primaryIncident?.cause || 'unknown'}. Impact is ${primaryIncident?.impactMinutes || 0} minutes delay. Check maintenance history, similar past incidents, and provide root cause analysis with recommended actions.`;

    fetch(`${BACKEND_URL}/knowledge/query`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        question,
        context: {
          incident: primaryIncident,
          lane: { id: laneId }
        }
      }),
    })
      .then(res => {
        if (!res.ok) throw new Error(`API error: ${res.status}`);
        return res.json();
      })
      .then((result) => {
        if (result.source !== "error" && result.answer && !result.answer.startsWith("Error") && !result.answer.startsWith("Knowledge Assistant")) {
          setMessages(prev => [
            ...prev,
            {
              role: "assistant",
              content: `## Knowledge Assistant Analysis\n\n${result.answer}`,
              source: result.source
            }
          ]);
        }
        setIsAnalyzing(false);
      })
      .catch((error) => {
        console.error("Error querying Knowledge Assistant:", error);
        // Boilerplate is already shown, so just mark as complete
        setIsAnalyzing(false);
      });
  }, [triggerAnalysis, incidentsKey, laneId]);

  // Don't show anything if analysis hasn't been triggered yet
  if (!triggerAnalysis) {
    return null;
  }

  if (incidents.length === 0) {
    return (
      <div className="border rounded-lg p-4 bg-muted/30">
        <div className="flex items-center gap-2 mb-2">
          <Brain className="h-4 w-4 text-muted-foreground" />
          <span className="font-medium text-sm">AirOps AI Root Cause Analysis</span>
        </div>
        <p className="text-xs text-muted-foreground">
          No active incidents detected on this lane.
        </p>
      </div>
    );
  }

  return (
    <div className="border rounded-lg overflow-hidden bg-gradient-to-br from-purple-500/5 to-blue-500/5">
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-600 to-blue-600 px-4 py-3">
        <div className="flex items-center gap-2">
          <Brain className="h-5 w-5 text-white" />
          <span className="font-semibold text-white">AirOps AI Root Cause Analysis</span>
          {isAnalyzing && (
            <div className="ml-auto flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-white animate-pulse"></div>
              <span className="text-xs text-white/90">Analyzing...</span>
            </div>
          )}
        </div>
      </div>

      {/* Messages */}
      <div className="p-4 space-y-3 max-h-[500px] overflow-y-auto">
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`${
              msg.role === "system"
                ? "text-xs text-muted-foreground italic"
                : msg.role === "user"
                ? "bg-primary/10 border border-primary/20 rounded-lg p-3 ml-8"
                : "bg-background border rounded-lg p-3"
            }`}
          >
            {msg.role === "user" && (
              <div className="flex items-start gap-2">
                <div className="font-medium text-sm text-primary">You:</div>
                <div className="text-sm flex-1">{msg.content}</div>
              </div>
            )}
            {msg.role === "assistant" && (
              <div className="prose prose-sm max-w-none">
                {(() => {
                  const normalizedContent = normalizeText(msg.content);
                  const lines = normalizedContent.split('\n');
                  const elements: JSX.Element[] = [];
                  let i = 0;

                  while (i < lines.length) {
                    const line = lines[i];

                    // Markdown tables
                    if (line.trim().startsWith('|') && line.trim().endsWith('|')) {
                      const tableLines: string[] = [];
                      while (i < lines.length && lines[i].trim().startsWith('|') && lines[i].trim().endsWith('|')) {
                        tableLines.push(lines[i]);
                        i++;
                      }
                      if (tableLines.length >= 2) {
                        const headerLine = tableLines[0];
                        const dataLines = tableLines.slice(2);
                        const headers = headerLine.split('|').map(h => h.trim()).filter(h => h.length > 0);
                        const rows = dataLines.map(l => l.split('|').map(c => c.trim()).filter(c => c.length > 0));
                        elements.push(
                          <div key={`table-${elements.length}`} className="my-4 overflow-x-auto">
                            <table className="min-w-full border-collapse border border-gray-300 text-sm">
                              <thead className="bg-gray-50">
                                <tr>{headers.map((h, hi) => <th key={hi} className="border border-gray-300 px-3 py-2 text-left font-semibold">{h}</th>)}</tr>
                              </thead>
                              <tbody>{rows.map((row, ri) => <tr key={ri} className="hover:bg-gray-50">{row.map((cell, ci) => <td key={ci} className="border border-gray-300 px-3 py-2">{cell}</td>)}</tr>)}</tbody>
                            </table>
                          </div>
                        );
                      }
                      continue;
                    }

                    // Markdown headers
                    if (line.trim().match(/^#{1,6}\s+/)) {
                      const level = line.match(/^(#{1,6})/)?.[0].length || 2;
                      const text = line.replace(/^#{1,6}\s+/, '').trim();
                      const fontSize = level === 1 ? 'text-lg' : level === 2 ? 'text-base' : 'text-sm';
                      elements.push(<div key={elements.length} className={`font-bold ${fontSize} mb-2 mt-4 first:mt-0`}>{text}</div>);
                    }
                    // Horizontal rules
                    else if (line.trim().match(/^[-*]{3,}$/)) {
                      elements.push(<hr key={elements.length} className="my-3 border-gray-300" />);
                    }
                    // Checkmark bullets
                    else if (line.trim().startsWith('- ✅') || line.trim().startsWith('✅')) {
                      elements.push(
                        <div key={elements.length} className="flex items-start gap-2 text-sm mb-1 ml-2">
                          <CheckCircle2 className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                          <span>{line.replace(/^[-\s]*✅\s*/, '')}</span>
                        </div>
                      );
                    }
                    // Bold text
                    else if (line.includes('**')) {
                      const parts = line.split(/(\*\*.*?\*\*)/g);
                      elements.push(
                        <div key={elements.length} className="text-sm mb-1">
                          {parts.map((part, j) =>
                            part.startsWith('**') ?
                              <strong key={j}>{part.replace(/\*\*/g, '')}</strong> :
                              part
                          )}
                        </div>
                      );
                    }
                    // Bullet points
                    else if (line.trim().match(/^[-•]\s/)) {
                      elements.push(
                        <div key={elements.length} className="flex items-start gap-2 text-sm mb-1 ml-2">
                          <span className="text-primary mt-1">•</span>
                          <span>{line.replace(/^[-•\s]*/, '').trim()}</span>
                        </div>
                      );
                    }
                    // Numbered lists
                    else if (line.trim().match(/^\d+\./)) {
                      elements.push(<div key={elements.length} className="text-sm mb-1 ml-2">{line}</div>);
                    }
                    // Emoji headers
                    else if (line.trim().match(/^[🔍📊⚠️📋💡]/)) {
                      elements.push(<div key={elements.length} className="text-sm mb-2 font-medium">{line}</div>);
                    }
                    // Regular text
                    else if (line.trim()) {
                      elements.push(<div key={elements.length} className="text-sm mb-1">{line}</div>);
                    } else {
                      elements.push(<div key={elements.length} className="h-2" />);
                    }

                    i++;
                  }
                  return elements;
                })()}
              </div>
            )}
            {msg.role === "system" && msg.content}
          </div>
        ))}

        {isSendingChat && (
          <div className="bg-background border rounded-lg p-3">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />
              <span>AI is thinking...</span>
            </div>
          </div>
        )}

        <div ref={chatEndRef} />

        {isAnalyzing && messages.length > 0 && (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <div className="flex gap-1">
              <div className="w-2 h-2 rounded-full bg-primary animate-bounce" style={{ animationDelay: '0ms' }}></div>
              <div className="w-2 h-2 rounded-full bg-primary animate-bounce" style={{ animationDelay: '150ms' }}></div>
              <div className="w-2 h-2 rounded-full bg-primary animate-bounce" style={{ animationDelay: '300ms' }}></div>
            </div>
            <span>Querying Knowledge Assistant...</span>
          </div>
        )}
      </div>

      {/* Footer */}
      {!isAnalyzing && messages.length > 0 && (
        <>
          <div className="border-t bg-muted/30 px-4 py-2">
            <div className="flex items-center justify-between text-xs text-muted-foreground">
              <span>AirOps AI Analysis</span>
              <span className="text-green-600 flex items-center gap-1">
                <CheckCircle2 className="h-3 w-3" />
                Complete
              </span>
            </div>
          </div>

          {/* Chat Input */}
          <div className="border-t p-4 bg-background">
            <div className="flex items-center gap-2 mb-2">
              <Brain className="h-4 w-4 text-primary" />
              <span className="text-sm font-medium">Ask a follow-up question:</span>
            </div>
            <div className="flex gap-2">
              <input
                type="text"
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="e.g., What preventive measures should we take?"
                className="flex-1 px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                disabled={isSendingChat}
              />
              <Button
                onClick={sendChatMessage}
                disabled={!chatInput.trim() || isSendingChat}
                size="sm"
                className="px-4"
              >
                {isSendingChat ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <>
                    <Send className="h-4 w-4 mr-1" />
                    Send
                  </>
                )}
              </Button>
            </div>
            <div className="mt-2 text-xs text-muted-foreground">
              Analyzing: {primaryIncident?.ref || 'Unknown'} on {laneId || 'Unknown lane'}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
