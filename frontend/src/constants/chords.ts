/**
 * Chord quality → OKLCH color.
 * Used by BassOrbShell nodal lines and atmosphere tint.
 *
 * Design rationale:
 *   Major    → warm amber/gold    (stable, open)
 *   Minor    → cool violet        (introspective)
 *   Dom7     → orange-red         (tension, wants to resolve)
 *   Maj7     → pale gold          (lush, jazzy)
 *   Min7     → blue-violet        (moody)
 *   Dim      → deep crimson       (maximum tension)
 *   Aug      → teal               (ambiguous, floating)
 *   HDim7    → dark magenta       (diminished + minor)
 *   Sus2/4   → neutral grey-blue  (suspended, unresolved but not tense)
 */
import type { ChordQuality } from "../types/hviz";

export const CHORD_COLOR: Record<ChordQuality, string> = {
  maj:   "oklch(75% 0.18  85°)",   // amber/gold
  min:   "oklch(55% 0.22 300°)",   // violet
  dom7:  "oklch(65% 0.25  45°)",   // orange-red
  maj7:  "oklch(80% 0.14  90°)",   // pale gold
  min7:  "oklch(50% 0.20 280°)",   // blue-violet
  dim:   "oklch(45% 0.28  20°)",   // crimson
  aug:   "oklch(60% 0.20 185°)",   // teal
  hdim7: "oklch(45% 0.25 330°)",   // dark magenta
  sus2:  "oklch(60% 0.10 240°)",   // neutral grey-blue
  sus4:  "oklch(60% 0.10 230°)",   // neutral grey-blue
};

export const CHORD_COLOR_FALLBACK = "oklch(50% 0.00 0°)";  // neutral grey
