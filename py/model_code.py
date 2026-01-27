"""
Model Utility Nodes - Architecture detection, universal latents, and intelligent shifts.

Supported Model Types:
SD1.5, SD2.0, SDXL, SD3, CASCADE_C, CASCADE_B, FLUX.1, FLUX.2, MOCHI, LTXV, LTXAV,
HYVid, HYVid1.5, HYImg2.1, HY3D, COSMOS_V, COSMOS_P, WAN2.1_T2V, WAN2.2_T2V,
LUMINA2, ZIMAGE, CHROMA, ACEStep, OMNIGEN2, QWEN_IMG, KANDINSKY5
"""

import torch
import math
import comfy
import comfy.model_patcher
import comfy.supported_models
from nodes import MAX_RESOLUTION
from .support.constants import DEF_FALSEBOOL, DEF_TRUEBOOL
from .support.scromfy_utils import adjust_ratios

# --- Model Detection ---

def get_model_architecture(model):
    """Detects model architecture and returns a standardized string name."""
    cfg = model.model.model_config
    
    # Flux Family
    if isinstance(cfg, comfy.supported_models.Flux):
        if cfg.unet_config.get("guidance_embed") is False: return "FLUX.1_SCHNELL"
        return "FLUX.1"
    if isinstance(cfg, comfy.supported_models.Flux2): return "FLUX.2"
    
    # SD Family
    if isinstance(cfg, comfy.supported_models.SDXL): return "SDXL"
    if isinstance(cfg, comfy.supported_models.SD3): return "SD3"
    if isinstance(cfg, (comfy.supported_models.SD15, comfy.supported_models.SD20)): return "SD"
    
    # Cascade
    if isinstance(cfg, comfy.supported_models.Stable_Cascade_C): return "CASCADE_C"
    if isinstance(cfg, comfy.supported_models.Stable_Cascade_B): return "CASCADE_B"
    
    # Hunyuan Family
    if isinstance(cfg, comfy.supported_models.HunyuanVideo15): return "HYVid1.5"
    if isinstance(cfg, comfy.supported_models.HunyuanVideo): return "HYVid"
    if isinstance(cfg, comfy.supported_models.HunyuanImage21): return "HYImg2.1"
    if isinstance(cfg, (comfy.supported_models.Hunyuan3Dv2, comfy.supported_models.Hunyuan3Dv2_1)): return "HY3D"
    if isinstance(cfg, comfy.supported_models.HunyuanDiT): return "HYDIT"
    
    # Wan Family
    if isinstance(cfg, comfy.supported_models.WAN21_T2V): return "WAN2.1"
    if isinstance(cfg, comfy.supported_models.WAN22_T2V): return "WAN2.2"
    
    # Cosmos Family
    if isinstance(cfg, (comfy.supported_models.CosmosT2V, comfy.supported_models.CosmosI2V)): return "COSMOS_V"
    if isinstance(cfg, (comfy.supported_models.CosmosT2IPredict2, comfy.supported_models.CosmosI2VPredict2)): return "COSMOS_P"
    
    # Video/Specials
    if isinstance(cfg, comfy.supported_models.GenmoMochi): return "MOCHI"
    if isinstance(cfg, comfy.supported_models.LTXV): return "LTXV"
    if isinstance(cfg, comfy.supported_models.LTXAV): return "LTXAV"
    if isinstance(cfg, comfy.supported_models.ZImage): return "ZIMAGE"
    if isinstance(cfg, comfy.supported_models.Lumina2): return "LUMINA2"
    if isinstance(cfg, comfy.supported_models.AuraFlow): return "AURA"
    
    # Others
    if isinstance(cfg, comfy.supported_models.Chroma): return "CHROMA"
    if isinstance(cfg, comfy.supported_models.ACEStep): return "ACEStep"
    if isinstance(cfg, comfy.supported_models.Omnigen2): return "OMNIGEN2"
    if isinstance(cfg, comfy.supported_models.QwenImage): return "QWEN_IMG"
    if isinstance(cfg, (comfy.supported_models.Kandinsky5, comfy.supported_models.Kandinsky5Image)): return "KANDINSKY5"
    
    return "UNKNOWN"

