import type { Meta, StoryObj } from '@storybook/react-webpack5';
import { Button } from './Button';

const meta: Meta<typeof Button> = {
  title: 'Atoms/Button',
  component: Button,
  parameters: { layout: 'centered' },
  argTypes: {
    variant: { control: 'select', options: ['primary', 'secondary', 'ghost', 'danger'] },
    size: { control: 'select', options: ['sm', 'md', 'lg'] },
    loading: { control: 'boolean' },
    disabled: { control: 'boolean' },
  },
};
export default meta;
type Story = StoryObj<typeof Button>;

export const Primary: Story = { args: { variant: 'primary', children: 'Start Rating' } };
export const Secondary: Story = { args: { variant: 'secondary', children: 'Explore Rankings' } };
export const Ghost: Story = { args: { variant: 'ghost', children: 'Detail Mode →' } };
export const Danger: Story = { args: { variant: 'danger', children: 'Delete' } };
export const Small: Story = { args: { variant: 'primary', size: 'sm', children: 'Sign in to save' } };
export const Large: Story = { args: { variant: 'primary', size: 'lg', children: 'Join Now' } };
export const Loading: Story = { args: { variant: 'primary', loading: true, children: 'Saving…' } };
export const Disabled: Story = { args: { variant: 'primary', disabled: true, children: 'Unavailable' } };

export const AllVariants: Story = {
  render: () => (
    <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'center' }}>
      <Button variant="primary">Primary</Button>
      <Button variant="secondary">Secondary</Button>
      <Button variant="ghost">Ghost</Button>
      <Button variant="danger">Danger</Button>
    </div>
  ),
};

export const AllSizes: Story = {
  render: () => (
    <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
      <Button size="sm">Small</Button>
      <Button size="md">Medium</Button>
      <Button size="lg">Large</Button>
    </div>
  ),
};
