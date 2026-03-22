"""
ComfyUI Moiré Grid Pattern Generator Nodes
Modularized suite for generating and warping moiré patterns.
Authored by Scruffy
MIT License
"""

import numpy as np
import torch
from typing import Optional, Tuple, List, Union

# Dependency check
try:
    from scipy import ndimage
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

def get_scipy_error_message():
    return "Scipy is required for warping operations. Please install it using 'pip install scipy'."

class MoireCoordinates:
    """
    Initializes a normalized coordinate grid for moiré patterns.
    
    This node creates a meshgrid of X and Y coordinates ranging from -1 to 1,
    which serves as the base for all subsequent warping and rendering operations.
    (z = x + iy, where x, y ∈ [-1, 1])
    """
    CATEGORY = "Scromfy/Image/Moire"
    FUNCTION = "init_coords"
    RETURN_TYPES = ("MOIRE_COORDS",)
    RETURN_NAMES = ("coords",)

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "width": ("INT", {"default": 1024, "min": 64, "max": 8192, "step": 8, "tooltip": "Width of the coordinate grid."}),
                "height": ("INT", {"default": 1024, "min": 64, "max": 8192, "step": 8, "tooltip": "Height of the coordinate grid."}),
            }
        }

    def init_coords(self, width: int, height: int) -> Tuple[Tuple[np.ndarray, np.ndarray]]:
        """
        Creates the normalized coordinate grid.
        
        Args:
            width: Width of the grid.
            height: Height of the grid.
            
        Returns:
            A tuple containing the meshgrid (mesh_x, mesh_y).
        """
        x = np.linspace(-1, 1, width)
        y = np.linspace(-1, 1, height)
        mesh_x, mesh_y = np.meshgrid(x, y)
        return ((mesh_x, mesh_y),)


class MoireWarpSinusoidal:
    """
    Applies a sinusoidal displacement (wave) to the coordinate grid.
    
    Formula:
    x' = x + amp_x * sin(freq_y * pi * y)
    y' = y + amp_y * sin(freq_x * pi * x)
    """
    CATEGORY = "Scromfy/Image/Moire"
    FUNCTION = "warp"
    RETURN_TYPES = ("MOIRE_COORDS",)
    RETURN_NAMES = ("coords",)

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "coords": ("MOIRE_COORDS",),
                "freq_x": ("FLOAT", {"default": 3.0, "min": 0.1, "max": 20.0, "step": 0.1, "tooltip": "Frequency of the X-axis wave."}),
                "freq_y": ("FLOAT", {"default": 3.0, "min": 0.1, "max": 20.0, "step": 0.1, "tooltip": "Frequency of the Y-axis wave."}),
                "amp_x": ("FLOAT", {"default": 0.15, "min": 0.0, "max": 1.0, "step": 0.01, "tooltip": "Amplitude (strength) of the X displacement."}),
                "amp_y": ("FLOAT", {"default": 0.15, "min": 0.0, "max": 1.0, "step": 0.01, "tooltip": "Amplitude (strength) of the Y displacement."}),
            }
        }

    def warp(self, coords: Tuple[np.ndarray, np.ndarray], freq_x: float, freq_y: float, amp_x: float, amp_y: float) -> Tuple[Tuple[np.ndarray, np.ndarray]]:
        """Applies sinusoidal warping."""
        x, y = coords
        x_out = x + amp_x * np.sin(freq_y * np.pi * y)
        y_out = y + amp_y * np.sin(freq_x * np.pi * x)
        return ((x_out, y_out),)


class MoireWarpBulge:
    """
    Applies a radial bulge or pinch distortion to the coordinate grid.
    
    Formula:
    f(z) = C + (z - C) * (1 + strength * exp(-|z-C| * 3))
    where C is the center point.
    """
    CATEGORY = "Scromfy/Image/Moire"
    FUNCTION = "warp"
    RETURN_TYPES = ("MOIRE_COORDS",)
    RETURN_NAMES = ("coords",)

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "coords": ("MOIRE_COORDS",),
                "strength": ("FLOAT", {"default": 0.5, "min": -2.0, "max": 2.0, "step": 0.05, "tooltip": "Positive for bulge, negative for pinch."}),
                "center_x": ("FLOAT", {"default": 0.0, "min": -1.0, "max": 1.0, "step": 0.05, "tooltip": "X coordinate of the center point."}),
                "center_y": ("FLOAT", {"default": 0.0, "min": -1.0, "max": 1.0, "step": 0.05, "tooltip": "Y coordinate of the center point."}),
            }
        }

    def warp(self, coords: Tuple[np.ndarray, np.ndarray], strength: float, center_x: float, center_y: float) -> Tuple[Tuple[np.ndarray, np.ndarray]]:
        """Applies bulge warping."""
        x, y = coords
        dx = x - center_x
        dy = y - center_y
        r = np.sqrt(dx**2 + dy**2) + 1e-10
        factor = 1 + strength * np.exp(-r * 3)
        x_out = center_x + (x - center_x) * factor
        y_out = center_y + (y - center_y) * factor
        return ((x_out, y_out),)


