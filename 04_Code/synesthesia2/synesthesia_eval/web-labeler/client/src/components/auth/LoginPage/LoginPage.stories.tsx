import type { Meta, StoryObj } from '@storybook/react-webpack5';
import { fn } from 'storybook/test';
import LoginPage from './LoginPage';

const meta: Meta<typeof LoginPage> = {
  title: 'Authentication/LoginPage',
  component: LoginPage,
  parameters: { layout: 'fullscreen' },
};
export default meta;
type Story = StoryObj<typeof LoginPage>;

export const Default: Story = {
  args: {
    onLogin: fn(),
    googleClientId: null,
  },
};

export const WithGoogle: Story = {
  args: {
    onLogin: fn(),
    googleClientId: '214450922102-3sbthhu9ijks0k117o03negn5ood50id.apps.googleusercontent.com',
  },
};
