import json
import re
import struct
import subprocess

# Note: Use libhidapi-hidraw, i.e. hidapi with hidraw support,
# or the joystick device will be gone when execution finishes.
import hidapi

class LookingGlassHID:
    def __init__(self, vendor_id=0x04d8, product_id=0xef7e, product_string=u'HoloPlay'):
        for dev in hidapi.enumerate(vendor_id=vendor_id, product_id=product_id):
            if dev.product_string == product_string:
                self.hiddev = hidapi.Device(dev)
                self.calibration = self.loadconfig()
                self.calculate_derived()
                break
        else:
            raise IOError("Looking Glass HID device not found")

    def flush(self):
        "Reads leftover HID data"
        more=True
        while more:
            more = self.hiddev.read(68, blocking=False, timeout_ms=100)

    def loadconfig(self):
        "Loads calibration JSON from LG HID"
        jsonlen = struct.unpack('>I', self.readpage(0, 4))[0] + 4
        assert jsonlen != 0xffffffff
        data = bytearray()
        while len(data) < jsonlen:
            page = len(data)//64
            l = min(64, jsonlen-64*page)
            data[64*page:] = self.readpage(page, l)
        return json.loads(data[4:].decode('ascii'))

    def calculate_derived(self):
        # Parse odd value-object format from json
        cfg = {key: value['value'] if isinstance(value, dict) else value for (key,value) in self.calibration.items()}
        # Calculate derived parameters
        cfg['tilt'] = cfg['screenH'] / cfg['screenW'] * cfg['slope']
        # Store configuration
        self.configuration = cfg

    def get_buttons(self):
        """Reads buttons (4 bits) from LG HID (blocking!)"""
        r = self.hiddev.read(68, blocking=True)
        if len(r)<68:
            r += self.hiddev.read(68-len(r), blocking=False)
            if r:
                byte = r[0]
                # Python 2 compatibility
                if isinstance(byte, str):
                    byte = ord(byte)
                return byte

    def readpage(self, addr=0, size=64):
        send = bytearray(struct.pack('>BH64x', 0, addr))
        self.hiddev.send_feature_report(send, b'\0')
        r = bytearray(self.hiddev.read(1+1+2+64, timeout_ms=1000))
        while r[1:4] != send[:3]:
            r = bytearray(self.hiddev.read(1+1+2+64, timeout_ms=1000))
        if len(r) < 1+1+2+64:
            r += bytearray(self.hiddev.read(1+1+2+64-len(r), timeout_ms=10))
        # First byte holds button bitmask
        # second byte is command for EEPROM management (0=read)
        # third and fourth are EEPROM page address
        # Verify 1:4 so we are reading the correct data
        assert r[1:4] == send[:3]
        return r[4:4+size]

    def shader(self, target='mpv', **extra):
        return shaders[target].format(**self.configuration, **extra)

    def screen(self):
        # Try to find the Looking Glass monitor
        monitors = subprocess.run(["xrandr", "--listactivemonitors"], capture_output=True, text=True).stdout
        for m in re.finditer(r'^ (?P<screen>[0-9]+): \S+ (?P<w>\d+)/\d+x(?P<h>\d+)/\d+\+(?P<x>\d+)\+(?P<y>\d+)\s+(?P<connector>\S+)',
                             monitors, re.MULTILINE):
            m = {k: int(v) if v.isdecimal() else v for (k,v) in m.groupdict().items()}
            if (m['w'] == self.configuration['screenW'] and
                m['h'] == self.configuration['screenH']):
                # TODO: Double-check EDID
                return m
        else:
            raise IOError("Can't find matching screen")


shaders = {'mpv': """
// mpv glsl shader hook for looking glass
// Usage sample:
//  mpv --screen=1 --fs-screen=1 --fs --glsl-shader=quiltshader.glsl --no-keepaspect *.mp4
// Decent sample frame: Holo Reality at 26 seconds, -ss 26 Holo*.mp4

//!HOOK MAINPRESUB
//!DESC Looking Glass Quilt renderer
//!BIND HOOKED
//!WIDTH {screenW}
//!HEIGHT {screenH}

// TODO: Fill these in from HID calibration data.
const float tilt = - {screenH}/{screenW} / {slope};
const float pitch = {screenW}/{DPI} * {pitch} * sin(atan({slope}));
const float center = fract({center} + tilt*pitch);
const float subp = 1.0 / (3*{screenW}) * pitch;

// not all the streams are 5x9 quilts.
// For instance Baby* is 4x8

const vec2 tiles = vec2({tilesX},{tilesY});

vec2 quilt_map(vec2 pos, float a) {{
  // Y major positive direction, X minor negative direction
  vec2 tile = vec2(tiles.x-1,0), dir=vec2(-1,1);
  a = fract(a)*tiles.y;
  tile.y += dir.y*floor(a);
  a = fract(a)*tiles.x;
  tile.x += dir.x*floor(a);
  return (tile+pos)/tiles;
}}

vec4 hook() {{
  vec4 res;
  float a;
  a = (HOOKED_pos.x + HOOKED_pos.y*tilt)*pitch - center;
  res.r = HOOKED_tex(quilt_map(HOOKED_pos, a)).r;
  res.g = HOOKED_tex(quilt_map(HOOKED_pos, a+subp)).g;
  res.b = HOOKED_tex(quilt_map(HOOKED_pos, a+2*subp)).b;
  res.a = 1.0;
  return res;
}}
""",
}

if __name__ == '__main__':
    from pprint import pprint

    lg = LookingGlassHID()

    from sys import argv

    if not argv[1:] or argv[1:] == ["calibration"]:
        pprint(lg.calibration)

    if argv[1:] == ["buttons"]:
        print("Reading buttons:")
        while True:
            print('\r{:04b}'.format(lg.get_buttons()), end='', flush=True)

    # TODO: mpv wrapper
    if argv[1:2] == ['mpv']:
        # Sizes: 4x8, 5x9
        import tempfile
        screen = lg.screen()

        # TODO: parameterise quilt size
        with tempfile.NamedTemporaryFile(mode='w', suffix='.glsl') as f:
            f.write(lg.shader('mpv', tilesX=4, tilesY=8))
            f.flush()

            subprocess.call(argv[1:2] + ['--geometry={w}x{h}+{x}+{y}'.format(**screen), '--fs',
                                         '--glsl-shader='+f.name, '--no-keepaspect'] + argv[2:])
