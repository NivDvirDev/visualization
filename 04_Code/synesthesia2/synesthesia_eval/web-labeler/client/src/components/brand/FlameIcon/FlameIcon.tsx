import React from 'react';

interface FlameIconProps {
  size?: number;
  className?: string;
  onClick?: () => void;
  animate?: boolean;
}

/**
 * FlameIcon — Compact SVG logo for headers
 * Imitates the Canva Wellspring design at small scale:
 * Teal elliptical water ripples, flames rising above, white glow center
 */
export function FlameIcon({ size = 40, className, onClick, animate = true }: FlameIconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 400 400"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      role="img"
      aria-label="Wellspring logo"
      className={className}
      onClick={onClick}
    >
      {animate && (
        <style>{`
          .fi-ripple1 { animation: fi-breathe 3.5s ease-in-out infinite; transform-origin: 200px 260px; }
          .fi-ripple2 { animation: fi-breathe 3.5s ease-in-out 0.5s infinite; transform-origin: 200px 250px; }
          .fi-ripple3 { animation: fi-breathe 3.5s ease-in-out 1s infinite; transform-origin: 200px 240px; }
          .fi-flame { animation: fi-flicker 2.5s ease-in-out infinite; }
          .fi-core { animation: fi-pulse 3s ease-in-out infinite; }

          @keyframes fi-breathe {
            0%, 100% { transform: scaleX(1); opacity: 1; }
            50% { transform: scaleX(1.025); opacity: 0.75; }
          }
          @keyframes fi-flicker {
            0%, 100% { opacity: 0.92; }
            30% { opacity: 1; }
            60% { opacity: 0.8; }
          }
          @keyframes fi-pulse {
            0%, 100% { opacity: 0.9; }
            50% { opacity: 1; }
          }
        `}</style>
      )}

      {/* === Light Rays — subtle behind flames === */}
      <g opacity="0.2">
        {Array.from({ length: 14 }, (_, i) => {
          const angle = -90 + (i * 12.86);
          const rad = (angle * Math.PI) / 180;
          const cx = 200, cy = 220;
          const r1 = 90, r2 = 155;
          return (
            <line
              key={i}
              x1={cx + r1 * Math.cos(rad)}
              y1={cy + r1 * Math.sin(rad)}
              x2={cx + r2 * Math.cos(rad)}
              y2={cy + r2 * Math.sin(rad)}
              stroke="#E8C87A"
              strokeWidth="1"
            />
          );
        })}
      </g>

      {/* === 7 Flame Tongues — symmetric, center tallest === */}

      {/* 1. Outermost Left */}
      <path
        className={animate ? 'fi-flame' : undefined}
        d="M 200,228 C 165,205 125,190 115,140 C 135,165 160,190 200,228 Z"
        fill="url(#fi-flameOuter)"
        opacity="0.88"
      />

      {/* 7. Outermost Right */}
      <path
        className={animate ? 'fi-flame' : undefined}
        d="M 200,228 C 235,205 275,190 285,140 C 265,165 240,190 200,228 Z"
        fill="url(#fi-flameOuter)"
        opacity="0.88"
      />

      {/* 2. Mid-Outer Left */}
      <path
        className={animate ? 'fi-flame' : undefined}
        d="M 200,225 C 175,195 148,170 145,115 C 160,150 178,185 200,225 Z"
        fill="url(#fi-flameMidOuter)"
        opacity="0.92"
      />

      {/* 6. Mid-Outer Right */}
      <path
        className={animate ? 'fi-flame' : undefined}
        d="M 200,225 C 225,195 252,170 255,115 C 240,150 222,185 200,225 Z"
        fill="url(#fi-flameMidOuter)"
        opacity="0.92"
      />

      {/* 3. Mid-Inner Left */}
      <path
        className={animate ? 'fi-flame' : undefined}
        d="M 200,222 C 185,192 168,162 168,100 C 178,140 190,180 200,222 Z"
        fill="url(#fi-flameMid)"
        opacity="0.95"
      />

      {/* 5. Mid-Inner Right */}
      <path
        className={animate ? 'fi-flame' : undefined}
        d="M 200,222 C 215,192 232,162 232,100 C 222,140 210,180 200,222 Z"
        fill="url(#fi-flameMid)"
        opacity="0.95"
      />

      {/* 4. Center Flame — tallest & widest */}
      <path
        className={animate ? 'fi-flame' : undefined}
        d="M 200,222 C 186,182 180,140 180,82 C 186,98 194,72 200,55 C 206,72 214,98 220,82 C 220,140 214,182 200,222 Z"
        fill="url(#fi-flameCenter)"
      />

      {/* === White Glow === */}
      <ellipse
        className={animate ? 'fi-core' : undefined}
        cx="200" cy="230"
        rx="55" ry="20"
        fill="url(#fi-centerGlow)"
      />

      {/* === Teal Water Ripples === */}
      <ellipse
        className={animate ? 'fi-ripple1' : undefined}
        cx="200" cy="260"
        rx="165" ry="45"
        stroke="url(#fi-tealGrad1)"
        strokeWidth="6"
        fill="none"
        opacity="0.7"
      />
      <ellipse
        className={animate ? 'fi-ripple2' : undefined}
        cx="200" cy="250"
        rx="120" ry="35"
        stroke="url(#fi-tealGrad2)"
        strokeWidth="5"
        fill="none"
        opacity="0.85"
      />
      <ellipse
        className={animate ? 'fi-ripple3' : undefined}
        cx="200" cy="240"
        rx="70" ry="22"
        stroke="url(#fi-tealGrad3)"
        strokeWidth="4"
        fill="none"
        opacity="1"
      />

      <defs>
        {/* Teal Water Gradients */}
        <linearGradient id="fi-tealGrad1" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stopColor="#1A7A7A" />
          <stop offset="50%" stopColor="#2BA5A5" />
          <stop offset="100%" stopColor="#1A7A7A" />
        </linearGradient>
        <linearGradient id="fi-tealGrad2" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stopColor="#1B8888" />
          <stop offset="50%" stopColor="#35B5B5" />
          <stop offset="100%" stopColor="#1B8888" />
        </linearGradient>
        <linearGradient id="fi-tealGrad3" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stopColor="#1D6B6B" />
          <stop offset="50%" stopColor="#2A9999" />
          <stop offset="100%" stopColor="#1D6B6B" />
        </linearGradient>

        {/* Flame Gradients */}
        <linearGradient id="fi-flameCenter" x1="200" y1="225" x2="200" y2="60" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="#FF6B35" />
          <stop offset="30%" stopColor="#FFB627" />
          <stop offset="60%" stopColor="#FFE082" />
          <stop offset="85%" stopColor="#FFF8E1" />
          <stop offset="100%" stopColor="#FFFFFF" />
        </linearGradient>
        <linearGradient id="fi-flameMidOuter" x1="200" y1="225" x2="200" y2="115" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="#E65100" />
          <stop offset="40%" stopColor="#FF6B35" />
          <stop offset="80%" stopColor="#FF8F00" />
          <stop offset="100%" stopColor="#FFB627" />
        </linearGradient>
        <linearGradient id="fi-flameMid" x1="200" y1="225" x2="200" y2="110" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="#FF6B35" />
          <stop offset="40%" stopColor="#FF8F00" />
          <stop offset="80%" stopColor="#FFB627" />
          <stop offset="100%" stopColor="#FFE082" />
        </linearGradient>
        <linearGradient id="fi-flameOuter" x1="200" y1="230" x2="200" y2="130" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="#D84315" />
          <stop offset="40%" stopColor="#E65100" />
          <stop offset="80%" stopColor="#FF6B35" />
          <stop offset="100%" stopColor="#FF8A65" />
        </linearGradient>

        {/* Center Glow */}
        <radialGradient id="fi-centerGlow" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="#FFFFFF" stopOpacity="0.95" />
          <stop offset="40%" stopColor="#FFF8E1" stopOpacity="0.7" />
          <stop offset="70%" stopColor="#B2EBF2" stopOpacity="0.3" />
          <stop offset="100%" stopColor="#1A8A8A" stopOpacity="0" />
        </radialGradient>
      </defs>
    </svg>
  );
}
