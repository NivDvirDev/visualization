import React, { useRef, useState, useCallback } from 'react';
import SwipeScoreOverlay from '../SwipeScoreOverlay/SwipeScoreOverlay';
import './SwipeCard.css';

interface ClipInfo {
  id: string;
  title?: string;
  videoUrl: string;
}

interface Props {
  clip: ClipInfo;
  onCommit: (score: number) => void;
  disabled: boolean;
  muted: boolean;
  onMuteToggle: () => void;
}

export function dragToScore(deltaX: number, cardWidth: number): number {
  const ratio = deltaX / (cardWidth * 0.6);
  const clamped = Math.max(-1, Math.min(1, ratio));
  if (clamped <= -0.5) return 1;
  if (clamped <= -0.167) return 2;
  if (clamped < 0.167) return 3;
  if (clamped < 0.5) return 4;
  return 5;
}

const SwipeCard: React.FC<Props> = ({ clip, onCommit, disabled, muted, onMuteToggle }) => {
  const cardRef = useRef<HTMLDivElement>(null);
  const dragStartX = useRef(0);
  const currentDeltaX = useRef(0);
  const isDragging = useRef(false);

  const [dragScore, setDragScore] = useState<number | null>(null);
  const [dragRatio, setDragRatio] = useState(0);
  const [phase, setPhase] = useState<'idle' | 'dragging' | 'committing' | 'snapping'>('idle');

  const snapBack = useCallback(() => {
    const card = cardRef.current;
    if (!card) return;
    setPhase('snapping');
    card.style.transform = '';
    setDragScore(null);
    setDragRatio(0);
    setTimeout(() => setPhase('idle'), 420);
  }, []);

  const commitSwipe = useCallback((direction: 'left' | 'right', score: number) => {
    const card = cardRef.current;
    if (!card) return;
    setPhase('committing');
    const flyX = direction === 'right' ? '130vw' : '-130vw';
    const rotate = direction === 'right' ? '30deg' : '-30deg';
    card.style.transition = 'transform 0.35s ease-in';
    card.style.transform = `translateX(${flyX}) rotate(${rotate})`;
    setTimeout(() => {
      card.style.transition = '';
      card.style.transform = '';
      setDragScore(null);
      setDragRatio(0);
      setPhase('idle');
      onCommit(score);
    }, 380);
  }, [onCommit]);

  const handlePointerDown = useCallback((e: React.PointerEvent<HTMLDivElement>) => {
    if (phase !== 'idle' || disabled) return;
    e.currentTarget.setPointerCapture(e.pointerId);
    dragStartX.current = e.clientX;
    currentDeltaX.current = 0;
    isDragging.current = true;
    setPhase('dragging');
  }, [phase, disabled]);

  const handlePointerMove = useCallback((e: React.PointerEvent<HTMLDivElement>) => {
    if (!isDragging.current) return;
    e.preventDefault();
    const deltaX = e.clientX - dragStartX.current;
    currentDeltaX.current = deltaX;
    const cardWidth = cardRef.current?.offsetWidth || 380;
    const rotate = (deltaX / cardWidth) * 15;

    if (cardRef.current) {
      cardRef.current.style.transform = `translateX(${deltaX}px) rotate(${rotate}deg)`;
    }

    const score = dragToScore(deltaX, cardWidth);
    const ratio = Math.max(-1, Math.min(1, deltaX / (cardWidth * 0.6)));
    setDragScore(score);
    setDragRatio(ratio);
  }, []);

  const handlePointerUp = useCallback(() => {
    if (!isDragging.current) return;
    isDragging.current = false;
    const deltaX = currentDeltaX.current;
    const cardWidth = cardRef.current?.offsetWidth || 380;
    const threshold = cardWidth * 0.08;

    if (Math.abs(deltaX) >= threshold) {
      const score = dragToScore(deltaX, cardWidth);
      commitSwipe(deltaX > 0 ? 'right' : 'left', score);
    } else {
      snapBack();
    }
  }, [commitSwipe, snapBack]);

  return (
    <div
      ref={cardRef}
      className={`swipe-card ${phase === 'snapping' ? 'swipe-card--snapping' : ''}`}
      onPointerDown={handlePointerDown}
      onPointerMove={handlePointerMove}
      onPointerUp={handlePointerUp}
      onPointerCancel={handlePointerUp}
    >
      <video
        key={clip.videoUrl}
        src={clip.videoUrl}
        autoPlay
        loop
        muted={muted}
        playsInline
        className="swipe-card-video"
      />
      <button
        className="swipe-card-sound-btn"
        onClick={(e) => { e.stopPropagation(); onMuteToggle(); }}
        title={muted ? 'Unmute' : 'Mute'}
      >
        {muted ? '🔇' : '🔊'}
      </button>
      <div className="swipe-card-label">
        <span className="swipe-card-id">{clip.id}</span>
        {clip.title && <span className="swipe-card-title">{clip.title}</span>}
      </div>
      <SwipeScoreOverlay score={dragScore} ratio={dragRatio} />
    </div>
  );
};

export default SwipeCard;
