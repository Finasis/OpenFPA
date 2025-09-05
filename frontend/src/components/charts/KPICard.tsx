import React from 'react';

interface KPICardProps {
  title: string;
  value: number;
  target?: number;
  unit?: string;
  trend?: 'up' | 'down' | 'stable';
  trendValue?: number;
  status?: 'good' | 'warning' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  valueFormatter?: (value: number) => string;
}

export function KPICard({
  title,
  value,
  target,
  unit = '',
  trend,
  trendValue,
  status = 'good',
  size = 'md',
  valueFormatter
}: KPICardProps) {
  const formatValue = valueFormatter || ((val: number) => {
    if (val >= 1000000) return `${(val / 1000000).toFixed(1)}M`;
    if (val >= 1000) return `${(val / 1000).toFixed(1)}K`;
    return val.toFixed(1);
  });

  const sizeClasses = {
    sm: 'p-4',
    md: 'p-6', 
    lg: 'p-8'
  };

  const titleSizes = {
    sm: 'text-sm',
    md: 'text-base',
    lg: 'text-lg'
  };

  const valueSizes = {
    sm: 'text-2xl',
    md: 'text-3xl',
    lg: 'text-4xl'
  };

  const statusColors = {
    good: 'border-l-green-500 bg-green-50',
    warning: 'border-l-yellow-500 bg-yellow-50',
    danger: 'border-l-red-500 bg-red-50'
  };

  const statusTextColors = {
    good: 'text-green-700',
    warning: 'text-yellow-700',
    danger: 'text-red-700'
  };

  const trendIcons = {
    up: '↗',
    down: '↘',
    stable: '→'
  };

  const trendColors = {
    up: 'text-green-600',
    down: 'text-red-600',
    stable: 'text-gray-600'
  };

  const variance = target ? ((value - target) / target) * 100 : null;

  return (
    <div className={`bg-white rounded-lg shadow-sm border-l-4 ${statusColors[status]} ${sizeClasses[size]}`}>
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <h3 className={`font-medium text-gray-900 ${titleSizes[size]}`}>
            {title}
          </h3>
          
          <div className={`font-bold ${statusTextColors[status]} ${valueSizes[size]} mt-2`}>
            {formatValue(value)}{unit}
          </div>

          <div className="flex items-center space-x-4 mt-3">
            {/* Trend indicator */}
            {trend && trendValue && (
              <div className={`flex items-center text-sm ${trendColors[trend]}`}>
                <span className="text-lg mr-1">{trendIcons[trend]}</span>
                <span className="font-medium">
                  {Math.abs(trendValue).toFixed(1)}%
                </span>
              </div>
            )}

            {/* Target comparison */}
            {target && (
              <div className="text-sm text-gray-600">
                <span className="font-medium">Target: </span>
                {formatValue(target)}{unit}
                {variance && (
                  <span className={`ml-2 font-medium ${variance >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    ({variance >= 0 ? '+' : ''}{variance.toFixed(1)}%)
                  </span>
                )}
              </div>
            )}
          </div>

          {/* Progress bar for target achievement */}
          {target && (
            <div className="mt-3">
              <div className="flex items-center justify-between text-xs text-gray-600 mb-1">
                <span>Progress to Target</span>
                <span>{((value / target) * 100).toFixed(0)}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className={`h-2 rounded-full transition-all duration-500 ${
                    value >= target ? 'bg-green-500' : value >= target * 0.8 ? 'bg-yellow-500' : 'bg-red-500'
                  }`}
                  style={{ width: `${Math.min((value / target) * 100, 100)}%` }}
                />
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}