/**
 * Phase 5 — Percussion Sky Crystals
 *
 * DLA crystal structures erupting from the scene boundary, growing inward.
 * Per-instrument spawn arc, color, branching angle, and decay rate.
 *
 * Instrument config:
 *   kick:     bottom boundary, deep red,   wide/smooth,  slow 2s decay
 *   snare:    left+right sides, white,     medium,       0.8s decay
 *   hihat:    top corners, cyan,           tight/sharp,  fast 0.2s decay
 *   cymbal:   full top arc, gold,          wide sweep,   3s shimmer
 *   softperc: any, soft purple,            Voronoi ripple, medium decay
 *
 * Hit sharpness → branching angle tightness:
 *   sharpness ≈ 1 → needle-like spikes
 *   sharpness ≈ 0 → rounded Voronoi cell expansion
 *
 * TODO Phase 5: implement (GPU DLA via WebGPU compute shader, WebGL ping-pong fallback)
 */

export function PercussionCrystals() {
  // TODO Phase 5
  return null;
}
