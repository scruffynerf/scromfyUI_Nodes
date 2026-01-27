"""
Scromfy Text Nodes - Specialized Graphical Text Elements
Includes the ScruffyTextBalloon node with complex SVG path generation.
"""

import os
import io
import math
import random
# import svg
# import cairosvg
from typing import Dict, List, Any, Optional
from PIL import Image, ImageDraw, ImageFont

# Import shared utilities
from .support.constants import (
    COLORS,
    COLOR_MAPPING,
    DEF_TRUEBOOL,
    DEF_FALSEBOOL,
    DEF_STRING_ML
)
from .support.scromfy_utils import (
    pil2tensor,
    get_color_values,
    rgb_to_hex,
    draw_masked_text,
    slerp_points,
    bez_split,
    BezierCurve,
    Point,
    ALIGN_OPTIONS,
    ROTATE_OPTIONS,
    JUSTIFY_OPTIONS
)

# =============================================================================
# SPEECH BALLOON HELPERS
# =============================================================================

def split_text_diamond(text: str, max_width: int) -> List[str]:
    """Splits text into a diamond-like shape suitable for balloons."""
    words = text.split()
    textlen = len(text)
    sorted_words = sorted(words, key=len, reverse=True)
    maxlen = len(sorted_words[0]) if sorted_words else 0
    if maxlen > max_width:
        max_width = maxlen + 1
    
    num_lines = math.ceil((textlen + 2) / max_width)
    total, placed = 0, False
    while not placed:
        while total < textlen:
            lengths = []
            for i in range(1, num_lines + 1):
                p = (num_lines - int(abs(i - ((num_lines + 1) / 2)))) / num_lines
                p = min(1.0, max(0.6, p + 0.1))
                lengths.append(max(maxlen, int(max_width * p)))
            total = sum(lengths)
            if textlen > total:
                num_lines += 1
        
        split_lines = [''] * len(lengths)
        cur = 0
        for i in range(len(lengths)):
            line_len = lengths[i]
            while cur < len(words) and (len(split_lines[i]) + len(words[cur]) <= max_width):
                split_lines[i] += words[cur] + ' '
                line_len -= (len(words[cur]) + 1)
                cur += 1
                if cur == len(words):
                    placed = True
                    break
                if line_len <= 0 or (cur < len(words) and line_len - len(words[cur]) <= 0):
                    break
            split_lines[i] = split_lines[i].strip()
        if not placed:
            num_lines += 1
            total = 0
    return list(filter(None, split_lines))

# =============================================================================
# MAIN BALLOON NODE (UNDER CONSTRUCTION - DISABLED)
# =============================================================================

