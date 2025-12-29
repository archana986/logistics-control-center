import { X, TrendingUp, AlertTriangle, CheckCircle, MessageSquare, Edit3, ThumbsUp, ThumbsDown } from 'lucide-react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { useState, useEffect } from 'react';
import type { LogisticsEvent } from '../types/activity';
import { approveEvent, rejectEvent, isEventApproved, isEventRejected, EVENT_STATE_CHANGED } from '@/lib/sessionState';

interface DetailDrawerProps {
  event: LogisticsEvent | null;
  isOpen: boolean;
  onClose: () => void;
}

export function EventDetailDrawer({ event, isOpen, onClose }: DetailDrawerProps) {
  const [isApproved, setIsApproved] = useState(false);
  const [isRejected, setIsRejected] = useState(false);
  const [showApprovedMessage, setShowApprovedMessage] = useState(false);
  const [showRejectedMessage, setShowRejectedMessage] = useState(false);

  // Update state when event changes
  useEffect(() => {
    if (event) {
      setIsApproved(isEventApproved(event.id));
      setIsRejected(isEventRejected(event.id));
    }
  }, [event]);

  // Listen for state changes from other components (like EventCard)
  useEffect(() => {
    if (!event) return;

    const handleStateChange = (e: Event) => {
      const customEvent = e as CustomEvent;
      if (customEvent.detail.eventId === event.id) {
        setIsApproved(isEventApproved(event.id));
        setIsRejected(isEventRejected(event.id));
      }
    };

    window.addEventListener(EVENT_STATE_CHANGED, handleStateChange);
    return () => window.removeEventListener(EVENT_STATE_CHANGED, handleStateChange);
  }, [event]);

  if (!isOpen || !event) return null;

  const handleApprove = () => {
    approveEvent(event.id);
    setIsApproved(true);
    setIsRejected(false);
    setShowApprovedMessage(true);
    setTimeout(() => setShowApprovedMessage(false), 3000);
  };

  const handleReject = () => {
    rejectEvent(event.id);
    setIsRejected(true);
    setIsApproved(false);
    setShowRejectedMessage(true);
    setTimeout(() => setShowRejectedMessage(false), 3000);
  };

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black bg-opacity-30 z-40 transition-opacity"
        onClick={onClose}
      />

      {/* Drawer */}
      <div className="fixed top-0 right-0 h-full w-[800px] bg-white shadow-2xl z-50 flex flex-col animate-slide-in">
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-600 to-blue-700 text-white px-8 py-6">
          <div className="flex items-start justify-between mb-4">
            <div className="flex-1">
              <h2 className="text-white mb-2 text-xl font-semibold">{event.title}</h2>
              <div className="flex items-center gap-3 text-blue-100 text-sm">
                <span>{event.timestamp}</span>
                <span>•</span>
                <span>{event.agentName}</span>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-blue-600 rounded-lg transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          <div className="flex items-center gap-2">
            <StatusBadge status={event.status} />
            {event.tags.map((tag) => (
              <TagBadge key={tag} tag={tag} />
            ))}
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto">
          <div className="p-8 space-y-8">
            {/* Overview Section */}
            <section>
              <h3 className="text-gray-900 mb-4 flex items-center gap-2 font-semibold">
                <TrendingUp className="w-5 h-5 text-blue-600" />
                Overview
              </h3>
              
              {/* Situation → Action → Outcome Flow */}
              <div className="bg-gradient-to-br from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-6 mb-4">
                <div className="space-y-4">
                  <div>
                    <div className="text-xs text-blue-600 mb-1 font-medium">SITUATION</div>
                    <div className="text-gray-900">{event.situation}</div>
                  </div>
                  <div className="border-l-2 border-blue-300 pl-4">
                    <div className="text-xs text-blue-600 mb-1 font-medium">ACTION TAKEN</div>
                    <div className="text-gray-900">{event.action}</div>
                  </div>
                  <div className="border-l-2 border-blue-300 pl-4">
                    <div className="text-xs text-blue-600 mb-1 font-medium">EXPECTED OUTCOME</div>
                    <div className="text-gray-900">{event.expectedOutcome}</div>
                  </div>
                </div>
              </div>

              <p className="text-gray-700 leading-relaxed">{event.overview.fullNarrative}</p>
            </section>

            {/* Visual Data Components */}
            <section>
              <h3 className="text-gray-900 mb-4 font-semibold">Data & Metrics</h3>

              {/* Metrics Grid */}
              <div className="grid grid-cols-2 gap-4 mb-6">
                <MetricCard
                  label="Capacity Remaining"
                  value={event.visualData.metrics.capacityRemaining}
                  trend="neutral"
                />
                <MetricCard
                  label="Risk Level"
                  value={event.visualData.metrics.riskLevel}
                  trend={event.visualData.metrics.riskLevel === 'Low' ? 'positive' : event.visualData.metrics.riskLevel === 'High' ? 'negative' : 'neutral'}
                />
                <MetricCard
                  label="Forecast Confidence"
                  value={event.visualData.metrics.forecastConfidence}
                  trend="positive"
                />
                <MetricCard
                  label="Revenue Impact"
                  value={event.visualData.metrics.revenueImpact}
                  trend={event.visualData.metrics.revenueImpact.startsWith('+') ? 'positive' : 'negative'}
                />
              </div>

              {/* Capacity vs Demand Chart */}
              <div className="bg-white border border-gray-200 rounded-lg p-4 mb-4">
                <div className="text-sm text-gray-900 mb-4 font-medium">Capacity vs Demand Forecast</div>
                <ResponsiveContainer width="100%" height={200}>
                  <LineChart data={event.visualData.capacityData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                    <XAxis dataKey="date" tick={{ fontSize: 12 }} stroke="#6b7280" />
                    <YAxis tick={{ fontSize: 12 }} stroke="#6b7280" />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#fff', border: '1px solid #e5e7eb', borderRadius: '8px' }}
                    />
                    <Legend />
                    <Line type="monotone" dataKey="capacity" stroke="#3b82f6" strokeWidth={2} name="Capacity" />
                    <Line type="monotone" dataKey="demand" stroke="#8b5cf6" strokeWidth={2} name="Demand" />
                  </LineChart>
                </ResponsiveContainer>
              </div>

              {/* Cost Deviation Chart */}
              <div className="bg-white border border-gray-200 rounded-lg p-4 mb-4">
                <div className="text-sm text-gray-900 mb-4 font-medium">Cost Deviation Analysis</div>
                <ResponsiveContainer width="100%" height={200}>
                  <BarChart data={event.visualData.costDeviationData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                    <XAxis dataKey="date" tick={{ fontSize: 12 }} stroke="#6b7280" />
                    <YAxis tick={{ fontSize: 12 }} stroke="#6b7280" />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#fff', border: '1px solid #e5e7eb', borderRadius: '8px' }}
                    />
                    <Legend />
                    <Bar dataKey="cost" fill="#3b82f6" name="Actual Cost" />
                    <Bar dataKey="baseline" fill="#e5e7eb" name="Baseline" />
                  </BarChart>
                </ResponsiveContainer>
              </div>

              {/* Benchmark */}
              <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 flex items-start gap-3">
                <TrendingUp className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
                <div>
                  <div className="text-sm text-amber-900 mb-1 font-medium">Historical Benchmark</div>
                  <div className="text-sm text-amber-700">{event.visualData.benchmark}</div>
                </div>
              </div>
            </section>

            {/* Explainability Panel */}
            <section>
              <h3 className="text-gray-900 mb-4 flex items-center gap-2 font-semibold">
                <AlertTriangle className="w-5 h-5 text-purple-600" />
                Why the Agent Did This
              </h3>

              {/* Confidence Score */}
              <div className="bg-purple-50 border border-purple-200 rounded-lg p-4 mb-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-purple-900 font-medium">Confidence Score</span>
                  <span className="text-purple-700 font-semibold">{event.explainability.confidenceScore}%</span>
                </div>
                <div className="w-full bg-purple-200 rounded-full h-2">
                  <div
                    className="bg-purple-600 h-2 rounded-full transition-all"
                    style={{ width: `${event.explainability.confidenceScore}%` }}
                  />
                </div>
              </div>

              {/* Key Signals */}
              <div className="mb-4">
                <div className="text-sm text-gray-900 mb-3 font-medium">Key Signals Used</div>
                <div className="space-y-2">
                  {event.explainability.keySignals.map((signal, idx) => (
                    <div key={idx} className="flex items-start gap-2 text-sm">
                      <CheckCircle className="w-4 h-4 text-green-600 flex-shrink-0 mt-0.5" />
                      <span className="text-gray-700">{signal}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Tradeoffs */}
              <div className="mb-4">
                <div className="text-sm text-gray-900 mb-3 font-medium">Decision Tradeoffs</div>
                <div className="space-y-3">
                  {event.explainability.tradeoffs.map((tradeoff, idx) => (
                    <div key={idx} className="bg-gray-50 border border-gray-200 rounded-lg p-3">
                      <div className="flex items-center justify-between text-sm mb-1">
                        <span className="text-gray-600">{tradeoff.factor1}</span>
                        <span className="text-gray-400">vs</span>
                        <span className="text-gray-600">{tradeoff.factor2}</span>
                      </div>
                      <div className="text-xs text-blue-600">→ Prioritized: {tradeoff.chosen}</div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Rationale */}
              <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 mb-4">
                <div className="text-sm text-gray-900 mb-2 font-medium">Model Rationale</div>
                <div className="text-sm text-gray-700 leading-relaxed">{event.explainability.rationale}</div>
              </div>

              {/* Operational Context */}
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="text-sm text-gray-900 mb-3 font-medium">Operational Context</div>
                <div className="space-y-2">
                  {event.explainability.operationalContext.map((context, idx) => (
                    <div key={idx} className="text-sm text-gray-700 flex items-start gap-2">
                      <span className="text-blue-600">•</span>
                      {context}
                    </div>
                  ))}
                </div>
              </div>
            </section>
          </div>
        </div>

        {/* Actions Footer */}
        <div className="border-t border-gray-200 bg-gray-50 px-8 py-6">
          {/* Success/Rejection Messages */}
          {showApprovedMessage && (
            <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg flex items-center gap-3 animate-fade-in">
              <CheckCircle className="w-5 h-5 text-green-600" />
              <span className="text-green-800 font-medium">Action approved successfully!</span>
            </div>
          )}
          {showRejectedMessage && (
            <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center gap-3 animate-fade-in">
              <X className="w-5 h-5 text-red-600" />
              <span className="text-red-800 font-medium">Action rejected.</span>
            </div>
          )}

          <div className="flex items-center justify-between gap-4">
            <div className="flex gap-3">
              <button className="flex items-center gap-2 px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">
                <MessageSquare className="w-4 h-4" />
                Comment
              </button>
              <button className="flex items-center gap-2 px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">
                <Edit3 className="w-4 h-4" />
                Modify Parameters
              </button>
            </div>
            
            <div className="flex gap-3">
              {(event.status === 'requires-approval' || event.status === 'pending') && !isApproved && !isRejected && (
                <>
                  <button 
                    onClick={handleReject}
                    className="flex items-center gap-2 px-6 py-2 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                  >
                    <ThumbsDown className="w-4 h-4" />
                    Reject
                  </button>
                  <button 
                    onClick={handleApprove}
                    className="flex items-center gap-2 px-6 py-2 text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
                  >
                    <ThumbsUp className="w-4 h-4" />
                    {event.status === 'requires-approval' ? 'Approve Action' : 'Approve'}
                  </button>
                </>
              )}
              {isApproved && (
                <div className="flex items-center gap-2 px-6 py-2 bg-green-100 text-green-800 border border-green-300 rounded-lg">
                  <CheckCircle className="w-5 h-5" />
                  <span className="font-medium">Approved</span>
                </div>
              )}
              {isRejected && (
                <div className="flex items-center gap-2 px-6 py-2 bg-red-100 text-red-800 border border-red-300 rounded-lg">
                  <X className="w-5 h-5" />
                  <span className="font-medium">Rejected</span>
                </div>
              )}
              {event.status === 'completed' && !isApproved && !isRejected && (
                <button className="px-6 py-2 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">
                  Request Exception
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </>
  );
}

function MetricCard({ label, value, trend }: { label: string; value: string; trend: 'positive' | 'negative' | 'neutral' }) {
  const trendColors = {
    positive: 'text-green-700 bg-green-50 border-green-200',
    negative: 'text-red-700 bg-red-50 border-red-200',
    neutral: 'text-gray-700 bg-gray-50 border-gray-200'
  };

  return (
    <div className={`border rounded-lg p-4 ${trendColors[trend]}`}>
      <div className="text-xs mb-1 opacity-75">{label}</div>
      <div className="text-xl font-semibold">{value}</div>
    </div>
  );
}

function StatusBadge({ status }: { status: LogisticsEvent['status'] }) {
  const config = {
    completed: {
      label: 'Completed',
      className: 'bg-green-500 bg-opacity-20 text-white border-white border-opacity-30'
    },
    pending: {
      label: 'Pending',
      className: 'bg-yellow-500 bg-opacity-20 text-white border-white border-opacity-30'
    },
    'requires-approval': {
      label: 'Requires Approval',
      className: 'bg-orange-500 bg-opacity-20 text-white border-white border-opacity-30'
    }
  };

  const { label, className } = config[status];

  return (
    <div className={`px-3 py-1 rounded-full border text-sm ${className}`}>
      {label}
    </div>
  );
}

function TagBadge({ tag }: { tag: string }) {
  return (
    <span className="px-2.5 py-1 rounded-md bg-white bg-opacity-20 border border-white border-opacity-30 text-xs text-white">
      {tag}
    </span>
  );
}

