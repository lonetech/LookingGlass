from pprint import pprint
import json
import struct

# Note: Use libhidapi-hidraw, i.e. hidapi with hidraw support,
# or the joystick device will be gone when execution finishes.
import hidapi

pagesize = 64


def rp(dev, addr=0, size=64):
    send = bytearray(struct.pack('>BH64x', 0, addr))
    dev.send_feature_report(send, b'\0')
    r = bytearray(dev.read(1+1+2+64, 1000))
    #print("read: ", len(r), r)
    # First byte holds button bitmask
    # second byte is command for EEPROM management (0=read)
    # third and fourth are EEPROM page address
    # Verify 1:4 so we are reading the correct data
    assert r[1:4] == send[:3]
    return r[4:4+size]


def loadconfig(dev):
    jsonlen = struct.unpack('>I', rp(dev, 0, 4))[0] + 4
    assert jsonlen != 0xffffffff
    #print jsonlen
    json = bytearray()
    while len(json) < jsonlen:
        page = len(json)//64
        l = min(64, jsonlen-64*page)
        json[64*page:] = rp(dev, page, l)
        #print json
    return json[4:]


def read_eeprom(devinfo):
    dev = hidapi.Device(devinfo)
    cfg = json.loads(loadconfig(dev).decode('ascii'))
    pprint(cfg)
    # TODO: Use calibration data. Sample code in lgdisplaytest.py
    return (dev, cfg)


for dev in hidapi.enumerate(vendor_id=0x04d8, product_id=0xef7e):
    if dev.product_string == u'HoloPlay':
        hiddev, cfg = read_eeprom(dev)
        while True:
            # Keep reading the button bitmask
            r = hiddev.read(1)
            if r:
                byte = r[0]
                # Python 2 compatibility
                if isinstance(byte, str):
                    byte = ord(byte)
                print('{:04b}'.format(byte))
