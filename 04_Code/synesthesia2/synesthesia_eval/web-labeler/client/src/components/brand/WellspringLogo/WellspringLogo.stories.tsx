import type { Meta, StoryObj } from '@storybook/react-webpack5';
import { WellspringLogo } from './WellspringLogo';

const meta: Meta<typeof WellspringLogo> = {
  title: 'Branding/WellspringLogo',
  component: WellspringLogo,
  parameters: { layout: 'centered' },
  argTypes: {
    size: { control: { type: 'range', min: 40, max: 400, step: 10 } },
    animate: { control: 'boolean' },
  },
};
export default meta;
type Story = StoryObj<typeof WellspringLogo>;

export const Default: Story = {
  args: { size: 200, animate: true },
};

export const Small: Story = {
  args: { size: 80, animate: true },
};

export const Large: Story = {
  args: { size: 300, animate: true },
};

export const Static: Story = {
  args: { size: 200, animate: false },
};

export const AllSizes: Story = {
  render: () => (
    <div style={{ display: 'flex', alignItems: 'center', gap: 24, padding: 20 }}>
      <WellspringLogo size={40} />
      <WellspringLogo size={80} />
      <WellspringLogo size={150} />
      <WellspringLogo size={250} />
    </div>
  ),
};
