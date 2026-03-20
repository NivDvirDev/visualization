import { dragToScore } from '../components/labeling/SwipeCard/SwipeCard';

describe('dragToScore', () => {
  it('returns 3 for no drag (deltaX=0)', () => {
    expect(dragToScore(0, 400)).toBe(3);
  });

  it('returns 5 for full right drag (>60% of card width)', () => {
    // 60% threshold: 0.6 * 0.6 * 400 = ratio >= 0.5 → score 5
    // deltaX=240 → ratio = 240/(400*0.6) = 1.0 → score 5
    expect(dragToScore(240, 400)).toBe(5);
  });

  it('returns 4 for partial right drag (0.167 <= ratio < 0.5)', () => {
    // deltaX=80 → ratio = 80/240 ≈ 0.333 → 0.167 <= 0.333 < 0.5 → score 4
    expect(dragToScore(80, 400)).toBe(4);
  });

  it('returns 1 for full left drag (>60% left)', () => {
    // deltaX=-240 → ratio = -1.0 → clamped=-1 → <= -0.5 → score 1
    expect(dragToScore(-240, 400)).toBe(1);
  });

  it('returns 2 for partial left drag (-0.5 < ratio <= -0.167)', () => {
    // deltaX=-80 → ratio = -80/240 ≈ -0.333 → -0.5 < -0.333 <= -0.167 → score 2
    expect(dragToScore(-80, 400)).toBe(2);
  });

  it('returns 3 for small right drag (ratio < 0.167)', () => {
    // deltaX=10 → ratio = 10/240 ≈ 0.042 → < 0.167 → score 3
    expect(dragToScore(10, 400)).toBe(3);
  });

  it('returns 3 for small left drag (ratio > -0.167)', () => {
    // deltaX=-10 → ratio ≈ -0.042 → > -0.167 → score 3
    expect(dragToScore(-10, 400)).toBe(3);
  });

  it('clamps ratio at 1.0 for very large right drag', () => {
    expect(dragToScore(10000, 400)).toBe(5);
  });

  it('clamps ratio at -1.0 for very large left drag', () => {
    expect(dragToScore(-10000, 400)).toBe(1);
  });

  it('boundary: exactly at 0.5 ratio returns 5', () => {
    // deltaX=120 → ratio = 120/240 = 0.5 → clamped = 0.5 → not < 0.5 → returns 5
    expect(dragToScore(120, 400)).toBe(5);
  });

  it('boundary: exactly at -0.5 ratio returns 1', () => {
    // deltaX=-120 → ratio = -0.5 → clamped = -0.5 → <= -0.5 → returns 1
    expect(dragToScore(-120, 400)).toBe(1);
  });
});