class MoireWarpSwirl:
    """
    Applies a rotational swirl distortion to the coordinate grid.
    
    Formula:
    f(z) = z * exp(i * theta)
    where theta = strength * exp(-|z| / radius)
    """
    CATEGORY = "Scromfy/Image/Moire"
    FUNCTION = "warp"
    RETURN_TYPES = ("MOIRE_COORDS",)
    RETURN_NAMES = ("coords",)

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "coords": ("MOIRE_COORDS",),
                "strength": ("FLOAT", {"default": 2.0, "min": -10.0, "max": 10.0, "step": 0.1, "tooltip": "Rotational strength of the swirl."}),
                "radius": ("FLOAT", {"default": 0.8, "min": 0.1, "max": 3.0, "step": 0.05, "tooltip": "Falloff radius for the effect."}),
            }
        }

    def warp(self, coords: Tuple[np.ndarray, np.ndarray], strength: float, radius: float) -> Tuple[Tuple[np.ndarray, np.ndarray]]:
        """Applies swirl warping."""
        x, y = coords
        r = np.sqrt(x**2 + y**2)
        angle = strength * np.exp(-r / radius)
        cos_a, sin_a = np.cos(angle), np.sin(angle)
        x_out = x * cos_a - y * sin_a
        y_out = x * sin_a + y * cos_a
        return ((x_out, y_out),)


class MoireWarpNoise:
    """
    Applies a multi-octave noise displacement to the coordinate grid.
    
    Formula:
    z' = z + sum( amp_i * noise(freq_i * z) )
    """
    CATEGORY = "Scromfy/Image/Moire"
    FUNCTION = "warp"
    RETURN_TYPES = ("MOIRE_COORDS",)
    RETURN_NAMES = ("coords",)

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "coords": ("MOIRE_COORDS",),
                "scale": ("FLOAT", {"default": 0.1, "min": 0.0, "max": 0.5, "step": 0.01, "tooltip": "Scale/amplitude of the noise."}),
                "octaves": ("INT", {"default": 3, "min": 1, "max": 8, "tooltip": "Number of noise layers to stack."}),
            }
        }

    def warp(self, coords: Tuple[np.ndarray, np.ndarray], scale: float, octaves: int) -> Tuple[Tuple[np.ndarray, np.ndarray]]:
        """Applies noise warping."""
        x, y = coords
        x_out, y_out = x.copy(), y.copy()
        for i in range(octaves):
            freq = 2 ** i
            amp = scale / (i + 1)
            x_out += amp * np.sin(freq * 7.3 * x_out + freq * 5.1 * y_out)
            y_out += amp * np.cos(freq * 6.7 * y_out + freq * 4.3 * x_out)
        return ((x_out, y_out),)


class MoireWarpWave:
    """
    Applies multiple intersecting wave patterns for complex interference.
    
    Formula:
    z' = z + sum( amp * sin(freq * pi * proj_i(z)) * dir_i )
    """
    CATEGORY = "Scromfy/Image/Moire"
    FUNCTION = "warp"
    RETURN_TYPES = ("MOIRE_COORDS",)
    RETURN_NAMES = ("coords",)

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "coords": ("MOIRE_COORDS",),
                "num_waves": ("INT", {"default": 4, "min": 1, "max": 12, "tooltip": "Number of waves in different directions."}),
                "amp": ("FLOAT", {"default": 0.1, "min": 0.0, "max": 0.5, "step": 0.01, "tooltip": "Amplitude of the waves."}),
            }
        }

    def warp(self, coords: Tuple[np.ndarray, np.ndarray], num_waves: int, amp: float) -> Tuple[Tuple[np.ndarray, np.ndarray]]:
        """Applies multi-wave warping."""
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
    """
    Applies barrel or pincushion lens distortion.
    
    Formula:
    f(z) = z * (1 + k1*|z|^2 + k2*|z|^4)
    """
    CATEGORY = "Scromfy/Image/Moire"
    FUNCTION = "warp"
    RETURN_TYPES = ("MOIRE_COORDS",)
    RETURN_NAMES = ("coords",)

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "coords": ("MOIRE_COORDS",),
                "k1": ("FLOAT", {"default": 0.3, "min": -1.0, "max": 1.0, "step": 0.05, "tooltip": "Primary distortion coefficient."}),
                "k2": ("FLOAT", {"default": 0.1, "min": -1.0, "max": 1.0, "step": 0.05, "tooltip": "Secondary distortion coefficient."}),
            }
        }

    def warp(self, coords: Tuple[np.ndarray, np.ndarray], k1: float, k2: float) -> Tuple[Tuple[np.ndarray, np.ndarray]]:
        """Applies barrel warping."""
        x, y = coords
        r2 = x**2 + y**2
        factor = 1 + k1 * r2 + k2 * r2**2
        x_out = x * factor
        y_out = y * factor
        return ((x_out, y_out),)


class MoireWarpRipple:
    """
    Applies concentric radial waves (ripples) from the origin.
    
    Formula:
    f(z) = z + amp * sin(freq * pi * |z|) * (z / |z|)
    """
    CATEGORY = "Scromfy/Image/Moire"
    FUNCTION = "warp"
    RETURN_TYPES = ("MOIRE_COORDS",)
    RETURN_NAMES = ("coords",)

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "coords": ("MOIRE_COORDS",),
                "freq": ("FLOAT", {"default": 8.0, "min": 1.0, "max": 30.0, "step": 0.5, "tooltip": "Frequency of the ripples."}),
                "amp": ("FLOAT", {"default": 0.08, "min": 0.0, "max": 0.5, "step": 0.01, "tooltip": "Amplitude (height) of the ripples."}),
            }
        }

    def warp(self, coords: Tuple[np.ndarray, np.ndarray], freq: float, amp: float) -> Tuple[Tuple[np.ndarray, np.ndarray]]:
        """Applies ripple warping."""
        x, y = coords
        r = np.sqrt(x**2 + y**2) + 1e-10
        displacement = amp * np.sin(freq * np.pi * r)
        x_out = x + displacement * x / r
        y_out = y + displacement * y / r
        return ((x_out, y_out),)


