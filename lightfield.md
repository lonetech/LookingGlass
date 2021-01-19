# Rendering concerns

The shader was originally written for MPV, which used texCoords 0..1 range. 
MPV didn't give access to hook the vertex shader. A more efficient shader 
is easily possible by moving calculations from the fragment shader 
to the vertex shader. 


Long Z distance between the optical surfaces; lenslet is thin, block is not.

We calculate $a$ as subpixel position across the lens. 
This doesn't take into account the distance in the thick block; the same lensing that alters the direction of the light also causes a displacement. Solution: displace the texture sampling by some factor of a. 


Dispersion

RGB may also divert by differing amounts. Try drawing a thin vertical line and see if its thickness varies with colour. 
This would simply be a distinct factor on a. https://en.wikipedia.org/wiki/Dispersion_(optics)


Coordinates across lenslet

Note: a is currently range 0..1 for the extremes of the views. This means 0.5 is central on the lens (straight forward). 
Both the factors above would be centered on that. 


3D effect of angled lenticular sheet

Another potentially interesting concern is that the direction is slanted. 
This means there is a Y dependence not just for where center is, but also what Y difference exists between the subpixel and eye. 


Index of refraction is generally lower for longer wavelengths. By how much may be different in the different materials. 
Snell's law applies at the surfaces. 


Interesting challenge: implement a light field rendering in Cycles. We could literally cast the rays per subpixel and generate the device specific frame instead of a quilt. Starting point: the raytracing modes for panoramic cameras. Second starting point: use_spherical_stereo in CameraStereoData. We can alter this with a linear superstereo mode. 


Quilt geometry: each is generally rendered for a particular viewpoint along a line. Currently we calculate the output angle then sample a tile linearly chosen based on that. Figure out what the relation actually is; I have a feeling there's a skew here. 
Because the outgoing angle for the extremes of one tile aren't the same at all; both are aimed at the same point. 
I think there's a fairly simple transformation that could be exploited here, without losing the perspective use. 
However, if it turns out to be linear that could be approximated already. 


Interesting concepts for light field rendering:
https://github.com/google/stereo-magnification - ML based extrapolation from stereo images.
That targets multiplane images; there's an extension that goes spherical plus depth for closer tracking of geometry. 
https://augmentedperception.github.io/deepviewvideo/

These are related formats, possibly more efficient than quilts. They rely on ray casting; for perspective, as used in a flat view, standard GPU geometry rendering helps. Possibly not the same when we have an actual light field output. 


Note: stereo magnification means we could actually get something nice out of the Evo. 


Notably, there are sample videos and a sample player available for inspection. (Probably need working webGL to show up.)

## Light field formats

I believe a good lightfield format for the Looking Glass is one OpenGL 3D texture, with the Z coordinate indicating horisontal camera position, and wrapping on. This would permit full interpolation. Wrapping because e.g. as you have the camera in front of an edge, half the image is outside the display; but that half is reusable for the mirrored position. This could also be stored as a layered image, e.g. MXR (multiview openexr) which blender supports, and be rendered as previously mentioned with proper acceleration. X coordinate means dx/dz, and Y coordinate remains position.

One could even use the wrapping to pick the middle perspective, which is a normal image (the only one, as all the others probably wrap), to be anywhere in the stack; that way default loading of the EXR as a single image would simply show a wide low resolution image. Actually, it's likely good in this format to alter the aspect ratio and have it use wide pixels. That of course hurts the pespective of the flat interpretation. 

Storage format doesn't need to have the wrap. Basically the format currently used is right, though it could be extended with the cropped views at the extremes. The distinction is simple to detect; if all images are the same size, the extremes are missing. If they start shrinking at the extremes, they have the closer edge (same direction the viewpoint has moved) in common with the main view. 

glCopyTexSubImage3D is our friend. It does have the slight downside that it can't do subpixel/texel adjustments; this means we may have a skew through the stack, even if we do straighten it as best we can. That skew should ideally be linear. 

Apparently the coordinates are called R, S and T. It is important that X be GL_REPEAT, though Y and Z may be good as GL_CLAMP_TO_BORDER. It's a minor thing; border clamp should be the least intensive and least artifacty. X and Y extremes are outside the proper view anyhow. We could clip ST a little if we want to eliminate the visible pixels outside the block. Z could clamp to edge also; it only applies to the extremes of angles, where the view breaks down anyway. 

