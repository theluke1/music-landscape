// Phase 4 — Bass Orb nodal line fragment shader
// TODO Phase 4: implement nodal line detection + chord quality color
uniform vec3 u_nodalColor;
void main() {
  gl_FragColor = vec4(u_nodalColor, 1.0);
}