class MoireWarpShear:
    """
    Applies linear directional slant (shear) to the coordinate grid.
    
    Formula:
    x' = x + shear_x * y
    y' = y + shear_y * x
    """
    CATEGORY = "Scromfy/Image/Moire"
    FUNCTION = "warp"
    RETURN_TYPES = ("MOIRE_COORDS",)
    RETURN_NAMES = ("coords",)

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "coords": ("MOIRE_COORDS",),
                "shear_x": ("FLOAT", {"default": 0.3, "min": -1.0, "max": 1.0, "step": 0.05, "tooltip": "Horizontal shear strength."}),
                "shear_y": ("FLOAT", {"default": 0.0, "min": -1.0, "max": 1.0, "step": 0.05, "tooltip": "Vertical shear strength."}),
            }
        }

    def warp(self, coords: Tuple[np.ndarray, np.ndarray], shear_x: float, shear_y: float) -> Tuple[Tuple[np.ndarray, np.ndarray]]:
        """Applies shear warping."""
        x, y = coords
        return ((x + shear_x * y, y + shear_y * x),)


class MoireWarpFisheye:
    """
    Applies extreme wide-angle 'fisheye' distortion.
    
    Formula:
    f(z) = z * atan(|z| * strength) / (|z| * strength)
    """
    CATEGORY = "Scromfy/Image/Moire"
    FUNCTION = "warp"
    RETURN_TYPES = ("MOIRE_COORDS",)
    RETURN_NAMES = ("coords",)

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "coords": ("MOIRE_COORDS",),
                "strength": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 3.0, "step": 0.1, "tooltip": "Strength of the fisheye effect."}),
            }
        }

    def warp(self, coords: Tuple[np.ndarray, np.ndarray], strength: float) -> Tuple[Tuple[np.ndarray, np.ndarray]]:
        """Applies fisheye warping."""
        x, y = coords
        if strength == 0:
            return (coords,)
        r = np.sqrt(x**2 + y**2) + 1e-10
        theta = np.arctan(r * strength)
        factor = theta / (r * strength)
        return ((x * factor, y * factor),)


class MoireWarpTwist:
    """
    Applies rotational distortion that increases with distance from the center.
    
    Formula:
    f(z) = z * exp(i * strength * |z|)
    """
    CATEGORY = "Scromfy/Image/Moire"
    FUNCTION = "warp"
    RETURN_TYPES = ("MOIRE_COORDS",)
    RETURN_NAMES = ("coords",)

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "coords": ("MOIRE_COORDS",),
                "strength": ("FLOAT", {"default": 1.0, "min": -5.0, "max": 5.0, "step": 0.1, "tooltip": "Strength of the rotation."}),
            }
        }

    def warp(self, coords: Tuple[np.ndarray, np.ndarray], strength: float) -> Tuple[Tuple[np.ndarray, np.ndarray]]:
        """Applies twist warping."""
        x, y = coords
        r = np.sqrt(x**2 + y**2)
        angle = strength * r
        cos_a, sin_a = np.cos(angle), np.sin(angle)
        x_out = x * cos_a - y * sin_a
        y_out = x * sin_a + y * cos_a
        return ((x_out, y_out),)


# =============================================================================
# COMPLEX PLANE TRANSFORMATION NODES
# =============================================================================

class MoireWarpComplexLog:
    """
    Applies a complex logarithm to the coordinate grid.
    
    Formula:
    w = log(z) = ln|z| + i*arg(z)
    
    This unwraps radial patterns (circles) into a rectangular grid, 
    periodic in the imaginary (Y) axis. Fundamental for Drosta effects.
    """
    CATEGORY = "Scromfy/Image/Moire/Complex"
    FUNCTION = "warp"
    RETURN_TYPES = ("MOIRE_COORDS",)
    RETURN_NAMES = ("coords",)

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "coords": ("MOIRE_COORDS",),
                "center_x": ("FLOAT", {"default": 0.0, "min": -1.0, "max": 1.0, "step": 0.01}),
                "center_y": ("FLOAT", {"default": 0.0, "min": -1.0, "max": 1.0, "step": 0.01}),
            }
        }

    def warp(self, coords: Tuple[np.ndarray, np.ndarray], center_x: float, center_y: float) -> Tuple[Tuple[np.ndarray, np.ndarray]]:
        x, y = coords
        dx = x - center_x
        dy = y - center_y
        r = np.sqrt(dx**2 + dy**2) + 1e-10
        theta = np.arctan2(dy, dx)
        
        # ln|z| is the new X, arg(z) is the new Y
        x_out = np.log(r)
        y_out = theta
        return ((x_out, y_out),)


