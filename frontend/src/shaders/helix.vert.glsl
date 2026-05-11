// Phase 3 — Pitch Helix particle vertex shader
// TODO Phase 3: implement
void main() {
  gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
  gl_PointSize = 4.0;
}