## Calibration

I've already done a couple of tests, like rendering a fairly narrow strip. There are many more variants of interest:

1. Field of view test by convergence. Select a values based on floor(a), such that center lenslet is lit straight forward and extreme lenslets are lit inwards. This should converge as a line at some distance. That distance should help us find both the angle spread per lenslet and the dispersion by comparing the convergence for red, green and blue. 

This is also viewable and automatable by eye or small camera (suggest taking ezviz camera and finding the spot using macro slide). At the convergence line, the eye will see the entire screen lit up. If the entire screen lights up white, we have matched the convergence. 

2. Light up all subpixels under one lenslet. This should also indicate the same factors. 

3. Light a vertical band as I've already attempted. This should be usable to fine tune our displacement factors. 

4. Align subpixels to cancel out displacement from two-stage refraction

Think of how to map out the displacement of subpixels. This is a considerable factor and visible. 
Light up an a value close to the extremes (a far from 0.5). The points should spread out. 
Compensate by taking the perpendicular to lenslet offset from a=0.5, as vector, and multiply it by a factor. 
That factor is dependent on the colour and block depth. The factor may also be helpful in aligning output angles. 

Not sure precisely which of all these patterns will be easiest for each step. Should implement a panel for controlling the test mode, with interactive adjustment of widths of lines, which colours are lit, etc. 

Perhaps the first thing to adjust is lighting up a thin line in XY plane, and tuning off-axis factor to make that line converge visually. This would be a line at an angle compared to the lenslets; vertical may do. a=any, x in narrow range. This displacement needs to be applied to texture sampling coordinate. 

Displacement: ST = XY + vector_orthog(lensline) * B * (fract(a)-0.5)
Angle adjustment: view/R = C * (fract(a)-0.5) + 0.5
Missing factor: lensline is slanted so affects Y also. That must show up in view. 
Factor to consider: view selection should also be affected by X. Goal is that center view is visible at perspective viewpoint, not infinity. Essentially, match up constant R with convergence mode. This factor is like the one above, so can be combined. 
R += XY(from center) dot EF. 

When views have been rotated for alignment, in order to do 3D bilinear sampling, we will also need to change S dependent on a. For the moment, stick to the quilt format. Because the quilt format doesn't cover the full light field, we should clamp view/R to border, not edge. Then we expand it a little, probably, to get a crisp transition from image to black rather than junk, as we move out of the view region. 

Starting point: B=0, C=1, D=0, E=0, F=0. Some are likely different for RGB. 
These can be added as uniforms with defaults in the shader. 

# Blender plugin
## Window creation
Uses bpy.ops.wm.window_new_main. Implementation in wm_window_new_main_exec in wm_window.c. 
Fullscreen toggle op is adjacent. Op uses wm_window_copy_test, which does the Ghost creation during WM_check. 

GHOST_CreateWindow takes a geometry hint, which would be our probed screen. It also takes a window state, which would be Fullscreen.
It is called in wm_window_ghostwindow_add, called by wm_window_ghostwindow_ensure which doesn't take those arguments. 
It does however read them from wm_init_state. This is our path. 
WIN_OVERRIDE_GEOM and WIN_OVERRIDE_WINSTATE are the appropriate flags, and they are conveniently reset after window creation. 

We want to export Initial Window State API from WM_api.h and wm_window.c to Python. 

Operators can take arguments. So make optional arguments geometry and fullscreen for the op. 
For geometry format: mathutils.geometry uses "box is a list where the first 4 items are [x, y, width, height, …]"

Successfully wrote a patch to enable window creation in the right place. 
 https://developer.blender.org/D10132 


## GHOST screen support
Ghost can report number of screens, current screen geometry, and full desktop geometry. 
It can't report each screen. 

Minimal improvement: add capability to request information about one screen at a time. 
So rather than GHOST_GetMainDisplayDimensions call GHOST_GetDisplayInfo. 
Would this require a new struct?

There's more related calls in GHOST_DisplayManager, but its primary purpose is mode switching. 

The X11 version only has some vidmode support, needs adding xrandr (or xinerama?) support. Xinerama can get positions and sizes. Xrandr can additionally report EDIDs and set modes. XRRMonitorInfo has name and bounding box, but that name is likely the connector. The name we're looking for needs to be parsed from the EDID property. We don't need full parsing; the name comes after \0\0\0\xfc\0 and is 13 bytes. We only want a prefix check, so LKG pads it up to an 8 byte substring check. 

