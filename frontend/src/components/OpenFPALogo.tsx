interface OpenFPALogoProps {
  className?: string;
  size?: 'sm' | 'md' | 'lg';
}

export default function OpenFPALogo({ className = '', size = 'md' }: OpenFPALogoProps) {
  const sizeClasses = {
    sm: 'w-32 h-12',
    md: 'w-48 h-18',
    lg: 'w-64 h-24'
  };

  return (
    <div className={`flex items-center ${sizeClasses[size]} ${className}`}>
      <svg
        viewBox="0 0 240 72"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="w-full h-full"
      >
        {/* Background circle for the icon */}
        <circle cx="36" cy="36" r="32" fill="#3B82F6" />
        
        {/* Chart/Analytics icon */}
        <g transform="translate(16, 16)">
          {/* Bar chart bars */}
          <rect x="6" y="28" width="6" height="12" fill="white" rx="1" />
          <rect x="15" y="20" width="6" height="20" fill="white" rx="1" />
          <rect x="24" y="24" width="6" height="16" fill="white" rx="1" />
          <rect x="33" y="16" width="6" height="24" fill="white" rx="1" />
          
          {/* Trend line */}
          <path
            d="M6 30 L18 22 L27 26 L36 18"
            stroke="white"
            strokeWidth="2"
            strokeLinecap="round"
            fill="none"
          />
          
          {/* Data points */}
          <circle cx="6" cy="30" r="2" fill="#EF4444" />
          <circle cx="18" cy="22" r="2" fill="#10B981" />
          <circle cx="27" cy="26" r="2" fill="#F59E0B" />
          <circle cx="36" cy="18" r="2" fill="#8B5CF6" />
        </g>
        
        {/* OpenFPA text */}
        <g>
          {/* "Open" text */}
          <text
            x="80"
            y="28"
            fontFamily="Inter, system-ui, sans-serif"
            fontSize="20"
            fontWeight="700"
            fill="#1F2937"
          >
            Open
          </text>
          
          {/* "FP&A" text */}
          <text
            x="80"
            y="50"
            fontFamily="Inter, system-ui, sans-serif"
            fontSize="24"
            fontWeight="800"
            fill="#3B82F6"
          >
            FP&A
          </text>
        </g>
        
        {/* Subtitle */}
        <text
          x="160"
          y="32"
          fontFamily="Inter, system-ui, sans-serif"
          fontSize="11"
          fill="#6B7280"
        >
          Financial Planning
        </text>
        <text
          x="160"
          y="46"
          fontFamily="Inter, system-ui, sans-serif"
          fontSize="11"
          fill="#6B7280"
        >
          & Analysis
        </text>
      </svg>
    </div>
  );
}