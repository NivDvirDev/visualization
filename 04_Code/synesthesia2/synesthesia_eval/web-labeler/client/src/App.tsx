import React from 'react';
import { Routes, Route } from 'react-router-dom';
import LabelerApp from './components/layout/LabelerApp/LabelerApp';
import RankingsPage from './components/community/RankingsPage/RankingsPage';
import ClipDetailPage from './components/community/ClipDetailPage/ClipDetailPage';

const App: React.FC = () => {
  return (
    <Routes>
      <Route path="/rankings" element={<RankingsPage />} />
      <Route path="/clip/:id" element={<ClipDetailPage />} />
      <Route path="*" element={<LabelerApp />} />
    </Routes>
  );
};

export default App;
