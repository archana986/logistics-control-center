interface LegendProps {
  viewMode?: 'congestion' | 'capacity';
}

export default function Legend({ viewMode = 'congestion' }: LegendProps) {
  return (
    <div className="absolute bottom-6 left-6 bg-card/95 backdrop-blur-sm border rounded-lg shadow-lg p-4 text-sm z-10">
      <div className="font-semibold mb-3">
        {viewMode === 'capacity' ? 'Capacity Utilization' : 'Network Flow Status'}
      </div>
      
      {viewMode === 'capacity' ? (
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <div className="w-8 h-1 rounded-full" style={{ backgroundColor: 'rgb(34, 197, 94)' }}></div>
            <span className="text-muted-foreground">Underutilized (&lt; 70%)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-8 h-1 rounded-full" style={{ backgroundColor: 'rgb(59, 130, 246)' }}></div>
            <span className="text-muted-foreground">Optimal (70-85%)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-8 h-1 rounded-full" style={{ backgroundColor: 'rgb(250, 204, 21)' }}></div>
            <span className="text-muted-foreground">Approaching (85-95%)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-8 h-1 rounded-full" style={{ backgroundColor: 'rgb(239, 68, 68)' }}></div>
            <span className="text-muted-foreground">Overcapacity (&gt; 95%)</span>
          </div>
        </div>
      ) : (
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <div className="w-8 h-1 rounded-full" style={{ backgroundColor: 'rgb(34, 197, 94)' }}></div>
            <span className="text-muted-foreground">On-time (&lt; 45m delay)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-8 h-1 rounded-full" style={{ backgroundColor: 'rgb(250, 204, 21)' }}></div>
            <span className="text-muted-foreground">Caution (45-90m delay)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-8 h-1 rounded-full" style={{ backgroundColor: 'rgb(239, 68, 68)' }}></div>
            <span className="text-muted-foreground">At-risk (&gt; 90m delay)</span>
          </div>
        </div>
      )}
      <div className="mt-4 pt-3 border-t">
        <div className="font-semibold mb-2">Lane Types</div>
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <svg width="32" height="16" className="flex-shrink-0">
              <path d="M 2 14 Q 16 2, 30 14" stroke="currentColor" strokeWidth="1.5" fill="none" />
            </svg>
            <span className="text-muted-foreground">Air (curved)</span>
          </div>
          <div className="flex items-center gap-2">
            <svg width="32" height="16" className="flex-shrink-0">
              <line x1="2" y1="8" x2="30" y2="8" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
            </svg>
            <span className="text-muted-foreground">Ground (flat, thicker)</span>
          </div>
        </div>
      </div>
      <div className="mt-4 pt-3 border-t">
        <div className="font-semibold mb-2">Hub Types</div>
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full" style={{ backgroundColor: 'rgb(147, 51, 234)' }}></div>
            <span className="text-muted-foreground">Air Hub</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full" style={{ backgroundColor: 'rgb(59, 130, 246)' }}></div>
            <span className="text-muted-foreground">Distribution Center</span>
          </div>
        </div>
      </div>
    </div>
  );
}

