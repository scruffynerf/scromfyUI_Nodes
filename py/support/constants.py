"""
Scromfy Node Constants - Colors and UI Options
"""

class AnyType(str):
    """A special class that is always equal in not equal comparisons. Credit to pythongosssss"""

    def __ne__(self, __value: object) -> bool:
        return False

ANY_ = AnyType("*")
DEF_ANYINPUT = (ANY_, {'forceInput': True})

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
    "gray": (128, 128, 128),
    "lightgray": (211, 211, 211),
    "darkgray": (169, 169, 169),
    "olive": (128, 128, 0),
    "lime": (0, 128, 0),
    "teal": (0, 128, 128),
    "navy": (0, 0, 128),
    "maroon": (128, 0, 0),
    "silver": (192, 192, 192),
    "gold": (255, 215, 0),
    "turquoise": (64, 224, 208),
    "lavender": (230, 230, 250),
    "violet": (238, 130, 238),
    "coral": (255, 127, 80),
    "indigo": (75, 0, 130),
}

COLORS = ["custom"] + sorted(list(COLOR_MAPPING.keys()))

ALIGN_OPTIONS = ["center", "top", "bottom"]
ROTATE_OPTIONS = ["text center", "image center"]
JUSTIFY_OPTIONS = ["center", "left", "right"]
PERSPECTIVE_OPTIONS = ["top", "bottom", "left", "right"]

# Default ComfyUI Types
DEF_FALSEBOOL = ("BOOLEAN", {"default": False, "label_on": "enabled", "label_off": "disabled"})
DEF_TRUEBOOL = ("BOOLEAN", {"default": True, "label_on": "enabled", "label_off": "disabled"})
DEF_PROMPT = ("STRING", {"default": "", "multiline": True, "dynamicPrompts": True})
DEF_STRING_ML = ("STRING", {"default": "", "multiline": True})
