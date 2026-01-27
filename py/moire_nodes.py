"""
ComfyUI Moiré Grid Pattern Generator Node
Authored by Scruffy
MIT License
"""

import numpy as np
import torch
from typing import Optional, Tuple, List



# --- Modular Components ---

class MoireCoordinates:
    """Initializes the coordinate grid for moiré patterns."""
    CATEGORY = "Scromfy/Image/Generate/Moire"
    FUNCTION = "init_coords"
    RETURN_TYPES = ("MOIRE_COORDS",)
    RETURN_NAMES = ("coords",)

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "width": ("INT", {"default": 1024, "min": 64, "max": 8192, "step": 8}),
                "height": ("INT", {"default": 1024, "min": 64, "max": 8192, "step": 8}),
            }
        }

    def init_coords(self, width, height):
        x = np.linspace(-1, 1, width)
        y = np.linspace(-1, 1, height)
        mesh_x, mesh_y = np.meshgrid(x, y)
        return ((mesh_x, mesh_y),)


class MoireWarpSinusoidal:
    CATEGORY = "Scromfy/Image/Generate/Moire/Warp"
    FUNCTION = "warp"
    RETURN_TYPES = ("MOIRE_COORDS",)
    RETURN_NAMES = ("coords",)

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "coords": ("MOIRE_COORDS",),
                "freq_x": ("FLOAT", {"default": 3.0, "min": 0.1, "max": 20.0, "step": 0.1}),
                "freq_y": ("FLOAT", {"default": 3.0, "min": 0.1, "max": 20.0, "step": 0.1}),
                "amp_x": ("FLOAT", {"default": 0.15, "min": 0.0, "max": 1.0, "step": 0.01}),
                "amp_y": ("FLOAT", {"default": 0.15, "min": 0.0, "max": 1.0, "step": 0.01}),
            }
        }

    def warp(self, coords, freq_x, freq_y, amp_x, amp_y):
        x, y = coords
        x_out = x + amp_x * np.sin(freq_y * np.pi * y)
        y_out = y + amp_y * np.sin(freq_x * np.pi * x)
        return ((x_out, y_out),)


class MoireWarpBulge:
    CATEGORY = "Scromfy/Image/Generate/Moire/Warp"
    FUNCTION = "warp"
    RETURN_TYPES = ("MOIRE_COORDS",)
    RETURN_NAMES = ("coords",)

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "coords": ("MOIRE_COORDS",),
                "strength": ("FLOAT", {"default": 0.5, "min": -2.0, "max": 2.0, "step": 0.05}),
                "center_x": ("FLOAT", {"default": 0.0, "min": -1.0, "max": 1.0, "step": 0.05}),
                "center_y": ("FLOAT", {"default": 0.0, "min": -1.0, "max": 1.0, "step": 0.05}),
            }
        }

    def warp(self, coords, strength, center_x, center_y):
        x, y = coords
        dx = x - center_x
        dy = y - center_y
        r = np.sqrt(dx**2 + dy**2) + 1e-10
        factor = 1 + strength * np.exp(-r * 3)
        x_out = center_x + (x - center_x) * factor
        y_out = center_y + (y - center_y) * factor
        return ((x_out, y_out),)


class MoireWarpSwirl:
    CATEGORY = "Scromfy/Image/Generate/Moire/Warp"
    FUNCTION = "warp"
    RETURN_TYPES = ("MOIRE_COORDS",)
    RETURN_NAMES = ("coords",)

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "coords": ("MOIRE_COORDS",),
                "strength": ("FLOAT", {"default": 2.0, "min": -10.0, "max": 10.0, "step": 0.1}),
                "radius": ("FLOAT", {"default": 0.8, "min": 0.1, "max": 3.0, "step": 0.05}),
            }
        }

    def warp(self, coords, strength, radius):
        x, y = coords
        r = np.sqrt(x**2 + y**2)
        angle = strength * np.exp(-r / radius)
        cos_a, sin_a = np.cos(angle), np.sin(angle)
        x_out = x * cos_a - y * sin_a
        y_out = x * sin_a + y * cos_a
        return ((x_out, y_out),)


