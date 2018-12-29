from pprint import pprint
import json
import struct

import hid

def rp(dev, addr=0, size=64):
    send = bytearray(struct.pack('>BBH64x', 0, 0, addr))
    #print repr(send)
    #print len(send)
    dev.send_feature_report(send)
    r = bytearray(dev.read(64, 1000))
    r += bytearray(dev.read(3+1, 1000))
    #print "read: ", len(r), r
    assert r[:4] == send[:4]
    return r[4:4+size]

def loadconfig(dev):
    jsonlen=struct.unpack('>I',rp(dev, 0, 4))[0] + 4
    assert jsonlen != 0xffffffff
    #print jsonlen
    json=bytearray()
    while len(json)<jsonlen:
        page=len(json)//64
        l=min(64,jsonlen-64*page)
        json[64*page:] = rp(dev, page, l)
        #print json
    return json[4:]

def read_eeprom(devinfo):
    dev = hid.device()
    dev.open_path(devinfo['path'])
    dev.set_nonblocking(1)
    #r=True
    #while r:
    #    r = bytearray(dev.read(64+3+1, 1000))
    #    #print r
    cfg = json.loads(loadconfig(dev).decode('ascii'))
    pprint(cfg)
    return cfg

for dev in hid.enumerate(vendor_id=0x04d8, product_id=0xef7e):
    if dev['product_string'] == u'HoloPlay':
        read_eeprom(dev)