class GetModelType:
    """Detects and returns the model architecture as a string."""
    @classmethod
    def INPUT_TYPES(cls): return {"required": {"model": ("MODEL", )}}
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("model_name",)
    CATEGORY = "Scromfy/Model"
    FUNCTION = "execute"
    def execute(self, model): return (get_model_architecture(model),)

# --- Universal Latent ---

class UniversalEmptyLatent:
    """
    Exhaustive Empty Latent generator with restored complex sizing logic.
    Supports over 20 model families with accurate noise floor constants.
    """
    def __init__(self):
        self.device = comfy.model_management.intermediate_device()

    @classmethod
    def INPUT_TYPES(cls):
        models = [
            "FLUX.1",
            "FLUX.1_SCHNELL",
            "FLUX.2",
            "QWEN_IMG",
            "LTXV",
            "LTXAV",
            "WAN2.1",
            "WAN2.2",
            "LUMINA2",
            "ZIMAGE",
            "CHROMA",
            "SD",
            "SDXL",
            "SD3",
            "CASCADE_C",
            "CASCADE_B",
            "MOCHI",
            "HYVid",
            "HYVid1.5",
            "HYImg2.1",
            "HY3D",
            "HYDIT",
            "COSMOS_V",
            "COSMOS_P",
            "ACEStep",
            "OMNIGEN2",
            "KANDINSKY5",
        ]
        resolutions = [
            "1024x1024 (1:1)",
            "512x1024 (1:2 or 8:16)",
            "576x1024 (9:16)",
            "640x960 (2:3 or 10:15)",
            "640x1024 (5:8 or 10:16)",
            "640x1280 (1:2 or 10:20)",
            "704x512 (11:8)",
            "704x576 (11:9)",
            "704x896 (11:14)",
            "704x1344 (11:21)",
            "704x1408 (1:2 or 11:22)",
            "768x960 (4:5 or 12:15)",
            "768x1024 (3:4 or 12:16)",
            "768x1280 (3:5 or 12:20)",
            "768x1344 (4:7 or 12:21)",
            "768x1536 (1:2 or 12:24)",
            "832x384 (13:6)",
            "832x1152 (13:18)",
            "832x1216 (13:19)",
            "896x384 (7:3 or 21:9)",
            "896x512 (7:4 or 14:8)",
            "896x1088 (14:17)",
            "896x1152 (7:9 or 14:18)",
            "960x512 (15:8)",
            "960x576 (5:3 or 15:9)",
            "960x640 (3:2 or 15:10)",
            "960x768 (5:4 or 15:12)",
            "960x1024 (15:16)",
            "960x1088 (7:8 or 15:17)",
            "960x1280 (3:4 or 15:20)",
            "1024x512 (2:1 or 16:8)",
            "1024x576 (16:9)",
            "1024x640 (8:5 or 16:10)",
            "1024x768 (4:3 or 16:12)",
            "1024x960 (16:15)",
            "1088x896 (17:14)",
            "1088x960 (17:15)",
            "1152x576 (2:1 or 18:9)",
            "1152x640 (9:5 or 18:10)",
            "1152x768 (3:2 or 18:12)",
            "1152x832 (18:13)",
            "1152x896 (9:7 or 18:14)",
            "1152x1152 (1:1)",
            "1216x832 (19:13)",
            "1280x640 (2:1 or 20:10)",
            "1280x768 (5:3 or 20:12)",
            "1280x896 (10:7 or 20:14)",
            "1280x960 (4:3 or 20:15)",
            "1280x1024 (5:4 or 20:16)",
            "1344x576 (7:3 or 21:9)",
            "1344x704 (21:11)",
            "1344x768 (7:4 or 21:12)",
            "1408x704 (2:1 or 22:11)",
            "1472x704 (23:11)",
            "1536x512 (3:1 or 24:8)",
            "1536x640 (12:5 or 24:10)",
            "1536x768 (2:1 or 24:12)",
            "1536x1024 (3:2 or 24:16)",
            "1600x640 (5:2 or 25:10)",
            "1600x960 (5:3 or 25:15)",
            "1600x1280 (5:4 or 25:20)",
            "1664x576 (26:9)",
            "1728x576 (3:1 or 27:9)",
            "2048x2048 (1:1)",
            "2048x1024 (2:1)",
            "1024x2048 (1:2)",
            "1536x1536 (1:1)",
            "1280x1280 (1:1)",
        ]
        return {
            "required": {
                "resolution": (resolutions, {"default": "1024x1024 (1:1)"}),
                "latent_type": (models, {"default": "FLUX.1"}),
            },
            "optional": {
                "ratio_x": ("INT", {"default": 1, "min": 0, "max": MAX_RESOLUTION // 8}),
                "ratio_y": ("INT", {"default": 1, "min": 0, "max": MAX_RESOLUTION // 8}),
                "altratio_xy": ("FLOAT", {"default": 0.001, "min": 0, "step": 0.001}),
                "use_exact_wh": DEF_FALSEBOOL,
                "max_width": ("INT", {"default": 1024, "min": 0, "max": MAX_RESOLUTION, "step": 8}),
                "max_height": ("INT", {"default": 1024, "min": 0, "max": MAX_RESOLUTION, "step": 8}),
                "min_width": ("INT", {"default": 0, "min": 0, "max": MAX_RESOLUTION, "step": 8}),
                "min_height": ("INT", {"default": 0, "min": 0, "max": MAX_RESOLUTION, "step": 8}),
                "pixels_64": DEF_FALSEBOOL,
                "fallback_8": DEF_FALSEBOOL,
                "batch_size": ("INT", {"default": 1, "min": 1, "max": 4096}),
                "modeloverride": ("STRING", {"multiline": False, "forceInput": True, "default": ""}),
            }
        }

    RETURN_TYPES = ("LATENT", "INT", "INT")
    RETURN_NAMES = ("LATENT", "width", "height")
    CATEGORY = "Scromfy/Latent"
    FUNCTION = "execute"

    def find_largest_pair_with_ratio(self, min_x, max_x, min_y, max_y, rx, ry, p64=True, f8=False):
        """Finds the largest dimensions that fit the ratio and constraints."""
        step = 64 if p64 else 8
        for x in range(max_x - (max_x % step), min_x - 1, -step):
            y = x * ry / rx
            if y.is_integer() and max_y >= y >= min_y:
                y = int(y)
                if p64:
                    if x % 64 == 0 and y % 64 == 0: return x, y
                elif x % 8 == 0 and y % 8 == 0: return x, y
        
        if p64 and f8: # Fallback to 8
            return self.find_largest_pair_with_ratio(min_x, max_x, min_y, max_y, rx, ry, False, False)
            
        new_rx, new_ry = adjust_ratios(rx, ry)
        return self.find_largest_pair_with_ratio(min_x, max_x, min_y, max_y, new_rx, new_ry, p64, f8)

    def execute(self, resolution, latent_type, **kwargs):
        batch_size = kwargs.get("batch_size", 1)
        use_exact = kwargs.get("use_exact_wh", False)
        l_type = kwargs.get("modeloverride") if kwargs.get("modeloverride") else latent_type
        
        # Sizing Logic
        if use_exact:
            width = int(kwargs.get("max_width")) if kwargs.get("max_width", 0) >= 8 else 1024
            height = int(kwargs.get("max_height")) if kwargs.get("max_height", 0) >= 8 else 1024
        elif kwargs.get("altratio_xy", 0) > 0 or (kwargs.get("ratio_x", 0) > 0 and kwargs.get("ratio_y", 0) > 0):
            rx, ry = kwargs.get("ratio_x", 1), kwargs.get("ratio_y", 1)
            if kwargs.get("altratio_xy", 0) > 0:
                rx, ry = kwargs.get("altratio_xy").as_integer_ratio()
            
            width, height = self.find_largest_pair_with_ratio(
                max(8, kwargs.get("min_width", 8)), kwargs.get("max_width", 1024),
                max(8, kwargs.get("min_height", 8)), kwargs.get("max_height", 1024),
                rx, ry, kwargs.get("pixels_64", False), kwargs.get("fallback_8", False)
            )
        else:
            wh = resolution.split(" ")[0].split("x")
            width, height = int(wh[0]), int(wh[1])

        # Final Rounding
        p_round = 64 if kwargs.get("pixels_64") and not kwargs.get("fallback_8") else 8
        width, height = int(width) - (int(width) % p_round), int(height) - (int(height) % p_round)
        
        # latent_channels, constant_val
        channels = 4
        c_val = 0.0
        
        # Exhaustive Constant Mapping
        # 16 Channels
        if any(x in l_type for x in ["SD3", "FLUX", "CASCADE", "HYVid", "COSMOS", "WAN", "LUMINA", "ZIMAGE", "HYImg"]):
            channels = 16
            if "SD3" in l_type: c_val = 0.0609
            elif "FLUX.1" in l_type: c_val = 0.1159
        elif "MOCHI" in l_type: channels = 12
        elif "LTXV" in l_type or "LTXAV" in l_type: channels = 128
        elif "WAN2.2" in l_type: channels = 48
        elif "CHROMA" in l_type: channels = 3
        elif "ACEStep" in l_type: channels = 8
        elif "HYImg2.1" in l_type: channels = 64

        latent = torch.ones([batch_size, channels, height // 8, width // 8], device=self.device) * c_val
        if c_val == 0.0: latent = torch.zeros_like(latent)
        
        return ({"samples": latent}, width, height)

# --- Sampler Shift ---

class ModelShiftWithAutoCalc:
    """Intelligent Sampling Shift that adjusts based on model architecture and resolution."""
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model": ("MODEL", ),
                "use_autocalc": DEF_TRUEBOOL,
                "manual_shift": ("FLOAT", {"default": 1.15, "min": 0.0, "max": 100.0, "step": 0.01}),
                "width": ("INT", {"default": 1024, "min": 16, "max": MAX_RESOLUTION, "step": 8}),
                "height": ("INT", {"default": 1024, "min": 16, "max": MAX_RESOLUTION, "step": 8}),
            }
        }

    RETURN_TYPES = ("MODEL", "FLOAT")
    RETURN_NAMES = ("MODEL", "Shift")
    CATEGORY = "Scromfy/Model"
    FUNCTION = "execute"

    def execute(self, model, use_autocalc, manual_shift, width, height):
        m = model.clone()
        arch = get_model_architecture(model)
        
        # Native base shifts from Core ComfyUI / Research
        SHIFT_DEFAULTS = {
            "SD3": 3.0,
            "CASCADE_C": 2.0,
            "CASCADE_B": 1.0,
            "AURA": 1.73,
            "MOCHI": 6.0,
            "LTXV": 2.37,
            "HYVid": 7.0,
            "HYVid1.5": 7.0,
            "HYImg2.1": 5.0,
            "WAN2.1": 8.0,
            "WAN2.2": 8.0,
            "LUMINA2": 6.0,
            "ZIMAGE": 3.0,
            "FLUX.1": 1.15,
            "FLUX.1_SCHNELL": 1.0,
            "FLUX.2": 2.02,
            "COSMOS_V": 1.0,
            "COSMOS_P": 1.0,
            "KANDINSKY5": 10.0,
            "ACEStep": 3.0,
            "OMNIGEN2": 2.6,
            "QWEN_IMG": 1.15,
            "UNKNOWN": 1.0,
        }
        
        base_shift = SHIFT_DEFAULTS.get(arch, 1.0)
        
        if use_autocalc:
            # Heuristic scaling: Shift adjusts with pixel density relative to 1024p
            log_px = math.log2(max(0.1, (width * height) / (1024 * 1024)))
            shift = round(base_shift * (1.0 + 0.5 * log_px), 2)
        else:
            shift = manual_shift

        sampling_base = comfy.model_sampling.ModelSamplingFlux
        sampling_type = comfy.model_sampling.CONST
        class ModelSamplingAdvanced(sampling_base, sampling_type): pass

        m_cfg = model.model.model_config if hasattr(model.model, "model_config") else model.model
        ms = ModelSamplingAdvanced(m_cfg)
        ms.set_parameters(shift=shift)
        m.add_object_patch("model_sampling", ms)
        
        if arch == "UNKNOWN": print(f"[Warning] Scromfy Shift: Unknown model config type {type(m_cfg)}")
        
        return (m, shift)

NODE_CLASS_MAPPINGS = {
    "GetModelType": GetModelType,
    "UniversalEmptyLatent": UniversalEmptyLatent,
    "ModelShiftWithAutoCalc": ModelShiftWithAutoCalc,
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "GetModelType": "Detect Model Type",
    "UniversalEmptyLatent": "Universal Empty Latent",
    "ModelShiftWithAutoCalc": "Model Shift (AutoCalc)",
}