class MoireWarpNoise:
    CATEGORY = "Scromfy/Image/Generate/Moire/Warp"
    FUNCTION = "warp"
    RETURN_TYPES = ("MOIRE_COORDS",)
    RETURN_NAMES = ("coords",)

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "coords": ("MOIRE_COORDS",),
                "scale": ("FLOAT", {"default": 0.1, "min": 0.0, "max": 0.5, "step": 0.01}),
                "octaves": ("INT", {"default": 3, "min": 1, "max": 8}),
            }
        }

    def warp(self, coords, scale, octaves):
        x, y = coords
        x_out, y_out = x.copy(), y.copy()
        for i in range(octaves):
            freq = 2 ** i
            amp = scale / (i + 1)
            x_out += amp * np.sin(freq * 7.3 * x_out + freq * 5.1 * y_out)
            y_out += amp * np.cos(freq * 6.7 * y_out + freq * 4.3 * x_out)
        return ((x_out, y_out),)


class MoireWarpWave:
    CATEGORY = "Scromfy/Image/Generate/Moire/Warp"
    FUNCTION = "warp"
    RETURN_TYPES = ("MOIRE_COORDS",)
    RETURN_NAMES = ("coords",)

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "coords": ("MOIRE_COORDS",),
                "num_waves": ("INT", {"default": 4, "min": 1, "max": 12}),
                "amp": ("FLOAT", {"default": 0.1, "min": 0.0, "max": 0.5, "step": 0.01}),
            }
        }

    def warp(self, coords, num_waves, amp):
        x, y = coords
        x_out, y_out = x.copy(), y.copy()
        for i in range(num_waves):
            angle = i * np.pi / num_waves
            freq = 3 + i * 0.5
            wave_x, wave_y = np.cos(angle), np.sin(angle)
            phase = x_out * wave_x + y_out * wave_y
            x_out += amp * np.sin(freq * np.pi * phase) * wave_y
            y_out += amp * np.sin(freq * np.pi * phase) * wave_x
        return ((x_out, y_out),)


class MoireWarpBarrel:
    CATEGORY = "Scromfy/Image/Generate/Moire/Warp"
    FUNCTION = "warp"
    RETURN_TYPES = ("MOIRE_COORDS",)
    RETURN_NAMES = ("coords",)

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "coords": ("MOIRE_COORDS",),
                "k1": ("FLOAT", {"default": 0.3, "min": -1.0, "max": 1.0, "step": 0.05}),
                "k2": ("FLOAT", {"default": 0.1, "min": -1.0, "max": 1.0, "step": 0.05}),
            }
        }

    def warp(self, coords, k1, k2):
        x, y = coords
        r2 = x**2 + y**2
        factor = 1 + k1 * r2 + k2 * r2**2
        x_out = x * factor
        y_out = y * factor
        return ((x_out, y_out),)


class MoireWarpRipple:
    CATEGORY = "Scromfy/Image/Generate/Moire/Warp"
    FUNCTION = "warp"
    RETURN_TYPES = ("MOIRE_COORDS",)
    RETURN_NAMES = ("coords",)

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "coords": ("MOIRE_COORDS",),
                "freq": ("FLOAT", {"default": 8.0, "min": 1.0, "max": 30.0, "step": 0.5}),
                "amp": ("FLOAT", {"default": 0.08, "min": 0.0, "max": 0.5, "step": 0.01}),
            }
        }

    def warp(self, coords, freq, amp):
        x, y = coords
        r = np.sqrt(x**2 + y**2) + 1e-10
        displacement = amp * np.sin(freq * np.pi * r)
        x_out = x + displacement * x / r
        y_out = y + displacement * y / r
        return ((x_out, y_out),)


class MoireWarpShear:
    CATEGORY = "Scromfy/Image/Generate/Moire/Warp"
    FUNCTION = "warp"
    RETURN_TYPES = ("MOIRE_COORDS",)
    RETURN_NAMES = ("coords",)

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "coords": ("MOIRE_COORDS",),
                "shear_x": ("FLOAT", {"default": 0.3, "min": -1.0, "max": 1.0, "step": 0.05}),
                "shear_y": ("FLOAT", {"default": 0.0, "min": -1.0, "max": 1.0, "step": 0.05}),
            }
        }

    def warp(self, coords, shear_x, shear_y):
        x, y = coords
        return ((x + shear_x * y, y + shear_y * x),)


