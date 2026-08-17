/**
 * Regression tests for the 2026-08-12 miscount.
 *
 * Anonymous guest ratings (POST /api/labels/anonymous) are stored with user_id NULL
 * and labeler 'anon_<ms>_<rand>'. Classifying on user_id alone made /api/stats report
 * labeled_human = 0 while 700 real anonymous ratings sat in the table, and made
 * exportJson() drop those ratings into the auto bucket — where, being keyed by clip_id,
 * they overwrote the Gemini auto-labels entirely.
 */
require('./setup');
const { pool } = require('../config');
const Label = require('../models/label');

const entry = (over = {}) => ({
  sync_quality: 4, harmony: 4, aesthetic_quality: 4, motion_smoothness: 4,
  pitch_accuracy: null, rhythm_accuracy: null, dynamics_accuracy: null,
  timbre_accuracy: null, melody_accuracy: null, overall_impression: 4,
  notes: null, created_at: '2026-08-10T00:00:00Z', updated_at: null,
  ...over,
});

describe('exportJson() anonymous classification', () => {
  beforeEach(() => jest.clearAllMocks());

  it('keeps the auto-label when an anonymous human rates the same clip', async () => {
    pool.query.mockResolvedValueOnce({
      rows: [
        entry({ clip_id: '001', labeler: 'gemini-2.0-flash', user_id: null, username: null }),
        entry({ clip_id: '001', labeler: 'anon_1786397867868_6vpzwh', user_id: null, username: null, overall_impression: 1 }),
      ],
    });

    const { human, auto } = await Label.exportJson();

    // The regression: auto['001'] used to be clobbered by the anon rating.
    expect(auto['001'].model).toBe('gemini-2.0-flash');
    expect(human['001']).toHaveLength(1);
    expect(human['001'][0]).toMatchObject({
      anonymous: true,
      session: 'anon_1786397867868_6vpzwh',
      overall_impression: 1,
      username: null,
    });
  });

  it('collects multiple anonymous sessions per clip instead of overwriting', async () => {
    pool.query.mockResolvedValueOnce({
      rows: [
        entry({ clip_id: '003', labeler: 'anon_1_a', user_id: null, username: null, overall_impression: 4 }),
        entry({ clip_id: '003', labeler: 'anon_2_b', user_id: null, username: null, overall_impression: 5 }),
      ],
    });

    const { human, auto } = await Label.exportJson();

    expect(human['003'].map((l) => l.overall_impression)).toEqual([4, 5]);
    expect(auto['003']).toBeUndefined();
  });

  it('still marks registered ratings as human and non-anon labelers as auto', async () => {
    pool.query.mockResolvedValueOnce({
      rows: [
        entry({ clip_id: '005', labeler: 'niv', user_id: 7, username: 'niv' }),
        entry({ clip_id: '006', labeler: 'gemini-2.0-flash', user_id: null, username: null }),
      ],
    });

    const { human, auto } = await Label.exportJson();

    expect(human['005'][0]).toMatchObject({ anonymous: false, username: 'niv', session: null });
    expect(auto['006'].model).toBe('gemini-2.0-flash');
    expect(human['006']).toBeUndefined();
  });
});

describe('stats() counts anonymous ratings as human', () => {
  beforeEach(() => jest.clearAllMocks());

  it('classifies on labeler as well as user_id, and splits the averages', async () => {
    pool.query
      .mockResolvedValueOnce({
        rows: [{
          total_clips: 81, labeled_human: 81, labeled_auto: 81, unlabeled: 0,
          total_users: 1, recent_users_7d: 0,
          human_ratings: 700, registered_ratings: 0,
          anonymous_ratings: 700, anonymous_sessions: 352,
        }],
      })
      .mockResolvedValueOnce({ rows: [{ sync_quality: '3.10', harmony: '3.20', aesthetic_quality: '3.30', motion_smoothness: '3.40' }] })
      .mockResolvedValueOnce({ rows: [{ sync_quality: '4.00', harmony: '4.10', aesthetic_quality: '4.20', motion_smoothness: '4.30' }] });

    const stats = await Label.stats();

    expect(stats.labeled_human).toBe(81);
    expect(stats.anonymous_ratings).toBe(700);
    expect(stats.anonymous_sessions).toBe(352);
    expect(stats.registered_ratings).toBe(0);
    expect(stats.avg_scores.sync_quality).toBe(3.1);
    expect(stats.avg_scores_auto.sync_quality).toBe(4.0);

    // The counting SQL must not classify on user_id alone.
    const countSql = pool.query.mock.calls[0][0];
    expect(countSql).toMatch(/labeler LIKE 'anon_%'/);
  });

  it('returns null averages when a bucket is empty', async () => {
    pool.query
      .mockResolvedValueOnce({
        rows: [{
          total_clips: 81, labeled_human: 0, labeled_auto: 0, unlabeled: 81,
          total_users: 0, recent_users_7d: 0,
          human_ratings: 0, registered_ratings: 0,
          anonymous_ratings: 0, anonymous_sessions: 0,
        }],
      })
      .mockResolvedValueOnce({ rows: [{ sync_quality: null, harmony: null, aesthetic_quality: null, motion_smoothness: null }] })
      .mockResolvedValueOnce({ rows: [{ sync_quality: null, harmony: null, aesthetic_quality: null, motion_smoothness: null }] });

    const stats = await Label.stats();

    expect(stats.avg_scores.harmony).toBeNull();
    expect(stats.avg_scores_auto.harmony).toBeNull();
  });
});
