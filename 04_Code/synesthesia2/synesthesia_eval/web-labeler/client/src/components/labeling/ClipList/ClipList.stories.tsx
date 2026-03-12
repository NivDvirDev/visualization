import type { Meta, StoryObj } from '@storybook/react-webpack5';
import { fn } from 'storybook/test';
import ClipList from './ClipList';
import { mockClips } from '../../../stories/mockData';

const meta: Meta<typeof ClipList> = {
  title: 'Navigation/ClipList',
  component: ClipList,
  parameters: { layout: 'fullscreen' },
};
export default meta;
type Story = StoryObj<typeof ClipList>;

export const Empty: Story = {
  args: {
    clips: [],
    selectedClipId: null,
    onSelect: fn(),
    mode: 'unlabeled',
    onModeChange: fn(),
    onRandom: fn(),
  },
};

export const WithClips: Story = {
  args: {
    clips: mockClips,
    selectedClipId: null,
    onSelect: fn(),
    mode: 'unlabeled',
    onModeChange: fn(),
    onRandom: fn(),
  },
};

export const WithSelection: Story = {
  args: {
    clips: mockClips,
    selectedClipId: mockClips[0].id,
    onSelect: fn(),
    mode: 'all',
    onModeChange: fn(),
    onRandom: fn(),
  },
};
