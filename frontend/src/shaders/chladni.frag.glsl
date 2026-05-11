// Phase 6 — Chladni floor fragment shader
// f(x,y) = cos(n·πx/a)·cos(m·πy/b) − cos(m·πx/a)·cos(n·πy/b)
// TODO Phase 6: implement with n, m driven by spectrogram_row dominant bins

uniform float u_n;
uniform float u_m;
uniform float u_time;

varying vec2 vUv;

const float PI = 3.14159265358979;

void main() {
  float x = vUv.x;
  float y = vUv.y;
  float f = cos(u_n * PI * x) * cos(u_m * PI * y)
          - cos(u_m * PI * x) * cos(u_n * PI * y);
  float brightness = smoothstep(0.0, 0.08, abs(f));  // bright near nodal lines
  gl_FragColor = vec4(vec3(1.0 - brightness), 1.0);
}
