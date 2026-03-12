const { pool } = require('../config');

jest.mock('../middleware/rateLimiter', () => ({
  authLimiter: (_req, _res, next) => next(),
  labelWriteLimiter: (_req, _res, next) => next(),
  globalLimiter: (_req, _res, next) => next(),
}));

// We need to test the real huggingface module, so unmock it
jest.unmock('../services/huggingface');

// Mock fetch globally
global.fetch = jest.fn();

// Re-require after unmocking
let HuggingFace;
beforeAll(() => {
  jest.isolateModules(() => {
    HuggingFace = require('../services/huggingface');
  });
});

beforeEach(() => {
  jest.clearAllMocks();
});

describe('HuggingFace.getVideoUrl', () => {
  it('returns correct resolve URL', () => {
    const url = HuggingFace.getVideoUrl('01_test_clip.mp4');
    expect(url).toContain('huggingface.co/datasets');
    expect(url).toContain('resolve/main/data/clips/01_test_clip.mp4');
  });

  it('encodes special characters in filename', () => {
    const url = HuggingFace.getVideoUrl('clip with spaces.mp4');
    expect(url).toContain('clip%20with%20spaces.mp4');
  });
});

describe('HuggingFace.listClipFiles', () => {
  it('filters to video files only', async () => {
    global.fetch.mockResolvedValue({
      ok: true,
      json: () =>
        Promise.resolve([
          { type: 'file', path: 'data/clips/01_test.mp4' },
          { type: 'file', path: 'data/clips/metadata.json' },
          { type: 'file', path: 'data/clips/02_clip.webm' },
          { type: 'directory', path: 'data/clips/thumbs' },
        ]),
    });

    const files = await HuggingFace.listClipFiles();

    expect(files).toHaveLength(2);
    expect(files[0]).toEqual({ id: '01', filename: '01_test.mp4' });
    expect(files[1]).toEqual({ id: '02', filename: '02_clip.webm' });
  });

  it('throws on API error', async () => {
    global.fetch.mockResolvedValue({
      ok: false,
      status: 403,
      statusText: 'Forbidden',
    });

    await expect(HuggingFace.listClipFiles()).rejects.toThrow('HuggingFace API error: 403');
  });
});

describe('HuggingFace.syncClips', () => {
  it('returns early when USE_HUGGINGFACE is false', async () => {
    // Config mock sets USE_HUGGINGFACE: false by default
    const result = await HuggingFace.syncClips();
    expect(result).toEqual({ synced: 0 });
    expect(global.fetch).not.toHaveBeenCalled();
  });
});

describe('HuggingFace.pushLabels', () => {
  it('skips push when disabled', async () => {
    // Config mock has USE_HUGGINGFACE: false and HF_TOKEN: ''
    const result = await HuggingFace.pushLabels();
    expect(result).toBe(false);
    expect(global.fetch).not.toHaveBeenCalled();
  });
});

describe('HuggingFace.fetchCommunityLabels', () => {
  it('returns empty array on 404', async () => {
    global.fetch.mockResolvedValue({ ok: false, status: 404 });

    const labels = await HuggingFace.fetchCommunityLabels();
    expect(labels).toEqual([]);
  });

  it('throws on non-404 error', async () => {
    global.fetch.mockResolvedValue({ ok: false, status: 500 });

    await expect(HuggingFace.fetchCommunityLabels()).rejects.toThrow('HuggingFace fetch error: 500');
  });

  it('returns parsed JSON on success', async () => {
    const mockLabels = [{ clip_id: '01', user: 'alice' }];
    global.fetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockLabels),
    });

    const labels = await HuggingFace.fetchCommunityLabels();
    expect(labels).toEqual(mockLabels);
  });
});
