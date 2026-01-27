"""
Scromfy Mask and Geometric Utility Nodes - Splitting, Borders, and LIR Analysis
Absolute Functional Restoration (Zero Loss)
"""

import torch
import numpy as np
import largestinteriorrectangle as lir
from PIL import Image
from typing import List, Tuple, Dict, Any, Optional

# Import shared utilities
from .support.constants import (
    DEF_FALSEBOOL,
    DEF_TRUEBOOL,
    COLOR_MAPPING
)
from .support.scromfy_utils import (
    tensor2pil,
    pil2tensor,
    hex_to_rgb,
    make_3d_mask,
    RectDimensions
)

# =============================================================================
# MASK ANALYSIS NODES
# =============================================================================

class LargestRectInMask:
    """Finds the largest rectangle that fits inside binary masks with visualization."""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "mask": ("MASK", ),
                "input_image": ("IMAGE", ),
                "threshold": ("FLOAT", {
                    "default": 0.0,
                    "min": 0,
                    "max": 1.0,
                    "step": 0.01
                }),
            }
        }

    RETURN_TYPES = (
        "INT", "INT", "INT", "INT", "INT", "INT", "INT", "INT", "INT", "BBOX", "IMAGE"
    )
    RETURN_NAMES = (
        "startX", "startY", "endX", "endY", "centerX", "centerY", "width", "height", "area", "bbox", "preview_image"
    )
    OUTPUT_IS_LIST = (
        True, True, True, True, True, True, True, True, True, True, True
    )
    FUNCTION = "execute"
    CATEGORY = "Scromfy/Mask"

    def preview_bbox(self, bbox: RectDimensions, image: torch.Tensor, line_width: int = 5) -> torch.Tensor:
        """Draws a red bounding box onto the image tensor for verification."""
        x_min, y_min, w, h = int(bbox.x), int(bbox.y), int(bbox.width), int(bbox.height)
        img = image.permute(2, 0, 1) # HWC -> CHW
        img_out = img.clone()
        clr = torch.tensor([1, 0, 0], dtype=torch.float32)
        
        for lw in range(line_width):
            if y_min + lw < img_out.shape[1]:
                img_out[:, y_min + lw, x_min:x_min + w] = clr[:, None]
            if y_min + h - lw < img_out.shape[1]:
                img_out[:, y_min + h - lw, x_min:x_min + w] = clr[:, None]
            if x_min + lw < img_out.shape[2]:
                img_out[:, y_min:y_min + h, x_min + lw] = clr[:, None]
            if x_min + w - lw < img_out.shape[2]:
                img_out[:, y_min:y_min + h, x_min + w - lw] = clr[:, None]
                
        return img_out.permute(1, 2, 0).unsqueeze(0) # CHW -> HWC then add batch

    def find_rect_in_mask(self, mask: np.ndarray, image: torch.Tensor, threshold: float) -> tuple:
        """Core LIR logic for a single mask item."""
        grid = (mask > threshold).astype(np.bool_)
        rect = lir.lir(grid)
        sx, sy, wx, wy = int(rect[0]), int(rect[1]), int(rect[2]), int(rect[3])
        ex, ey = sx + wx, sy + wy
        cx, cy = (sx + ex) // 2, (sy + ey) // 2
        area = wx * wy
        bbox = RectDimensions(sx, sy, wx, wy)
        preview = self.preview_bbox(bbox, image)
        return sx, sy, ex, ey, cx, cy, wx, wy, area, bbox, preview

    def execute(self, mask, input_image, threshold):
        res_sx, res_sy, res_ex, res_ey, res_cx, res_cy, res_wx, res_wy, res_area, res_bbox, res_preview = (
            [], [], [], [], [], [], [], [], [], [], []
        )

        image_base = input_image[0]
        mask_pile = []

        if isinstance(mask, torch.Tensor):
            if mask.dim() == 3:
                mask_pile = [m.numpy() for m in torch.unbind(mask, dim=0)]
            elif mask.dim() == 4:
                mask_pile = [m.numpy() for m in torch.unbind(mask.squeeze(1), dim=0)]
            elif mask.dim() == 2:
                mask_pile = [mask.numpy()]
        elif isinstance(mask, list):
            mask_pile = [m.cpu().numpy() if hasattr(m, "cpu") else m for m in mask]

        for m_item in mask_pile:
            sx, sy, ex, ey, cx, cy, wx, wy, area, bbox, preview = self.find_rect_in_mask(m_item, image_base, threshold)
            res_sx.append(sx)
            res_sy.append(sy)
            res_ex.append(ex)
            res_ey.append(ey)
            res_cx.append(cx)
            res_cy.append(cy)
            res_wx.append(wx)
            res_wy.append(wy)
            res_area.append(area)
            res_bbox.append(bbox)
            res_preview.append(preview)

        return (
            res_sx, res_sy, res_ex, res_ey, res_cx, res_cy, res_wx, res_wy, res_area, res_bbox, torch.stack(res_preview).squeeze(1)
        )

