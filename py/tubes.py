"""
Tubes – Named, dictionary-based data passing system for ComfyUI.
The "Scromfy Way" of avoiding noodle soup and improving workflow clarity.
"""

import os
import re
import json
import hashlib
import torch
import numpy as np
import folder_paths
import comfy
from typing import Dict, Any, List, Optional
from PIL import Image
from PIL.PngImagePlugin import PngInfo

from .support.constants import AnyType

# =============================================================================
# SECTION: Constants & Field Definitions
# =============================================================================

TUBE_FIELDS: Dict[str, str] = {
    "positive": "CONDITIONING",
    "negative": "CONDITIONING",
    "image": "IMAGE",
    "mask": "MASK",
    "latent": "LATENT",
    "model": "MODEL",
    "vae": "VAE",
    "clip": "CLIP",
    "loras": "LORA_STACK",
    "prompt": "STRING",
    "neg_prompt": "STRING",
    "steps": "INT",
    "cfg": "FLOAT",
    "denoise": "FLOAT",
    "clip_skip": "INT",
    "seed": "INT",
    "width": "INT",
    "height": "INT",
    "model_name": "STRING",
    "vae_name": "STRING",
    "clip_name": "STRING",
    "sampler": "SAMPLER",
    "sampler_name": "STRING",
    "scheduler": "SCHEDULER",
    "scheduler_name": "STRING",
    "filename": "STRING",


}

TUBE_DEFAULTS: Dict[str, Any] = {
    "steps": 8,
    "cfg": 1.0,
    "denoise": 1.0,
    "clip_skip": 1,
    "seed": 1,
    "sampler_name": "euler",
    "scheduler_name": "normal",
    "prompt": "",
    "neg_prompt": "",
    "model_name": "",
    "width": 1024,
    "height": 1024,
    "loras": [],
}

def merge_tube(base: dict | None, overrides: dict | None) -> dict:
    return merge_tube_with_strategy(base, overrides, "override")

def merge_tube_with_strategy(base: dict | None, overrides: dict | None, strategy: str = "override") -> dict:
    result = dict(base) if isinstance(base, dict) else {}
    if not overrides: return result
    
    for k, v in overrides.items():
        if v is None: continue
        
        if k not in result or result[k] in (None, ""):
            # Target is empty, just set it
            result[k] = v
        else:
            if strategy == "override":
                result[k] = v
            elif strategy == "only if empty/none":
                # Do nothing, we already have a value and shouldn't override
                pass
            elif strategy == "combine":
                v1, v2 = result[k], v
                # Combine values or lists
                if isinstance(v1, list) and isinstance(v2, list):
                    res = list(v1)
                    for item in v2:
                        # Simple membership check (works for most ComfyUI types)
                        if item not in res: res.append(item)
                    result[k] = res
                elif isinstance(v1, list):
                    if v2 not in v1: result[k] = v1 + [v2]
                elif isinstance(v2, list):
                    if v1 not in v2: result[k] = [v1] + v2
                else:
                    if v1 != v2: result[k] = [v1, v2]
    return result

def resolve_tube_value(key: str, val, defaults: dict | None):
    if val not in (None, ""): return val
    if defaults and key in defaults and defaults[key] is not None: return defaults[key]
    return TUBE_DEFAULTS.get(key)

# =============================================================================
# SECTION: Hashing & Metadata Utilities
# =============================================================================

def get_sha256(file_path: str) -> str:
    file_no_ext = os.path.splitext(file_path)[0]
    hash_file = file_no_ext + ".sha256"
    if os.path.exists(hash_file):
        try:
            with open(hash_file, "r") as f: return f.read().strip()
        except: pass
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for b in iter(lambda: f.read(4096), b""): h.update(b)
    try:
        with open(hash_file, "w") as f: f.write(h.hexdigest())
    except: pass
    return h.hexdigest()

class PromptMetadataExtractor:
    EMBEDDING = r'embedding:([^,\s\(\)\:]+)'
    LORA = r'<lora:([^>:]+)(?::[^>]+)?>'
    def __init__(self, prompts):
        self.e, self.l = {}, {}
        for p in prompts:
            for em in re.findall(self.EMBEDDING, p, re.I | re.M):
                path = folder_paths.get_full_path("embeddings", em)
                if path: self.e[f'embed:{em}'] = get_sha256(path)[:10]
            for lo in re.findall(self.LORA, p, re.I | re.M):
                names = folder_paths.get_filename_list("loras")
                m = next((x for x in names if x.endswith(lo+".safetensors") or x.endswith(lo)), None)
                path = folder_paths.get_full_path("loras", m) if m else None
                if path: self.l[f'LORA:{lo}'] = get_sha256(path)[:10]

