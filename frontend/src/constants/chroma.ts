/**
 * CHROMA_COLOR — canonical pitch-class to color mapping.
 *
 * 12 hues evenly distributed across the OKLCH wheel in ~29° steps.
 * Lightness tuned per region: yellows pulled down (harsh on dark), blues/purples
 * lifted (naturally darker). Chroma kept high throughout for vibrancy on black.
 *
 * Format: oklch(lightness% chroma hue°) — perceptually uniform, safe for lerp.
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
 *   - CHROMA_RGB below: pre-converted [r,g,b] for GLSL uniforms
 */
export const CHROMA_COLOR: readonly string[] = [
  "oklch(68% 0.22  29°)",    //  0  C    — warm scarlet
  "oklch(70% 0.22  58°)",    //  1  C#   — deep orange
  "oklch(73% 0.18  85°)",    //  2  D    — golden yellow
  "oklch(70% 0.20 113°)",    //  3  D#   — lime / chartreuse
  "oklch(68% 0.21 145°)",    //  4  E    — spring green
  "oklch(66% 0.20 173°)",    //  5  F    — emerald / teal
  "oklch(68% 0.20 200°)",    //  6  F#   — cornflower sky
  "oklch(67% 0.21 228°)",    //  7  G    — royal blue
  "oklch(65% 0.22 258°)",    //  8  G#   — violet-indigo
  "oklch(65% 0.22 290°)",    //  9  A    — rich purple
  "oklch(67% 0.23 320°)",    // 10  A#   — hot pink / fuchsia
  "oklch(68% 0.21 350°)",    // 11  B    — rose-crimson
] as const;

/**
 * CHROMA_RGB — pre-converted linear-sRGB [r, g, b] triples (0–1) for passing
 * as vec3 uniforms to GLSL shaders. Computed once at module load from CHROMA_COLOR
 * via the browser's CSS color parsing pipeline.
 *
 * Usage in a React component:
 *   const color = new THREE.Color(...CHROMA_RGB[pitchClass]);
 */
export const CHROMA_RGB: readonly [number, number, number][] = (() => {
  if (typeof document === "undefined") {
    // SSR / Node fallback — return unit white; real values come from the browser
    return Array(12).fill([1, 1, 1]) as [number, number, number][];
  }
  const canvas = document.createElement("canvas");
  canvas.width = canvas.height = 1;
  const ctx = canvas.getContext("2d")!;
  return CHROMA_COLOR.map((css) => {
    ctx.clearRect(0, 0, 1, 1);
    ctx.fillStyle = css;
    ctx.fillRect(0, 0, 1, 1);
    const [r, g, b] = ctx.getImageData(0, 0, 1, 1).data;
    return [r / 255, g / 255, b / 255] as [number, number, number];
  });
})();

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
