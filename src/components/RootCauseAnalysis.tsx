import { useEffect, useState, useRef } from "react";
import type { JSX } from "react";
import { Brain, TrendingUp, AlertTriangle, CheckCircle2, Clock, Send, Loader2 } from "lucide-react";
import type { Incident } from "@/types/domain";
import { Button } from "@/components/ui/button";
import { queryKnowledge } from "@/lib/mockApi";

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
    .replace(/‑/g, '-')  // Non-breaking hyphen to regular hyphen
    .replace(/–/g, '-')  // En dash to regular hyphen
    .replace(/—/g, '-')  // Em dash to regular hyphen
    .replace(/'/g, "'")  // Smart quote to regular quote
    .replace(/'/g, "'")  // Smart quote to regular quote
    .replace(/"/g, '"')  // Smart quote to regular quote
    .replace(/"/g, '"')  // Smart quote to regular quote
    .replace(/…/g, '...'); // Ellipsis to three dots
};

export default function RootCauseAnalysis({ incidents, triggerAnalysis = false, laneId }: RootCauseAnalysisProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [chatInput, setChatInput] = useState("");
  const [isSendingChat, setIsSendingChat] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);
  
  // Check if there's any mechanical or maintenance incident
  const hasMechanicalIssue = incidents.some(inc => 
    inc.type === 'maintenance_check' ||
    inc.type === 'equipment_issue' ||
    inc.cause.toLowerCase().includes("landing gear") ||
    inc.cause.toLowerCase().includes("mechanical") ||
    inc.cause.toLowerCase().includes("hydraulic") ||
    inc.cause.toLowerCase().includes("maintenance")
  );
  
  // Get the specific mechanical incident for analysis
  const mechanicalIncident = incidents.find(inc => 
    inc.type === 'maintenance_check' ||
    inc.type === 'equipment_issue' ||
    inc.cause.toLowerCase().includes("landing gear") ||
    inc.cause.toLowerCase().includes("mechanical") ||
    inc.cause.toLowerCase().includes("hydraulic") ||
    inc.cause.toLowerCase().includes("maintenance")
  );
  
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
    setMessages(prev => [...prev, {
      role: "user",
      content: userMessage
    }]);
    
    try {
      const response = await fetch(`${BACKEND_URL}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message: userMessage,
          context: {
            incident: mechanicalIncident,
            lane: { id: laneId }
          }
        }),
      });
      
      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }
      
      const data = await response.json();
      
      // Add AI response to chat
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
    if (!hasMechanicalIssue || !triggerAnalysis) return;

    // Start AI analysis using Knowledge Assistant
    setIsAnalyzing(true);
    setMessages([]); // Clear any existing messages
    
    // Add initial system message
    setMessages([{
      role: "system",
      content: "Initiating automated root cause analysis...",
      source: "system"
    }]);
    
    // Build question for Knowledge Assistant
    const incidentRef = mechanicalIncident?.ref || "Unknown";
    const incidentType = mechanicalIncident?.type?.replace(/_/g, ' ') || "mechanical issue";
    const question = `Analyze incident ${incidentRef} on lane ${laneId || 'unknown'}. This is a ${incidentType} with cause: ${mechanicalIncident?.cause || 'unknown'}. Check maintenance history, similar past incidents, and provide root cause analysis with recommended actions.`;
    
    // Query Knowledge Assistant
    queryKnowledge(question, {
      incident: mechanicalIncident,
      lane: { id: laneId }
    }).then((result) => {
      // Add analysis messages
      setMessages(prev => [
        ...prev,
        {
          role: "assistant",
          content: `🔍 Analyzing incident: ${incidentRef} - ${incidentType}`,
          source: result.source
        },
        {
          role: "assistant",
          content: "📊 Querying historical maintenance database and incident reports...",
          source: result.source
        },
        {
          role: "assistant",
          content: result.answer || "Analysis complete. No specific recommendations available.",
          source: result.source
        }
      ]);
      setIsAnalyzing(false);
    }).catch((error) => {
      console.error("Error querying Knowledge Assistant:", error);
      // Fallback to simple analysis
      setMessages(prev => [
        ...prev,
        {
          role: "assistant",
          content: `⚠️ **Analysis Complete**\n\n**Incident**: ${mechanicalIncident?.cause || 'Unknown'}\n\n**Impact**: ${mechanicalIncident?.impactMinutes || 0} minutes delay\n\n**Assessment**: Maintenance issue detected with ${((mechanicalIncident?.confidence || 0) * 100).toFixed(0)}% confidence.\n\n**Status**: \n• ✅ Issue identified\n• ✅ Standard monitoring procedures recommended\n\n**Note**: Unable to access detailed analysis. Please check back later.`,
          source: "fallback"
        }
      ]);
      setIsAnalyzing(false);
    });
  }, [hasMechanicalIssue, mechanicalIncident, triggerAnalysis, incidentsKey, laneId]);

  // Don't show anything if analysis hasn't been triggered yet
  if (!triggerAnalysis) {
    return null;
  }

  if (!hasMechanicalIssue) {
    return (
      <div className="border rounded-lg p-4 bg-muted/30">
        <div className="flex items-center gap-2 mb-2">
          <Brain className="h-4 w-4 text-muted-foreground" />
          <span className="font-medium text-sm">AirOps AI Root Cause Analysis</span>
        </div>
        <p className="text-xs text-muted-foreground">
          No mechanical incidents detected. AI analysis will activate when aircraft maintenance issues are identified.
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
                  // Normalize special unicode characters
                  const normalizedContent = normalizeText(msg.content);
                  const lines = normalizedContent.split('\n');
                  const elements: JSX.Element[] = [];
                  let i = 0;
                  
                  while (i < lines.length) {
                    const line = lines[i];
                    
                    // Check if this is a markdown table line
                    if (line.trim().startsWith('|') && line.trim().endsWith('|')) {
                      // Collect all consecutive table lines
                      const tableLines: string[] = [];
                      while (i < lines.length && lines[i].trim().startsWith('|') && lines[i].trim().endsWith('|')) {
                        tableLines.push(lines[i]);
                        i++;
                      }
                      
                      // Parse and render the table
                      if (tableLines.length >= 2) {
                        const headerLine = tableLines[0];
                        // Skip separator line (index 1)
                        const dataLines = tableLines.slice(2);
                        
                        // Parse header
                        const headers = headerLine.split('|')
                          .map(h => h.trim())
                          .filter(h => h.length > 0);
                        
                        // Parse data rows
                        const rows = dataLines.map(line => 
                          line.split('|')
                            .map(cell => cell.trim())
                            .filter(cell => cell.length > 0)
                        );
                        
                        elements.push(
                          <div key={`table-${elements.length}`} className="my-4 overflow-x-auto">
                            <table className="min-w-full border-collapse border border-gray-300 text-sm">
                              <thead className="bg-gray-50">
                                <tr>
                                  {headers.map((header, idx) => (
                                    <th key={idx} className="border border-gray-300 px-3 py-2 text-left font-semibold">
                                      {header}
                                    </th>
                                  ))}
                                </tr>
                              </thead>
                              <tbody>
                                {rows.map((row, rowIdx) => (
                                  <tr key={rowIdx} className="hover:bg-gray-50">
                                    {row.map((cell, cellIdx) => (
                                      <td key={cellIdx} className="border border-gray-300 px-3 py-2">
                                        {cell}
                                      </td>
                                    ))}
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        );
                      }
                      continue;
                    }
                    
                    // Handle headers
                    if (line.startsWith('⚠️ **') || line.startsWith('📋 **') || line.startsWith('💡 **')) {
                      const text = line.replace(/[⚠️📋💡]\s*\*\*(.*?)\*\*/g, '$1');
                      elements.push(
                        <div key={elements.length} className="font-bold text-sm mb-2 mt-3 first:mt-0 flex items-center gap-2">
                          {line.startsWith('⚠️') && <AlertTriangle className="h-4 w-4 text-orange-500" />}
                          {line.startsWith('📋') && <Clock className="h-4 w-4 text-blue-500" />}
                          {line.startsWith('💡') && <TrendingUp className="h-4 w-4 text-green-500" />}
                          {text}
                        </div>
                      );
                    }
                    // Handle markdown headers (##, ###, etc.)
                    else if (line.trim().match(/^#{1,6}\s+/)) {
                      const level = line.match(/^(#{1,6})/)?.[0].length || 2;
                      const text = line.replace(/^#{1,6}\s+/, '').trim();
                      const fontSize = level === 1 ? 'text-lg' : level === 2 ? 'text-base' : 'text-sm';
                      elements.push(
                        <div key={elements.length} className={`font-bold ${fontSize} mb-2 mt-4 first:mt-0`}>
                          {text}
                        </div>
                      );
                    }
                    // Handle bold text
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
                    // Handle horizontal rules (---)
                    else if (line.trim().match(/^[-]{3,}$/)) {
                      elements.push(
                        <hr key={elements.length} className="my-3 border-gray-300" />
                      );
                    }
                    // Handle bullet points with checkmarks
                    else if (line.trim().startsWith('• ✅') || line.trim().startsWith('✅')) {
                      elements.push(
                        <div key={elements.length} className="flex items-start gap-2 text-sm mb-1 ml-2">
                          <CheckCircle2 className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                          <span>{line.replace(/^[•\s]*✅\s*/, '')}</span>
                        </div>
                      );
                    }
                    // Handle regular bullet points
                    else if (line.trim().startsWith('• ') || line.trim().startsWith('- ')) {
                      elements.push(
                        <div key={elements.length} className="flex items-start gap-2 text-sm mb-1 ml-2">
                          <span className="text-primary mt-1">•</span>
                          <span>{line.replace(/^[•\-\s]*/, '').trim()}</span>
                        </div>
                      );
                    }
                    // Handle numbered lists
                    else if (line.trim().match(/^\d+\./)) {
                      elements.push(
                        <div key={elements.length} className="text-sm mb-1 ml-2">{line}</div>
                      );
                    }
                    // Handle emoji lines
                    else if (line.trim().match(/^[🔍📊⚠️📋💡]/)) {
                      elements.push(
                        <div key={elements.length} className="text-sm mb-2 font-medium">{line}</div>
                      );
                    }
                    // Regular lines
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
            <span>Processing...</span>
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
              Connected to: {mechanicalIncident?.ref || 'Unknown'} on {laneId || 'Unknown lane'}
            </div>
          </div>
        </>
      )}
    </div>
  );
}

