import re, sys
import bpy

# Find the Looking Glass addon module
LookingGlassAddon = [module for (name,module) in sys.modules.items()
     if name.endswith('looking_glass_global_variables')][0].LookingGlassAddon

window = LookingGlassAddon.lightfieldWindow

import subprocess

def run(args):
    print(' '.join(args))
    return subprocess.run(args, check=True, capture_output=True).stdout

def place_window(window):
    dev = LookingGlassAddon.deviceList[0]
    
    for windowid in run('xdotool search --classname Blender'.split()).split():
        windowid = windowid.decode('ascii')
        # Check if this is the window
        geometry = run(['xdotool', 'getwindowgeometry', '--shell', windowid])
        geometry = {k.decode('ascii'): int(v) for (k,v) in 
                    [r.split(b'=',1) for r in geometry.lower().split(b'\n') if b'=' in r]}
        print(geometry)
        for attr in 'x y width height'.split():
            if getattr(window,attr) != geometry[attr]:
                continue
        else:
            # This window is a match!
            run(['xdotool', 'set_window', '--name', 'Blender Looking Glass', windowid,
                'windowmove', windowid, str(dev['x']), str(dev['y']),
                # Setting the size is meaningless because the shader doesn't know about window decorations etc
                #'windowsize', windowid, str(dev['width']), str(dev['height']),
                ])
            # Fullscreen it - TODO: find out how to set rather than toggle
            bpy.ops.wm.window_fullscreen_toggle(dict(window=LookingGlassAddon.lightfieldWindow))

place_window(window)