# =============================================================================
# SECTION: Tube Save Images (Restored functional parity)
# =============================================================================

class TubeSaveImages:
    def __init__(self):
        self.output_dir = folder_paths.output_directory
        self.type = 'output'
        self.sampler_map = {
            'euler_ancestral': 'Euler a',
            'euler': 'Euler',
            'lms': 'LMS',
            'heun': 'Heun',
            'dpm_2': 'DPM2',
            'dpm_2_ancestral': 'DPM2 a',
            'dpmpp_2s_ancestral': 'DPM++ 2S a',
            'dpmpp_2m': 'DPM++ 2M',
            'dpmpp_sde': 'DPM++ SDE',
            'dpmpp_2m_sde': 'DPM++ 2M SDE',
            'dpmpp_3m_sde': 'DPM++ 3M SDE',
            'dpm_fast': 'DPM fast',
            'dpm_adaptive': 'DPM adaptive',
            'ddim': 'DDIM',
            'plms': 'PLMS',
            'uni_pc_bh2': 'UniPC',
            'uni_pc': 'UniPC',
            'lcm': 'LCM',
        }

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
                "output_path": ("STRING", {"default": "[time(%Y-%m-%d)]"}),
                "filename_prefix": ("STRING", {"default": "image"}),
                "extension": (['png', 'jpg', 'jpeg', 'webp'],),
                "save_generation_data": ("BOOLEAN", {"default": True}),
                "embed_workflow": ("BOOLEAN", {"default": False}),
            },
            "optional": {"tube": ("TUBE",)},
            "hidden": {"prompt": "PROMPT", "extra_pnginfo": "EXTRA_PNGINFO"},
        }

    RETURN_TYPES = ("IMAGE", "STRING")
    FUNCTION = "save"
    OUTPUT_NODE = True
    CATEGORY = "Scromfy/Image"

    def save(self, images, output_path, filename_prefix, extension, save_generation_data, embed_workflow, tube=None, prompt=None, extra_pnginfo=None):
        params = ""
        if tube and isinstance(tube, dict):
            p, n = str(tube.get("prompt","")), str(tube.get("neg_prompt",""))
            s, c = int(tube.get("steps",20)), float(tube.get("cfg",7.0))
            sm, sc = str(tube.get("sampler_name","euler")), str(tube.get("scheduler_name","normal"))
            m, seed = str(tube.get("model_name","")), int(tube.get("seed",0))
            w, h = int(tube.get("width",512)), int(tube.get("height",512))
            
            # Format Civitai Sampler
            c_sm = self.sampler_map.get(sm, sm)
            if sc == "karras": c_sm += " Karras"
            
            # Extract hashes
            model_hash = ""
            if m:
                cp = folder_paths.get_full_path("checkpoints", m)
                if cp: model_hash = get_sha256(cp)[:10]
            
            mx = PromptMetadataExtractor([p, n])
            hashes = mx.e | mx.l | {"model": model_hash}
            if m: hashes[f"Model:{os.path.splitext(os.path.basename(m))[0]}"] = model_hash
            
            params = f"{p}\nNegative prompt: {n}\nSteps: {s}, Sampler: {c_sm}, CFG scale: {c}, Seed: {seed}, Size: {w}x{h}, Hashes: {json.dumps(hashes)}, Version: ComfyUI"

        # Path Setup
        out = output_path if output_path and output_path != "." else self.output_dir
        if not os.path.isabs(out): out = os.path.join(self.output_dir, out)
        os.makedirs(out, exist_ok=True)
        
        results, files = [], []
        for idx, image in enumerate(images):
            counter = len(os.listdir(out)) + 1
            file = f"{filename_prefix}_{counter:04}.{extension}"
            full_p = os.path.join(out, file)
            
            i = 255. * image.cpu().numpy()
            img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))
            
            metadata = PngInfo()
            if embed_workflow:
                if prompt: metadata.add_text("prompt", json.dumps(prompt))
                if extra_pnginfo:
                    for k in extra_pnginfo: metadata.add_text(k, json.dumps(extra_pnginfo[k]))
            if params and save_generation_data: metadata.add_text("parameters", params)
            
            if extension in ["jpg", "jpeg"]: img.save(full_p, quality=95)
            elif extension == "webp": img.save(full_p, quality=95)
            else: img.save(full_p, pnginfo=metadata)
            
            files.append(full_p)
            results.append({"filename": file, "subfolder": output_path, "type": self.type})

        return {"ui": {"images": results, "files": files}, "result": (images, files)}

