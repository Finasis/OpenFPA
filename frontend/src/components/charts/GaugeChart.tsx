import React from 'react';

interface GaugeChartProps {
  value: number;
  max: number;
  min?: number;
  title: string;
  subtitle?: string;
  color?: 'green' | 'blue' | 'red' | 'yellow' | 'purple';
  size?: 'sm' | 'md' | 'lg';
}

export function GaugeChart({ 
  value, 
  max, 
  min = 0, 
  title, 
  subtitle,
  color = 'blue',
  size = 'md'
}: GaugeChartProps) {
  const percentage = Math.min(Math.max(((value - min) / (max - min)) * 100, 0), 100);
  const rotation = (percentage / 100) * 180 - 90; // -90 to 90 degrees
  
  const sizeClasses = {
    sm: 'w-24 h-12',
    md: 'w-32 h-16', 
    lg: 'w-40 h-20'
  };
  
  const textSizes = {
    sm: { title: 'text-xs', value: 'text-lg', subtitle: 'text-xs' },
    md: { title: 'text-sm', value: 'text-xl', subtitle: 'text-xs' },
    lg: { title: 'text-base', value: 'text-2xl', subtitle: 'text-sm' }
  };
  
  const colors = {
    green: 'text-green-600 stroke-green-500',
    blue: 'text-blue-600 stroke-blue-500', 
    red: 'text-red-600 stroke-red-500',
    yellow: 'text-yellow-600 stroke-yellow-500',
    purple: 'text-purple-600 stroke-purple-500'
  };

  return (
    <div className="flex flex-col items-center p-4 bg-white rounded-lg shadow-sm border">
      <h3 className={`font-semibold text-gray-900 mb-2 text-center ${textSizes[size].title}`}>
        {title}
      </h3>
      
      <div className={`relative ${sizeClasses[size]} mb-2`}>
        <svg className="w-full h-full" viewBox="0 0 100 50">
          {/* Background arc */}
          <path
            d="M 10 40 A 30 30 0 0 1 90 40"
            fill="none"
            stroke="#e5e7eb"
            strokeWidth="8"
            strokeLinecap="round"
          />
          
          {/* Progress arc */}
          <path
            d="M 10 40 A 30 30 0 0 1 90 40"
            fill="none"
            className={colors[color] ? colors[color].split(' ')[1] : 'stroke-blue-500'}
            strokeWidth="8"
            strokeLinecap="round"
            strokeDasharray={`${(percentage / 100) * 126} 126`}
            style={{ transition: 'stroke-dasharray 0.5s ease-in-out' }}
          />
          
          {/* Center dot */}
          <circle
            cx="50"
            cy="40"
            r="2"
            fill="#6b7280"
          />
          
          {/* Needle */}
          <line
            x1="50"
            y1="40"
            x2="35"
            y2="40"
            stroke="#374151"
            strokeWidth="2"
            strokeLinecap="round"
            transform={`rotate(${rotation} 50 40)`}
            style={{ transition: 'transform 0.5s ease-in-out' }}
          />
        </svg>
        
        {/* Min/Max labels */}
        <div className="absolute bottom-0 left-0 text-xs text-gray-500">
          {min}
        </div>
        <div className="absolute bottom-0 right-0 text-xs text-gray-500">
          {max}
        </div>
      </div>
      
      <div className={`font-bold ${colors[color] ? colors[color].split(' ')[0] : 'text-blue-600'} ${textSizes[size].value}`}>
        {typeof value === 'number' ? value.toFixed(1) : value}
      </div>
      
      {subtitle && (
        <div className={`text-gray-600 text-center mt-1 ${textSizes[size].subtitle}`}>
          {subtitle}
        </div>
      )}
    </div>
  );
}