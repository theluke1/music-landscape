/**
 * Phase 4 — Spherical Harmonics Bass Orbs
 *
 * 3 concentric shells of orbs, each deformed by real spherical harmonics Y_l^m.
 * Every unique bass note → a unique atomic orbital shape.
 *
 * Mapping:
 *   l = clamp(bass_octave - 1, 0, 5)
 *   m = pitch_class_to_m(bass_pitch_class, l)   (maps pc 0–11 into -l..l)
 *
 * Shell radii: 1.2, 1.8, 2.6 (inner=fundamental, mid=2nd harmonic, outer=3rd)
 *
 * Key behaviors:
 *   - SH shape snap speed driven by bass.attack_sharpness (same lerp formula as helix)
 *   - Nodal lines (where Y_l^m ≈ 0) highlighted bright
 *   - Nodal line color = CHORD_COLOR[chord.quality]
 *   - Orb radius pulses with bass.vel
 *
 * TODO Phase 4: implement
 */

export function BassOrbShell() {
  // TODO Phase 4
  return null;
}