# =============================================================================
# SECTION: CORE TUBE NODES
# =============================================================================

class TubeInNode:
    """Collect values into a TUBE. Only overrides modified widget values."""
    WIDGET_DEFAULTS = {
        "steps": 0,
        "cfg": 0.0,
        "denoise": 0.0,
        "seed": 0,
        "width": 0,
        "height": 0,
        "prompt": "",
        "neg_prompt": "",
        "model_name": "",
        "loras": [],
    }
    @classmethod
    def INPUT_TYPES(cls):
        optional = {"tube_in": ("TUBE",)}
        for f, t in TUBE_FIELDS.items():
            if t == "SAMPLER": t = comfy.samplers.KSampler.SAMPLERS
            if t == "SCHEDULER": t = comfy.samplers.KSampler.SCHEDULERS
            optional[f] = (t,)
        return {"required": {}, "optional": optional}
    RETURN_TYPES = ("TUBE",)
    FUNCTION = "execute"
    CATEGORY = "Scromfy/Tubes"
    def execute(self, tube_in=None, **kwargs):
        overrides = {}
        for k, v in kwargs.items():
            if v is None: continue
            if isinstance(v, list) and not v: continue
            if k in self.WIDGET_DEFAULTS and v == self.WIDGET_DEFAULTS[k]: continue
            overrides[k] = v
        return (merge_tube(tube_in, overrides),)

class TubeOutNode:
    """Extract values from a TUBE with passthru."""
    @classmethod
    def INPUT_TYPES(cls): return {"required": {"tube_in": ("TUBE",)}}
    @classmethod
    def get_outputs(cls):
        out_t = ["TUBE"]
        for f in TUBE_FIELDS.values():
            if f == "SAMPLER": f = comfy.samplers.KSampler.SAMPLERS
            elif f == "SCHEDULER": f = comfy.samplers.KSampler.SCHEDULERS
            out_t.append(f)
        return tuple(out_t), ("tube",) + tuple(TUBE_FIELDS.keys())
    
    RETURN_TYPES, RETURN_NAMES = get_outputs.__func__(None)
    FUNCTION = "execute"
    CATEGORY = "Scromfy/Tubes"
    def execute(self, tube_in):
        t = tube_in if isinstance(tube_in, dict) else {}
        return (t,) + tuple(t.get(k) for k in TUBE_FIELDS.keys())


class TubeMerge:
    """Merge two TUBEs with strategy."""
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "tube_a": ("TUBE",),
                "tube_b": ("TUBE",),
                "strategy": (["override", "only if empty/none", "combine"], {"default": "override"}),
            }
        }
    RETURN_TYPES = ("TUBE",)
    FUNCTION = "execute"
    CATEGORY = "Scromfy/Tubes"
    def execute(self, tube_a, tube_b, strategy):
        return (merge_tube_with_strategy(tube_a, tube_b, strategy),)

class TubeGetValue:
    """Retrieve a single value from a tube."""
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "tube": ("TUBE",),
                "key": ("STRING", {"default": "prompt"}),
            }
        }
    RETURN_TYPES = (AnyType("*"), "TUBE",)
    RETURN_NAMES = ("value", "tube")
    FUNCTION = "get"
    CATEGORY = "Scromfy/Tubes"
    def get(self, tube, key):
        t = tube if isinstance(tube, dict) else {}
        return (t.get(key), t)

class TubeSetValue:
    """Set a single value into a tube."""
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "tube": ("TUBE",),
                "key": ("STRING", {"default": "new_key"}),
                "value": (AnyType("*"),),
                "strategy": (["override", "only if empty/none", "combine"], {"default": "override"}),
            }
        }
    RETURN_TYPES = ("TUBE",)
    FUNCTION = "set"
    CATEGORY = "Scromfy/Tubes"
    def set(self, tube, key, value, strategy):
        return (merge_tube_with_strategy(tube, {key: value}, strategy),)

