import React from 'react';

interface BarChartData {
  label: string;
  value: number;
  target?: number;
  color?: string;
}

interface BarChartProps {
  data: BarChartData[];
  title: string;
  height?: number;
  showTargets?: boolean;
  valueFormatter?: (value: number) => string;
}

export function BarChart({ 
  data, 
  title, 
  height = 300, 
  showTargets = false,
  valueFormatter = (value) => value.toLocaleString()
}: BarChartProps) {
  const maxValue = Math.max(
    ...data.map(d => Math.max(d.value, d.target || 0))
  );
  
  const colors = [
    'bg-blue-500',
    'bg-green-500', 
    'bg-purple-500',
    'bg-yellow-500',
    'bg-red-500',
    'bg-indigo-500',
    'bg-pink-500',
    'bg-gray-500'
  ];

  return (
    <div className="bg-white p-6 rounded-lg shadow-sm border">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">{title}</h3>
      
      <div className="relative" style={{ height }}>
        <div className="flex items-end justify-between h-full space-x-2">
          {data.map((item, index) => {
            const barHeight = (item.value / maxValue) * (height - 60);
            const targetHeight = showTargets && item.target 
              ? (item.target / maxValue) * (height - 60)
              : 0;
            
            return (
              <div key={item.label} className="flex flex-col items-center flex-1">
                <div className="relative w-full max-w-16 mb-2">
                  {/* Target line */}
                  {showTargets && item.target && (
                    <div 
                      className="absolute w-full border-t-2 border-dashed border-gray-400 z-10"
                      style={{ 
                        bottom: `${targetHeight}px`,
                        height: '2px'
                      }}
                      title={`Target: ${valueFormatter(item.target)}`}
                    />
                  )}
                  
                  {/* Bar */}
                  <div
                    className={`${item.color || colors[index % colors.length]} w-full rounded-t transition-all duration-500 ease-out flex items-end justify-center pb-1`}
                    style={{ height: `${Math.max(barHeight, 4)}px` }}
                  >
                    <span className="text-white text-xs font-medium">
                      {valueFormatter(item.value)}
                    </span>
                  </div>
                </div>
                
                {/* Label */}
                <div className="text-xs text-gray-600 text-center font-medium max-w-16">
                  {item.label}
                </div>
              </div>
            );
          })}
        </div>
      </div>
      
      {showTargets && (
        <div className="flex items-center justify-center mt-4 text-sm text-gray-600">
          <div className="flex items-center">
            <div className="w-4 h-0 border-t-2 border-dashed border-gray-400 mr-2"></div>
            <span>Target</span>
          </div>
        </div>
      )}
    </div>
  );
}