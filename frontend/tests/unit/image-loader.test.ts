import { describe, expect, it } from "vitest";

import imageLoader from "@/lib/image-loader";

describe("imageLoader", () => {
  it("hotlinks Unsplash through its CDN with size, quality and auto format", () => {
    const url = new URL(
      imageLoader({ src: "https://images.unsplash.com/photo-1?ixid=abc", width: 640, quality: 70 }),
    );
    expect(url.origin).toBe("https://images.unsplash.com");
    expect(url.searchParams.get("ixid")).toBe("abc");
    expect(url.searchParams.get("w")).toBe("640");
    expect(url.searchParams.get("q")).toBe("70");
    expect(url.searchParams.get("auto")).toBe("format");
  });

  it("sends everything else through the Next.js optimiser", () => {
    expect(imageLoader({ src: "/media/catalog/a.png", width: 384 })).toBe(
      "/_next/image?url=%2Fmedia%2Fcatalog%2Fa.png&w=384&q=75",
    );
  });
});
