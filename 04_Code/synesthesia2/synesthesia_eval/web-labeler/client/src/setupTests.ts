// Polyfill TextEncoder/TextDecoder for jsdom (needed by react-router v7)
import { TextEncoder, TextDecoder } from 'util';

Object.assign(global, {
  TextEncoder,
  TextDecoder,
});

import '@testing-library/jest-dom';