class MoireWarpComplexExp:
    """
    Applies a complex exponential to the coordinate grid.
    
    Formula:
    z' = exp(w) = exp(u+iv) = exp(u) * (cos(v) + i*sin(v))
    
    This wraps a rectangular grid back into a radial/concentric pattern.
    Inverse of the Complex Log.
    """
    CATEGORY = "Scromfy/Image/Moire/Complex"
    FUNCTION = "warp"
    RETURN_TYPES = ("MOIRE_COORDS",)
    RETURN_NAMES = ("coords",)

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "coords": ("MOIRE_COORDS",),
                "scale": ("FLOAT", {"default": 1.0, "min": 0.1, "max": 10.0, "step": 0.1}),
            }
        }

    def warp(self, coords: Tuple[np.ndarray, np.ndarray], scale: float) -> Tuple[Tuple[np.ndarray, np.ndarray]]:
        u, v = coords
        r = np.exp(u) * scale
        x_out = r * np.cos(v)
        y_out = r * np.sin(v)
        return ((x_out, y_out),)


class MoireWarpComplexPower:
    """
    Applies a complex power transformation to the coordinate grid.
    
    Formula:
    z' = z^c = exp(c * log(z))
    where c = real + i*imag
    
    This is a conformal map that creates swirling zoom effects (Drosta style).
    """
    CATEGORY = "Scromfy/Image/Moire/Complex"
    FUNCTION = "warp"
    RETURN_TYPES = ("MOIRE_COORDS",)
    RETURN_NAMES = ("coords",)

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "coords": ("MOIRE_COORDS",),
                "power_real": ("FLOAT", {"default": 1.0, "min": -5.0, "max": 5.0, "step": 0.1}),
                "power_imag": ("FLOAT", {"default": 0.0, "min": -5.0, "max": 5.0, "step": 0.1}),
                "center_x": ("FLOAT", {"default": 0.0, "min": -1.0, "max": 1.0, "step": 0.01}),
                "center_y": ("FLOAT", {"default": 0.0, "min": -1.0, "max": 1.0, "step": 0.01}),
            }
        }

    def warp(self, coords: Tuple[np.ndarray, np.ndarray], power_real: float, power_imag: float, center_x: float, center_y: float) -> Tuple[Tuple[np.ndarray, np.ndarray]]:
        x, y = coords
        dx = x - center_x
        dy = y - center_y
        r = np.sqrt(dx**2 + dy**2) + 1e-10
        theta = np.arctan2(dy, dx)
        
        # log(z) = ln(r) + i*theta
        # c * log(z) = (pr + i*pi) * (ln_r + i*theta)
        # = (pr*ln_r - pi*theta) + i*(pr*theta + pi*ln_r)
        ln_r = np.log(r)
        real_part = power_real * ln_r - power_imag * theta
        imag_part = power_real * theta + power_imag * ln_r
        
        new_r = np.exp(real_part)
        x_out = center_x + new_r * np.cos(imag_part)
        y_out = center_y + new_r * np.sin(imag_part)
        return ((x_out, y_out),)


class MoireWarpComplexLinear:
    """
    Applies a linear transformation in the complex plane.
    
    Formula:
    z' = a*z + b
    where a and b are complex numbers.
    a controls scaling and rotation.
    b controls translation.
    """
    CATEGORY = "Scromfy/Image/Moire/Complex"
    FUNCTION = "warp"
    RETURN_TYPES = ("MOIRE_COORDS",)
    RETURN_NAMES = ("coords",)

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "coords": ("MOIRE_COORDS",),
                "scale_rotate_re": ("FLOAT", {"default": 1.0, "min": -5.0, "max": 5.0, "step": 0.1}),
                "scale_rotate_im": ("FLOAT", {"default": 0.0, "min": -5.0, "max": 5.0, "step": 0.1}),
                "translate_re": ("FLOAT", {"default": 0.0, "min": -2.0, "max": 2.0, "step": 0.01}),
                "translate_im": ("FLOAT", {"default": 0.0, "min": -2.0, "max": 2.0, "step": 0.01}),
            }
        }

    def warp(self, coords: Tuple[np.ndarray, np.ndarray], scale_rotate_re: float, scale_rotate_im: float, 
             translate_re: float, translate_im: float) -> Tuple[Tuple[np.ndarray, np.ndarray]]:
        x, y = coords
        # (xr + i*yi) * (ar + i*ai) + (br + i*bi)
        # = (xr*ar - yi*ai + br) + i*(xr*ai + yi*ar + bi)
        x_out = x * scale_rotate_re - y * scale_rotate_im + translate_re
        y_out = x * scale_rotate_im + y * scale_rotate_re + translate_im
        return ((x_out, y_out),)


class MoireWarpComplexInversion:
    """
    Applies complex inversion to the coordinate grid.
    
    Formula:
    f(z) = 1 / z
    
    This maps the "inside outer" through a circle inversion. 
    Points near the origin move to infinity and vice versa.
    """
    CATEGORY = "Scromfy/Image/Moire/Complex"
    FUNCTION = "warp"
    RETURN_TYPES = ("MOIRE_COORDS",)
    RETURN_NAMES = ("coords",)

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "coords": ("MOIRE_COORDS",),
                "center_x": ("FLOAT", {"default": 0.0}),
                "center_y": ("FLOAT", {"default": 0.0}),
                "radius": ("FLOAT", {"default": 1.0, "min": 0.01}),
            }
        }

    def warp(self, coords: Tuple[np.ndarray, np.ndarray], center_x: float, center_y: float, radius: float) -> Tuple[Tuple[np.ndarray, np.ndarray]]:
        x, y = coords
        dx = x - center_x
        dy = y - center_y
        denom = dx**2 + dy**2 + 1e-10
        # 1/z = conj(z) / |z|^2
        x_out = center_x + (dx * radius**2) / denom
        y_out = center_y - (dy * radius**2) / denom
        return ((x_out, y_out),)