class MoireWarpFisheye:
    CATEGORY = "Scromfy/Image/Generate/Moire/Warp"
    FUNCTION = "warp"
    RETURN_TYPES = ("MOIRE_COORDS",)
    RETURN_NAMES = ("coords",)

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "coords": ("MOIRE_COORDS",),
                "strength": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 3.0, "step": 0.1}),
            }
        }

    def warp(self, coords, strength):
        x, y = coords
        if strength == 0:
            return (coords,)
        r = np.sqrt(x**2 + y**2) + 1e-10
        theta = np.arctan(r * strength)
        factor = theta / (r * strength)
        return ((x * factor, y * factor),)


class MoireWarpTwist:
    CATEGORY = "Scromfy/Image/Generate/Moire/Warp"
    FUNCTION = "warp"
    RETURN_TYPES = ("MOIRE_COORDS",)
    RETURN_NAMES = ("coords",)

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "coords": ("MOIRE_COORDS",),
                "strength": ("FLOAT", {"default": 1.0, "min": -5.0, "max": 5.0, "step": 0.1}),
            }
        }

    def warp(self, coords, strength):
        x, y = coords
        r = np.sqrt(x**2 + y**2)
        angle = strength * r
        cos_a, sin_a = np.cos(angle), np.sin(angle)
        x_out = x * cos_a - y * sin_a
        y_out = x * sin_a + y * cos_a
        return ((x_out, y_out),)


class MoireRenderer:
    """Renders a moiré pattern from coordinates."""
    CATEGORY = "Scromfy/Image/Generate/Moire"
    FUNCTION = "render"
    RETURN_TYPES = ("IMAGE", "MASK")
    RETURN_NAMES = ("image", "mask")

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "coords": ("MOIRE_COORDS",),
                "pattern_type": (["checker", "grid", "dots"],),
                "grid_size": ("FLOAT", {"default": 30.0, "min": 1.0, "max": 200.0, "step": 0.5}),
                "grid_thickness": ("FLOAT", {"default": 0.1, "min": 0.01, "max": 0.5, "step": 0.01}),
                "dot_radius": ("FLOAT", {"default": 0.3, "min": 0.05, "max": 0.5, "step": 0.01}),
                "invert": ("BOOLEAN", {"default": False}),
            }
        }

    def render(self, coords, pattern_type, grid_size, grid_thickness, dot_radius, invert):
        x, y = coords
        pattern = MoirePatternGenerator._static_generate_pattern(x, y, grid_size, pattern_type, grid_thickness, dot_radius)
        if invert:
            pattern = 1.0 - pattern
        
        pattern_rgb = np.stack([pattern, pattern, pattern], axis=-1)
        image_tensor = torch.from_numpy(pattern_rgb).unsqueeze(0).float()
        mask_tensor = torch.from_numpy(pattern).unsqueeze(0).float()
        return (image_tensor, mask_tensor)


class MoireMultiGridRenderer:
    """Renders a multi-layer moiré pattern from coordinates."""
    CATEGORY = "Scromfy/Image/Generate/Moire"
    FUNCTION = "render"
    RETURN_TYPES = ("IMAGE", "MASK")
    RETURN_NAMES = ("image", "mask")

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "coords": ("MOIRE_COORDS",),
                "pattern_type": (["checker", "grid", "dots"],),
                "grid_size": ("FLOAT", {"default": 30.0, "min": 1.0, "max": 200.0, "step": 0.5}),
                "grid_thickness": ("FLOAT", {"default": 0.1, "min": 0.01, "max": 0.5, "step": 0.01}),
                "dot_radius": ("FLOAT", {"default": 0.3, "min": 0.05, "max": 0.5, "step": 0.01}),
                "grid_layers": ("INT", {"default": 3, "min": 2, "max": 8}),
                "grid_ratio": ("FLOAT", {"default": 1.5, "min": 1.1, "max": 4.0, "step": 0.1}),
                "grid_blend_mode": (["xor", "add", "multiply", "difference"],),
                "invert": ("BOOLEAN", {"default": False}),
            }
        }

    def render(self, coords, pattern_type, grid_size, grid_thickness, dot_radius, 
               grid_layers, grid_ratio, grid_blend_mode, invert):
        x, y = coords
        
        # This is essentially the same logic as _generate_pattern_multi but using static pattern generator
        layers = []
        for i in range(grid_layers):
            freq = grid_size * (grid_ratio ** i)
            layer = MoirePatternGenerator._static_generate_pattern(x, y, freq, pattern_type, 
                                                                    grid_thickness, dot_radius)
            layers.append(layer)
        
        # Blend layers
        result = layers[0]
        for layer in layers[1:]:
            if grid_blend_mode == "add":
                result = np.clip(result + layer, 0, 1)
            elif grid_blend_mode == "multiply":
                result = result * layer
            elif grid_blend_mode == "xor":
                result = np.abs(result - layer)
            elif grid_blend_mode == "difference":
                result = np.abs(result - layer)
        
        pattern = result.astype(np.float32)
        if invert:
            pattern = 1.0 - pattern
        
        pattern_rgb = np.stack([pattern, pattern, pattern], axis=-1)
        image_tensor = torch.from_numpy(pattern_rgb).unsqueeze(0).float()
        mask_tensor = torch.from_numpy(pattern).unsqueeze(0).float()
        return (image_tensor, mask_tensor)


