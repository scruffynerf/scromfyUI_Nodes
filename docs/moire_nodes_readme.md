# Moiré Nodes for ComfyUI

A set of nodes for generating complex moiré patterns and applying stackable distortion warps to images and masks.

## Why Moiré Nodes?

At [Banodoco](https://www.banodoco.ai), in discussion with other artists, we've found that using a moire patterned latent as the noise base for image refining can lead to more better results than traditional random noise.
Does it work? You be the judge.
You might want to mask out skin tones, or other areas you don't want to be affected by the moire pattern.


## Features

### 1. Moiré Pattern Generator
Generates warped checkerboard, grid, or dot patterns with optional multi-grid overlays.
- **Pattern Types**: Checkerboard, Grid lines, and Dots.
- **Multi-Grid**: Overlay multiple grid layers with different ratios and blend modes (Add, Multiply, XOR, Difference) to create complex interference patterns.
- **Stackable Warps**: Apply multiple distortion effects in series.
- **Warp Shuffling**: Randomize the order of applied warps using a seed for infinite variation.
- **Input Warping**: Apply these same distortions to an input image or mask.

### 2. Moiré Warp Image/Mask
A node dedicated to applying the suite of moiré distortions to existing images or masks.  This one is just for fun mostly.

## Distortion Types
- **Sinusoidal**: Wave-based distortions.
- **Bulge**: Radial expansion or contraction.
- **Swirl**: Voronoi-like rotational twisting.
- **Noise**: Pseudo-random displacement.
- **Wave**: Multiple interfering wave patterns.
- **Barrel**: Lens-style barrel or pincushion distortion.
- **Ripple**: Concentric radial waves.
- **Shear**: Linear directional Slant.
- **Fisheye**: Extreme wide-angle lens effect.
- **Twist**: Rotational distortion increasing with distance from center.
