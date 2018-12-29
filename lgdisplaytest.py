#! /usr/bin/env python3

# Run with DISPLAY=:0.1 to place on screen 1
# (you can check with xdpyinfo that your LG is that screen)
# DISPLAY=:0.1 xrandr --listmonitors --verbose
# That shows the EDID, which should include the name. 
# Mine is named: Toshiba LKG01Do12HjQE
# LKG01 is likely identifying Looking Glass.

import json
import pygame
from math import *

lgeeprom = json.load(open("lookingglasseeprom.json"))
def v(n):
    return lgeeprom[n]['value']

# Panel resolution
size = (int(v('screenW')), int(v('screenH')))
# Physical image width
screenInches = size[0]/v('DPI')
pitch = v('pitch') * screenInches * cos(atan(1.0/v('slope')))
tilt = size[1]/(size[0]*v('slope'))
subp = 1.0 / (3*size[0])
center = v('center')

# Note: The tilt applies to the lenses, so 
# the transition from one view to the next is not a 
# vertical line! 

pygame.init()

screen = pygame.display.set_mode(size, pygame.FULLSCREEN)
pygame.mouse.set_visible(False)
surface = pygame.display.get_surface()

surface.fill(pygame.Color('red'))

def frac(n):
    return n - floor(n)

# Next task: Calculate per-pixel colours.
for y in range(size[1]):
    # Flip because Pygame has Y going down, GL has Y going up
    ty = 1-float(y)/size[1]
    for x in range(size[0]):
        rgb=[x%256,y%256,0]
        tx = float(x)/size[0]
        for i in range(3):
            a = (tx + i*subp + ty*tilt) * pitch - center
            # Sample view: white if viewed from right,
            # black if viewed from left, 
            # disturbing if viewed head on
            rgb[i] = 255 if frac(a)<0.5 else 0
        surface.set_at((x,y), pygame.Color(*rgb))
pygame.display.update()

while True:
    e = pygame.event.wait()
    if e.type in (pygame.QUIT, pygame.KEYDOWN):
        break

