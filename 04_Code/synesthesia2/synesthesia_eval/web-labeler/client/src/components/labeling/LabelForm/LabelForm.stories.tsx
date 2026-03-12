import type { Meta, StoryObj } from '@storybook/react-webpack5';
import { fn } from 'storybook/test';
import LabelForm from './LabelForm';
import {
  mockExistingLabelPartial,
  mockExistingLabelFull,
  mockAutoLabel,
} from '../../../stories/mockData';

const meta: Meta<typeof LabelForm> = {
  title: 'Labeling/LabelForm',
  component: LabelForm,
  parameters: { layout: 'centered' },
  args: {
    onSave: fn(),
    onSkip: fn(),
    onPrev: fn(),
    onNext: fn(),
    saving: false,
  },
};
export default meta;
type Story = StoryObj<typeof LabelForm>;

export const Empty: Story = {
  args: {
    clipId: '001',
    existingLabel: undefined,
    autoLabel: undefined,
  },
};

export const PartiallyRated: Story = {
  args: {
    clipId: '001',
    existingLabel: mockExistingLabelPartial,
    autoLabel: undefined,
  },
};

export const FullyRated: Story = {
  args: {
    clipId: '001',
    existingLabel: mockExistingLabelFull,
    autoLabel: undefined,
  },
};

export const WithAutoLabel: Story = {
  args: {
    clipId: '001',
    existingLabel: undefined,
    autoLabel: mockAutoLabel,
  },
};

export const Saving: Story = {
  args: {
    clipId: '001',
    existingLabel: mockExistingLabelFull,
    saving: true,
  },
};
