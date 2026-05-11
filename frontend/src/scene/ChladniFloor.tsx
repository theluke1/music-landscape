/**
 * Phase 6 — Chladni Standing Wave Floor
 *
 * Shader-based rectangular plate simulation.
 *
 * f(x,y) = cos(n·πx/a)·cos(m·πy/b) − cos(m·πx/a)·cos(n·πy/b)
 *
 * n, m driven by dominant frequency bins from spectrogram_row.
 * Nodal lines (f≈0) rendered bright white; antinodes dark.
 * Updates every frame on GPU — no mesh subdivision needed.
 *
 * Also contains:
 *   - Waveform ribbon at front edge
 *   - Atmosphere mist particles (other stem energy → density)
 *
 * TODO Phase 6: implement
 */

export function ChladniFloor() {
  // TODO Phase 6
  return null;
}