class MoireImageWarp:
    """Applies coordinates to an existing image."""
    CATEGORY = "Scromfy/Image/Transform/Moire"
    FUNCTION = "apply"
    RETURN_TYPES = ("IMAGE", "MASK")
    RETURN_NAMES = ("image", "mask")

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "coords": ("MOIRE_COORDS",),
                "image": ("IMAGE",),
            },
            "optional": {
                "mask": ("MASK",),
            }
        }

    def apply(self, coords, image, mask=None):
        x, y = coords
        img_np = image[0].cpu().numpy()
        result_img = MoirePatternGenerator._static_apply_warp_to_image(img_np, x, y)
        out_image = torch.from_numpy(result_img).unsqueeze(0).float()
        
        if mask is not None:
            mask_np = mask[0].cpu().numpy() if len(mask.shape) == 3 else mask.cpu().numpy()
            result_mask = MoirePatternGenerator._static_apply_warp_to_image(mask_np, x, y)
            out_mask = torch.from_numpy(result_mask).unsqueeze(0).float()
        else:
            out_mask = torch.zeros(1, out_image.shape[1], out_image.shape[2])
            
        return (out_image, out_mask)


def shuffle_with_seed(items: List[str], seed: int) -> List[str]:
    """Shuffle a list deterministically based on seed."""
    # Constrain seed to numpy's valid range (0 to 2^32-1)
    safe_seed = seed % (2**32)
    rng = np.random.RandomState(safe_seed)
    indices = list(range(len(items)))
    rng.shuffle(indices)
    return [items[i] for i in indices]