class MoireWarpComplexSine:
    """
    Applies the complex sine function to the coordinate grid.
    
    Formula:
    f(z) = sin(z) = sin(x)cosh(y) + i*cos(x)sinh(y)
    
    A conformal map that creates unique periodic tiling patterns.
    """
    CATEGORY = "Scromfy/Image/Moire/Complex"
    FUNCTION = "warp"
    RETURN_TYPES = ("MOIRE_COORDS",)
    RETURN_NAMES = ("coords",)

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "coords": ("MOIRE_COORDS",),
                "freq": ("FLOAT", {"default": 1.0, "min": 0.1, "max": 10.0}),
            }
        }

    def warp(self, coords: Tuple[np.ndarray, np.ndarray], freq: float) -> Tuple[Tuple[np.ndarray, np.ndarray]]:
        x, y = coords
        fx, fy = x * freq, y * freq
        x_out = np.sin(fx) * np.cosh(fy)
        y_out = np.cos(fx) * np.sinh(fy)
        return ((x_out, y_out),)


class MoireWarpComplexCos:
    """
    Applies the complex cosine function to the coordinate grid.
    
    Formula:
    f(z) = cos(z) = cos(x)cosh(y) - i*sin(x)sinh(y)
    """
    CATEGORY = "Scromfy/Image/Moire/Complex"
    FUNCTION = "warp"
    RETURN_TYPES = ("MOIRE_COORDS",)
    RETURN_NAMES = ("coords",)

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "coords": ("MOIRE_COORDS",),
                "freq": ("FLOAT", {"default": 1.0, "min": 0.1, "max": 10.0}),
            }
        }

    def warp(self, coords: Tuple[np.ndarray, np.ndarray], freq: float) -> Tuple[Tuple[np.ndarray, np.ndarray]]:
        x, y = coords
        fx, fy = x * freq, y * freq
        x_out = np.cos(fx) * np.cosh(fy)
        y_out = -np.sin(fx) * np.sinh(fy)
        return ((x_out, y_out),)


class MoireWarpComplexTan:
    """
    Applies the complex tangent function to the coordinate grid.
    
    Formula:
    f(z) = tan(z) = sin(z) / cos(z)
    """
    CATEGORY = "Scromfy/Image/Moire/Complex"
    FUNCTION = "warp"
    RETURN_TYPES = ("MOIRE_COORDS",)
    RETURN_NAMES = ("coords",)

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "coords": ("MOIRE_COORDS",),
                "freq": ("FLOAT", {"default": 1.0, "min": 0.1, "max": 10.0}),
            }
        }

    def warp(self, coords: Tuple[np.ndarray, np.ndarray], freq: float) -> Tuple[Tuple[np.ndarray, np.ndarray]]:
        x, y = coords
        # z = x + iy
        z = (x + 1j * y) * freq
        res = np.tan(z)
        return ((res.real, res.imag),)


class MoireWarpComplexHyperbolic:
    """
    Applies complex hyperbolic functions (sinh, cosh, tanh) to the coordinate grid.
    """
    CATEGORY = "Scromfy/Image/Moire/Complex"
    FUNCTION = "warp"
    RETURN_TYPES = ("MOIRE_COORDS",)
    RETURN_NAMES = ("coords",)

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "coords": ("MOIRE_COORDS",),
                "func": (["sinh", "cosh", "tanh"],),
                "freq": ("FLOAT", {"default": 1.0, "min": 0.1, "max": 10.0}),
            }
        }

    def warp(self, coords: Tuple[np.ndarray, np.ndarray], func: str, freq: float) -> Tuple[Tuple[np.ndarray, np.ndarray]]:
        x, y = coords
        z = (x + 1j * y) * freq
        if func == "sinh":
            res = np.sinh(z)
        elif func == "cosh":
            res = np.cosh(z)
        else:
            res = np.tanh(z)
        return ((res.real, res.imag),)


class MoireWarpComplexSquare:
    """
    Applies a complex square (or power n) function.
    
    Formula:
    f(z) = z^n
    where n is an integer or float.
    
    For n=2, it doubles the angle and squares the radius. 
    Useful for creating symmetric patterns or sector expansions.
    """
    CATEGORY = "Scromfy/Image/Moire/Complex"
    FUNCTION = "warp"
    RETURN_TYPES = ("MOIRE_COORDS",)
    RETURN_NAMES = ("coords",)

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "coords": ("MOIRE_COORDS",),
                "n": ("FLOAT", {"default": 2.0, "min": -5.0, "max": 5.0, "step": 0.1}),
            }
        }

    def warp(self, coords: Tuple[np.ndarray, np.ndarray], n: float) -> Tuple[Tuple[np.ndarray, np.ndarray]]:
        x, y = coords
        r = np.sqrt(x**2 + y**2) + 1e-10
        theta = np.arctan2(y, x)
        
        new_r = r ** n
        new_theta = theta * n
        
        x_out = new_r * np.cos(new_theta)
        y_out = new_r * np.sin(new_theta)
        return ((x_out, y_out),)


