import os
import sys
import torch
import numpy as np

# Mocking ComfyUI environment if necessary, but we can just import the classes
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from py.moire_nodes import (
    MoireCoordinates, MoireWarpSinusoidal, MoireRenderer, 
    MoirePatternGenerator, MoireWarpImage
)

def test_modular_workflow():
    print("Testing Modular Workflow...")
    # 1. Coordinates
    coords_node = MoireCoordinates()
    (coords,) = coords_node.init_coords(512, 512)
    assert isinstance(coords, tuple)
    assert coords[0].shape == (512, 512)
    print("✓ MoireCoordinates ok")
    
    # 2. Warp
    warp_node = MoireWarpSinusoidal()
    (warped_coords,) = warp_node.warp(coords, 3.0, 3.0, 0.1, 0.1)
    assert warped_coords[0].shape == (512, 512)
    assert not np.array_equal(coords[0], warped_coords[0])
    print("✓ MoireWarpSinusoidal ok")
    
    # 3. Renderer
    renderer = MoireRenderer()
    img, mask = renderer.render(warped_coords, "checker", 30.0, 0.1, 0.3, False)
    assert img.shape == (1, 512, 512, 3)
    assert mask.shape == (1, 512, 512)
    print("✓ MoireRenderer ok")

def test_legacy_compatibility():
    print("Testing Legacy Compatibility...")
    # MoirePatternGenerator
    gen = MoirePatternGenerator()
    img, mask = gen.generate(
        512, 512, "checker", 30.0, 0.1, 0.3, False,
        False, 3, 1.5, "xor",
        False, 0,
        True, 3.0, 3.0, 0.1, 0.1,
        False, 0.5, 0.0, 0.0,
        False, 2.0, 0.8,
        False, 0.1, 3,
        False, 4, 0.1,
        False, 0.3, 0.1,
        False, 8.0, 0.08,
        False, 0.3, 0.0,
        False, 1.0,
        False, 1.0
    )
    assert img.shape == (1, 512, 512, 3)
    assert mask.shape == (1, 512, 512)
    print("✓ MoirePatternGenerator (Legacy) ok")
    
    # MoireWarpImage
    warp_img = MoireWarpImage()
    img_in = torch.zeros(1, 512, 512, 3)
    img_out, mask_out = warp_img.warp(
        False, 0, 1.0,
        True, 0.15, 3.0,
        False, 0.5,
        False, 2.0,
        False, 0.1,
        False, 0.1,
        False, 0.3,
        False, 0.08,
        False, 0.3,
        False, 1.0,
        False, 1.0,
        image=img_in
    )
    assert img_out.shape == (1, 512, 512, 3)
    print("✓ MoireWarpImage (Legacy) ok")

if __name__ == "__main__":
    try:
        test_modular_workflow()
        test_legacy_compatibility()
        print("\nAll sanity checks passed!")
    except Exception as e:
        print(f"\nTests failed: {e}")
        sys.exit(1)
