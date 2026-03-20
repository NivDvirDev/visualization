import React, { useState, useEffect, useCallback, useRef } from 'react';
import './Carousel.css';

export interface CarouselProps {
  children: React.ReactNode[];
  autoPlay?: boolean;
  autoPlayInterval?: number;
  showDots?: boolean;
  showArrows?: boolean;
  loop?: boolean;
  gap?: number;
}

/**
 * Carousel — pure React + CSS slide carousel atom.
 * No external library. Uses transform: translateX on the inner track.
 * Supports autoPlay, dot indicators, arrow navigation, loop, and keyboard control.
 */
export const Carousel: React.FC<CarouselProps> = ({
  children,
  autoPlay = false,
  autoPlayInterval = 4000,
  showDots = true,
  showArrows = true,
  loop = true,
  gap = 0,
}) => {
  const count = children.length;
  const [currentIndex, setCurrentIndex] = useState(0);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const clamp = useCallback(
    (idx: number) => {
      if (loop) return (idx + count) % count;
      return Math.max(0, Math.min(idx, count - 1));
    },
    [count, loop],
  );

  const goTo = useCallback(
    (idx: number) => setCurrentIndex(clamp(idx)),
    [clamp],
  );

  const prev = useCallback(() => goTo(currentIndex - 1), [currentIndex, goTo]);
  const next = useCallback(() => goTo(currentIndex + 1), [currentIndex, goTo]);

  /* autoPlay */
  useEffect(() => {
    if (!autoPlay) return;
    timerRef.current = setInterval(next, autoPlayInterval);
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [autoPlay, autoPlayInterval, next]);

  /* keyboard navigation */
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'ArrowLeft') { e.preventDefault(); prev(); }
      if (e.key === 'ArrowRight') { e.preventDefault(); next(); }
    },
    [prev, next],
  );

  const isAtStart = !loop && currentIndex === 0;
  const isAtEnd = !loop && currentIndex === count - 1;

  const trackStyle: React.CSSProperties = {
    transform: `translateX(calc(-${currentIndex * 100}% - ${currentIndex * gap}px))`,
    gap: gap > 0 ? `${gap}px` : undefined,
  };

  return (
    <div
      className="atom-carousel"
      onKeyDown={handleKeyDown}
      tabIndex={0}
      aria-roledescription="carousel"
    >
      {/* viewport clips the track */}
      <div className="atom-carousel-viewport">
        <div className="atom-carousel-track" style={trackStyle}>
          {React.Children.map(children, (child, i) => (
            <div
              className="atom-carousel-slide"
              key={i}
              aria-hidden={i !== currentIndex}
              role="group"
              aria-roledescription="slide"
              aria-label={`Slide ${i + 1} of ${count}`}
            >
              {child}
            </div>
          ))}
        </div>
      </div>

      {/* Previous arrow */}
      {showArrows && (
        <button
          className="atom-carousel-arrow atom-carousel-arrow--prev"
          onClick={prev}
          disabled={isAtStart}
          aria-label="Previous slide"
        >
          ‹
        </button>
      )}

      {/* Next arrow */}
      {showArrows && (
        <button
          className="atom-carousel-arrow atom-carousel-arrow--next"
          onClick={next}
          disabled={isAtEnd}
          aria-label="Next slide"
        >
          ›
        </button>
      )}

      {/* Dot indicators */}
      {showDots && count > 1 && (
        <div className="atom-carousel-dots" role="tablist" aria-label="Slide indicators">
          {Array.from({ length: count }, (_, i) => (
            <button
              key={i}
              role="tab"
              aria-selected={i === currentIndex}
              aria-label={`Go to slide ${i + 1}`}
              className={[
                'atom-carousel-dot',
                i === currentIndex ? 'atom-carousel-dot--active' : '',
              ].filter(Boolean).join(' ')}
              onClick={() => goTo(i)}
            />
          ))}
        </div>
      )}
    </div>
  );
};
