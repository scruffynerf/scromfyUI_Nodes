"""
Scromfy Node Utilities - PIL, SVG, Geometric, and Layout Helpers
Absolute Functional Restoration (Zero Loss)
"""

import random
import torch
import numpy as np
import json
import os
import math
from PIL import Image, ImageFont, ImageDraw
from dataclasses import dataclass
from typing import List, Tuple, Dict, Any, Optional

# =============================================================================
# CONSTANTS & DEFINITIONS
# =============================================================================

XYZW_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "tmpgen",
    "currentgen.json"
)

# Shared return type definitions for consistency
DEF_STRING_ML = ("STRING", {"default": "", "multiline": True})
DEF_STRING = ("STRING", {"default": ""})
DEF_STRING_INPUT = ("STRING", {"default": "", "forceInput": True})
DEF_PROMPT = ("STRING", {"default": "", "multiline": True, "dynamicPrompts": True})
DEF_FALSEBOOL = ("BOOLEAN", {"default": False, "label_on": "enabled", "label_off": "disabled"})
DEF_TRUEBOOL = ("BOOLEAN", {"default": True, "label_on": "enabled", "label_off": "disabled"})

class AnyType(str):
    """A special class that is always equal in not equal comparisons."""
    def __ne__(self, __value: object) -> bool:
        return False

ANY_ = AnyType("*")
DEF_ANYINPUT = (ANY_, {'forceInput': True})

# Layout Options
ALIGN_OPTIONS = ["center", "top", "bottom"]
ROTATE_OPTIONS = ["text center", "image center"]
JUSTIFY_OPTIONS = ["center", "left", "right"]
PERSPECTIVE_OPTIONS = ["top", "bottom", "left", "right"]

# =============================================================================
# COLOR DYNAMICS
# =============================================================================

COLOR_MAPPING = {
    "white": (255, 255, 255),
    "black": (0, 0, 0),
    "red": (255, 0, 0),
    "green": (0, 255, 0),
    "blue": (0, 0, 255),
    "yellow": (255, 255, 0),
    "cyan": (0, 255, 255),
    "magenta": (255, 0, 255),
    "orange": (255, 165, 0),
    "purple": (128, 0, 128),
    "pink": (255, 192, 203),
    "brown": (165, 42, 42),
    "brown2": (160, 85, 15),
    "gray": (128, 128, 128),
    "lightgray": (211, 211, 211),
    "darkgray": (169, 169, 169),
    "darkgray2": (102, 102, 102),
    "olive": (128, 128, 0),
    "lime": (0, 128, 0),
    "teal": (0, 128, 128),
    "navy": (0, 0, 128),
    "maroon": (128, 0, 0),
    "fuchsia": (255, 0, 128),
    "aqua": (0, 255, 128),
    "silver": (192, 192, 192),
    "gold": (255, 215, 0),
    "turquoise": (64, 224, 208),
    "lavender": (230, 230, 250),
    "violet": (238, 130, 238),
    "coral": (255, 127, 80),
    "indigo": (75, 0, 130),
    "darkblue": (0, 0, 139),
    "mediumblue": (0, 0, 205),
    "darkgreen": (0, 100, 0),
    "darkcyan": (0, 139, 139),
    "deepskyblue": (0, 191, 255),
    "darkturquoise": (0, 206, 209),
    "mediumspringgreen": (0, 250, 154),
    "springgreen": (0, 255, 127),
    "midnightblue": (25, 25, 112),
    "dodgerblue": (30, 144, 255),
    "lightseagreen": (32, 178, 170),
    "forestgreen": (34, 139, 34),
    "seagreen": (46, 139, 87),
    "darkslategray": (47, 79, 79),
    "darkslategrey": (47, 79, 79),
    "limegreen": (50, 205, 50),
    "mediumseagreen": (60, 179, 113),
    "royalblue": (65, 105, 225),
    "steelblue": (70, 130, 180),
    "darkslateblue": (72, 61, 139),
    "mediumturquoise": (72, 209, 204),
    "darkolivegreen": (85, 107, 47),
    "cadetblue": (95, 158, 160),
    "cornflowerblue": (100, 149, 237),
    "mediumaquamarine": (102, 205, 170),
    "dimgrey": (105, 105, 105),
    "dimgray": (105, 105, 105),
    "slateblue": (106, 90, 205),
    "olivedrab": (107, 142, 35),
    "slategrey": (112, 128, 144),
    "slategray": (112, 128, 144),
    "lightslategray": (119, 136, 153),
    "lightslategrey": (119, 136, 153),
    "mediumslateblue": (123, 104, 238),
    "lawngreen": (124, 252, 0),
    "chartreuse": (127, 255, 0),
    "aquamarine": (127, 255, 212),
    "grey": (128, 128, 128),
    "skyblue": (135, 206, 235),
    "lightskyblue": (135, 206, 250),
    "blueviolet": (138, 43, 226),
    "darkred": (139, 0, 0),
    "darkmagenta": (139, 0, 139),
    "saddlebrown": (139, 69, 19),
    "darkseagreen": (143, 188, 143),
    "lightgreen": (144, 238, 144),
    "mediumpurple": (147, 112, 219),
    "darkviolet": (148, 0, 211),
    "palegreen": (152, 251, 152),
    "darkorchid": (153, 50, 204),
    "yellowgreen": (154, 205, 50),
    "sienna": (160, 82, 45),
    "lightblue": (173, 216, 230),
    "greenyellow": (173, 255, 47),
    "paleturquoise": (175, 238, 238),
    "lightsteelblue": (176, 196, 222),
    "powderblue": (176, 224, 230),
    "firebrick": (178, 34, 34),
    "darkgoldenrod": (184, 134, 11),
    "mediumorchid": (186, 85, 211),
    "rosybrown": (188, 143, 143),
    "darkkhaki": (189, 183, 107),
    "mediumvioletred": (199, 21, 133),
    "indianred": (205, 92, 92),
    "peru": (205, 133, 63),
    "chocolate": (210, 105, 30),
    "tan": (210, 180, 140),
    "lightgrey": (211, 211, 211),
    "thistle": (216, 191, 216),
    "orchid": (218, 112, 214),
    "goldenrod": (218, 165, 32),
    "palevioletred": (219, 112, 147),
    "crimson": (220, 20, 60),
    "gainsboro": (220, 220, 220),
    "plum": (221, 160, 221),
    "burlywood": (222, 184, 135),
    "lightcyan": (224, 255, 255),
    "darksalmon": (233, 150, 122),
    "palegoldenrod": (238, 232, 170),
    "lightcoral": (240, 128, 128),
    "khaki": (240, 230, 140),
    "aliceblue": (240, 248, 255),
    "honeydew": (240, 255, 240),
    "azure": (240, 255, 255),
    "sandybrown": (244, 164, 96),
    "wheat": (245, 222, 179),
    "beige": (245, 245, 220),
    "whitesmoke": (245, 245, 245),
    "mintcream": (245, 255, 250),
    "ghostwhite": (248, 248, 255),
    "salmon": (250, 128, 114),
    "antiquewhite": (250, 235, 215),
    "linen": (250, 240, 230),
    "lightgoldenrodyellow": (250, 250, 210),
    "oldlace": (253, 245, 230),
    "deeppink": (255, 20, 147),
    "orangered": (255, 69, 0),
    "tomato": (255, 99, 71),
    "hotpink": (255, 105, 180),
    "darkorange": (255, 140, 0),
    "lightsalmon": (255, 160, 122),
    "lightpink": (255, 182, 193),
    "peachpuff": (255, 218, 185),
    "navajowhite": (255, 222, 173),
    "moccasin": (255, 228, 181),
    "bisque": (255, 228, 196),
    "mistyrose": (255, 228, 225),
    "blanchedalmond": (255, 235, 205),
    "papayawhip": (255, 239, 213),
    "lavenderblush": (255, 240, 245),
    "seashell": (255, 245, 238),
    "cornsilk": (255, 248, 220),
    "lemonchiffon": (255, 250, 205),
    "floralwhite": (255, 250, 240),
    "snow": (255, 250, 250),
    "lightyellow": (255, 255, 224),
    "ivory": (255, 255, 240),
}

