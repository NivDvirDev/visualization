import React from 'react';
import { FlameIcon } from '../../brand/FlameIcon/FlameIcon';
import StatsPanel from '../../community/StatsPanel/StatsPanel';
import { Stats, User } from '../../../types';
import './Header.css';

interface HeaderProps {
  stats: Stats | null;
  user: User;
  showLeaderboard: boolean;
  onToggleLeaderboard: () => void;
  onLogout: () => void;
  onNavigateRankings: () => void;
}

const Header: React.FC<HeaderProps> = ({
  stats,
  user,
  showLeaderboard,
  onToggleLeaderboard,
  onLogout,
  onNavigateRankings,
}) => {
  return (
    <header className="app-header">
      <FlameIcon size={40} className="app-logo" />
      {stats && <StatsPanel stats={stats} />}
      <div className="user-info">
        <button
          className="btn-rankings-link"
          onClick={onNavigateRankings}
          title="Public Rankings"
        >
          Rankings
        </button>
        <button
          className={`btn-trophy${showLeaderboard ? ' active' : ''}`}
          onClick={onToggleLeaderboard}
          title="Leaderboard"
        >
          &#127942;
        </button>
        <span className="user-name">{user.username}</span>
        <button className="btn-logout" onClick={onLogout}>Logout</button>
      </div>
    </header>
  );
};

export default Header;
