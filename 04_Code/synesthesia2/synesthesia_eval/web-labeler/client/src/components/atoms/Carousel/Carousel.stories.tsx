import React from 'react';
import type { Meta, StoryObj } from '@storybook/react-webpack5';
import { Carousel } from './Carousel';

const meta: Meta<typeof Carousel> = {
  title: 'Atoms/Carousel',
  component: Carousel,
  parameters: {
    layout: 'padded',
    backgrounds: {
      default: 'parchment',
      values: [{ name: 'parchment', value: '#F5F1E8' }],
    },
  },
  argTypes: {
    autoPlay: { control: 'boolean' },
    autoPlayInterval: { control: 'number' },
    showDots: { control: 'boolean' },
    showArrows: { control: 'boolean' },
    loop: { control: 'boolean' },
    gap: { control: 'number' },
  },
};
export default meta;
type Story = StoryObj<typeof Carousel>;

/* ---- Coloured placeholder panels ---- */
const SLIDES = [
  { bg: 'linear-gradient(135deg, #FF6B35, #FFB627)', label: 'Slide 1 — Flame Spiral' },
  { bg: 'linear-gradient(135deg, #2BA5A5, #1A1A2E)', label: 'Slide 2 — Teal Deep' },
  { bg: 'linear-gradient(135deg, #D84315, #FF6B35)', label: 'Slide 3 — Ember' },
  { bg: 'linear-gradient(135deg, #FFB627, #FFF3E0)', label: 'Slide 4 — Gold Parchment' },
  { bg: 'linear-gradient(135deg, #2E7D32, #43A047)', label: 'Slide 5 — Forest' },
];

const SlidePanel: React.FC<{ bg: string; label: string }> = ({ bg, label }) => (
  <div
    style={{
      background: bg,
      height: 240,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      borderRadius: 10,
      fontFamily: 'var(--font-display)',
      fontSize: 14,
      color: '#fff',
      letterSpacing: '0.05em',
      textShadow: '0 1px 4px rgba(0,0,0,0.4)',
    }}
  >
    {label}
  </div>
);

const slides = SLIDES.map((s) => <SlidePanel key={s.label} bg={s.bg} label={s.label} />);

export const Default: Story = {
  render: () => (
    <div style={{ width: 480 }}>
      <Carousel showDots showArrows loop>
        {slides}
      </Carousel>
    </div>
  ),
};

export const AutoPlay: Story = {
  render: () => (
    <div style={{ width: 480 }}>
      <Carousel showDots showArrows loop autoPlay autoPlayInterval={2500}>
        {slides}
      </Carousel>
    </div>
  ),
};

export const NoLoop: Story = {
  render: () => (
    <div style={{ width: 480 }}>
      <Carousel showDots showArrows loop={false}>
        {slides}
      </Carousel>
    </div>
  ),
};

export const DotsOnly: Story = {
  render: () => (
    <div style={{ width: 480 }}>
      <Carousel showDots showArrows={false} loop>
        {slides}
      </Carousel>
    </div>
  ),
};

export const ArrowsOnly: Story = {
  render: () => (
    <div style={{ width: 480 }}>
      <Carousel showDots={false} showArrows loop>
        {slides}
      </Carousel>
    </div>
  ),
};

export const ThreeSlides: Story = {
  render: () => (
    <div style={{ width: 480 }}>
      <Carousel showDots showArrows loop>
        {slides.slice(0, 3)}
      </Carousel>
    </div>
  ),
};

export const Narrow: Story = {
  render: () => (
    <div style={{ width: 280 }}>
      <Carousel showDots showArrows loop>
        {slides}
      </Carousel>
    </div>
  ),
};
