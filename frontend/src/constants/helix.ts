/**
 * Helix geometry constants — Phase 3.
 *
 * All positions computed as:
 *   x = HELIX_RADIUS * cos(fifthsIdx * TWO_PI / 12)
 *   y = octave * HELIX_HEIGHT_PER_OCTAVE
 *   z = HELIX_RADIUS * sin(fifthsIdx * TWO_PI / 12)
 *
 * Key change: rotate the helix's azimuthal origin by Δfifths_idx * (2π/12).
 * This makes every node move, not just recolor — the whole constellation shifts.
 */

export const HELIX_RADIUS = 2.5;
export const HELIX_HEIGHT_PER_OCTAVE = 1.2;
export const HELIX_MIDI_MIN = 21;   // A0
export const HELIX_MIDI_MAX = 108;  // C8

/** Key change animation duration in seconds */
export const KEY_CHANGE_DURATION_S = 0.8;

/**
 * Snap lerp factor based on attack_sharpness (0–1).
 * Hard attack (sharpness≈1) → near-instant snap.
 * Legato (sharpness≈0) → very slow morph.
 *
 * lerpFactor = mix(0.004, 0.85, attack_sharpness)
 * Applied per frame: current = lerp(current, target, lerpFactor)
 */
export const SNAP_LERP_MIN = 0.004;   // ~0.4% per frame at 60fps ≈ 500ms
export const SNAP_LERP_MAX = 0.85;    // ~85% per frame ≈ 10–15ms snap
