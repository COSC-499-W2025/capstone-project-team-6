import "@testing-library/jest-dom";
import { vi } from 'vitest';

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
};

global.localStorage = localStorageMock;

// Node ≥ v25 ships an experimental built-in `localStorage` that is an empty
// object (no getItem/setItem/removeItem/clear).  This shadows the full
// Web-Storage-API implementation that jsdom would normally provide, causing
// "localStorage.clear is not a function" on Windows/Linux with newer Node
// versions while Macs on v20/v22 LTS work fine.
//
// The guard below only kicks in when the native localStorage is broken and
// replaces it with a minimal spec-compliant in-memory stub so tests work
// everywhere regardless of Node version or OS.
if (typeof globalThis.localStorage === 'undefined' || typeof globalThis.localStorage.clear !== 'function') {
  const store = {};
  globalThis.localStorage = {
    getItem: (key) => (key in store ? store[key] : null),
    setItem: (key, value) => { store[key] = String(value); },
    removeItem: (key) => { delete store[key]; },
    clear: () => { Object.keys(store).forEach((k) => delete store[k]); },
    key: (index) => Object.keys(store)[index] ?? null,
    get length() { return Object.keys(store).length; },
  };
}
