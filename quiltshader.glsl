// mpv glsl shader hook for looking glass
// Usage sample:
//  mpv --screen=1 --fs-screen=1 --fs --glsl-shader=quiltshader.glsl --no-keepaspect *.mp4

//!HOOK MAINPRESUB
//!DESC Looking Glass Quilt renderer
//!BIND HOOKED
//!WIDTH 2560
//!HEIGHT 1600

// TODO: Fill these in from HID calibration data.
const float tilt = -0.12039111681976107; //{tilt};
const float pitch = 370.66407267416486; //{pitch};
const float center = 0.13695651292800903; //{center};
const float subp = 1.0 / (3*2560); //{subp};

// FIXME: I have two layers of errors in this rendering.
// First it has severe colour shifts. 
// Second it has discontinuities suggesting the tile mapping is badly ordered.
// Thirdly, not all the streams are 5x9 quilts.
// For instance Baby* is 4x8

const float quilt_width = 5;
const float quilt_height = 9;
const float quilt_stride = 1.0 / quilt_height;
const vec2 quilt_scale = vec2 (1.0/quilt_width, 1.0/quilt_height);

vec2 quilt_map(vec2 pos, float a) {
  vec2 tile = vec2(0,0);
  a = fract(a)*quilt_width;
  tile.y = floor(a) * quilt_scale.y;
  tile.x = floor(mod(a*quilt_height, quilt_width)) * quilt_scale.x;
  return fma(pos, quilt_scale, tile);
}

vec4 hook() {
  vec4 res;
  float a;
  a = (HOOKED_pos.x + HOOKED_pos.y*tilt)*pitch - center;
  res.x = HOOKED_tex(quilt_map(HOOKED_pos, a)).x;
  res.y = HOOKED_tex(quilt_map(HOOKED_pos, a+subp)).y;
  res.z = HOOKED_tex(quilt_map(HOOKED_pos, a+2*subp)).z;
  res.w = 1.0;
  return res;
}