class ScruffyTextBalloon:
    """Generates advanced stylistic speech balloons with SVG paths."""
    
    @classmethod
    def INPUT_TYPES(cls):
        font_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "fonts")
        fonts = [f for f in os.listdir(font_dir) if f.lower().endswith(".ttf")] if os.path.exists(font_dir) else []
        
        return {
            "required": {
                "text": ("STRING", {"multiline": True, "default": "Hello Scromfy!"}),
                "autoformat": DEF_TRUEBOOL,
                "max_text_width": ("INT", {"default": 30, "min": 3, "max": 80}),
                "balloon_type": (['round', 'rectangle', 'cloud', 'spiky', 'wavy'], ),
                "balloon_complexity": ("INT", {"default": 1, "min": 1, "max": 5}),
                "balloon_complexity_random": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 10,
                    "display": "slider"
                }),
                "balloon_tweak_random": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 200,
                    "display": "slider"
                }),
                "balloon_tweak_min": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 200,
                    "display": "slider"
                }),
                "taillocation": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 360,
                    "display": "slider"
                }),
                "tailangle": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 360,
                    "display": "slider"
                }),
                "tailsize": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 200,
                    "display": "slider"
                }),
                "tailcurve": ("INT", {
                    "default": 0,
                    "min": -30,
                    "max": 30,
                    "display": "slider"
                }),
                "autosize": DEF_TRUEBOOL,
                "max_image_width": ("INT", {"default": 512, "min": 64, "max": 2048}),
                "max_image_height": ("INT", {"default": 512, "min": 64, "max": 2048}),
                "font_size": ("INT", {"default": 50, "min": 1, "max": 1024}),
                "font_name": (fonts, ),
                "align": (ALIGN_OPTIONS, ),
                "justify": (JUSTIFY_OPTIONS, ),
                "margins": ("INT", {"default": 0}),
                "line_spacing": ("INT", {"default": 0}),
                "position_x": ("INT", {"default": 0}),
                "position_y": ("INT", {"default": 0}),
                "rotation_angle": ("FLOAT", {"default": 0.0, "min": -360.0, "max": 360.0}),
                "rotation_options": (ROTATE_OPTIONS, ),
                "font_color": (COLORS, ),
                "background_color": (COLORS, {"default": "white"}),
                "balloon_stroke_color": (COLORS, {"default": "black"}),
            },
            "optional": {
                "font_color_hex": ("STRING", {"default": "#000000"}),
                "bg_color_hex": ("STRING", {"default": "#FFFFFF"}),
                "balloon_stroke_hex": ("STRING", {"default": "#000000"}),
            }
        }

    RETURN_TYPES = ("IMAGE", )
    FUNCTION = "execute"
    CATEGORY = "Scromfy/Text"

    def execute(
        self, text, max_image_width, max_image_height, font_name, font_size,
        font_color, background_color, balloon_stroke_color, margins,
        line_spacing, position_x, position_y, align, justify,
        rotation_angle, rotation_options, balloon_complexity,
        balloon_complexity_random, autosize, autoformat, balloon_type,
        tailsize, taillocation, tailangle, tailcurve,
        balloon_tweak_random, balloon_tweak_min, max_text_width,
        font_color_hex='#000000', bg_color_hex='#FFFFFF',
        balloon_stroke_hex='#000000'
    ):
        text_color = get_color_values(font_color, font_color_hex)
        bg_color = get_color_values(background_color, bg_color_hex)
        outline_color = get_color_values(balloon_stroke_color, balloon_stroke_hex)
        bg_hex = rgb_to_hex(bg_color)
        outline_hex = rgb_to_hex(outline_color)

        size = (max_image_width, max_image_height)
        text_image = Image.new('RGB', size, text_color)
        text_mask = Image.new('L', size)
        
        # Split logic
        if autoformat:
            text_lines = split_text_diamond(text, max_text_width)
        else:
            text_lines = text.split('\n')
        
        reformatted_text = '\n'.join(text_lines)
        
        # Autosize
        if autosize:
            longest = max(text_lines, key=len)
            font_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "fonts", font_name)
            while font_size > 1:
                try: font = ImageFont.truetype(font_path, font_size)
                except: font = ImageFont.load_default()
                bbox = font.getbbox(longest)
                tw = bbox[2] - bbox[0]
                if tw * 1.1 > max_image_width: font_size -= 1
                else: break

        # Draw Mask
        rotated_text_mask = draw_masked_text(
            text_mask, reformatted_text, font_name, font_size,
            margins, line_spacing, position_x, position_y,
            align, justify, rotation_angle, rotation_options
        )

        # SVG Path Generation
        margin = 15
        bw, bh = max_image_width - margin, max_image_height/2 - margin
        xm, ym = max_image_width/2, max_image_height/2
        kappa = 0.5522848
        ox, oy = float((bw / 2) * kappa), float((bh / 2) * kappa)
        
        # Base Points (Oval)
        pts = [
            Point(xm - bw/2, ym),
            Point(xm - bw/2, ym - oy), Point(xm - ox, ym - bh/2), Point(xm, ym - bh/2),
            Point(xm + ox, ym - bh/2), Point(xm + bw/2, ym - oy), Point(xm + bw/2, ym),
            Point(xm + bw/2, ym + oy), Point(xm + ox, ym + bh/2), Point(xm, ym + bh/2),
            Point(xm - ox, ym + bh/2), Point(xm - bw/2, ym + oy), Point(xm - bw/2, ym)
        ]
        
        # Build curves list
        path_curves = [
            BezierCurve(pts[0], pts[1], pts[2], pts[3]),
            BezierCurve(pts[3], pts[4], pts[5], pts[6]),
            BezierCurve(pts[6], pts[7], pts[8], pts[9]),
            BezierCurve(pts[9], pts[10], pts[11], pts[12])
        ]

        if balloon_complexity > 1:
            for _ in range(1, balloon_complexity):
                new_curves = []
                for c in path_curves:
                    t = 0.5 + ((balloon_complexity_random/100) * (random.random() - 0.5))
                    new_curves.extend(bez_split(c, t))
                path_curves = new_curves

        # Tweaking
        direction = 1 if balloon_type == "cloud" else -1
        tweak_curves = []
        for c in path_curves:
            if balloon_type == "wavy": direction = -direction
            tsz = (balloon_tweak_min + (balloon_tweak_random * random.random())) / 100
            
            p1, cp1, cp2, p2 = c.points
            t1x = (cp1.x - xm) * (1 + (tsz * direction)) + xm
            t1y = (cp1.y - ym) * (1 + (tsz * direction)) + ym
            t2x = (cp2.x - xm) * (1 + (tsz * direction)) + xm
            t2y = (cp2.y - ym) * (1 + (tsz * direction)) + ym
            
            tweak_curves.append(BezierCurve(p1, Point(t1x, t1y), Point(t2x, t2y), p2))
        
        # Tail Calculation
        tail_seg_idx = int(len(tweak_curves) / 360 * ((taillocation + 270) % 360))
        final_path = []
        for idx, c in enumerate(tweak_curves):
            p1, cp1, cp2, p2 = c.points
            if idx == 0: 
                final_path.append(svg.M(p1.x, p1.y))
            
            if idx == tail_seg_idx and tailsize > 0:
                t_spot = slerp_points(p1, p2, 0.5)
                # Split curve to insert tail
                splits = bez_split(c, 0.3 / balloon_complexity)
                c_head = splits[0]
                splits2 = bez_split(splits[1], 0.45 + (balloon_complexity / 5))
                c_tail = splits2[1]
                
                final_path.append(svg.C(c_head.points[1].x, c_head.points[1].y, c_head.points[2].x, c_head.points[2].y, c_head.points[3].x, c_head.points[3].y))
                
                tx = tailsize * math.sin(math.radians(tailangle))
                ty = tailsize * math.cos(math.radians(tailangle))
                
                if tailcurve != 0:
                    tcx = (tailcurve * math.sin(math.radians(tailangle + 90))) + tx/2 + t_spot.x
                    tcy = (tailcurve * math.cos(math.radians(tailangle + 90))) + ty/2 + t_spot.y
                    final_path.append(svg.Q(tcx, tcy, tx + t_spot.x, ty + t_spot.y))
                    final_path.append(svg.Q(tcx, tcy, c_tail.points[0].x, c_tail.points[0].y))
                else:
                    final_path.append(svg.L(tx + t_spot.x, ty + t_spot.y))
                    final_path.append(svg.L(c_tail.points[0].x, c_tail.points[0].y))
                
                final_path.append(svg.C(c_tail.points[1].x, c_tail.points[1].y, c_tail.points[2].x, c_tail.points[2].y, c_tail.points[3].x, c_tail.points[3].y))
            else:
                final_path.append(svg.C(cp1.x, cp1.y, cp2.x, cp2.y, p2.x, p2.y))
        
        final_path.append(svg.Z())

        mysvg = svg.SVG(
            width=max_image_width, height=max_image_height,
            elements=[svg.Path(
                d=final_path, fill=bg_hex, stroke=outline_hex, stroke_width=5,
                transform=[svg.Rotate(-rotation_angle, xm, ym)]
            )]
        )
        
        svg_png = cairosvg.svg2png(bytestring=bytes(str(mysvg), encoding="utf-8"))
        svg_image = Image.open(io.BytesIO(svg_png)).convert("RGB")
        
        final_image = Image.composite(text_image, svg_image, rotated_text_mask)
        return (pil2tensor(final_image), )

# =============================================================================
# MAPPING
# =============================================================================

NODE_CLASS_MAPPINGS = {
    # "ScruffyTextBalloon": ScruffyTextBalloon
}

NODE_DISPLAY_NAME_MAPPINGS = {
    # "ScruffyTextBalloon": "Speech Balloon"
}