class TubeGetJSON:
    """Retrieve multiple keys as JSON from a tube."""
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "tube": ("TUBE",),
                "keys_json": ("STRING", {"multiline": True, "default": '["prompt", "seed"]'}),
            }
        }
    RETURN_TYPES = ("JSON", "TUBE",)
    RETURN_NAMES = ("json_out", "tube")
    FUNCTION = "get"
    CATEGORY = "Scromfy/Tubes"
    def get(self, tube, keys_json):
        t = tube if isinstance(tube, dict) else {}
        try: keys = json.loads(keys_json)
        except: keys = []
        if not isinstance(keys, list): keys = [keys]
        out = {k: t.get(k) for k in keys}
        return (out, t)

class TubeSetJSON:
    """Set multiple values from JSON into a tube."""
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "tube": ("TUBE",),
                "data_json": ("STRING", {"multiline": True, "default": '{"key": "value"}'}),
                "strategy": (["override", "only if empty/none", "combine"], {"default": "override"}),
            }
        }
    RETURN_TYPES = ("TUBE",)
    FUNCTION = "set"
    CATEGORY = "Scromfy/Tubes"
    def set(self, tube, data_json, strategy):
        try: data = json.loads(data_json)
        except: data = {}
        if not isinstance(data, dict): data = {}
        return (merge_tube_with_strategy(tube, data, strategy),)

class TubeInspector:
    """Inspect a TUBE and output summary/JSON."""
    @classmethod
    def INPUT_TYPES(cls): return {"required": {"tube": ("TUBE",)}}
    RETURN_TYPES = ("STRING", "JSON STRING", "JSON")
    RETURN_NAMES = ("summary", "json_pretty", "json")
    FUNCTION = "execute"
    CATEGORY = "Scromfy/Tubes"
    def execute(self, tube):
        t = tube if isinstance(tube, dict) else {}
        lines = []
        for k in sorted(t.keys()):
            v = t[k]
            if isinstance(v, (str, int, float)): lines.append(f"{k}: {v}")
            elif isinstance(v, list): lines.append(f"{k}: list[{len(v)}]")
            elif isinstance(v, dict): lines.append(f"{k}: dict[{len(v)}]")
            else: lines.append(f"{k}: {type(v).__name__}")
        try: jsonstring_out = json.dumps(t, indent=4, ensure_ascii=False, default=str)
        except: jsonstring_out = "{}"
        return ("\n".join(lines), jsonstring_out, json.loads(jsonstring_out))

class TubeFilter:
    """Filter keys in a tube (Whitelist/Blacklist)."""
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "tube": ("TUBE",),
                "mode": (["whitelist", "blacklist"], {"default": "whitelist"}),
                "keys": ("STRING", {"multiline": True, "default": "prompt, seed"}),
            }
        }
    RETURN_TYPES = ("TUBE",)
    FUNCTION = "filter"
    CATEGORY = "Scromfy/Tubes"
    def filter(self, tube, mode, keys):
        t = dict(tube) if isinstance(tube, dict) else {}
        key_list = [k.strip() for k in keys.split(",") if k.strip()]
        if mode == "whitelist":
            return ({k: t[k] for k in key_list if k in t},)
        else: # blacklist
            for k in key_list:
                if k in t: del t[k]
            return (t,)

class TubePrune:
    """Remove empty/None values from a tube."""
    @classmethod
    def INPUT_TYPES(cls): return {"required": {"tube": ("TUBE",)}}
    RETURN_TYPES = ("TUBE",)
    FUNCTION = "prune"
    CATEGORY = "Scromfy/Tubes"
    def prune(self, tube):
        t = tube if isinstance(tube, dict) else {}
        clean = {k: v for k, v in t.items() if v not in (None, "", [], {})}
        return (clean,)

class TubeRenameKey:
    """Rename a key in a tube."""
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "tube": ("TUBE",),
                "old_name": ("STRING", {"default": "old_key"}),
                "new_name": ("STRING", {"default": "new_key"}),
            }
        }
    RETURN_TYPES = ("TUBE",)
    FUNCTION = "rename"
    CATEGORY = "Scromfy/Tubes"
    def rename(self, tube, old_name, new_name):
        t = dict(tube) if isinstance(tube, dict) else {}
        if old_name in t:
            t[new_name] = t.pop(old_name)
        return (t,)

class TubeDiff:
    """Find differences between two tubes (returns items in B diff from A)."""
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "tube_a": ("TUBE",),
                "tube_b": ("TUBE",),
            }
        }
    RETURN_TYPES = ("TUBE",)
    FUNCTION = "diff"
    CATEGORY = "Scromfy/Tubes"
    def diff(self, tube_a, tube_b):
        ta = tube_a if isinstance(tube_a, dict) else {}
        tb = tube_b if isinstance(tube_b, dict) else {}
        diff = {}
        for k, v in tb.items():
            if k not in ta or ta[k] != v:
                diff[k] = v
        return (diff,)