class MoirePatternGenerator:
    """ComfyUI node for generating moiré patterns with stackable warps."""
    
    CATEGORY = "Scromfy/Image/Generate"
    FUNCTION = "generate"
    RETURN_TYPES = ("IMAGE", "MASK")
    RETURN_NAMES = ("image", "mask")
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                # === DIMENSIONS ===
                "width": ("INT", {"default": 1024, "min": 64, "max": 8192, "step": 8}),
                "height": ("INT", {"default": 1024, "min": 64, "max": 8192, "step": 8}),
                
                # === BASE PATTERN ===
                "pattern_type": (["checker", "grid", "dots"],),
                "grid_size": ("FLOAT", {"default": 30.0, "min": 1.0, "max": 200.0, "step": 0.5,
                              "tooltip": "Base grid frequency - higher = smaller squares"}),
                "grid_thickness": ("FLOAT", {"default": 0.1, "min": 0.01, "max": 0.5, "step": 0.01,
                                  "tooltip": "Line thickness for grid pattern"}),
                "dot_radius": ("FLOAT", {"default": 0.3, "min": 0.05, "max": 0.5, "step": 0.01,
                              "tooltip": "Dot size for dots pattern"}),
                "invert": ("BOOLEAN", {"default": False}),
                
                # === MULTI-GRID OVERLAY ===
                "enable_multi_grid": ("BOOLEAN", {"default": False}),
                "grid_layers": ("INT", {"default": 3, "min": 2, "max": 8,
                               "tooltip": "Number of grid layers to overlay"}),
                "grid_ratio": ("FLOAT", {"default": 1.5, "min": 1.1, "max": 4.0, "step": 0.1,
                              "tooltip": "Size ratio between successive grid layers"}),
                "grid_blend_mode": (["xor", "add", "multiply", "difference"],),
                
                # === WARP ORDER ===
                "shuffle_warps": ("BOOLEAN", {"default": False}),
                "shuffle_seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff,
                                "tooltip": "Seed for randomizing warp order"}),
                
                # === SINUSOIDAL WARP ===
                "enable_sinusoidal": ("BOOLEAN", {"default": True}),
                "sin_freq_x": ("FLOAT", {"default": 3.0, "min": 0.1, "max": 20.0, "step": 0.1}),
                "sin_freq_y": ("FLOAT", {"default": 3.0, "min": 0.1, "max": 20.0, "step": 0.1}),
                "sin_amp_x": ("FLOAT", {"default": 0.15, "min": 0.0, "max": 1.0, "step": 0.01}),
                "sin_amp_y": ("FLOAT", {"default": 0.15, "min": 0.0, "max": 1.0, "step": 0.01}),
                
                # === BULGE WARP ===
                "enable_bulge": ("BOOLEAN", {"default": False}),
                "bulge_strength": ("FLOAT", {"default": 0.5, "min": -2.0, "max": 2.0, "step": 0.05}),
                "bulge_center_x": ("FLOAT", {"default": 0.0, "min": -1.0, "max": 1.0, "step": 0.05}),
                "bulge_center_y": ("FLOAT", {"default": 0.0, "min": -1.0, "max": 1.0, "step": 0.05}),
                
                # === SWIRL WARP ===
                "enable_swirl": ("BOOLEAN", {"default": False}),
                "swirl_strength": ("FLOAT", {"default": 2.0, "min": -10.0, "max": 10.0, "step": 0.1}),
                "swirl_radius": ("FLOAT", {"default": 0.8, "min": 0.1, "max": 3.0, "step": 0.05}),
                
                # === NOISE WARP ===
                "enable_noise": ("BOOLEAN", {"default": False}),
                "noise_scale": ("FLOAT", {"default": 0.1, "min": 0.0, "max": 0.5, "step": 0.01}),
                "noise_octaves": ("INT", {"default": 3, "min": 1, "max": 8}),
                
                # === WAVE WARP ===
                "enable_wave": ("BOOLEAN", {"default": False}),
                "wave_num": ("INT", {"default": 4, "min": 1, "max": 12}),
                "wave_amp": ("FLOAT", {"default": 0.1, "min": 0.0, "max": 0.5, "step": 0.01}),
                
                # === BARREL WARP ===
                "enable_barrel": ("BOOLEAN", {"default": False}),
                "barrel_k1": ("FLOAT", {"default": 0.3, "min": -1.0, "max": 1.0, "step": 0.05}),
                "barrel_k2": ("FLOAT", {"default": 0.1, "min": -1.0, "max": 1.0, "step": 0.05}),
                
                # === RIPPLE WARP ===
                "enable_ripple": ("BOOLEAN", {"default": False}),
                "ripple_freq": ("FLOAT", {"default": 8.0, "min": 1.0, "max": 30.0, "step": 0.5}),
                "ripple_amp": ("FLOAT", {"default": 0.08, "min": 0.0, "max": 0.5, "step": 0.01}),
                
                # === SHEAR WARP ===
                "enable_shear": ("BOOLEAN", {"default": False}),
                "shear_x": ("FLOAT", {"default": 0.3, "min": -1.0, "max": 1.0, "step": 0.05}),
                "shear_y": ("FLOAT", {"default": 0.0, "min": -1.0, "max": 1.0, "step": 0.05}),
                
                # === FISHEYE WARP ===
                "enable_fisheye": ("BOOLEAN", {"default": False}),
                "fisheye_strength": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 3.0, "step": 0.1}),
                
                # === TWIST WARP ===
                "enable_twist": ("BOOLEAN", {"default": False}),
                "twist_strength": ("FLOAT", {"default": 1.0, "min": -5.0, "max": 5.0, "step": 0.1}),
            },
            "optional": {
                "input_image": ("IMAGE",),
                "input_mask": ("MASK",),
            }
        }

    # Internal helper methods for static access by new nodes
    @staticmethod
    def _static_generate_pattern(x, y, frequency, pattern_type, grid_thickness, dot_radius):
        """Generate the base pattern (static version)."""
        scaled_x = x * frequency
        scaled_y = y * frequency
        
        if pattern_type == "checker":
            pattern = (np.floor(scaled_x) + np.floor(scaled_y)) % 2
        elif pattern_type == "grid":
            line_x = np.abs(scaled_x - np.round(scaled_x)) < grid_thickness
            line_y = np.abs(scaled_y - np.round(scaled_y)) < grid_thickness
            pattern = (line_x | line_y).astype(np.float32)
        else:  # dots
            dx = scaled_x - np.round(scaled_x)
            dy = scaled_y - np.round(scaled_y)
            dist = np.sqrt(dx**2 + dy**2)
            pattern = (dist < dot_radius).astype(np.float32)
        
        return pattern.astype(np.float32)

    @staticmethod
    def _static_apply_warp_to_image(image: np.ndarray, x_warped: np.ndarray, 
                                 y_warped: np.ndarray) -> np.ndarray:
        """Apply warp coordinates to remap an image (static version)."""
        try:
            from scipy import ndimage
        except ImportError:
            print("[Warning] Scromfy Moire: scipy not installed, warping will fail.")
            return image
        
        h, w = image.shape[:2]
        map_x = ((x_warped + 1) / 2 * (w - 1)).astype(np.float32)
        map_y = ((y_warped + 1) / 2 * (h - 1)).astype(np.float32)
        
        if len(image.shape) == 2:
            return ndimage.map_coordinates(image, [map_y, map_x], order=1, mode='reflect')
        else:
            result = np.zeros_like(image)
            for c in range(image.shape[2]):
                result[:, :, c] = ndimage.map_coordinates(
                    image[:, :, c], [map_y, map_x], order=1, mode='reflect'
                )
            return result
    
    def _create_coordinate_grid(self, width: int, height: int) -> Tuple[np.ndarray, np.ndarray]:
        """Create normalized coordinate grids centered at origin."""
        x = np.linspace(-1, 1, width)
        y = np.linspace(-1, 1, height)
        return np.meshgrid(x, y)
    
    def _warp_sinusoidal(self, x, y, freq_x, freq_y, amp_x, amp_y):
        x_out = x + amp_x * np.sin(freq_y * np.pi * y)
        y_out = y + amp_y * np.sin(freq_x * np.pi * x)
        return x_out, y_out
    
    def _warp_bulge(self, x, y, strength, center_x, center_y):
        dx = x - center_x
        dy = y - center_y
        r = np.sqrt(dx**2 + dy**2) + 1e-10
        factor = 1 + strength * np.exp(-r * 3)
        return center_x + (x - center_x) * factor, center_y + (y - center_y) * factor
    
    def _warp_swirl(self, x, y, strength, radius):
        r = np.sqrt(x**2 + y**2)
        angle = strength * np.exp(-r / radius)
        cos_a, sin_a = np.cos(angle), np.sin(angle)
        return x * cos_a - y * sin_a, x * sin_a + y * cos_a
    
    def _warp_noise(self, x, y, scale, octaves):
        x_out, y_out = x.copy(), y.copy()
        for i in range(octaves):
            freq = 2 ** i
            amp = scale / (i + 1)
            x_out += amp * np.sin(freq * 7.3 * x_out + freq * 5.1 * y_out)
            y_out += amp * np.cos(freq * 6.7 * y_out + freq * 4.3 * x_out)
        return x_out, y_out
    
    def _warp_wave(self, x, y, num_waves, amp):
        x_out, y_out = x.copy(), y.copy()
        for i in range(num_waves):
            angle = i * np.pi / num_waves
            freq = 3 + i * 0.5
            wave_x, wave_y = np.cos(angle), np.sin(angle)
            phase = x_out * wave_x + y_out * wave_y
            x_out += amp * np.sin(freq * np.pi * phase) * wave_y
            y_out += amp * np.sin(freq * np.pi * phase) * wave_x
        return x_out, y_out
    
    def _warp_barrel(self, x, y, k1, k2):
        r2 = x**2 + y**2
        factor = 1 + k1 * r2 + k2 * r2**2
        return x * factor, y * factor
    
    def _warp_ripple(self, x, y, freq, amp):
        r = np.sqrt(x**2 + y**2) + 1e-10
        displacement = amp * np.sin(freq * np.pi * r)
        return x + displacement * x / r, y + displacement * y / r
    
    def _warp_shear(self, x, y, shear_x, shear_y):
        return x + shear_x * y, y + shear_y * x
    
    def _warp_fisheye(self, x, y, strength):
        if strength == 0:
            return x, y
        r = np.sqrt(x**2 + y**2) + 1e-10
        theta = np.arctan(r * strength)
        factor = theta / (r * strength)
        return x * factor, y * factor
    
    def _warp_twist(self, x, y, strength):
        r = np.sqrt(x**2 + y**2)
        angle = strength * r
        cos_a, sin_a = np.cos(angle), np.sin(angle)
        return x * cos_a - y * sin_a, x * sin_a + y * cos_a
    
    def _apply_warp_to_image(self, image: np.ndarray, x_warped: np.ndarray, 
                              y_warped: np.ndarray) -> np.ndarray:
        """Apply warp coordinates to remap an image."""
        try:
            from scipy import ndimage
        except ImportError:
            print("[Warning] Scromfy Moire: scipy not installed, warping will fail.")
            return image
        
        h, w = image.shape[:2]
        map_x = ((x_warped + 1) / 2 * (w - 1)).astype(np.float32)
        map_y = ((y_warped + 1) / 2 * (h - 1)).astype(np.float32)
        
        if len(image.shape) == 2:
            return ndimage.map_coordinates(image, [map_y, map_x], order=1, mode='reflect')
        else:
            result = np.zeros_like(image)
            for c in range(image.shape[2]):
                result[:, :, c] = ndimage.map_coordinates(
                    image[:, :, c], [map_y, map_x], order=1, mode='reflect'
                )
            return result
    
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
            # Legacy expected mask input to be warped and returned as both image (RGB) and mask
            # MoireImageWarp.apply returns (IMAGE, MASK). 
            # If we only have mask, we can wrap it as image first.
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
    
    def _generate_pattern_multi(self, x, y, grid_size, pattern_type, 
                                 grid_thickness, dot_radius,
                                 enable_multi_grid, grid_layers, 
                                 grid_ratio, grid_blend_mode):
        """Generate pattern with optional multi-grid overlay."""
        if not enable_multi_grid:
            return self._generate_pattern(x, y, grid_size, pattern_type, 
                                          grid_thickness, dot_radius)
        
        # Generate multiple grid layers
        layers = []
        for i in range(grid_layers):
            freq = grid_size * (grid_ratio ** i)
            layer = self._generate_pattern(x, y, freq, pattern_type, 
                                           grid_thickness, dot_radius)
            layers.append(layer)
        
        # Blend layers
        result = layers[0]
        for layer in layers[1:]:
            if grid_blend_mode == "add":
                result = np.clip(result + layer, 0, 1)
            elif grid_blend_mode == "multiply":
                result = result * layer
            elif grid_blend_mode == "xor":
                # XOR-like: where they differ = 1
                result = np.abs(result - layer)
            elif grid_blend_mode == "difference":
                result = np.abs(result - layer)
        
        return result.astype(np.float32)
    
    def _generate_pattern(self, x, y, frequency, pattern_type, grid_thickness, dot_radius):
        """Generate the base pattern."""
        scaled_x = x * frequency
        scaled_y = y * frequency
        
        if pattern_type == "checker":
            pattern = (np.floor(scaled_x) + np.floor(scaled_y)) % 2
        elif pattern_type == "grid":
            line_x = np.abs(scaled_x - np.round(scaled_x)) < grid_thickness
            line_y = np.abs(scaled_y - np.round(scaled_y)) < grid_thickness
            pattern = (line_x | line_y).astype(np.float32)
        else:  # dots
            dx = scaled_x - np.round(scaled_x)
            dy = scaled_y - np.round(scaled_y)
            dist = np.sqrt(dx**2 + dy**2)
            pattern = (dist < dot_radius).astype(np.float32)
        
        return pattern.astype(np.float32)


