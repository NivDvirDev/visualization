import type { Meta, StoryObj } from '@storybook/react-webpack5';
import { WellspringIcon } from './WellspringIcon';

const meta: Meta<typeof WellspringIcon> = {
  title: 'Branding/WellspringIcon',
  component: WellspringIcon,
  parameters: { layout: 'centered' },
  argTypes: {
    size: { control: { type: 'range', min: 40, max: 400, step: 10 } },
    animate: { control: 'boolean' },
  },
};
export default meta;
type Story = StoryObj<typeof WellspringIcon>;

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
      <WellspringIcon size={40} />
      <WellspringIcon size={80} />
      <WellspringIcon size={150} />
      <WellspringIcon size={250} />
    </div>
  ),
};
