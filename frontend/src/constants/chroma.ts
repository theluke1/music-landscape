/**
 * CHROMA_COLOR — canonical pitch-class to color mapping.
 *
 * !! TODO: Replace placeholder values with your personal associations !!
 *
 * Format: OKLCH strings — perceptually uniform, safe for linear interpolation.
 * oklch(lightness% chroma hue°)
 *
 * Index = pitch class:
 *   0=C, 1=C#, 2=D, 3=D#, 4=E, 5=F,
 *   6=F#, 7=G, 8=G#, 9=A, 10=A#, 11=B
 *
 * This constant is used by:
 *   - PitchHelix: node and particle color
 *   - BassOrbShell: nodal line tint (mixed with chord quality color)
 *   - PercussionCrystals: not used (instrument-specific colors there)
 *   - ChladniFloor: not used directly
 *   - Debug overlay: note label colors
 */
export const CHROMA_COLOR: readonly string[] = [
  "oklch(65% 0.20   0°)",    //  0  C       — PLACEHOLDER
  "oklch(60% 0.22  30°)",    //  1  C#/Db   — PLACEHOLDER
  "oklch(70% 0.18  60°)",    //  2  D        — PLACEHOLDER
  "oklch(65% 0.20  90°)",    //  3  D#/Eb   — PLACEHOLDER
  "oklch(75% 0.16 120°)",    //  4  E        — PLACEHOLDER
  "oklch(60% 0.22 150°)",    //  5  F        — PLACEHOLDER
  "oklch(55% 0.24 180°)",    //  6  F#/Gb   — PLACEHOLDER
  "oklch(65% 0.20 210°)",    //  7  G        — PLACEHOLDER
  "oklch(60% 0.22 240°)",    //  8  G#/Ab   — PLACEHOLDER
  "oklch(65% 0.20 270°)",    //  9  A        — PLACEHOLDER
  "oklch(60% 0.22 300°)",    // 10  A#/Bb   — PLACEHOLDER
  "oklch(55% 0.20 330°)",    // 11  B        — PLACEHOLDER
] as const;

/**
 * CHROMA_HUE_DEG — hue angle only (degrees), for use in GLSL uniforms.
 * Parsed from CHROMA_COLOR at startup — do not edit directly.
 */
export const CHROMA_HUE_DEG: readonly number[] = CHROMA_COLOR.map((s) => {
  const m = s.match(/oklch\([^)]+\s+([\d.]+)°\)/);
  return m ? parseFloat(m[1]) : 0;
});

/**
 * Circle of fifths index → pitch class mapping.
 * Spatially adjacent positions on the helix are harmonically close.
 *
 *   Fifths order: C G D A E B F# Db Ab Eb Bb F
 *   Index:        0 1 2 3 4 5  6  7  8  9 10 11
 */
export const FIFTHS_ORDER: readonly number[] = [0, 7, 2, 9, 4, 11, 6, 1, 8, 3, 10, 5];

/** Reverse map: pitch class → fifths index (for helix angle computation) */
export const PC_TO_FIFTHS_IDX: readonly number[] = (() => {
  const arr = new Array<number>(12);
  FIFTHS_ORDER.forEach((pc, i) => { arr[pc] = i; });
  return arr;
})();
