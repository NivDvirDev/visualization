import React from 'react';
import { useNavigate } from 'react-router-dom';
import { FlameIcon } from '../../brand/FlameIcon/FlameIcon';
import StatsPanel from '../../community/StatsPanel/StatsPanel';
import { Button } from '../../atoms';
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
  const navigate = useNavigate();
  return (
    <header className="app-header">
      <FlameIcon size={40} className="app-logo" />
      {stats && <StatsPanel stats={stats} />}
      <div className="user-info">
        <Button
          variant="primary"
          size="sm"
          onClick={() => navigate('/swipe')}
          title="Quick Rate Mode"
        >
          ⚡ Quick Mode
        </Button>
        <Button
          variant="secondary"
          size="sm"
          onClick={onNavigateRankings}
          title="Public Rankings"
        >
          Rankings
        </Button>
        <button
          className={`btn-trophy${showLeaderboard ? ' active' : ''}`}
          onClick={onToggleLeaderboard}
          title="Leaderboard"
        >
          &#127942;
        </button>
        <span className="user-name">{user.username}</span>
        <Button variant="danger" size="sm" onClick={onLogout}>Logout</Button>
      </div>
    </header>
  );
};

export default Header;
