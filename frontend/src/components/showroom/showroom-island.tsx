"use client";

import { lazy, Suspense, useRef, type ReactNode } from "react";

import { useNearViewport } from "@/components/motion/use-motion-ok";

import type { ShowroomWall } from "./types";

const ShowroomRoom = lazy(() => import("./showroom-room"));

/**
 * Keeps the 3D room out of the first-load JS: the server-rendered flat salon (`children`) stays
 * until the section nears the viewport, then the room loads and takes its place at the same size.
 * The room is functional, not decorative, so it loads under reduced motion too (it just cuts).
 */
export function ShowroomIsland({
  walls,
  title,
  children,
}: {
  walls: ShowroomWall[];
  title: string;
  children: ReactNode;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const armed = useNearViewport(ref, true, { includeVisible: true });
  return (
    <div ref={ref}>
      {armed ? (
        <Suspense fallback={children}>
          <ShowroomRoom walls={walls} title={title} />
        </Suspense>
      ) : (
        children
      )}
    </div>
  );
}