# =============================================================================
# MASK MANIPULATION NODES
# =============================================================================

class SplitMaskByGrid:
    """Splits a mask into a grid of smaller masks with binary/invert support."""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "mask": ("MASK", ),
                "rows": ("INT", {"default": 2, "min": 1}),
                "columns": ("INT", {"default": 2, "min": 1}),
                "invert": DEF_FALSEBOOL,
                "binary": DEF_FALSEBOOL,
                "threshold": ("FLOAT", {"default": 0.0, "min": 0, "max": 1.0, "step": 0.01}),
            }
        }

    RETURN_TYPES = ("MASK", "MASK")
    RETURN_NAMES = ("batched_mask", "mask_list")
    OUTPUT_IS_LIST = (False, True)
    FUNCTION = "execute"
    CATEGORY = "Scromfy/Mask"

    def execute(self, mask, rows, columns, invert, binary, threshold):
        _, H, W = mask.shape
        rh, cw = H // rows, W // columns
        masks = []
        for i in range(rows):
            for j in range(columns):
                m = torch.zeros_like(mask)
                m[:, i*rh:(i+1)*rh, j*cw:(j+1)*cw] = mask[:, i*rh:(i+1)*rh, j*cw:(j+1)*cw]
                if binary: m = (m > threshold).float()
                if invert: m = 1.0 - m
                masks.append(m)
        
        batched = torch.stack(masks, dim=0).unsqueeze(1)
        m_list = [make_3d_mask(x) for x in masks]
        return (batched, m_list)

# =============================================================================
# IMAGE MANIPULATION NODES
# =============================================================================

class ScruffyBorder:
    """Adds nested stylistic borders with optional alpha and side selection."""
    
    @classmethod
    def INPUT_TYPES(cls):
        color_list = ["Use Color Picker"] + sorted(list(COLOR_MAPPING.keys()))
        return {
            "required": {
                "image": ("IMAGE", ),
                "color": ("COLOR", {"default": "#000000"}),
                "color_v": (color_list, {"default": "Use Color Picker"}),
                "border_size": ("INT", {"default": 2, "min": 1}),
                "top": DEF_TRUEBOOL,
                "bottom": DEF_TRUEBOOL,
                "left": DEF_TRUEBOOL,
                "right": DEF_TRUEBOOL,
                "second_border": DEF_TRUEBOOL,
                "color2": ("COLOR", {"default": "#FFFFFF"}),
                "color2_v": (color_list, {"default": "Use Color Picker"}),
                "border2_size": ("INT", {"default": 1, "min": 0}),
            }
        }

    RETURN_TYPES = ("IMAGE", )
    FUNCTION = "execute"
    CATEGORY = "Scromfy/Image"

    def execute(self, image, color, color_v, border_size, second_border, color2, color2_v, border2_size, top, bottom, left, right):
        # Resolve Colors: Dropdown overrides picker if not 'Use Color Picker'
        if color_v != "Use Color Picker":
            rgb = COLOR_MAPPING.get(color_v, (0, 0, 0))
            color = "#{:02x}{:02x}{:02x}".format(*rgb)
        
        if color2_v != "Use Color Picker":
            rgb = COLOR_MAPPING.get(color2_v, (255, 255, 255))
            color2 = "#{:02x}{:02x}{:02x}".format(*rgb)

        rgb1 = hex_to_rgb(color)
        rgb2 = hex_to_rgb(color2)
        
        pil_img = tensor2pil(image)
        data = np.array(pil_img)
        ch = image.shape[3]
        
        def apply_b(arr, sz, clr):
            b_val = list(clr) + ([255] if ch == 4 else [])
            if top: arr[:sz, :] = b_val
            if bottom: arr[-sz:, :] = b_val
            if left: arr[:, :sz] = b_val
            if right: arr[:, -sz:] = b_val

        if second_border:
            apply_b(data, border2_size, rgb2)
        apply_b(data, border_size, rgb1)
        
        res_pil = Image.fromarray(data, mode='RGBA' if ch == 4 else 'RGB')
        return (pil2tensor(res_pil), )

# =============================================================================
# MAPPING
# =============================================================================

NODE_CLASS_MAPPINGS = {
    "LargestRectInMask": LargestRectInMask,
    "SplitMaskByGrid": SplitMaskByGrid,
    "ScruffyBorder": ScruffyBorder
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LargestRectInMask": "Largest Rect in Mask (Advanced)",
    "SplitMaskByGrid": "Split Mask by Grid (Advanced)",
    "ScruffyBorder": "Add Scruffy Border"
}
