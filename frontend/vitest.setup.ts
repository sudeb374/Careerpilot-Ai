import { afterEach, vi } from "vitest";
import { cleanup } from "@testing-library/react";

const defaultFetch = vi.fn().mockResolvedValue({
  ok: true,
  status: 200,
  json: async () => ({}),
});
global.fetch = defaultFetch;

// Automatically unmount React trees after each test
afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
  global.fetch = defaultFetch;
});

// Polyfill window.matchMedia
Object.defineProperty(window, "matchMedia", {
  writable: true,
  configurable: true,
  value: vi.fn().mockImplementation((query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(), // Deprecated
    removeListener: vi.fn(), // Deprecated
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

// Polyfill ResizeObserver
global.ResizeObserver = class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
} as unknown as typeof global.ResizeObserver;

// Polyfill IntersectionObserver
global.IntersectionObserver = class IntersectionObserver {
  readonly root: Element | null = null;
  readonly rootMargin: string = "";
  readonly thresholds: ReadonlyArray<number> = [];
  observe() {}
  unobserve() {}
  disconnect() {}
  takeRecords() {
    return [];
  }
} as unknown as typeof global.IntersectionObserver;

// Polyfill scrollTo
window.scrollTo = vi.fn();

// Polyfill URL.createObjectURL and revokeObjectURL
if (!URL.createObjectURL) {
  URL.createObjectURL = vi.fn(() => "blob:mock-url");
}
if (!URL.revokeObjectURL) {
  URL.revokeObjectURL = vi.fn();
}