class MoireWarpComplexMobius:
    """
    Applies a general Möbius transformation to the coordinate grid.
    
    Formula:
    f(z) = (az + b) / (cz + d)
    where a, b, c, d are complex numbers.
    The most general conformal mapping for circles and lines.
    """
    CATEGORY = "Scromfy/Image/Moire/Complex"
    FUNCTION = "warp"
    RETURN_TYPES = ("MOIRE_COORDS",)
    RETURN_NAMES = ("coords",)

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "coords": ("MOIRE_COORDS",),
                "a_re": ("FLOAT", {"default": 1.0}), "a_im": ("FLOAT", {"default": 0.0}),
                "b_re": ("FLOAT", {"default": 0.0}), "b_im": ("FLOAT", {"default": 0.0}),
                "c_re": ("FLOAT", {"default": 0.0}), "c_im": ("FLOAT", {"default": 0.0}),
                "d_re": ("FLOAT", {"default": 1.0}), "d_im": ("FLOAT", {"default": 0.0}),
            }
        }

    def warp(self, coords: Tuple[np.ndarray, np.ndarray], 
             a_re, a_im, b_re, b_im, c_re, c_im, d_re, d_im) -> Tuple[Tuple[np.ndarray, np.ndarray]]:
        x, y = coords
        # z = x + iy
        # num = (a_re + i*a_im)(x + iy) + (b_re + i*b_im)
        num_re = a_re * x - a_im * y + b_re
        num_im = a_re * y + a_im * x + b_im
        
        # den = (c_re + i*c_im)(x + iy) + (d_re + i*d_im)
        den_re = c_re * x - c_im * y + d_re
        den_im = c_re * y + c_im * x + d_im
        
        denom = den_re**2 + den_im**2 + 1e-10
        
        # (num_re + i*num_im) / (den_re + i*den_im)
        # = (num_re + i*num_im)(den_re - i*den_im) / denom
        x_out = (num_re * den_re + num_im * den_im) / denom
        y_out = (num_im * den_re - num_re * den_im) / denom
        return ((x_out, y_out),)


# =============================================================================
# NOISE & TEXTURE GENERATION NODES
# =============================================================================