The Windows version actually already extracts display names, but doesn't pass them on, and doesn't know the positions. GetMonitorInfo can retrieve both name and placement. https://docs.microsoft.com/en-us/windows/win32/gdi/multiple-display-monitors-functions The mode thing in place now gets adapters, but it can also get monitor names with an extra call: https://docs.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-enumdisplaydevicesa
[17:25]LoneTech:there's a somewhat cryptic note about it and getting first the adapter name, then the monitor name
[17:26]reg.cs:Yeah. You need to call it twice. Have a look in freeHPC.py. It does exactly that

The Mac version retrieves NSScreen, which does have name and position. This seems the simplest platform. 


# The path of the light through a Looking Glass

We start out at a subpixel. This has a position in X,Y which GLSL receives as in vec2 texCoords. 
texCoords has a range from 0 to 1 (arbitrary; the vertex shader mapped it from -1..+1). 
The subpixels have different placement. flipSubp indicates RGB or BGR order. 
So X moves 1/3 pixel per channel. That gives the physical X location, which combined with Y forms 
our texture coordinates. 

The ray goes straight out from the image modulator and colour filter into a lenticular sheet. 
This sheet can be regarded as thin, and is mounted at some angle to the display. We can express 
these parameters by 3 values: pitch, slope and center. 

Next, we need to handle points in relation to the lenticular sheet. 

	slope = tan(sheetangle)
	alonglenslet = [ 1 slope ]
	acrosslenslet = [ slope -1 ]

    lensletvector = [ slope*pitch  pitch  center ]

To find the position across the lenticular sheet of a particular sample, in units of one lenslet,
we take (X*slope + Y) * pitch + center. This can be done with a vector dot product:

    a = lensletvector dot [ X Y 1 ]

The ray is then refracted at an angle. Which particular angle depends on the lens and wavelength, 
as well as this position across the lenslet. 
It is helpful in the math to keep it around the center. The actual angle of deflection is then 
dependent of the lens shape, but we can approximate it as linear, and just scale it with the 
range of light directions (viewCone, a value in degrees) to produce the angle. 

    angle = viewCone * (a-round(a)) * wavelenthfactor

The integer portion we removed here indicates which lenslet the ray is passing through. 

The Looking Glass has a large block with high index of refraction, which will amplify the deflection 
when the ray passes into the air. However, this is quite a thick block, so the ray travels some 
distance at the initial angle. This modifies the point from which the ray leaves the display. 

    ST = XY + angle * thicknessfactor * lensletvector.xy

This thickness factor was previously assumed to be 0. It needs to be calibrated too. 

Now we have the position from which light is visible, which is typically the ST coordinates on 
a texture. But we need to know which texture. That's a format specific transformation based on 
`a`. The current shader just maps it linearly to the available views:

    view = (a + 0.5) * views

However, there's another complication here. The views rendered each are a normal perspective 
picture, with a viewpoint positioned somewhere relative to the display. If we consider the 
central view, an observer there has a view vector of `[ S T observerdistance ]`. Those are 
thus the points where the rays must show the central view. This must now be matched up with 
which horisontal observer position sees each subpixel. 

The ray we've been calculating so far is that going straight out. The lenslet is linear, 
so it's actually one of many rays from that subpixel, all spread out in a plane. That 
plane thus contains our ray, and has a slant in common with the lenslet. 

    viewvector = [ S T observerdistance ]
    ray plane intersects point [ S T 0 ]
	[ lensletvector.y -lensletvector.x 0 ] is parallel with ray plane	

The direction of the ray from each texel is view dependent. It is:

    texelvector(S T viewObserverX observerdistance) = [ viewObserverX 0 observerdistance ] - [ S T 0 ]

viewObserverX and observerdistance are properties of the view's perspective. observerdistance 
is assumed constant across all views. 

We want to find the point where the observer viewpoint line intersects with the ray plane. 
If we find a perpendicular vector:

	raynormal = outraydir cross [ lensletvector.y -lensletvector.x 0 ]
	raynormal dot [ S T 0 ] = raynormal dot [ viewObserverX 0 observerdistance ]

outraydir is the direction of our reference ray after it passes out into the air.

	outraydir = refract(norm(ST-XY), [0 0 1], eta)
