/**
 * useFeatureFrame — syncs the Zustand store to the current audio clock position.
 *
 * Call once at the App level. Reads currentTime from useAudioClock,
 * looks up the nearest frame in hviz.frames, and pushes it into the store.
 *
 * Also tracks key changes: when chord.root changes significantly and persists
 * for >3 frames, updates tonicPitchClass and triggers helixRotationOffset animation.
 */

import { useEffect, useRef } from "react";
import { useMusicalStore } from "../store";
import { PC_TO_FIFTHS_IDX } from "../constants/chroma";
import { KEY_CHANGE_DURATION_S } from "../constants/helix";

const KEY_CONFIRM_FRAMES = 3;   // root must hold for this many frames to register as key change

export function useFeatureFrame(currentTime: number): void {
  const { hviz, setFrame, tonicPitchClass, setTonicPitchClass, setHelixRotationOffset } =
    useMusicalStore();

  const pendingRootRef = useRef<{ root: number; count: number } | null>(null);
  const animStartRef = useRef<number | null>(null);
  const animFromRef = useRef(0);
  const animToRef = useRef(0);
  const rafRef = useRef<number>(0);

  useEffect(() => {
    if (!hviz) return;
    const { frames, meta } = hviz;
    const idx = Math.min(Math.round(currentTime * meta.fps), frames.length - 1);
    const frame = frames[idx];
    setFrame(frame, idx);

    // Key change detection
    const root = frame.chord.root;
    if (root !== null) {
      if (pendingRootRef.current?.root === root) {
        pendingRootRef.current.count++;
      } else {
        pendingRootRef.current = { root, count: 1 };
      }

      if (
        pendingRootRef.current.count >= KEY_CONFIRM_FRAMES &&
        root !== tonicPitchClass
      ) {
        const fromFifths = tonicPitchClass !== null ? PC_TO_FIFTHS_IDX[tonicPitchClass] : 0;
        const toFifths = PC_TO_FIFTHS_IDX[root];
        const delta = ((toFifths - fromFifths + 6) % 12) - 6;  // shortest path on circle
        animFromRef.current = (toFifths - delta) * ((2 * Math.PI) / 12);
        animToRef.current = toFifths * ((2 * Math.PI) / 12);
        animStartRef.current = performance.now();
        setTonicPitchClass(root);
        pendingRootRef.current = null;
      }
    }
  }, [currentTime, hviz, setFrame, tonicPitchClass, setTonicPitchClass]);

  // Key change rotation animation (runs independently of audio clock)
  useEffect(() => {
    const animate = (now: number) => {
      if (animStartRef.current !== null) {
        const elapsed = (now - animStartRef.current) / 1000;
        const t = Math.min(elapsed / KEY_CHANGE_DURATION_S, 1);
        const eased = t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t;  // ease in-out quad
        setHelixRotationOffset(
          animFromRef.current + (animToRef.current - animFromRef.current) * eased,
        );
        if (t >= 1) animStartRef.current = null;
      }
      rafRef.current = requestAnimationFrame(animate);
    };
    rafRef.current = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(rafRef.current);
  }, [setHelixRotationOffset]);
}
