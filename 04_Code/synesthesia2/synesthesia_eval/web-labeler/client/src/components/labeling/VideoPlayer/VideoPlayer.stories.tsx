import type { Meta, StoryObj } from '@storybook/react-webpack5';
import VideoPlayer from './VideoPlayer';
import { mockClipDetail } from '../../../stories/mockData';

const meta: Meta<typeof VideoPlayer> = {
  title: 'Labeling/VideoPlayer',
  component: VideoPlayer,
  parameters: { layout: 'centered' },
};
export default meta;
type Story = StoryObj<typeof VideoPlayer>;

export const Default: Story = {
  args: {
    clipId: '001',
    filename: '001_Audio Visualization in Blender #1.mp4',
    metadata: mockClipDetail,
    useHuggingFace: false,
  },
};
