import os
import sys
import numpy as np
from PIL import Image, ImageDraw

# Add project root to sys.path
sys.path.append(os.getcwd())

from py.moire_nodes import (
    MoireCoordinates, MoireImageWarp,
    MoireWarpSinusoidal, MoireWarpBulge, MoireWarpSwirl, MoireWarpNoise, 
    MoireWarpWave, MoireWarpBarrel, MoireWarpRipple, MoireWarpShear, 
    MoireWarpFisheye, MoireWarpTwist,
    MoireWarpComplexLog, MoireWarpComplexExp, MoireWarpComplexPower, 
    MoireWarpComplexLinear, MoireWarpComplexInversion, MoireWarpComplexSine, 
    MoireWarpComplexCos, MoireWarpComplexTan, MoireWarpComplexHyperbolic,
    MoireWarpComplexSquare, MoireWarpComplexMobius,
    MoireNoiseGenerator
)

def create_base_grid(size=512, spacing=32):
    img = Image.new('L', (size, size), 0)
    draw = ImageDraw.Draw(img)
    for i in range(0, size + 1, spacing):
        draw.line([(i, 0), (i, size)], fill=255, width=2)
        draw.line([(0, i), (size, i)], fill=255, width=2)
    return np.array(img).astype(np.float32) / 255.0

