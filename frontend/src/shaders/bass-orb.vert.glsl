// Phase 4 — Bass Orb SH displacement vertex shader
// TODO Phase 4: implement Y_l^m vertex displacement
void main() {
  gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
}
