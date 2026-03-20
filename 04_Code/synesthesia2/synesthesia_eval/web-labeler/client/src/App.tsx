import React from 'react';
import { Routes, Route } from 'react-router-dom';
import LabelerApp from './components/layout/LabelerApp/LabelerApp';
import RankingsPage from './components/community/RankingsPage/RankingsPage';
import ClipDetailPage from './components/community/ClipDetailPage/ClipDetailPage';
import UserProfilePage from './components/community/UserProfilePage/UserProfilePage';
import LandingPage from './components/community/LandingPage/LandingPage';
import SwipeMode from './components/labeling/SwipeMode/SwipeMode';
import PrivacyPolicy from './components/legal/PrivacyPolicy/PrivacyPolicy';
import TermsOfService from './components/legal/TermsOfService/TermsOfService';

const App: React.FC = () => {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/rankings" element={<RankingsPage />} />
      <Route path="/clip/:id" element={<ClipDetailPage />} />
      <Route path="/user/:username" element={<UserProfilePage />} />
      <Route path="/swipe" element={<SwipeMode />} />
      <Route path="/privacy" element={<PrivacyPolicy />} />
      <Route path="/terms" element={<TermsOfService />} />
      <Route path="*" element={<LabelerApp />} />
    </Routes>
  );
};

export default App;
