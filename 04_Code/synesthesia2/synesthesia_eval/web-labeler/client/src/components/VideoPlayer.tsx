import React, { useState, useEffect, useRef, useCallback } from 'react';
import { ClipDetail } from '../types';
import { getVideoUrl } from '../api';

interface VideoPlayerProps {
  clipId: string;
  filename: string;
  metadata: ClipDetail;
  useHuggingFace?: boolean;
}

const VideoPlayer: React.FC<VideoPlayerProps> = ({ clipId, filename, metadata, useHuggingFace }) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [showMeta, setShowMeta] = useState(false);
  const [videoUrl, setVideoUrl] = useState(`/videos/${encodeURIComponent(filename)}`);

  const resolveVideoUrl = useCallback(() => {
    if (useHuggingFace) {
      getVideoUrl(filename).then((url) => {
        setVideoUrl(url);
      });
    } else {
      setVideoUrl(`/videos/${encodeURIComponent(filename)}`);
    }
  }, [filename, useHuggingFace]);

  // Resolve URL on mount and when clip changes
  useEffect(() => {
    setShowMeta(false);
    resolveVideoUrl();
  }, [clipId, resolveVideoUrl]);

  const toggleMeta = useCallback(() => {
    setShowMeta((prev) => !prev);
  }, []);

  return (
    <div className="video-player">
      <div className="video-container">
        <video key={videoUrl} ref={videoRef} controls autoPlay loop>
          <source src={videoUrl} type="video/mp4" />
          Your browser does not support the video element.
        </video>
      </div>
      <button className="video-info-btn" onClick={toggleMeta} title="Clip metadata">
        {showMeta ? '\u2715' : '\u24D8'}
      </button>
      {showMeta && (
        <div className="video-meta-overlay">
          <pre>{JSON.stringify(metadata, null, 2)}</pre>
        </div>
      )}
    </div>
  );
};

export default VideoPlayer;