class MoireNoiseGenerator:
    """
    Generates high-quality spectral and cellular noise patterns.
    
    These patterns provide a structural "skeleton" for image refinement.
    Flavors:
    - White: Traditional Gaussian noise.
    - Blue: High-pass filtered (even distribution, no clumping).
    - Pink: 1/f spectral density (natural/organic).
    - Brownian: 1/f^2 spectral density (soft (clouds/smoke)).
    - Voronoi: Cellular/crystalline distance fields.
    - Gabor: Locally oriented structural noise.
    """
    CATEGORY = "Scromfy/Image/Moire"
    FUNCTION = "generate"
    RETURN_TYPES = ("IMAGE", "MASK")
    RETURN_NAMES = ("image", "mask")

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "width": ("INT", {"default": 1024, "min": 64, "max": 4096, "step": 8}),
                "height": ("INT", {"default": 1024, "min": 64, "max": 4096, "step": 8}),
                "flavor": (["white", "blue", "pink", "brownian", "voronoi", "gabor"],),
                "scale": ("FLOAT", {"default": 1.0, "min": 0.01, "max": 10.0, "step": 0.01}),
                "seed": ("INT", {"default": 42, "min": 0, "max": 0xffffffffffffffff}),
            },
            "optional": {
                "gabor_angle": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 180.0, "step": 1.0}),
                "voronoi_density": ("FLOAT", {"default": 20.0, "min": 1.0, "max": 200.0, "step": 1.0}),
            }
        }

    def _generate_spectral_noise(self, h: int, w: int, alpha: float, seed: int) -> np.ndarray:
        """Generates noise with 1/f^alpha spectral density."""
        rng = np.random.default_rng(seed)
        white = rng.standard_normal((h, w))
        
        # FFT to frequency domain
        freq_white = np.fft.fft2(white)
        
        # Create 1/f^alpha filter
        uy = np.fft.fftfreq(h)
        ux = np.fft.fftfreq(w)
        ux, uy = np.meshgrid(ux, uy)
        rho = np.sqrt(ux**2 + uy**2)
        rho[0, 0] = 1.0 # Avoid division by zero
        
        # Adjust filter for noise type
        # Power spectrum P(f) ~ 1/f^alpha => Magnitude |H(f)| ~ 1/f^(alpha/2)
        filt = 1.0 / (rho ** (alpha / 2.0))
        filt[0, 0] = 0.0 # DC component to zero
        
        filtered = freq_white * filt
        result = np.fft.ifft2(filtered).real
        
        # Normalize
        result = (result - result.min()) / (result.max() - result.min() + 1e-10)
        return result.astype(np.float32)

    def _generate_voronoi(self, h: int, w: int, density: float, seed: int) -> np.ndarray:
        """Generates a Voronoi distance field."""
        rng = np.random.default_rng(seed)
        num_points = int(density * 10) # Simple heuristic
        points = rng.random((num_points, 2))
        points[:, 0] *= w
        points[:, 1] *= h
        
        # Grid of coords
        y, x = np.mgrid[0:h, 0:w]
        coords = np.stack([x.ravel(), y.ravel()], axis=-1)
        
        # Find distance to nearest point
        # Using a simple brute force for now, can optimize if needed
        # dists[i] = min distance from pixel i to any point
        from scipy.spatial import cKDTree
        tree = cKDTree(points)
        dists, _ = tree.query(coords)
        
        result = dists.reshape(h, w)
        result = (result - result.min()) / (result.max() - result.min() + 1e-10)
        return result.astype(np.float32)

    def _generate_gabor(self, h: int, w: int, scale: float, angle: float, seed: int) -> np.ndarray:
        """Generates oriented Gabor-like structural noise."""
        rng = np.random.default_rng(seed)
        result = np.zeros((h, w), dtype=np.float32)
        
        # Parameters for Gabor kernels
        num_patches = 100
        patch_size = 64
        theta = np.deg2rad(angle)
        
        # Simple approximation: sum of oriented wavelets
        y, x = np.mgrid[-patch_size//2:patch_size//2, -patch_size//2:patch_size//2]
        
        # Precompute a single Gabor kernel
        sigma = patch_size / 4.0
        lambda_ = patch_size / 4.0
        x_theta = x * np.cos(theta) + y * np.sin(theta)
        y_theta = -x * np.sin(theta) + y * np.cos(theta)
        kernel = np.exp(-0.5 * (x_theta**2 + y_theta**2) / sigma**2) * np.cos(2 * np.pi * x_theta / lambda_)
        
        for _ in range(num_patches):
            px = rng.integers(0, w - patch_size)
            py = rng.integers(0, h - patch_size)
            amp = rng.uniform(0.5, 1.0)
            result[py:py+patch_size, px:px+patch_size] += amp * kernel
            
        # Normalize
        result = (result - result.min()) / (result.max() - result.min() + 1e-10)
        return result

    def generate(self, width: int, height: int, flavor: str, scale: float, seed: int, 
                 gabor_angle: float = 0.0, voronoi_density: float = 20.0) -> Tuple[torch.Tensor, torch.Tensor]:
        
        if flavor == "white":
            rng = np.random.default_rng(seed)
            pattern = rng.standard_normal((height, width)).astype(np.float32)
            pattern = (pattern - pattern.min()) / (pattern.max() - pattern.min() + 1e-10)
        elif flavor == "blue":
            pattern = self._generate_spectral_noise(height, width, -2.0, seed) # High pass
        elif flavor == "pink":
            pattern = self._generate_spectral_noise(height, width, 1.0, seed)
        elif flavor == "brownian":
            pattern = self._generate_spectral_noise(height, width, 2.0, seed)
        elif flavor == "voronoi":
            pattern = self._generate_voronoi(height, width, voronoi_density, seed)
        elif flavor == "gabor":
            pattern = self._generate_gabor(height, width, scale, gabor_angle, seed)
        else:
            pattern = np.zeros((height, width), dtype=np.float32)

        # Apply overall scale (contrast/frequency adjustment if needed, but for now just normalization)
        # We can implement frequency scaling by resizing or using the filter
        
        pattern_rgb = np.stack([pattern, pattern, pattern], axis=-1)
        image_tensor = torch.from_numpy(pattern_rgb).unsqueeze(0).float()
        mask_tensor = torch.from_numpy(pattern).unsqueeze(0).float()
        return (image_tensor, mask_tensor)


# =============================================================================
# RENDERING NODES
# =============================================================================

class MoireRenderer:
    """Renders a single-layer moiré pattern from coordinate grids."""
    CATEGORY = "Scromfy/Image/Moire"
    FUNCTION = "render"
    RETURN_TYPES = ("IMAGE", "MASK")
    RETURN_NAMES = ("image", "mask")

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "coords": ("MOIRE_COORDS",),
                "pattern_type": (["checker", "grid", "dots"], {"tooltip": "Base pattern geometry."}),
                "grid_size": ("FLOAT", {"default": 30.0, "min": 1.0, "max": 200.0, "step": 0.5, "tooltip": "Overall scale of the pattern."}),
                "grid_thickness": ("FLOAT", {"default": 0.1, "min": 0.01, "max": 0.5, "step": 0.01, "tooltip": "Line width for 'grid' mode."}),
                "dot_radius": ("FLOAT", {"default": 0.3, "min": 0.05, "max": 0.5, "step": 0.01, "tooltip": "Radius for 'dots' mode."}),
                "invert": ("BOOLEAN", {"default": False, "tooltip": "Flips the black and white values."}),
            }
        }

    @staticmethod
    def _generate_pattern(x: np.ndarray, y: np.ndarray, frequency: float, pattern_type: str, grid_thickness: float, dot_radius: float) -> np.ndarray:
        """Internal helper for base pattern generation."""
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

    def render(self, coords: Tuple[np.ndarray, np.ndarray], pattern_type: str, grid_size: float, 
               grid_thickness: float, dot_radius: float, invert: bool) -> Tuple[torch.Tensor, torch.Tensor]:
        """Renders the pattern into IMAGE and MASK tensors."""
        x, y = coords
        pattern = self._generate_pattern(x, y, grid_size, pattern_type, grid_thickness, dot_radius)
        if invert:
            pattern = 1.0 - pattern
        
        pattern_rgb = np.stack([pattern, pattern, pattern], axis=-1)
        image_tensor = torch.from_numpy(pattern_rgb).unsqueeze(0).float()
        mask_tensor = torch.from_numpy(pattern).unsqueeze(0).float()
        return (image_tensor, mask_tensor)