def create_checkerboard(size=512, square_size=8):
    # Create x and y indices
    x = np.arange(size)
    y = np.arange(size)
    # Use broadcasting to create the checkerboard
    checker = ((x[:, None] // square_size) + (y[None, :] // square_size)) % 2
    return checker.astype(np.float32)

def create_recursive_grid(size=512, levels=6):
    img = Image.new('L', (size, size), 0)
    draw = ImageDraw.Draw(img)
    
    def draw_recursive(cx, cy, s, depth):
        if depth == 0:
            return
        
        x0, y0 = cx - s//2, cy - s//2
        x1, y1 = cx + s//2, cy + s//2
        
        # Draw 8x8 grid lines in this square
        step = s // 8
        for i in range(9):
            # Vertical
            draw.line([(x0 + i*step, y0), (x0 + i*step, y1)], fill=255, width=1)
            # Horizontal
            draw.line([(x0, y0 + i*step), (x1, y0 + i*step)], fill=255, width=1)
            
        # Recurse into central 2x2
        draw_recursive(cx, cy, s // 2, depth - 1)

    draw_recursive(size // 2, size // 2, size, levels)
    return np.array(img).astype(np.float32) / 255.0

def save_sample(image_np, filename):
    img = Image.fromarray((image_np * 255).astype(np.uint8))
    img.save(os.path.join("docs", "images", filename))
    print(f"Saved {filename}")

def main():
    size = 512
    base_grid = create_base_grid(size)
    node_coords = MoireCoordinates()
    (coords,) = node_coords.init_coords(size, size)
    warper = MoireImageWarp()
    
    samples = [
        (MoireWarpSinusoidal(), {"freq_x": 4.0, "freq_y": 4.0, "amp_x": 0.1, "amp_y": 0.1}, "sinusoidal.png"),
        (MoireWarpBulge(), {"strength": 0.8, "center_x": 0.0, "center_y": 0.0}, "bulge.png"),
        (MoireWarpSwirl(), {"strength": 3.0, "radius": 1.0}, "swirl.png"),
        (MoireWarpNoise(), {"scale": 0.15, "octaves": 4}, "noise.png"),
        (MoireWarpWave(), {"num_waves": 5, "amp": 0.1}, "wave.png"),
        (MoireWarpBarrel(), {"k1": 0.4, "k2": 0.2}, "barrel.png"),
        (MoireWarpRipple(), {"freq": 5.0, "amp": 0.1}, "ripple.png"),
        (MoireWarpShear(), {"shear_x": 0.5, "shear_y": 0.0}, "shear.png"),
        (MoireWarpFisheye(), {"strength": 1.5}, "fisheye.png"),
        (MoireWarpTwist(), {"strength": 2.0}, "twist.png"),
        
        # Complex
        (MoireWarpComplexLog(), {"center_x": 0.0, "center_y": 0.0}, "complex_log.png"),
        (MoireWarpComplexExp(), {"scale": 1.0}, "complex_exp.png"),
        (MoireWarpComplexPower(), {"power_real": 1.5, "power_imag": 0.5, "center_x": 0.0, "center_y": 0.0}, "complex_power.png"),
        (MoireWarpComplexLinear(), {"scale_rotate_re": 1.2, "scale_rotate_im": 0.3, "translate_re": 0.1, "translate_im": 0.1}, "complex_linear.png"),
        (MoireWarpComplexInversion(), {"center_x": 0.0, "center_y": 0.0, "radius": 0.5}, "complex_inversion.png"),
        (MoireWarpComplexSine(), {"freq": 1.0}, "complex_sine.png"),
        (MoireWarpComplexCos(), {"freq": 1.0}, "complex_cos.png"),
        (MoireWarpComplexTan(), {"freq": 1.0}, "complex_tan.png"),
        (MoireWarpComplexHyperbolic(), {"func": "tanh", "freq": 1.0}, "complex_hyperbolic.png"),
        (MoireWarpComplexSquare(), {"n": 2.0}, "complex_square.png"),
        (MoireWarpComplexMobius(), {"a_re": 1.0, "a_im": 0.0, "b_re": 0.5, "b_im": 0.0, "c_re": 0.5, "c_im": 0.0, "d_re": 1.0, "d_im": 0.0}, "complex_mobius.png"),
    ]
    
    # Generate standard and complex samples
    for node, params, filename in samples:
        (warped_coords,) = node.warp(coords, **params)
        warped_grid = warper._apply_warp_to_image(base_grid, warped_coords[0], warped_coords[1])
        save_sample(warped_grid, filename)
        
    # Generate Droste sequence (Base -> Log -> Linear -> Exp)
    print("Generating Droste sequence with recursive grid...")
    recursive_grid = create_recursive_grid(size)
    save_sample(recursive_grid, "droste_0_grid.png")
    
    # 2. Log Transform
    log_node = MoireWarpComplexLog()
    (log_coords,) = log_node.warp(coords, center_x=0.0, center_y=0.0)
    log_grid = warper._apply_warp_to_image(recursive_grid, log_coords[0], log_coords[1])
    save_sample(log_grid, "droste_1_log.png")
    
    # 3. Linear (Slant + Rotation)
    linear_node = MoireWarpComplexLinear()
    # scale_rotate_im=-0.4 is the "spin" to match the video.
    # translate_im=1.5708 (pi/2) is the 90 degree CCW rotation.
    (slanted_coords,) = linear_node.warp(log_coords, scale_rotate_re=1.0, scale_rotate_im=-0.4, translate_re=0.0, translate_im=1.5708)
    slanted_grid = warper._apply_warp_to_image(recursive_grid, slanted_coords[0], slanted_coords[1])
    save_sample(slanted_grid, "droste_2_linear.png")
    
    # 4. Exp Transform (Wrap back)
    exp_node = MoireWarpComplexExp()
    (final_coords,) = exp_node.warp(slanted_coords, scale=1.0)
    droste_grid = warper._apply_warp_to_image(recursive_grid, final_coords[0], final_coords[1])
    save_sample(droste_grid, "droste_3_exp.png")

    # 5. Noise Flavors
    print("Generating noise flavors...")
    noise_gen = MoireNoiseGenerator()
    noise_flavors = [
        ("white", {}, "noise_white.png"),
        ("blue", {}, "noise_blue.png"),
        ("pink", {}, "noise_pink.png"),
        ("brownian", {}, "noise_brownian.png"),
        ("voronoi", {"voronoi_density": 30.0}, "noise_voronoi.png"),
        ("gabor", {"gabor_angle": 45.0}, "noise_gabor.png"),
    ]
    
    for flavor, params, filename in noise_flavors:
        (img_tensor, _) = noise_gen.generate(size, size, flavor, scale=1.0, seed=42, **params)
        # Extract the 2D numpy array from (1, H, W, 3) or (1, H, W)
        img_np = img_tensor[0].cpu().numpy()
        if len(img_np.shape) == 3:
            img_np = img_np[:, :, 0]
        save_sample(img_np, filename)

    # 6. High-frequency Checkerboard Warp (for Comparison Table)
    print("Generating checkerboard warp for comparison...")
    checkerboard = create_checkerboard(size, square_size=4)
    (noise_coords,) = MoireWarpNoise().warp(coords, scale=0.15, octaves=4)
    checker_warp = warper._apply_warp_to_image(checkerboard, noise_coords[0], noise_coords[1])
    save_sample(checker_warp, "noise_checker_warp.png")

if __name__ == "__main__":
    main()
