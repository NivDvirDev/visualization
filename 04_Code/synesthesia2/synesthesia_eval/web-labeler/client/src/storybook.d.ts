// Type declarations for Storybook 10 packages under CRA's moduleResolution: "node"
declare module '@storybook/react-webpack5' {
  export { Meta, StoryObj, Preview, StorybookConfig } from '@storybook/react-webpack5/dist/index';
}

declare module 'storybook/test' {
  export { fn, expect, userEvent, within } from 'storybook/dist/test/index';
}
