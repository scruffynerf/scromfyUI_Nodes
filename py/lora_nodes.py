"""
LoRA Utility Nodes - Dynamic loading and prompt-based parsing.
"""

import re
import folder_paths
from nodes import LoraLoader

class LoraListFromInstalled:
    """Lists installed LoRAs with filtering capabilities."""
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "specific_loras": ("STRING", {"multiline": True, "default": ""}),
                "filter_from_all": ("STRING", {"multiline": True, "default": ".safetensors"})
            }
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING", "STRING", "STRING", "STRING", "INT")
    RETURN_NAMES = ("Paths 1by1", "Paths as List", "Clean Filenames 1by1", "Clean Filenames as List", "Syntax 1by1", "Syntax as List", "num_loras")
    OUTPUT_IS_LIST = (True, False, True, False, True, False, False)
    FUNCTION = "execute"
    CATEGORY = "Scromfy/Loras"

    def execute(self, specific_loras, filter_from_all):
        if specific_loras:
            results = specific_loras.split("\n")
        else:
            search_terms = [t.lower() for t in filter_from_all.split("\n") if t.strip()]
            all_loras = folder_paths.get_filename_list("loras")
            results = list(filter(lambda l: any(t in l.lower() for t in search_terms), all_loras))

        pattern = re.compile(r".+\/(.*)\.safetensors")
        shortnames = [match[1] for item in results if (match := pattern.match(item))]
        syntax = [f"<lora:{item}:1.0>" for item in results]
        return (results, results, shortnames, shortnames, syntax, syntax, len(results))

class GetLorasFromPrompt:
    """Extracts and loads LoRAs from prompt strings using <lora:name:strength> syntax."""
    def __init__(self):
        self.lora_list = folder_paths.get_filename_list("loras")

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model": ("MODEL", ),
                "clip": ("CLIP", ),
                "prompt": ("STRING", {"multiline": True, "default": ""}),
            }
        }

    RETURN_TYPES = ("MODEL", "CLIP", "STRING")
    RETURN_NAMES = ("MODEL", "CLIP", "CleanedPrompt")
    FUNCTION = "execute"
    CATEGORY = "Scromfy/Loras"

    def execute(self, model, clip, prompt):
        lora_info_list = re.findall(r"<(?:lora:)?([^\>\:]*):?([^>]*)>", prompt)
        prompt_clean = re.sub(r"<(?:lora:)?([^\:\>]*):?([^>]*)>", "", prompt)
        
        out_model, out_clip = model, clip
        processed = ""
        for name, strength in lora_info_list:
            s_m = s_c = 1.0
            if strength and ":" in strength:
                parts = strength.split(":")
                s_m, s_c = float(parts[0]), float(parts[1])
            elif strength:
                s_m = s_c = float(strength)
            
            matches = [l for l in self.lora_list if name in l]
            if matches:
                out_model, out_clip = LoraLoader().load_lora(out_model, out_clip, matches[0], s_m, s_c)
                processed += f"Loaded: {name} ({s_m}/{s_c})\n"
            else:
                processed += f"Missing: {name}\n"

        return {"ui": {"text": processed}, "result": (out_model, out_clip, prompt_clean)}

NODE_CLASS_MAPPINGS = {
    "LoraListFromInstalled": LoraListFromInstalled,
    "GetLorasFromPrompt": GetLorasFromPrompt
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "LoraListFromInstalled": "LoRA List (Dynamic)",
    "GetLorasFromPrompt": "Extract LoRAs from Prompt"
}
