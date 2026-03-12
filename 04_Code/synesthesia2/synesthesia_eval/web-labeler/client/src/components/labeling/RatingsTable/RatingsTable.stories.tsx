import type { Meta, StoryObj } from '@storybook/react-webpack5';
import RatingsTable from './RatingsTable';
import { mockLabels } from '../../../stories/mockData';

const meta: Meta<typeof RatingsTable> = {
  title: 'Labeling/RatingsTable',
  component: RatingsTable,
  parameters: { layout: 'centered' },
};
export default meta;
type Story = StoryObj<typeof RatingsTable>;

export const NoLabels: Story = {
  args: {
    labels: [],
  },
};

export const MultiUser: Story = {
  args: {
    labels: mockLabels.filter((l) => l.user_id != null),
    currentUsername: 'testuser',
  },
};

export const WithAuto: Story = {
  args: {
    labels: mockLabels,
    currentUsername: 'testuser',
  },
};
