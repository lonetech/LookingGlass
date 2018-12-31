// mpv glsl shader hook for looking glass
// Usage sample:
//  mpv --screen=1 --fs-screen=1 --fs --glsl-shader=quiltshader.glsl --no-keepaspect *.mp4
// Decent sample frame: Holo Reality at 26 seconds, -ss 26 Holo*.mp4

//!HOOK MAINPRESUB
//!DESC Looking Glass Quilt renderer
//!BIND HOOKED
//!WIDTH 2560
//!HEIGHT 1600

// TODO: Fill these in from HID calibration data.
const float tilt = -0.12039111681976107; //{tilt};
const float pitch = 370.66407267416486; //{pitch};
const float center = 0.5 + 0.13695651292800903; //{center};
const float subp = 1.0 / (3*2560) * pitch; //{subp};

// not all the streams are 5x9 quilts.
// For instance Baby* is 4x8

const vec2 tiles = vec2(5,9);

vec2 quilt_map(vec2 pos, float a) {
  // Y major positive direction, X minor negative direction
  vec2 tile = vec2(tiles.x-1,0), dir=vec2(-1,1);
  a = fract(a)*tiles.y;
  tile.y += dir.y*floor(a);
  a = fract(a)*tiles.x;
  tile.x += dir.x*floor(a);
  return (tile+pos)/tiles;
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

