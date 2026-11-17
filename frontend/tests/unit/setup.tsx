import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterEach, expect, vi } from "vitest";
import * as matchers from "vitest-axe/matchers";

expect.extend(matchers);
afterEach(cleanup);

/** matchMedia stub; tests flip `reducedMotion` to exercise both code paths. */
export const media = { reducedMotion: false, finePointer: true };
Object.defineProperty(window, "matchMedia", {
  writable: true,
  value: vi.fn((query: string) => ({
    matches: query.includes("reduce")
      ? media.reducedMotion
      : query.includes("pointer: fine")
        ? media.finePointer
        : false,
    media: query,
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    addListener: vi.fn(),
    removeListener: vi.fn(),
    onchange: null,
    dispatchEvent: vi.fn(),
  })),
});

class IO {
  observe = vi.fn();
  unobserve = vi.fn();
  disconnect = vi.fn();
  takeRecords = vi.fn(() => []);
}
Object.defineProperty(window, "IntersectionObserver", { writable: true, value: IO });

vi.mock("next/image", () => ({
  default: ({ fill: _f, priority: _p, fetchPriority: _fp, ...props }: Record<string, unknown>) => (
    <img {...props} />
  ),
  getImageProps: (p: Record<string, unknown>) => ({ props: { ...p, srcSet: `${p.src} 640w` } }),
}));

class RO {
  observe = vi.fn();
  unobserve = vi.fn();
  disconnect = vi.fn();
}
Object.defineProperty(window, "ResizeObserver", { writable: true, value: RO });
HTMLCanvasElement.prototype.getContext = vi.fn(() => null) as unknown as HTMLCanvasElement["getContext"];
