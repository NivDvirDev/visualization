import React from 'react';

interface WellspringIconProps {
  size?: number;
  className?: string;
  animate?: boolean;
}

/**
 * WellspringIcon — Pure SVG geometric construction
 * Imitates the Canva Wellspring design:
 * Teal elliptical water ripples at bottom, flames rising above,
 * white glow at center, light rays emanating behind
 */
export function WellspringIcon({ size = 80, className, animate = true }: WellspringIconProps) {
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
    >
      {animate && (
        <style>{`
          .wl-ripple1 { animation: wl-breathe 4s ease-in-out infinite; transform-origin: 200px 260px; }
          .wl-ripple2 { animation: wl-breathe 4s ease-in-out 0.6s infinite; transform-origin: 200px 250px; }
          .wl-ripple3 { animation: wl-breathe 4s ease-in-out 1.2s infinite; transform-origin: 200px 240px; }
          .wl-flame-c { animation: wl-flicker-c 3s ease-in-out infinite; transform-origin: 200px 200px; }
          .wl-flame-ml { animation: wl-flicker 2.6s ease-in-out 0.3s infinite; }
          .wl-flame-mr { animation: wl-flicker 2.6s ease-in-out 0.6s infinite; }
          .wl-flame-ol { animation: wl-flicker 3s ease-in-out 0.15s infinite; }
          .wl-flame-or { animation: wl-flicker 3s ease-in-out 0.45s infinite; }
          .wl-core { animation: wl-pulse 3s ease-in-out infinite; }
          .wl-rays { animation: wl-ray-pulse 4s ease-in-out infinite; }

          @keyframes wl-breathe {
            0%, 100% { transform: scaleX(1); opacity: 1; }
            50% { transform: scaleX(1.03); opacity: 0.7; }
          }
          @keyframes wl-flicker-c {
            0%, 100% { transform: scaleY(1); }
            50% { transform: scaleY(1.04); }
          }
          @keyframes wl-flicker {
            0%, 100% { opacity: 0.92; }
            25% { opacity: 1; }
            60% { opacity: 0.78; }
          }
          @keyframes wl-pulse {
            0%, 100% { opacity: 0.9; }
            50% { opacity: 1; }
          }
          @keyframes wl-ray-pulse {
            0%, 100% { opacity: 0.25; }
            50% { opacity: 0.4; }
          }
        `}</style>
      )}

      {/* === Light Rays — behind everything === */}
      <g className={animate ? 'wl-rays' : undefined} opacity="0.25">
        {Array.from({ length: 18 }, (_, i) => {
          const angle = -90 + (i * 10);
          const rad = (angle * Math.PI) / 180;
          const cx = 200, cy = 220;
          const r1 = 100, r2 = 165;
          return (
            <line
              key={i}
              x1={cx + r1 * Math.cos(rad)}
              y1={cy + r1 * Math.sin(rad)}
              x2={cx + r2 * Math.cos(rad)}
              y2={cy + r2 * Math.sin(rad)}
              stroke="#E8C87A"
              strokeWidth="0.8"
            />
          );
        })}
      </g>

      {/* === 7 Flame Tongues — symmetric, center tallest === */}

      {/* 1. Outermost Left — curling, dark red-orange */}
      <path
        className={animate ? 'wl-flame-ol' : undefined}
        d="M 200,228 C 165,205 125,190 115,140 C 135,165 160,190 200,228 Z"
        fill="url(#wl-flameOuter)"
        opacity="0.88"
      />

      {/* 7. Outermost Right — curling, dark red-orange */}
      <path
        className={animate ? 'wl-flame-or' : undefined}
        d="M 200,228 C 235,205 275,190 285,140 C 265,165 240,190 200,228 Z"
        fill="url(#wl-flameOuter)"
        opacity="0.88"
      />

      {/* 2. Mid-Outer Left — red to orange */}
      <path
        className={animate ? 'wl-flame-ml' : undefined}
        d="M 200,225 C 175,195 148,170 145,115 C 160,150 178,185 200,225 Z"
        fill="url(#wl-flameMidOuter)"
        opacity="0.92"
      />

      {/* 6. Mid-Outer Right — red to orange */}
      <path
        className={animate ? 'wl-flame-mr' : undefined}
        d="M 200,225 C 225,195 252,170 255,115 C 240,150 222,185 200,225 Z"
        fill="url(#wl-flameMidOuter)"
        opacity="0.92"
      />

      {/* 3. Mid-Inner Left — orange to yellow */}
      <path
        className={animate ? 'wl-flame-ml' : undefined}
        d="M 200,222 C 185,192 168,162 168,100 C 178,140 190,180 200,222 Z"
        fill="url(#wl-flameMid)"
        opacity="0.95"
      />

      {/* 5. Mid-Inner Right — orange to yellow */}
      <path
        className={animate ? 'wl-flame-mr' : undefined}
        d="M 200,222 C 215,192 232,162 232,100 C 222,140 210,180 200,222 Z"
        fill="url(#wl-flameMid)"
        opacity="0.95"
      />

      {/* 4. Center Flame — tallest & widest, white-hot → yellow → orange */}
      <path
        className={animate ? 'wl-flame-c' : undefined}
        d="M 200,222 C 186,182 180,140 180,82 C 186,98 194,72 200,55 C 206,72 214,98 220,82 C 220,140 214,182 200,222 Z"
        fill="url(#wl-flameCenter)"
      />

      {/* === White Glow — where fire meets water === */}
      <ellipse
        className={animate ? 'wl-core' : undefined}
        cx="200" cy="230"
        rx="55" ry="20"
        fill="url(#wl-centerGlow)"
      />

      {/* === Teal Water Ripples — elliptical, perspective view === */}

      {/* Outer ripple — largest, lightest */}
      <ellipse
        className={animate ? 'wl-ripple1' : undefined}
        cx="200" cy="260"
        rx="165" ry="45"
        stroke="url(#wl-tealGrad1)"
        strokeWidth="6"
        fill="none"
        opacity="0.7"
      />

      {/* Middle ripple */}
      <ellipse
        className={animate ? 'wl-ripple2' : undefined}
        cx="200" cy="250"
        rx="120" ry="35"
        stroke="url(#wl-tealGrad2)"
        strokeWidth="5"
        fill="none"
        opacity="0.85"
      />

      {/* Inner ripple — smallest, most opaque */}
      <ellipse
        className={animate ? 'wl-ripple3' : undefined}
        cx="200" cy="240"
        rx="70" ry="22"
        stroke="url(#wl-tealGrad3)"
        strokeWidth="4"
        fill="none"
        opacity="1"
      />

      <defs>
        {/* Teal Water Gradients */}
        <linearGradient id="wl-tealGrad1" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stopColor="#1A7A7A" />
          <stop offset="50%" stopColor="#2BA5A5" />
          <stop offset="100%" stopColor="#1A7A7A" />
        </linearGradient>
        <linearGradient id="wl-tealGrad2" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stopColor="#1B8888" />
          <stop offset="50%" stopColor="#35B5B5" />
          <stop offset="100%" stopColor="#1B8888" />
        </linearGradient>
        <linearGradient id="wl-tealGrad3" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stopColor="#1D6B6B" />
          <stop offset="50%" stopColor="#2A9999" />
          <stop offset="100%" stopColor="#1D6B6B" />
        </linearGradient>

        {/* Flame Gradients */}
        <linearGradient id="wl-flameCenter" x1="200" y1="225" x2="200" y2="60" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="#FF6B35" />
          <stop offset="30%" stopColor="#FFB627" />
          <stop offset="60%" stopColor="#FFE082" />
          <stop offset="85%" stopColor="#FFF8E1" />
          <stop offset="100%" stopColor="#FFFFFF" />
        </linearGradient>
        <linearGradient id="wl-flameMidOuter" x1="200" y1="225" x2="200" y2="115" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="#E65100" />
          <stop offset="40%" stopColor="#FF6B35" />
          <stop offset="80%" stopColor="#FF8F00" />
          <stop offset="100%" stopColor="#FFB627" />
        </linearGradient>
        <linearGradient id="wl-flameMid" x1="200" y1="225" x2="200" y2="110" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="#FF6B35" />
          <stop offset="40%" stopColor="#FF8F00" />
          <stop offset="80%" stopColor="#FFB627" />
          <stop offset="100%" stopColor="#FFE082" />
        </linearGradient>
        <linearGradient id="wl-flameOuter" x1="200" y1="230" x2="200" y2="130" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="#D84315" />
          <stop offset="40%" stopColor="#E65100" />
          <stop offset="80%" stopColor="#FF6B35" />
          <stop offset="100%" stopColor="#FF8A65" />
        </linearGradient>

        {/* Center Glow */}
        <radialGradient id="wl-centerGlow" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="#FFFFFF" stopOpacity="0.95" />
          <stop offset="40%" stopColor="#FFF8E1" stopOpacity="0.7" />
          <stop offset="70%" stopColor="#B2EBF2" stopOpacity="0.3" />
          <stop offset="100%" stopColor="#1A8A8A" stopOpacity="0" />
        </radialGradient>
      </defs>
    </svg>
  );
}
