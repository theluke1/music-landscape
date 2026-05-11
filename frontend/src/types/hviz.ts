/**
 * TypeScript types for the .hviz feature file format.
 * Canonical spec: /hviz-spec.md
 */

export interface HvizMeta {
  title: string;
  duration_s: number;
  fps: number;
  stem_sr: number;
  version: string;
}

export interface MelodyFrame {
  midi: number | null;
  pitch_hz: number | null;
  conf: number;
  vel: number;
  /** 0 = legato, 1 = hard attack — drives helix snap speed */
  attack: number;
}

export interface BassFrame {
  midi: number | null;
  pitch_hz: number | null;
  octave: number | null;
  pitch_class: number | null;
  conf: number;
  vel: number;
  /** 0 = legato, 1 = hard attack — drives SH orb snap speed */
  attack_sharpness: number;
}

export type ChordQuality =
  | "maj" | "min" | "dom7" | "maj7" | "min7"
  | "dim" | "aug" | "hdim7" | "sus2" | "sus4";

export interface ChordFrame {
  root: number | null;       // pitch class 0–11
  quality: ChordQuality | null;
  conf: number;
}

export interface DrumSharpness {
  kick: number;
  snare: number;
  hihat: number;
  cymbal: number;
  softperc: number;
}

export interface DrumFrame {
  kick: number;
  snare: number;
  hihat: number;
  cymbal: number;
  softperc: number;
  sharpness: DrumSharpness;
}

export interface PerceptualFrame {
  energy: number;    // → particle speed, bloom intensity
  valence: number;   // → warm/cool color temperature bias
  tension: number;   // → camera shake, field turbulence
  density: number;   // → atmosphere particle count, mist thickness
}

export interface HvizFrame {
  t: number;
  melody: MelodyFrame;
  bass: BassFrame;
  chord: ChordFrame;
  drums: DrumFrame;
  /** 12-dim chroma vector, normalised, index = pitch class */
  chroma: [number, number, number, number, number, number,
           number, number, number, number, number, number];
  /** 128 mel-scale bins, normalised 0–1 — for Chladni floor shader */
  spectrogram_row: number[];
  perceptual: PerceptualFrame;
}

export interface HvizSegment {
  start: number;
  end: number;
  label: string;
}

export interface HvizFile {
  meta: HvizMeta;
  frames: HvizFrame[];
  segments: HvizSegment[];
}
