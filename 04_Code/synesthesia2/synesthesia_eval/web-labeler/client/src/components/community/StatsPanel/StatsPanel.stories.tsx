import type { Meta, StoryObj } from '@storybook/react-webpack5';
import StatsPanel from './StatsPanel';
import { mockStats } from '../../../stories/mockData';

const meta: Meta<typeof StatsPanel> = {
  title: 'Stats/StatsPanel',
  component: StatsPanel,
  parameters: { layout: 'centered' },
};
export default meta;
type Story = StoryObj<typeof StatsPanel>;

export const Normal: Story = {
  args: {
    stats: mockStats,
  },
};

export const ZeroState: Story = {
  args: {
    stats: {
      total_clips: 83,
      labeled_human: 0,
      labeled_auto: 0,
      unlabeled: 83,
    },
  },
};
