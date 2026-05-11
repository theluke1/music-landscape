/**
 * Phase 3 — Pitch Helix Constellation
 *
 * The melody as a morphing 3D particle network.
 * Each MIDI note maps to a node on a helix arranged by circle-of-fifths angle.
 * Active notes connect with Catmull-Rom spline particle tubes.
 *
 * Key behaviors:
 *   - Node color = CHROMA_COLOR[pitch_class]
 *   - Node brightness = velocity
 *   - Whole helix rotates azimuthally on key change (helixRotationOffset from store)
 *   - snap lerp factor = mix(SNAP_LERP_MIN, SNAP_LERP_MAX, melody.attack)
 *   - Held notes: connection "ripples" — never static
 *   - Breath oscillation along helix axis
 *
 * TODO Phase 3: implement
 */

export function PitchHelix() {
  // TODO Phase 3
  return null;
}
