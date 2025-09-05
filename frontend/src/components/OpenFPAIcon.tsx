interface OpenFPAIconProps {
  className?: string;
  size?: number;
}

export default function OpenFPAIcon({ className = '', size = 36 }: OpenFPAIconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 72 72"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      {/* Background circle */}
      <circle cx="36" cy="36" r="36" fill="#3B82F6" />
      
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
    </svg>
  );
}