class TubeContains:
    """Check if a tube contains a specific key."""
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "tube": ("TUBE",),
                "key": ("STRING", {"default": "prompt"}),
            }
        }
    RETURN_TYPES = ("BOOLEAN",)
    FUNCTION = "check"
    CATEGORY = "Scromfy/Tubes"
    def check(self, tube, key):
        t = tube if isinstance(tube, dict) else {}
        return (key in t,)

class TubeToFile:
    """Save a tube to a JSON file."""
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "tube": ("TUBE",),
                "filename": ("STRING", {"default": "tube.json"}),
                "input_or_output": (["output", "input"], {"default": "output"}),
            }
        }
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("filepath",)
    FUNCTION = "save"
    CATEGORY = "Scromfy/Tubes"
    OUTPUT_NODE = True
    def save(self, tube, filename, input_or_output):
        t = tube if isinstance(tube, dict) else {}
        base_path = folder_paths.get_output_directory() if input_or_output == "output" else folder_paths.get_input_directory()
        full_path = os.path.join(base_path, filename)
        with open(full_path, "w", encoding="utf-8") as f:
            json.dump(t, f, indent=4, ensure_ascii=False, default=str)
        return (full_path,)

class FileToTube:
    """Load a tube from a JSON file."""
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "filename": ("STRING", {"default": "tube.json"}),
                "input_or_output": (["input", "output"], {"default": "input"}),
            }
        }
    RETURN_TYPES = ("TUBE",)
    FUNCTION = "load"
    CATEGORY = "Scromfy/Tubes"
    def load(self, filename, input_or_output):
        base_path = folder_paths.get_input_directory() if input_or_output == "input" else folder_paths.get_output_directory()
        full_path = os.path.join(base_path, filename)
        if not os.path.exists(full_path): return ({},)
        with open(full_path, "r", encoding="utf-8") as f:
            try: return (json.load(f),)
            except: return ({},)

class TubeModifyString:
    """Modify a string value in a tube with prefix/suffix."""
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "tube": ("TUBE",),
                "key": ("STRING", {"default": "prompt"}),
                "prefix": ("STRING", {"default": ""}),
                "suffix": ("STRING", {"default": ""}),
                "delimiter": ("STRING", {"default": ", "}),
            }
        }
    RETURN_TYPES = ("TUBE",)
    FUNCTION = "modify"
    CATEGORY = "Scromfy/Tubes"
    def modify(self, tube, key, prefix, suffix, delimiter):
        t = dict(tube) if isinstance(tube, dict) else {}
        val = str(t.get(key, ""))
        if prefix:
            val = prefix + delimiter + val if val else prefix
        if suffix:
            val = val + delimiter + suffix if val else suffix
        t[key] = val
        return (t,)

NODE_CLASS_MAPPINGS = {
    "TubeIn": TubeInNode,
    "TubeOut": TubeOutNode,
    "TubeSaveImages": TubeSaveImages,
    "TubeMerge": TubeMerge,
    "TubeInspector": TubeInspector,
    "TubeGetValue": TubeGetValue,
    "TubeSetValue": TubeSetValue,
    "TubeGetJSON": TubeGetJSON,
    "TubeSetJSON": TubeSetJSON,
    "TubeFilter": TubeFilter,
    "TubePrune": TubePrune,
    "TubeRenameKey": TubeRenameKey,
    "TubeDiff": TubeDiff,
    "TubeContains": TubeContains,
    "TubeToFile": TubeToFile,
    "FileToTube": FileToTube,
    "TubeModifyString": TubeModifyString,
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "TubeIn": "Tube In",
    "TubeOut": "Tube Out",
    "TubeSaveImages": "Tube Save Images",
    "TubeMerge": "Tube Merge",
    "TubeInspector": "Tube Inspector",
    "TubeGetValue": "Tube Get Value",
    "TubeSetValue": "Tube Set Value",
    "TubeGetJSON": "Tube Get JSON",
    "TubeSetJSON": "Tube Set JSON",
    "TubeFilter": "Tube Filter",
    "TubePrune": "Tube Prune",
    "TubeRenameKey": "Tube Rename Key",
    "TubeDiff": "Tube Diff",
    "TubeContains": "Tube Contains",
    "TubeToFile": "Tube to File",
    "FileToTube": "File to Tube",
    "TubeModifyString": "Tube Modify String",
}
