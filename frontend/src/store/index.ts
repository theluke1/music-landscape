/**
 * Global Zustand store — single source of truth for musical state per frame.
 *
 * Updated each animation frame by useAudioClock → useFeatureFrame.
 * All scene components read from here; nothing passes props down the tree.
 */

import { create } from "zustand";
import type { HvizFile, HvizFrame, HvizMeta } from "../types/hviz";

interface MusicalState {
  // Job (set once upload + processing completes)
  jobId: string | null;

  // Feature data
  hviz: HvizFile | null;
  frame: HvizFrame | null;

  // Playback
  isPlaying: boolean;
  currentTime: number;   // seconds (from AudioContext.currentTime)
  frameIndex: number;

  // Derived tonal state (updated by useFeatureFrame)
  tonicPitchClass: number | null;  // detected key center, 0–11
  helixRotationOffset: number;     // azimuthal rotation for key change animation, radians

  // Actions
  setJobId: (id: string) => void;
  loadHviz: (data: HvizFile) => void;
  setPlaying: (v: boolean) => void;
  setCurrentTime: (t: number) => void;
  setFrame: (frame: HvizFrame, index: number) => void;
  setTonicPitchClass: (pc: number | null) => void;
  setHelixRotationOffset: (r: number) => void;
}

export const useMusicalStore = create<MusicalState>((set) => ({
  jobId: null,
  hviz: null,
  frame: null,
  isPlaying: false,
  currentTime: 0,
  frameIndex: 0,
  tonicPitchClass: null,
  helixRotationOffset: 0,

  setJobId: (id) => set({ jobId: id }),
  loadHviz: (data) => set({ hviz: data }),
  setPlaying: (v) => set({ isPlaying: v }),
  setCurrentTime: (t) => set({ currentTime: t }),
  setFrame: (frame, index) => set({ frame, frameIndex: index }),
  setTonicPitchClass: (pc) => set({ tonicPitchClass: pc }),
  setHelixRotationOffset: (r) => set({ helixRotationOffset: r }),
}));
