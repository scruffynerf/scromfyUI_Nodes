"""
Legacy Moiré Pattern Nodes for ComfyUI
Separated for backward compatibility.
"""

import numpy as np
import torch
from typing import List, Tuple
from .moire_nodes import (
    MoireCoordinates, 
    MoireWarpSinusoidal, 
    MoireWarpBulge, 
    MoireWarpSwirl, 
    MoireWarpNoise, 
    MoireWarpWave, 
    MoireWarpBarrel, 
    MoireWarpRipple, 
    MoireWarpShear, 
    MoireWarpFisheye, 
    MoireWarpTwist, 
    MoireRenderer, 
    MoireMultiGridRenderer, 
    MoireImageWarp
)

def shuffle_with_seed(items: List[str], seed: int) -> List[str]:
    """Shuffle a list deterministically based on seed."""
    safe_seed = seed % (2**32)
    rng = np.random.RandomState(safe_seed)
    indices = list(range(len(items)))
    rng.shuffle(indices)
    return [items[i] for i in indices]

class MoirePatternGenerator:
    """Legacy monolithic node for generating moiré patterns with stackable warps."""
    
    CATEGORY = "Scromfy/Image/Moire/Legacy"
    FUNCTION = "generate"
    RETURN_TYPES = ("IMAGE", "MASK")
    RETURN_NAMES = ("image", "mask")
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "width": ("INT", {"default": 1024, "min": 64, "max": 8192, "step": 8}),
                "height": ("INT", {"default": 1024, "min": 64, "max": 8192, "step": 8}),
                "pattern_type": (["checker", "grid", "dots"],),
                "grid_size": ("FLOAT", {"default": 30.0, "min": 1.0, "max": 200.0, "step": 0.5}),
                "grid_thickness": ("FLOAT", {"default": 0.1, "min": 0.01, "max": 0.5, "step": 0.01}),
                "dot_radius": ("FLOAT", {"default": 0.3, "min": 0.05, "max": 0.5, "step": 0.01}),
                "invert": ("BOOLEAN", {"default": False}),
                "enable_multi_grid": ("BOOLEAN", {"default": False}),
                "grid_layers": ("INT", {"default": 3, "min": 2, "max": 8}),
                "grid_ratio": ("FLOAT", {"default": 1.5, "min": 1.1, "max": 4.0, "step": 0.1}),
                "grid_blend_mode": (["xor", "add", "multiply", "difference"],),
                "shuffle_warps": ("BOOLEAN", {"default": False}),
                "shuffle_seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff}),
                "enable_sinusoidal": ("BOOLEAN", {"default": True}),
                "sin_freq_x": ("FLOAT", {"default": 3.0, "min": 0.1, "max": 20.0, "step": 0.1}),
                "sin_freq_y": ("FLOAT", {"default": 3.0, "min": 0.1, "max": 20.0, "step": 0.1}),
                "sin_amp_x": ("FLOAT", {"default": 0.15, "min": 0.0, "max": 1.0, "step": 0.01}),
                "sin_amp_y": ("FLOAT", {"default": 0.15, "min": 0.0, "max": 1.0, "step": 0.01}),
                "enable_bulge": ("BOOLEAN", {"default": False}),
                "bulge_strength": ("FLOAT", {"default": 0.5, "min": -2.0, "max": 2.0, "step": 0.05}),
                "bulge_center_x": ("FLOAT", {"default": 0.0, "min": -1.0, "max": 1.0, "step": 0.05}),
                "bulge_center_y": ("FLOAT", {"default": 0.0, "min": -1.0, "max": 1.0, "step": 0.05}),
                "enable_swirl": ("BOOLEAN", {"default": False}),
                "swirl_strength": ("FLOAT", {"default": 2.0, "min": -10.0, "max": 10.0, "step": 0.1}),
                "swirl_radius": ("FLOAT", {"default": 0.8, "min": 0.1, "max": 3.0, "step": 0.05}),
                "enable_noise": ("BOOLEAN", {"default": False}),
                "noise_scale": ("FLOAT", {"default": 0.1, "min": 0.0, "max": 0.5, "step": 0.01}),
                "noise_octaves": ("INT", {"default": 3, "min": 1, "max": 8}),
                "enable_wave": ("BOOLEAN", {"default": False}),
                "wave_num": ("INT", {"default": 4, "min": 1, "max": 12}),
                "wave_amp": ("FLOAT", {"default": 0.1, "min": 0.0, "max": 0.5, "step": 0.01}),
                "enable_barrel": ("BOOLEAN", {"default": False}),
                "barrel_k1": ("FLOAT", {"default": 0.3, "min": -1.0, "max": 1.0, "step": 0.05}),
                "barrel_k2": ("FLOAT", {"default": 0.1, "min": -1.0, "max": 1.0, "step": 0.05}),
                "enable_ripple": ("BOOLEAN", {"default": False}),
                "ripple_freq": ("FLOAT", {"default": 8.0, "min": 1.0, "max": 30.0, "step": 0.5}),
                "ripple_amp": ("FLOAT", {"default": 0.08, "min": 0.0, "max": 0.5, "step": 0.01}),
                "enable_shear": ("BOOLEAN", {"default": False}),
                "shear_x": ("FLOAT", {"default": 0.3, "min": -1.0, "max": 1.0, "step": 0.05}),
                "shear_y": ("FLOAT", {"default": 0.0, "min": -1.0, "max": 1.0, "step": 0.05}),
                "enable_fisheye": ("BOOLEAN", {"default": False}),
                "fisheye_strength": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 3.0, "step": 0.1}),
                "enable_twist": ("BOOLEAN", {"default": False}),
                "twist_strength": ("FLOAT", {"default": 1.0, "min": -5.0, "max": 5.0, "step": 0.1}),
            },
            "optional": {
                "input_image": ("IMAGE",),
                "input_mask": ("MASK",),
            }
        }

    def generate(self, width, height,
                 pattern_type, grid_size, grid_thickness, dot_radius, invert,
                 enable_multi_grid, grid_layers, grid_ratio, grid_blend_mode,
                 shuffle_warps, shuffle_seed,
                 enable_sinusoidal, sin_freq_x, sin_freq_y, sin_amp_x, sin_amp_y,
                 enable_bulge, bulge_strength, bulge_center_x, bulge_center_y,
                 enable_swirl, swirl_strength, swirl_radius,
                 enable_noise, noise_scale, noise_octaves,
                 enable_wave, wave_num, wave_amp,
                 enable_barrel, barrel_k1, barrel_k2,
                 enable_ripple, ripple_freq, ripple_amp,
                 enable_shear, shear_x, shear_y,
                 enable_fisheye, fisheye_strength,
                 enable_twist, twist_strength,
                 input_image=None, input_mask=None):
        
        # 1. Initialize Coordinates
        if input_image is not None:
            height, width = input_image.shape[1], input_image.shape[2]
        elif input_mask is not None:
            height, width = input_mask.shape[1], input_mask.shape[2]
            
        coords_node = MoireCoordinates()
        (coords,) = coords_node.init_coords(width, height)
        
        # 2. Build Warp List
        warp_map = {
            "sinusoidal": (enable_sinusoidal, MoireWarpSinusoidal().warp, (sin_freq_x, sin_freq_y, sin_amp_x, sin_amp_y)),
            "bulge": (enable_bulge, MoireWarpBulge().warp, (bulge_strength, bulge_center_x, bulge_center_y)),
            "swirl": (enable_swirl, MoireWarpSwirl().warp, (swirl_strength, swirl_radius)),
            "noise": (enable_noise, MoireWarpNoise().warp, (noise_scale, noise_octaves)),
            "wave": (enable_wave, MoireWarpWave().warp, (wave_num, wave_amp)),
            "barrel": (enable_barrel, MoireWarpBarrel().warp, (barrel_k1, barrel_k2)),
            "ripple": (enable_ripple, MoireWarpRipple().warp, (ripple_freq, ripple_amp)),
            "shear": (enable_shear, MoireWarpShear().warp, (shear_x, shear_y)),
            "fisheye": (enable_fisheye, MoireWarpFisheye().warp, (fisheye_strength,)),
            "twist": (enable_twist, MoireWarpTwist().warp, (twist_strength,)),
        }
        
        enabled_names = [name for name, (enabled, _, _) in warp_map.items() if enabled]
        if shuffle_warps and len(enabled_names) > 1:
            enabled_names = shuffle_with_seed(enabled_names, shuffle_seed)
        
        # 3. Apply Warps
        for name in enabled_names:
            _, warp_fn, args = warp_map[name]
            (coords,) = warp_fn(coords, *args)
            
        # 4. Render or Warp Image
        if input_image is not None:
            return MoireImageWarp().apply(coords, input_image, input_mask)
        elif input_mask is not None:
            mask_rgb = torch.stack([input_mask, input_mask, input_mask], dim=-1)
            img_out, mask_out = MoireImageWarp().apply(coords, mask_rgb, input_mask)
            if invert:
                img_out = 1.0 - img_out
                mask_out = 1.0 - mask_out
            return (img_out, mask_out)
        else:
            if enable_multi_grid:
                return MoireMultiGridRenderer().render(coords, pattern_type, grid_size, grid_thickness, dot_radius, 
                                                        grid_layers, grid_ratio, grid_blend_mode, invert)
            else:
                return MoireRenderer().render(coords, pattern_type, grid_size, grid_thickness, dot_radius, invert)

