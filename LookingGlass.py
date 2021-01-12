import json
import struct

# Note: Use libhidapi-hidraw, i.e. hidapi with hidraw support,
# or the joystick device will be gone when execution finishes.
import hidapi

class LookingGlassHID:
    def __init__(self, vendor_id=0x04d8, product_id=0xef7e, product_string=u'HoloPlay'):
        for dev in hidapi.enumerate(vendor_id=vendor_id, product_id=product_id):
            if dev.product_string == product_string:
                self.hiddev = hidapi.Device(dev)
                self.calibration = self.loadconfig()
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

if __name__ == '__main__':
    from pprint import pprint

    lg = LookingGlassHID()
    pprint(lg.calibration)
    print("Reading buttons:")
    while True:
        print('\r{:04b}'.format(lg.get_buttons()), end='', flush=True)
