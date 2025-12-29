import { ArrowRight, CheckCircle, Clock, AlertCircle, ChevronRight, ThumbsUp, ThumbsDown, X } from 'lucide-react';
import { useState, useEffect } from 'react';
import type { LogisticsEvent } from '../types/activity';
import { approveEvent, rejectEvent, isEventApproved, isEventRejected, EVENT_STATE_CHANGED } from '@/lib/sessionState';

interface EventCardProps {
  event: LogisticsEvent;
  onClick: () => void;
}

export function EventCard({ event, onClick }: EventCardProps) {
  const [isApproved, setIsApproved] = useState(false);
  const [isRejected, setIsRejected] = useState(false);

  useEffect(() => {
    setIsApproved(isEventApproved(event.id));
    setIsRejected(isEventRejected(event.id));
  }, [event.id]);

  // Listen for state changes from other components
  useEffect(() => {
    const handleStateChange = (e: Event) => {
      const customEvent = e as CustomEvent;
      if (customEvent.detail.eventId === event.id) {
        setIsApproved(isEventApproved(event.id));
        setIsRejected(isEventRejected(event.id));
      }
    };

    window.addEventListener(EVENT_STATE_CHANGED, handleStateChange);
    return () => window.removeEventListener(EVENT_STATE_CHANGED, handleStateChange);
  }, [event.id]);

  const handleApprove = (e: React.MouseEvent) => {
    e.stopPropagation();
    approveEvent(event.id);
    setIsApproved(true);
    setIsRejected(false);
  };

  const handleReject = (e: React.MouseEvent) => {
    e.stopPropagation();
    rejectEvent(event.id);
    setIsRejected(true);
    setIsApproved(false);
  };
  return (
    <div
      onClick={onClick}
      className="bg-white rounded-lg border border-gray-200 p-6 hover:border-blue-300 hover:shadow-md transition-all cursor-pointer group"
    >
      {/* Header Row */}
      <div className="flex items-start justify-between gap-4 mb-3">
        <div className="flex-1">
          <h3 className="text-gray-900 group-hover:text-blue-700 transition-colors font-semibold">
            {event.title}
          </h3>
        </div>
        <div className="flex items-center gap-2">
          {isApproved && (
            <div className="flex items-center gap-1.5 px-2.5 py-1 bg-green-100 text-green-700 border border-green-200 rounded-full text-xs font-medium">
              <CheckCircle className="w-3.5 h-3.5" />
              Approved
            </div>
          )}
          {isRejected && (
            <div className="flex items-center gap-1.5 px-2.5 py-1 bg-red-100 text-red-700 border border-red-200 rounded-full text-xs font-medium">
              <X className="w-3.5 h-3.5" />
              Rejected
            </div>
          )}
          {!isApproved && !isRejected && <StatusBadge status={event.status} />}
          <ChevronRight className="w-5 h-5 text-gray-400 group-hover:text-blue-600 transition-colors" />
        </div>
      </div>

      {/* Summary */}
      <p className="text-gray-600 mb-4 text-sm">{event.summary}</p>

      {/* Situation → Action → Outcome */}
      <div className="bg-blue-50 border border-blue-100 rounded-lg p-4 mb-4">
        <div className="flex items-center gap-3 text-sm">
          <div className="flex-1">
            <div className="text-gray-500 text-xs mb-1">Situation</div>
            <div className="text-gray-900 text-xs">{event.situation}</div>
          </div>
          <ArrowRight className="w-4 h-4 text-blue-400 flex-shrink-0" />
          <div className="flex-1">
            <div className="text-gray-500 text-xs mb-1">Action</div>
            <div className="text-gray-900 text-xs">{event.action}</div>
          </div>
          <ArrowRight className="w-4 h-4 text-blue-400 flex-shrink-0" />
          <div className="flex-1">
            <div className="text-gray-500 text-xs mb-1">Expected Outcome</div>
            <div className="text-gray-900 text-xs">{event.expectedOutcome}</div>
          </div>
        </div>
      </div>

      {/* Tags */}
      <div className="flex flex-wrap gap-2 mb-4">
        {event.tags.map((tag) => (
          <TagBadge key={tag} tag={tag} />
        ))}
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between pt-4 border-t border-gray-100">
        <div className="flex items-center gap-4 text-sm text-gray-600">
          <div className="flex items-center gap-1.5">
            <Clock className="w-4 h-4" />
            {event.timestamp}
          </div>
          <div className="text-gray-400">•</div>
          <div className="text-xs">{event.agentName}</div>
        </div>

        <div className="flex gap-2">
          {(event.status === 'requires-approval' || event.status === 'pending') && !isApproved && !isRejected && (
            <>
              <button
                onClick={handleReject}
                className="flex items-center gap-1.5 px-3 py-1.5 text-sm text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
              >
                <ThumbsDown className="w-3.5 h-3.5" />
                Reject
              </button>
              <button
                onClick={handleApprove}
                className="flex items-center gap-1.5 px-3 py-1.5 text-sm text-white bg-blue-600 rounded-md hover:bg-blue-700 transition-colors"
              >
                <ThumbsUp className="w-3.5 h-3.5" />
                Approve
              </button>
            </>
          )}
          <button
            className="px-3 py-1.5 text-sm text-blue-600 bg-blue-50 rounded-md hover:bg-blue-100 transition-colors"
          >
            View Details
          </button>
        </div>
      </div>
    </div>
  );
}

function StatusBadge({ status }: { status: LogisticsEvent['status'] }) {
  const config = {
    completed: {
      icon: <CheckCircle className="w-4 h-4" />,
      label: 'Completed',
      className: 'bg-green-100 text-green-700 border-green-200'
    },
    pending: {
      icon: <Clock className="w-4 h-4" />,
      label: 'Pending',
      className: 'bg-yellow-100 text-yellow-700 border-yellow-200'
    },
    'requires-approval': {
      icon: <AlertCircle className="w-4 h-4" />,
      label: 'Requires Approval',
      className: 'bg-orange-100 text-orange-700 border-orange-200'
    }
  };

  const { icon, label, className } = config[status];

  return (
    <div className={`flex items-center gap-1.5 px-3 py-1 rounded-full border text-xs ${className}`}>
      {icon}
      {label}
    </div>
  );
}

function TagBadge({ tag }: { tag: string }) {
  const colorMap: Record<string, string> = {
    'Revenue': 'bg-emerald-100 text-emerald-700 border-emerald-200',
    'Efficiency': 'bg-blue-100 text-blue-700 border-blue-200',
    'NPS': 'bg-purple-100 text-purple-700 border-purple-200',
    'SLA Risk': 'bg-red-100 text-red-700 border-red-200',
    'Forecast': 'bg-indigo-100 text-indigo-700 border-indigo-200',
    'Anomaly': 'bg-amber-100 text-amber-700 border-amber-200',
    'Quote': 'bg-cyan-100 text-cyan-700 border-cyan-200',
    'External': 'bg-orange-100 text-orange-700 border-orange-200',
  };

  return (
    <span className={`px-2.5 py-1 rounded-md border text-xs ${colorMap[tag] || 'bg-gray-100 text-gray-700 border-gray-200'}`}>
      {tag}
    </span>
  );
}

