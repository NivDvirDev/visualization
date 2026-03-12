import type { Meta, StoryObj } from '@storybook/react-webpack5';
import ProgressBar from './ProgressBar';

const meta: Meta<typeof ProgressBar> = {
  title: 'Navigation/ProgressBar',
  component: ProgressBar,
  parameters: { layout: 'centered' },
};
export default meta;
type Story = StoryObj<typeof ProgressBar>;

export const Empty: Story = {
  args: {
    total: 83,
    labeled: 0,
    remaining: 83,
  },
};

export const Partial: Story = {
  args: {
    total: 83,
    labeled: 29,
    remaining: 54,
  },
};

export const Complete: Story = {
  args: {
    total: 83,
    labeled: 83,
    remaining: 0,
  },
};
