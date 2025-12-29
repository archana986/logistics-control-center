import { Drawer, DrawerContent, DrawerHeader, DrawerTitle, DrawerFooter } from "@/components/ui/drawer";
import { Button } from "@/components/ui/button";
import { generateCustomerUpdateWithAI, generateSpotQuoteWithAI } from "@/lib/genai";
import { useEffect, useState } from "react";
import { Copy, Send, CheckCircle2, Loader2, Sparkles, DollarSign } from "lucide-react";

interface GenAIDrawerProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  payload: any | null;
  onApprove?: () => void;
}

export default function GenAIDrawer({ open, onOpenChange, payload, onApprove }: GenAIDrawerProps) {
  const [copied, setCopied] = useState(false);
  const [sent, setSent] = useState(false);
  const [loading, setLoading] = useState(false);
  const [text, setText] = useState("");
  const [source, setSource] = useState<string>("");

  // Generate message when drawer opens or payload changes
  useEffect(() => {
    if (!open || !payload) {
      setText("");
      setSource("");
      return;
    }

    const generateContent = async () => {
      setLoading(true);
      try {
        if (payload.mode === 'capacity') {
          // Generate spot quote
          const { laneId, action, lane, volumeChange } = payload;
          const result = await generateSpotQuoteWithAI({
            laneId,
            action,
            lane,
            volumeChange,
          });
          setText(result.quote);
          setSource(result.source);
        } else {
          // Generate customer update (congestion mode)
          const { customerName, laneId, strategy, incidentSummary, customer, incident } = payload;
          const result = await generateCustomerUpdateWithAI({
            customerName: customerName || "Valued Customer",
            laneId,
            strategy,
            incidentSummary: incidentSummary || "operational disruption",
            customer,
            incident,
          });
          setText(result.message);
          setSource(result.source);
        }
      } catch (error) {
        console.error("Error generating content:", error);
        setText("Error generating content. Please try again.");
        setSource("error");
      } finally {
        setLoading(false);
      }
    };

    generateContent();
  }, [open, payload]);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleSend = () => {
    // Demo only - no actual sending
    setSent(true);
    
    // If this is a capacity quote being approved, trigger the callback
    if (payload?.mode === 'capacity' && onApprove) {
      onApprove();
    }
    
    setTimeout(() => {
      onOpenChange(false);
      setSent(false);
    }, 1500);
  };

  const isCapacityMode = payload?.mode === 'capacity';
  const title = isCapacityMode ? "AI-Generated Spot Pricing Quote" : "AI-Generated Customer Message";

  return (
    <Drawer open={open} onOpenChange={onOpenChange}>
      <DrawerContent className="max-h-[85vh]">
        <div className="mx-auto w-full max-w-4xl">
          <DrawerHeader>
            <DrawerTitle className="flex items-center gap-2">
              {isCapacityMode && <DollarSign className="h-5 w-5" />}
              {title}
            </DrawerTitle>
          </DrawerHeader>

          <div className="p-4 pb-0">
            <div className="bg-muted/50 rounded-lg p-4 mb-2">
              {loading ? (
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  {isCapacityMode ? 'Generating spot pricing quote with Databricks AI...' : 'Generating personalized message with Databricks AI...'}
                </div>
              ) : (
                <>
                  <div className="flex items-center gap-2 text-sm text-muted-foreground mb-2">
                    {source === "databricks" ? (
                      <>
                        <Sparkles className="h-4 w-4 text-primary" />
                        {isCapacityMode 
                          ? 'Generated using Databricks foundation model with capacity analysis and pricing intelligence'
                          : 'Generated using Databricks foundation model with network context and incident analysis'}
                      </>
                    ) : source === "fallback" ? (
                      <>
                        <div className="w-2 h-2 rounded-full bg-amber-500"></div>
                        Generated using fallback logic (Databricks model unavailable)
                      </>
                    ) : source === "fallback-local" ? (
                      <>
                        <div className="w-2 h-2 rounded-full bg-amber-500"></div>
                        Generated locally (Backend unavailable)
                      </>
                    ) : (
                      <>
                        <div className="w-2 h-2 rounded-full bg-primary animate-pulse"></div>
                        {isCapacityMode
                          ? 'Generated using capacity analysis and market pricing data'
                          : 'Generated using network context, incident analysis, and customer interaction history'}
                      </>
                    )}
                  </div>
                  {!isCapacityMode && payload?.customer?.recentInteractions && payload.customer.recentInteractions.length > 0 && (
                    <div className="mt-2 flex items-center gap-2 text-xs text-green-600">
                      <CheckCircle2 className="h-3 w-3" />
                      Personalized using {payload.customer.recentInteractions.slice(0, 2).length} recent interaction(s)
                    </div>
                  )}
                  {isCapacityMode && payload?.action && (
                    <div className="mt-2 flex items-center gap-2 text-xs text-blue-600">
                      <CheckCircle2 className="h-3 w-3" />
                      Based on {payload.action.type === 'pull_forward' ? 'pull forward' : 'hold back'} optimization strategy
                    </div>
                  )}
                </>
              )}
            </div>

            {loading ? (
              <div className="w-full h-80 border rounded-lg flex items-center justify-center bg-muted/20">
                <div className="flex flex-col items-center gap-3">
                  <Loader2 className="h-8 w-8 animate-spin text-primary" />
                  <p className="text-sm text-muted-foreground">Analyzing incident and generating message...</p>
                </div>
              </div>
            ) : (
              <textarea
                className="w-full h-80 p-4 border rounded-lg font-mono text-sm bg-background resize-none focus:outline-none focus:ring-2 focus:ring-ring"
                value={text}
                readOnly
              />
            )}
          </div>

          <DrawerFooter>
            <div className="flex gap-3 w-full">
              <Button
                variant="outline"
                onClick={handleCopy}
                className="flex-1"
                disabled={loading || !text}
              >
                {copied ? (
                  <>
                    <CheckCircle2 className="mr-2 h-4 w-4" />
                    Copied!
                  </>
                ) : (
                  <>
                    <Copy className="mr-2 h-4 w-4" />
                    Copy to Clipboard
                  </>
                )}
              </Button>
              <Button
                onClick={handleSend}
                disabled={sent || loading || !text}
                className="flex-1"
              >
                {sent ? (
                  <>
                    <CheckCircle2 className="mr-2 h-4 w-4" />
                    {isCapacityMode ? 'Approved!' : 'Sent!'}
                  </>
                ) : (
                  <>
                    {isCapacityMode ? <DollarSign className="mr-2 h-4 w-4" /> : <Send className="mr-2 h-4 w-4" />}
                    {isCapacityMode ? 'Approve Quote' : 'Mark as Sent'}
                  </>
                )}
              </Button>
            </div>
          </DrawerFooter>
        </div>
      </DrawerContent>
    </Drawer>
  );
}

