import math
import sys
import json

# Call with the following arguments:
# python shadergen.py [views_x] [views_y] [calibration.json]

# Generates glsl shader file based on visual calibration file
calib = json.load(open(sys.argv[3]))

def v(n):
    return calib[n]['value']

views_x = sys.argv[1] 
views_y = sys.argv[2]
# Panel resolution
size = (int(v('screenW')), int(v('screenH')))
# Physical image width
screenInches = size[0]/v('DPI')
pitch = v('pitch') * screenInches * math.cos(math.atan(1.0/v('slope')))
tilt = size[1]/(size[0]*v('slope'))
subp = 1.0 / (3*size[0]) * pitch
center = v('center')

shader_text = '''
//!HOOK MAINPRESUB
//!DESC Looking Glass Quilt renderer
//!BIND HOOKED
//!WIDTH ''' + str(size[0]) + '''
//!HEIGHT ''' + str(size[1]) + '''

const float pitch = '''+str(pitch)+''';
const float center = '''+str(center)+''';
const float tilt = '''+str(tilt)+''';
const float subp = '''+str(subp)+''';

const vec2 tiles = vec2('''+str(float(views_x))+''','''+str(float(views_y))+''');

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
  a = (HOOKED_pos.x + (1.0 - HOOKED_pos.y)*tilt)*pitch - center;
  res.x = HOOKED_tex(quilt_map(HOOKED_pos, a)).x;
  res.y = HOOKED_tex(quilt_map(HOOKED_pos, a+subp)).y;
  res.z = HOOKED_tex(quilt_map(HOOKED_pos, a+2*subp)).z;
  res.w = 1.0;
  return res;
}
'''
print(shader_text)
