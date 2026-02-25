import React, { Component } from 'react';
import { ClipDetail } from '../types';

interface VideoPlayerProps {
  clipId: string;
  filename: string;
  metadata: ClipDetail;
}

interface VideoPlayerState {
  showMeta: boolean;
}

class VideoPlayer extends Component<VideoPlayerProps, VideoPlayerState> {
  state: VideoPlayerState = { showMeta: false };

  componentDidUpdate(prevProps: VideoPlayerProps) {
    if (prevProps.clipId !== this.props.clipId) {
      this.setState({ showMeta: false });
    }
  }

  toggleMeta = () => {
    this.setState((s) => ({ showMeta: !s.showMeta }));
  };

  render() {
    const { filename, metadata } = this.props;
    const { showMeta } = this.state;
    const videoUrl = `/videos/${encodeURIComponent(filename)}`;

    return (
      <div className="video-player">
        <video key={filename} controls autoPlay>
          <source src={videoUrl} type="video/mp4" />
          Your browser does not support the video element.
        </video>
        <div className="video-meta">
          <button className="video-meta-toggle" onClick={this.toggleMeta}>
            {showMeta ? 'Hide' : 'Show'} metadata
          </button>
          {showMeta && (
            <div className="video-meta-content">
              {JSON.stringify(metadata, null, 2)}
            </div>
          )}
        </div>
      </div>
    );
  }
}

export default VideoPlayer;
