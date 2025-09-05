import React from 'react';

interface LineChartDataPoint {
  label: string;
  value: number;
  target?: number;
}

interface LineChartProps {
  data: LineChartDataPoint[];
  title: string;
  height?: number;
  showTarget?: boolean;
  valueFormatter?: (value: number) => string;
  color?: string;
}

export function LineChart({ 
  data, 
  title, 
  height = 200,
  showTarget = false,
  valueFormatter = (value) => value.toLocaleString(),
  color = 'rgb(59, 130, 246)' // blue-500
}: LineChartProps) {
  if (!data.length) return null;

  const maxValue = Math.max(...data.map(d => Math.max(d.value, d.target || 0)));
  const minValue = Math.min(...data.map(d => Math.min(d.value, d.target || 0)));
  const range = maxValue - minValue;
  const chartHeight = height - 60; // Leave space for labels

  const getY = (value: number) => {
    return chartHeight - ((value - minValue) / range) * chartHeight;
  };

  const getX = (index: number) => {
    return (index / (data.length - 1)) * 100;
  };

  // Generate path for actual values
  const actualPath = data.map((point, index) => {
    const x = getX(index);
    const y = getY(point.value);
    return `${index === 0 ? 'M' : 'L'} ${x} ${y}`;
  }).join(' ');

  // Generate path for target values if enabled
  const targetPath = showTarget ? data.map((point, index) => {
    const x = getX(index);
    const y = getY(point.target || 0);
    return `${index === 0 ? 'M' : 'L'} ${x} ${y}`;
  }).join(' ') : '';

  return (
    <div className="bg-white p-6 rounded-lg shadow-sm border">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">{title}</h3>
      
      <div className="relative">
        <svg width="100%" height={height} className="overflow-visible">
          {/* Grid lines */}
          <defs>
            <pattern id="grid" width="20" height="20" patternUnits="userSpaceOnUse">
              <path d="M 20 0 L 0 0 0 20" fill="none" stroke="#f3f4f6" strokeWidth="1"/>
            </pattern>
          </defs>
          <rect width="100%" height={chartHeight} fill="url(#grid)" />
          
          {/* Target line */}
          {showTarget && targetPath && (
            <path
              d={targetPath}
              fill="none"
              stroke="#9ca3af"
              strokeWidth="2"
              strokeDasharray="5,5"
              vectorEffect="non-scaling-stroke"
            />
          )}
          
          {/* Actual line */}
          <path
            d={actualPath}
            fill="none"
            stroke={color}
            strokeWidth="3"
            strokeLinecap="round"
            strokeLinejoin="round"
            vectorEffect="non-scaling-stroke"
          />
          
          {/* Data points */}
          {data.map((point, index) => (
            <g key={index}>
              <circle
                cx={`${getX(index)}%`}
                cy={getY(point.value)}
                r="4"
                fill={color}
                stroke="white"
                strokeWidth="2"
              />
              
              {/* Hover tooltip */}
              <g className="opacity-0 hover:opacity-100 transition-opacity">
                <rect
                  x={`${getX(index)}%`}
                  y={getY(point.value) - 30}
                  width="60"
                  height="20"
                  rx="4"
                  fill="rgba(0,0,0,0.8)"
                  transform="translate(-30, 0)"
                />
                <text
                  x={`${getX(index)}%`}
                  y={getY(point.value) - 15}
                  textAnchor="middle"
                  className="text-xs fill-white"
                >
                  {valueFormatter(point.value)}
                </text>
              </g>
            </g>
          ))}
          
          {/* X-axis labels */}
          {data.map((point, index) => (
            <text
              key={index}
              x={`${getX(index)}%`}
              y={height - 10}
              textAnchor="middle"
              className="text-xs fill-gray-600"
            >
              {point.label}
            </text>
          ))}
        </svg>
        
        {/* Y-axis labels */}
        <div className="absolute left-0 top-0 h-full flex flex-col justify-between text-xs text-gray-600 -ml-12">
          <span>{valueFormatter(maxValue)}</span>
          <span>{valueFormatter((maxValue + minValue) / 2)}</span>
          <span>{valueFormatter(minValue)}</span>
        </div>
      </div>
      
      {showTarget && (
        <div className="flex items-center justify-center mt-4 text-sm text-gray-600">
          <div className="flex items-center">
            <div className="w-4 h-0 border-t-2 border-dashed border-gray-400 mr-2"></div>
            <span>Target</span>
          </div>
          <div className="flex items-center ml-4">
            <div className="w-4 h-0 border-t-2" style={{ borderColor: color }}></div>
            <span className="ml-2">Actual</span>
          </div>
        </div>
      )}
    </div>
  );
}