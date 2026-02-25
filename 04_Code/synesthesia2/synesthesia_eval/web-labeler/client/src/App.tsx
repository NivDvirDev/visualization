import React, { Component } from 'react';
import { getClips, getClip, getStats, saveLabel } from './api';
import ClipList from './components/ClipList';
import VideoPlayer from './components/VideoPlayer';
import LabelForm from './components/LabelForm';
import StatsPanel from './components/StatsPanel';
import { ClipSummary, ClipDetail, ClipMode, Label, LabelData, Stats } from './types';

interface AppState {
  clips: ClipSummary[];
  selectedClipId: string | null;
  selectedClip: ClipDetail | null;
  mode: ClipMode;
  stats: Stats | null;
  saving: boolean;
}

class App extends Component<{}, AppState> {
  state: AppState = {
    clips: [],
    selectedClipId: null,
    selectedClip: null,
    mode: 'unlabeled',
    stats: null,
    saving: false,
  };

  componentDidMount() {
    this.loadClips();
    this.loadStats();
  }

  loadClips = () => {
    getClips(this.state.mode).then((clips) => {
      this.setState({ clips });
    });
  };

  loadStats = () => {
    getStats().then((stats) => this.setState({ stats }));
  };

  loadClip = (id: string) => {
    getClip(id).then((clip) => {
      this.setState({ selectedClipId: id, selectedClip: clip });
    });
  };

  handleModeChange = (mode: ClipMode) => {
    this.setState({ mode }, this.loadClips);
  };

  handleSelect = (id: string) => {
    this.loadClip(id);
  };

  handleSave = (clipId: string, labelData: LabelData) => {
    this.setState({ saving: true });
    saveLabel(clipId, { labeler: 'human', ...labelData }).then(() => {
      this.setState({ saving: false });
      this.loadClips();
      this.loadStats();
      this.goToNext();
    });
  };

  handleSkip = () => {
    this.goToNext();
  };

  goToNext = () => {
    const { clips, selectedClipId } = this.state;
    const idx = clips.findIndex((c) => c.id === selectedClipId);
    if (idx >= 0 && idx < clips.length - 1) {
      this.loadClip(clips[idx + 1].id);
    }
  };

  goToPrev = () => {
    const { clips, selectedClipId } = this.state;
    const idx = clips.findIndex((c) => c.id === selectedClipId);
    if (idx > 0) {
      this.loadClip(clips[idx - 1].id);
    }
  };

  handleRandom = () => {
    const { clips } = this.state;
    if (clips.length === 0) return;
    const clip = clips[Math.floor(Math.random() * clips.length)];
    this.loadClip(clip.id);
  };

  render() {
    const { clips, selectedClipId, selectedClip, mode, stats, saving } = this.state;
    const humanLabel: Label | undefined = selectedClip
      ? (selectedClip.labels || []).find((l) => l.labeler === 'human')
      : undefined;
    const autoLabel: Label | undefined = selectedClip
      ? (selectedClip.labels || []).find((l) => l.labeler !== 'human')
      : undefined;

    return (
      <div className="app">
        <header className="app-header">
          <h1>Synesthesia Web Labeler</h1>
          {stats && <StatsPanel stats={stats} />}
        </header>
        <main className="app-main">
          <ClipList
            clips={clips}
            selectedClipId={selectedClipId}
            onSelect={this.handleSelect}
            mode={mode}
            onModeChange={this.handleModeChange}
            onRandom={this.handleRandom}
          />
          <div className="app-content">
            {selectedClip ? (
              <React.Fragment>
                <VideoPlayer
                  clipId={selectedClip.id}
                  filename={selectedClip.filename}
                  metadata={selectedClip}
                />
                <LabelForm
                  clipId={selectedClip.id}
                  existingLabel={humanLabel}
                  autoLabel={autoLabel}
                  onSave={this.handleSave}
                  onSkip={this.handleSkip}
                  onPrev={this.goToPrev}
                  onNext={this.goToNext}
                  saving={saving}
                />
              </React.Fragment>
            ) : (
              <div className="empty-state">
                <p>Select a clip from the sidebar to begin labeling.</p>
              </div>
            )}
          </div>
        </main>
        <footer className="app-footer">
          Synesthesia Eval &mdash; Web Labeler v1.0
        </footer>
      </div>
    );
  }
}

export default App;
