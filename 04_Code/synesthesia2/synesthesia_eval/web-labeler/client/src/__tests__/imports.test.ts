/**
 * Import resolution tests — verify all components can be imported
 * from their new co-located folder paths after restructuring.
 */

describe('Component imports resolve correctly', () => {
  // auth
  test('LoginPage', () => {
    const mod = require('../components/auth/LoginPage/LoginPage');
    expect(mod.default).toBeDefined();
  });

  // layout
  test('LabelerApp', () => {
    const mod = require('../components/layout/LabelerApp/LabelerApp');
    expect(mod.default).toBeDefined();
  });
  test('Header', () => {
    const mod = require('../components/layout/Header/Header');
    expect(mod.default).toBeDefined();
  });
  test('Footer', () => {
    const mod = require('../components/layout/Footer/Footer');
    expect(mod.default).toBeDefined();
  });
  test('ProgressBar', () => {
    const mod = require('../components/layout/ProgressBar/ProgressBar');
    expect(mod.default).toBeDefined();
  });

  // labeling
  test('ClipList', () => {
    const mod = require('../components/labeling/ClipList/ClipList');
    expect(mod.default).toBeDefined();
  });
  test('VideoPlayer', () => {
    const mod = require('../components/labeling/VideoPlayer/VideoPlayer');
    expect(mod.default).toBeDefined();
  });
  test('LabelForm', () => {
    const mod = require('../components/labeling/LabelForm/LabelForm');
    expect(mod.default).toBeDefined();
  });
  test('RatingsTable', () => {
    const mod = require('../components/labeling/RatingsTable/RatingsTable');
    expect(mod.default).toBeDefined();
  });

  // community
  test('StatsPanel', () => {
    const mod = require('../components/community/StatsPanel/StatsPanel');
    expect(mod.default).toBeDefined();
  });
  test('Leaderboard', () => {
    const mod = require('../components/community/Leaderboard/Leaderboard');
    expect(mod.default).toBeDefined();
  });
  test('RankingsPage', () => {
    const mod = require('../components/community/RankingsPage/RankingsPage');
    expect(mod.default).toBeDefined();
  });
  test('ClipDetailPage', () => {
    const mod = require('../components/community/ClipDetailPage/ClipDetailPage');
    expect(mod.default).toBeDefined();
  });

  // brand (named exports)
  test('FlameIcon', () => {
    const mod = require('../components/brand/FlameIcon/FlameIcon');
    expect(mod.FlameIcon).toBeDefined();
  });
  test('WellspringLogo', () => {
    const mod = require('../components/brand/WellspringLogo/WellspringLogo');
    expect(mod.WellspringLogo).toBeDefined();
  });
});

describe('App.tsx imports resolve correctly', () => {
  test('App', () => {
    const mod = require('../App');
    expect(mod.default).toBeDefined();
  });
});

describe('Shared modules resolve correctly', () => {
  test('types.ts', () => {
    const mod = require('../types');
    expect(mod).toBeDefined();
  });
  test('api.ts', () => {
    const mod = require('../api');
    expect(mod).toBeDefined();
  });
  test('mockData.ts', () => {
    const mod = require('../stories/mockData');
    expect(mod.mockClips).toBeDefined();
    expect(mod.mockUser).toBeDefined();
    expect(mod.mockStats).toBeDefined();
    expect(mod.mockLeaderboard).toBeDefined();
  });
});