class MoireMultiGridRenderer:
    """Renders multiple layered moiré patterns with customizable blending."""
    CATEGORY = "Scromfy/Image/Moire"
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
                "grid_layers": ("INT", {"default": 3, "min": 2, "max": 8, "tooltip": "Number of layers to stack."}),
                "grid_ratio": ("FLOAT", {"default": 1.5, "min": 1.1, "max": 4.0, "step": 0.1, "tooltip": "Frequency multiplier per layer."}),
                "grid_blend_mode": (["xor", "add", "multiply", "difference"], {"tooltip": "Mathematical operation for blending layers."}),
                "invert": ("BOOLEAN", {"default": False}),
            }
        }

    def render(self, coords: Tuple[np.ndarray, np.ndarray], pattern_type: str, grid_size: float, grid_thickness: float, dot_radius: float, 
               grid_layers: int, grid_ratio: float, grid_blend_mode: str, invert: bool) -> Tuple[torch.Tensor, torch.Tensor]:
        """Renders stacked patterns."""
        x, y = coords
        layers = []
        for i in range(grid_layers):
            freq = grid_size * (grid_ratio ** i)
            layer = MoireRenderer._generate_pattern(x, y, freq, pattern_type, grid_thickness, dot_radius)
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
    """Applies coordinate-based distortions to an existing image or mask."""
    CATEGORY = "Scromfy/Image/Moire"
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

    @staticmethod
    def _apply_warp_to_image(image: np.ndarray, x_warped: np.ndarray, y_warped: np.ndarray) -> np.ndarray:
        """Internal helper for remapping images using scipy."""
        if not HAS_SCIPY:
            print(f"[Warning] Scromfy Moire: {get_scipy_error_message()}")
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

    def apply(self, coords: Tuple[np.ndarray, np.ndarray], image: torch.Tensor, mask: Optional[torch.Tensor] = None) -> Tuple[torch.Tensor, torch.Tensor]:
        """Applies remapping to tensors."""
        x, y = coords
        img_np = image[0].cpu().numpy()
        result_img = self._apply_warp_to_image(img_np, x, y)
        out_image = torch.from_numpy(result_img).unsqueeze(0).float()
        
        if mask is not None:
            mask_np = mask[0].cpu().numpy() if len(mask.shape) == 3 else mask.cpu().numpy()
            result_mask = self._apply_warp_to_image(mask_np, x, y)
            out_mask = torch.from_numpy(result_mask).unsqueeze(0).float()
        else:
            out_mask = torch.zeros(1, out_image.shape[1], out_image.shape[2])
            
        return (out_image, out_mask)


# ComfyUI node mappings
NODE_CLASS_MAPPINGS = {
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
    
    # Complex Transforms
    "MoireWarpComplexLog": MoireWarpComplexLog,
    "MoireWarpComplexExp": MoireWarpComplexExp,
    "MoireWarpComplexPower": MoireWarpComplexPower,
    "MoireWarpComplexLinear": MoireWarpComplexLinear,
    "MoireWarpComplexInversion": MoireWarpComplexInversion,
    "MoireWarpComplexSine": MoireWarpComplexSine,
    "MoireWarpComplexCos": MoireWarpComplexCos,
    "MoireWarpComplexTan": MoireWarpComplexTan,
    "MoireWarpComplexHyperbolic": MoireWarpComplexHyperbolic,
    "MoireWarpComplexSquare": MoireWarpComplexSquare,
    "MoireWarpComplexMobius": MoireWarpComplexMobius,
    
    "MoireRenderer": MoireRenderer,
    "MoireMultiGridRenderer": MoireMultiGridRenderer,
    "MoireImageWarp": MoireImageWarp,
    "MoireNoiseGenerator": MoireNoiseGenerator,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "MoireCoordinates": "Moiré Coordinates 🧩",
    "MoireWarpSinusoidal": "Moiré Warp Sinusoidal 🌊",
    "MoireWarpBulge": "Moiré Warp Bulge 🎈",
    "MoireWarpSwirl": "Moiré Warp Swirl 🌀",
    "MoireWarpNoise": "Moiré Warp Noise 🎲",
    "MoireWarpWave": "Moiré Warp Multi-Wave 📡",
    "MoireWarpBarrel": "Moiré Warp Barrel 🛢️",
    "MoireWarpRipple": "Moiré Warp Ripple 🔘",
    "MoireWarpShear": "Moiré Warp Shear 📐",
    "MoireWarpFisheye": "Moiré Warp Fisheye 🐟",
    "MoireWarpTwist": "Moiré Warp Twist 🌪️",
    
    # Complex Transforms
    "MoireWarpComplexLog": "Moiré Complex Log 🪵",
    "MoireWarpComplexExp": "Moiré Complex Exp ⚡",
    "MoireWarpComplexPower": "Moiré Complex Power 🔋",
    "MoireWarpComplexLinear": "Moiré Complex Linear 📏",
    "MoireWarpComplexInversion": "Moiré Complex Inversion 🙃",
    "MoireWarpComplexSine": "Moiré Complex Sine 📐",
    "MoireWarpComplexCos": "Moiré Complex Cosine 📐",
    "MoireWarpComplexTan": "Moiré Complex Tangent 📐",
    "MoireWarpComplexHyperbolic": "Moiré Complex Hyperbolic 📐",
    "MoireWarpComplexSquare": "Moiré Complex Power N 🧊",
    "MoireWarpComplexMobius": "Moiré Complex Möbius 💍",
    
    "MoireRenderer": "Moiré Renderer 🎨",
    "MoireMultiGridRenderer": "Moiré Multi-Grid Renderer 🎭",
    "MoireImageWarp": "Moiré Image Warp 🖼️",
    "MoireNoiseGenerator": "Moiré Noise Generator 🎲🧪",
}