class MoireWarpImage:
    """Simplified node that just warps an existing image/mask with moiré distortions."""
    
    CATEGORY = "Scromfy/Image/Transform"
    FUNCTION = "warp"
    RETURN_TYPES = ("IMAGE", "MASK")
    RETURN_NAMES = ("image", "mask")
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                # === WARP ORDER ===
                "shuffle_warps": ("BOOLEAN", {"default": False}),
                "shuffle_seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff}),
                
                # === GLOBAL STRENGTH ===
                "global_strength": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 3.0, "step": 0.05,
                                   "tooltip": "Multiplier for all warp strengths"}),
                
                # === SINUSOIDAL WARP ===
                "enable_sinusoidal": ("BOOLEAN", {"default": True}),
                "sin_amp": ("FLOAT", {"default": 0.15, "min": 0.0, "max": 1.0, "step": 0.01}),
                "sin_freq": ("FLOAT", {"default": 3.0, "min": 0.1, "max": 20.0, "step": 0.1}),
                
                # === BULGE WARP ===
                "enable_bulge": ("BOOLEAN", {"default": False}),
                "bulge_strength": ("FLOAT", {"default": 0.5, "min": -2.0, "max": 2.0, "step": 0.05}),
                
                # === SWIRL WARP ===
                "enable_swirl": ("BOOLEAN", {"default": False}),
                "swirl_strength": ("FLOAT", {"default": 2.0, "min": -10.0, "max": 10.0, "step": 0.1}),
                
                # === NOISE WARP ===
                "enable_noise": ("BOOLEAN", {"default": False}),
                "noise_scale": ("FLOAT", {"default": 0.1, "min": 0.0, "max": 0.5, "step": 0.01}),
                
                # === WAVE WARP ===
                "enable_wave": ("BOOLEAN", {"default": False}),
                "wave_amp": ("FLOAT", {"default": 0.1, "min": 0.0, "max": 0.5, "step": 0.01}),
                
                # === BARREL WARP ===
                "enable_barrel": ("BOOLEAN", {"default": False}),
                "barrel_k1": ("FLOAT", {"default": 0.3, "min": -1.0, "max": 1.0, "step": 0.05}),
                
                # === RIPPLE WARP ===
                "enable_ripple": ("BOOLEAN", {"default": False}),
                "ripple_amp": ("FLOAT", {"default": 0.08, "min": 0.0, "max": 0.5, "step": 0.01}),
                
                # === SHEAR WARP ===
                "enable_shear": ("BOOLEAN", {"default": False}),
                "shear_x": ("FLOAT", {"default": 0.3, "min": -1.0, "max": 1.0, "step": 0.05}),
                
                # === FISHEYE WARP ===
                "enable_fisheye": ("BOOLEAN", {"default": False}),
                "fisheye_strength": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 3.0, "step": 0.1}),
                
                # === TWIST WARP ===
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
        
        # Process and warp using modular nodes
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
            # Blank image for mask-only input (legacy behavior)
            img_blank = torch.zeros(1, height, width, 3)
            return MoireImageWarp().apply(coords, img_blank, mask)


