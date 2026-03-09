import React, { useState, useEffect } from 'react';
import { getLeaderboard, getMyStats } from '../api';

interface LeaderEntry {
  username: string;
  total_labels: number;
}

interface MyStats {
  total_labels: number;
  clips_remaining: number;
  current_streak: number;
  badges: string[];
}

const BADGE_MAP: Record<string, { icon: string; label: string }> = {
  first_label: { icon: '⭐', label: 'First Label' },
  five_streak: { icon: '🔥', label: '5-Day Streak' },
  ten_labels: { icon: '🎯', label: '10 Labels' },
  completionist: { icon: '👑', label: 'Completionist' },
};

const MEDALS = ['🏆', '🥈', '🥉'];

const Leaderboard: React.FC<{ user: any }> = ({ user }) => {
  const [leaders, setLeaders] = useState<LeaderEntry[]>([]);
  const [myStats, setMyStats] = useState<MyStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const [lb, ms] = await Promise.all([
          getLeaderboard().catch(() => []),
          user ? getMyStats().catch(() => null) : Promise.resolve(null),
        ]);
        setLeaders(lb);
        setMyStats(ms);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [user]);

  if (loading) return <div className="leaderboard-loading">Loading...</div>;

  return (
    <div className="leaderboard">
      {myStats && (
        <div className="my-stats-card">
          <h3>Your Stats</h3>
          <div className="my-stats-grid">
            <div className="stat-item">
              <span className="stat-value">{myStats.total_labels}</span>
              <span className="stat-label">Labels</span>
            </div>
            <div className="stat-item">
              <span className="stat-value">{myStats.clips_remaining}</span>
              <span className="stat-label">Remaining</span>
            </div>
            <div className="stat-item">
              <span className="stat-value">{myStats.current_streak} 🔥</span>
              <span className="stat-label">Streak</span>
            </div>
          </div>
          {myStats.badges.length > 0 && (
            <div className="badges-row">
              {myStats.badges.map((b) => (
                <span key={b} className="badge-pill" title={BADGE_MAP[b]?.label || b}>
                  {BADGE_MAP[b]?.icon || '🏅'} {BADGE_MAP[b]?.label || b}
                </span>
              ))}
            </div>
          )}
        </div>
      )}

      <h3 className="leaderboard-title">Leaderboard</h3>
      <table className="leaderboard-table">
        <thead>
          <tr>
            <th>#</th>
            <th>User</th>
            <th>Labels</th>
          </tr>
        </thead>
        <tbody>
          {leaders.length === 0 ? (
            <tr>
              <td colSpan={3} className="leaderboard-empty">
                No labels yet — be the first!
              </td>
            </tr>
          ) : (
            leaders.map((entry, i) => (
              <tr
                key={entry.username}
                className={user?.username === entry.username ? 'leaderboard-me' : ''}
              >
                <td>{MEDALS[i] || i + 1}</td>
                <td>{entry.username}</td>
                <td>{entry.total_labels}</td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
};

export default Leaderboard;