COLORS = ["custom"] + list(COLOR_MAPPING.keys())

def hex_to_rgb(hex_color: str) -> tuple:
    hex_color = hex_color.lstrip("#")
    return (
        int(hex_color[:2], 16),
        int(hex_color[2:4], 16),
        int(hex_color[4:6], 16)
    )

def rgb_to_hex(colortuple: tuple) -> str:
    return "#{:02x}{:02x}{:02x}".format(
        colortuple[0],
        colortuple[1],
        colortuple[2]
    )

def get_color_values(color: str, color_hex: str = "#000000", color_map: dict = COLOR_MAPPING) -> tuple:
    if color == "custom":
        return hex_to_rgb(color_hex)
    return color_map.get(color, (0, 0, 0))

def interpolate_color(color0: tuple, color1: tuple, t: float) -> tuple:
    return tuple(
        int(c0 * (1 - t) + c1 * t)
        for c0, c1 in zip(color0, color1)
    )

def random_rgb() -> tuple:
    return (
        random.randint(0, 255),
        random.randint(0, 255),
        random.randint(0, 255)
    )

# =============================================================================
# GEOMETRIC & LAYOUT HELPERS
# =============================================================================

@dataclass
class Point:
    x: float
    y: float
    def __iter__(self):
        return iter((self.x, self.y))

class BezierCurve:
    def __init__(self, p1: Point, p2: Point, p3: Point, p4: Point):
        self.points = [p1, p2, p3, p4]
    def __iter__(self):
        return iter(self.points)

def slerp(a: float, b: float, t: float = 0.5) -> float:
    return a * (1 - t) + b * t

def slerp_points(p1: Point, p2: Point, t: float = 0.5) -> Point:
    return Point(
        slerp(p1.x, p2.x, t),
        slerp(p1.y, p2.y, t)
    )