# ComfyUI node mappings
NODE_CLASS_MAPPINGS = {
    "MoirePatternGenerator": MoirePatternGenerator,
    "MoireWarpImage": MoireWarpImage,
    "MoireCoordinates": MoireCoordinates,
    "MoireWarpSinusoidal": MoireWarpSinusoidal,
    "MoireWarpBulge": MoireWarpBulge,
    "MoireWarpSwirl": MoireWarpSwirl,
    "MoireWarpNoise": MoireWarpNoise,
    "MoireWarpWave": MoireWarpWave,
    "MoireWarpBarrel": MoireWarpBarrel,
    "MoireWarpRipple": MoireWarpRipple,
    "MoireWarpShear": MoireWarpShear,
    "MoireWarpFisheye": MoireWarpFisheye,
    "MoireWarpTwist": MoireWarpTwist,
    "MoireRenderer": MoireRenderer,
    "MoireMultiGridRenderer": MoireMultiGridRenderer,
    "MoireImageWarp": MoireImageWarp,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "MoirePatternGenerator": "Moiré Pattern Generator (Legacy)",
    "MoireWarpImage": "Moiré Warp Image/Mask (Legacy)",
    "MoireCoordinates": "Moiré Coordinates",
    "MoireWarpSinusoidal": "Moiré Warp Sinusoidal",
    "MoireWarpBulge": "Moiré Warp Bulge",
    "MoireWarpSwirl": "Moiré Warp Swirl",
    "MoireWarpNoise": "Moiré Warp Noise",
    "MoireWarpWave": "Moiré Warp Wave",
    "MoireWarpBarrel": "Moiré Warp Barrel",
    "MoireWarpRipple": "Moiré Warp Ripple",
    "MoireWarpShear": "Moiré Warp Shear",
    "MoireWarpFisheye": "Moiré Warp Fisheye",
    "MoireWarpTwist": "Moiré Warp Twist",
    "MoireRenderer": "Moiré Renderer",
    "MoireMultiGridRenderer": "Moiré Multi-Grid Renderer",
    "MoireImageWarp": "Moiré Image Warp",
}