class MoireWarpImage:
    """Legacy node for warping an existing image/mask with moiré distortions."""
    
    CATEGORY = "Scromfy/Image/Moire/Legacy"
    FUNCTION = "warp"
    RETURN_TYPES = ("IMAGE", "MASK")
    RETURN_NAMES = ("image", "mask")
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "shuffle_warps": ("BOOLEAN", {"default": False}),
                "shuffle_seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff}),
                "global_strength": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 3.0, "step": 0.05}),
                "enable_sinusoidal": ("BOOLEAN", {"default": True}),
                "sin_amp": ("FLOAT", {"default": 0.15, "min": 0.0, "max": 1.0, "step": 0.01}),
                "sin_freq": ("FLOAT", {"default": 3.0, "min": 0.1, "max": 20.0, "step": 0.1}),
                "enable_bulge": ("BOOLEAN", {"default": False}),
                "bulge_strength": ("FLOAT", {"default": 0.5, "min": -2.0, "max": 2.0, "step": 0.05}),
                "enable_swirl": ("BOOLEAN", {"default": False}),
                "swirl_strength": ("FLOAT", {"default": 2.0, "min": -10.0, "max": 10.0, "step": 0.1}),
                "enable_noise": ("BOOLEAN", {"default": False}),
                "noise_scale": ("FLOAT", {"default": 0.1, "min": 0.0, "max": 0.5, "step": 0.01}),
                "enable_wave": ("BOOLEAN", {"default": False}),
                "wave_amp": ("FLOAT", {"default": 0.1, "min": 0.0, "max": 0.5, "step": 0.01}),
                "enable_barrel": ("BOOLEAN", {"default": False}),
                "barrel_k1": ("FLOAT", {"default": 0.3, "min": -1.0, "max": 1.0, "step": 0.05}),
                "enable_ripple": ("BOOLEAN", {"default": False}),
                "ripple_amp": ("FLOAT", {"default": 0.08, "min": 0.0, "max": 0.5, "step": 0.01}),
                "enable_shear": ("BOOLEAN", {"default": False}),
                "shear_x": ("FLOAT", {"default": 0.3, "min": -1.0, "max": 1.0, "step": 0.05}),
                "enable_fisheye": ("BOOLEAN", {"default": False}),
                "fisheye_strength": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 3.0, "step": 0.1}),
                "enable_twist": ("BOOLEAN", {"default": False}),
                "twist_strength": ("FLOAT", {"default": 1.0, "min": -5.0, "max": 5.0, "step": 0.1}),
            },
            "optional": {
                "image": ("IMAGE",),
                "mask": ("MASK",),
            }
        }
    
    def warp(self, shuffle_warps, shuffle_seed, global_strength,
             enable_sinusoidal, sin_amp, sin_freq,
             enable_bulge, bulge_strength,
             enable_swirl, swirl_strength,
             enable_noise, noise_scale,
             enable_wave, wave_amp,
             enable_barrel, barrel_k1,
             enable_ripple, ripple_amp,
             enable_shear, shear_x,
             enable_fisheye, fisheye_strength,
             enable_twist, twist_strength,
             image=None, mask=None):
        
        if image is None and mask is None:
            width, height = 512, 512
        elif image is not None:
            height, width = image.shape[1], image.shape[2]
        else:
            height, width = mask.shape[1], mask.shape[2]
            
        coords_node = MoireCoordinates()
        (coords,) = coords_node.init_coords(width, height)
        s = global_strength
        
        warp_map = {
            "sinusoidal": (enable_sinusoidal, MoireWarpSinusoidal().warp, (sin_freq, sin_freq, sin_amp * s, sin_amp * s)),
            "bulge": (enable_bulge, MoireWarpBulge().warp, (bulge_strength * s, 0, 0)),
            "swirl": (enable_swirl, MoireWarpSwirl().warp, (swirl_strength * s, 0.8)),
            "noise": (enable_noise, MoireWarpNoise().warp, (noise_scale * s, 3)),
            "wave": (enable_wave, MoireWarpWave().warp, (4, wave_amp * s)),
            "barrel": (enable_barrel, MoireWarpBarrel().warp, (barrel_k1 * s, 0.1 * s)),
            "ripple": (enable_ripple, MoireWarpRipple().warp, (8.0, ripple_amp * s)),
            "shear": (enable_shear, MoireWarpShear().warp, (shear_x * s, 0)),
            "fisheye": (enable_fisheye, MoireWarpFisheye().warp, (fisheye_strength * s,)),
            "twist": (enable_twist, MoireWarpTwist().warp, (twist_strength * s,)),
        }
        
        enabled_names = [name for name, (enabled, _, _) in warp_map.items() if enabled]
        if shuffle_warps and len(enabled_names) > 1:
            enabled_names = shuffle_with_seed(enabled_names, shuffle_seed)
            
        for name in enabled_names:
            _, warp_fn, args = warp_map[name]
            (coords,) = warp_fn(coords, *args)
            
        if image is not None:
            return MoireImageWarp().apply(coords, image, mask)
        else:
            img_blank = torch.zeros(1, height, width, 3)
            return MoireImageWarp().apply(coords, img_blank, mask)

NODE_CLASS_MAPPINGS = {
    "MoirePatternGenerator": MoirePatternGenerator,
    "MoireWarpImage": MoireWarpImage,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "MoirePatternGenerator": "Moiré Pattern Generator (Legacy)",
    "MoireWarpImage": "Moiré Warp Image/Mask (Legacy)",
}