def bez_split(curve: BezierCurve, t: float = 0.5) -> List[BezierCurve]:
    """De Casteljau's Algorithm for Bezier splitting"""
    pts = curve.points
    e = slerp_points(pts[0], pts[1], t)
    f = slerp_points(pts[1], pts[2], t)
    g = slerp_points(pts[2], pts[3], t)
    h = slerp_points(e, f, t)
    j = slerp_points(f, g, t)
    k = slerp_points(h, j, t)
    return [
        BezierCurve(pts[0], e, h, k),
        BezierCurve(k, j, g, pts[3])
    ]

class RectDimensions:
    def __init__(self, x: int, y: int, width: int, height: int):
        self.x, self.y, self.width, self.height = x, y, width, height
    def __iter__(self):
        return iter((self.x, self.y, self.width, self.height))

def adjust_ratios(ratio_x: int, ratio_y: int) -> tuple:
    return (ratio_x - 1, ratio_y) if ratio_x > ratio_y else (ratio_x, ratio_y - 1)

def get_divisors(num: int) -> List[int]:
    if num <= 1:
        return [1, 1]
    divs = [i for i in range(1, num + 1) if num % i == 0]
    divs.reverse()
    return divs

# =============================================================================
# TENSOR & IMAGE PROCESSING
# =============================================================================

def tensor2pil(image: torch.Tensor) -> Image.Image:
    return Image.fromarray(
        np.clip(255.0 * image.cpu().numpy().squeeze(), 0, 255).astype(np.uint8)
    )

def pil2tensor(image: Image.Image) -> torch.Tensor:
    return torch.from_numpy(np.array(image).astype(np.float32) / 255.0).unsqueeze(0)

def make_3d_mask(mask: torch.Tensor) -> torch.Tensor:
    if len(mask.shape) == 4:
        return mask.squeeze(0)
    if len(mask.shape) == 2:
        return mask.unsqueeze(0)
    return mask

def resize_and_center_image(pil_image: Image.Image, sw: int, sh: int) -> tuple:
    iw, ih = pil_image.size
    f = min(sw / iw, sh / ih)
    nw, nh = int(iw * f), int(ih * f)
    res = pil_image.resize((nw, nh))
    return res, (sw - nw) // 2, (sh - nh) // 2

# =============================================================================
# TEXT & JSON UTILS
# =============================================================================

def justify_text(justify: str, iw: int, lw: int, margins: int) -> float:
    if justify == "left":
        return float(margins)
    if justify == "right":
        return float(iw - lw - margins)
    return float(iw / 2 - lw / 2)

def align_text(align: str, ih: int, th: int, py: int, margins: int) -> float:
    if align == "bottom":
        return float(ih - th + py - margins)
    if align == "center":
        return float(ih / 2 - th / 2 + py)
    return float(py + margins)

def find_control_value(key: str, path: str = XYZW_PATH) -> Any:
    try:
        with open(path, 'r') as f:
            data = json.load(f)
        for k, v in data.items():
            if k.endswith("_control") and v == key:
                l = k.split('_')[0]
                return data.get(f"{l}_value")
    except:
        pass
    return None

def write_json_to_file(data: Any, path: str = XYZW_PATH) -> None:
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as f:
            json.dump(data, f, indent=4, sort_keys=True)
    except Exception as e:
        print(f"Scromfy Utils: Failed to write JSON: {e}")

def draw_masked_text(
    mask_image: Image.Image,
    text: str,
    font_name: str,
    font_size: int,
    margins: int,
    line_spacing: int,
    pos_x: int,
    pos_y: int,
    align: str,
    justify: str,
    rotation: float,
    rotation_options: str = "text center"
) -> Image.Image:
    """Draws multi-line text onto a mask with enhanced layout logic."""
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    font_path = os.path.join(root_dir, "fonts", font_name)
    
    try:
        font = ImageFont.truetype(font_path, font_size)
    except:
        font = ImageFont.load_default()

    draw = ImageDraw.Draw(mask_image)
    w_img, h_img = mask_image.size
    lines = text.split('\n')
    
    metrics = []
    max_w, max_h = 0, 0
    for line in lines:
        bbox = font.getbbox(line)
        w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        metrics.append((line, w, h))
        max_w = max(max_w, w)
        max_h = max(max_h, h + line_spacing)
    
    total_h = max_h * len(lines)
    cur_y = align_text(align, h_img, total_h, pos_y, margins)
    sum_y = 0
    
    for line, wl, hl in metrics:
        cur_x = float(pos_x) + justify_text(justify, w_img, wl, margins)
        draw.text((cur_x, cur_y), line, fill=255, font=font)
        sum_y += cur_y
        cur_y += max_h

    # Centered Rotation
    tx_mid = float(pos_x) + justify_text(justify, w_img, max_w, margins) + max_w / 2
    ty_mid = sum_y / len(lines)
    
    if rotation != 0:
        if rotation_options == "text center":
            return mask_image.rotate(rotation, center=(tx_mid, ty_mid))
        return mask_image.rotate(rotation, center=(w_img / 2, h_img / 2))
        
    return mask_image
