"""
Common utilities for Image Browser nodes.
Shared between Civitai, CivSearch, Danbooru, and Genur browsers.
"""

import io
import json
import os
import re
import urllib.request
from typing import Any, Dict, List, Optional

import numpy as np
import torch
from PIL import Image

# Relative import to the Tubes implementation
from ..tubes import TUBE_DEFAULTS, merge_tube, resolve_tube_value

# =============================================================================
# SECTION: Type Definitions
# =============================================================================

class AnyType(str):
    """A special class that is always equal in not equal comparisons."""
    def __ne__(self, __value: object) -> bool:
        return False

# =============================================================================
# SECTION: Type Conversion & Basic Helpers
# =============================================================================

def clamp_int(v: Any, lo: int, hi: int, default: int) -> int:
    try: return max(lo, min(hi, int(str(v))))
    except: return default

def truthy(v: Any) -> bool:
    return str(v).strip().lower() in ("1", "true", "yes", "on")

def safe_int(val: Any, default: Optional[int] = None) -> Optional[int]:
    if val is None: return default
    try: return int(val)
    except: return default

def safe_float(val: Any, default: Optional[float] = None) -> Optional[float]:
    if val is None: return default
    try: return float(val)
    except: return default

# =============================================================================
# SECTION: Favorites Storage
# =============================================================================

def load_favorites(filepath: str) -> Dict[str, Any]:
    if not os.path.exists(filepath): return {}
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except: return {}

def save_favorites(filepath: str, data: Dict[str, Any]) -> None:
    try:
        tmp = filepath + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        os.replace(tmp, filepath)
    except Exception as e:
        print(f"Scromfy Browser: Error saving favorites to {filepath}: {e}")

# =============================================================================
# SECTION: Image & Downloader
# =============================================================================

def empty_image_tensor() -> torch.Tensor:
    return torch.zeros(1, 1, 1, 3, dtype=torch.float32)

def download_image_to_tensor(url: str, timeout_s: int = 30) -> torch.Tensor:
    import tempfile
    
    try:
        import imageio
    except ImportError:
        print("Scromfy Browser: imageio not installed, video downloads generally require it.")
        imageio = None

    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=timeout_s) as resp:
        data = resp.read()

    # Heuristic check for video extensions
    lower_url = url.split("?")[0].lower()
    is_video = lower_url.endswith((".mp4", ".webm", ".mov", ".avi", ".mkv"))

    # Try PIL first if not obviously a video (PIL handles images and some GIFs)
    if not is_video:
        try:
            img = Image.open(io.BytesIO(data))
            if getattr(img, "is_animated", False):
                frames = []
                for i in range(img.n_frames):
                    img.seek(i)
                    frames.append(np.array(img.convert("RGB")))
                arr = np.array(frames).astype(np.float32) / 255.0
                return torch.from_numpy(arr)
            else:
                img = img.convert("RGB")
                arr = np.array(img).astype(np.float32) / 255.0
                return torch.from_numpy(arr)[None, ...]
        except Exception:
            # If PIL failed, might be a video that PIL didn't recognize, fall through
            pass

    # Video handling with imageio
    if imageio:
        try:
            # Create temp file because many video readers need a seekable file path
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(lower_url)[1] or ".mp4") as tf:
                tf.write(data)
                tf.flush()
                tf_name = tf.name
            
            try:
                # imageio.mimread reads all frames
                # using ffmpeg backend usually
                frames = imageio.mimread(tf_name, memtest=False)
                if not frames:
                    raise ValueError("No frames read from video")
                
                # Convert to numpy array
                arr = np.array(frames)
                
                # Handle different shapes [T, H, W, C] vs [H, W, C] if single frame?
                # mimread returns list of numpy arrays commonly
                if arr.ndim == 3: # Single frame [H, W, C]
                    arr = arr[None, ...]
                
                # Normalize
                arr = arr.astype(np.float32) / 255.0
                
                # Ensure RGB (drop Alpha if present to match standard Comfy images usually being RGB)
                if arr.shape[-1] == 4:
                    arr = arr[..., :3]
                
                return torch.from_numpy(arr)
            finally:
                try:
                    os.unlink(tf_name)
                except:
                    pass
        except Exception as e:
            print(f"Scromfy Browser: Failed to load video with imageio: {e}")

    # Fallback return empty
    print(f"Scromfy Browser: Could not load content from {url} as image or video.")
    return empty_image_tensor()

# =============================================================================
# SECTION: TUBES Integration
# =============================================================================

def build_tube_from_metadata(
    img_prompt: str, img_neg_prompt: str,
    img_steps: int, img_cfg: float,
    img_sampler: str, img_scheduler: str,
    img_model_name: str,
    img_width: int, img_height: int,
    img_seed: int, img_loras: list,
    img_clip_skip: int = None,
    img_image = None,
    defaults_tube: dict = None
) -> dict:
    """Build a TUBE dict from image metadata with fallback to defaults."""
    result = {}
    result["prompt"] = resolve_tube_value("prompt", img_prompt, defaults_tube)
    result["neg_prompt"] = resolve_tube_value("neg_prompt", img_neg_prompt, defaults_tube)
    result["steps"] = int(resolve_tube_value("steps", img_steps, defaults_tube) or 8)
    result["cfg"] = float(resolve_tube_value("cfg", img_cfg, defaults_tube) or 1.0)
    result["sampler_name"] = str(resolve_tube_value("sampler_name", img_sampler, defaults_tube) or "euler")
    result["scheduler_name"] = str(resolve_tube_value("scheduler_name", img_scheduler, defaults_tube) or "normal")
    result["model_name"] = str(resolve_tube_value("model_name", img_model_name, defaults_tube) or "")
    result["width"] = int(resolve_tube_value("width", img_width, defaults_tube) or 1024)
    result["height"] = int(resolve_tube_value("height", img_height, defaults_tube) or 1024)
    result["seed"] = int(resolve_tube_value("seed", img_seed, defaults_tube) or 1)
    result["clip_skip"] = int(resolve_tube_value("clip_skip", img_clip_skip, defaults_tube) or 1)
    result["loras"] = img_loras if img_loras else resolve_tube_value("loras", None, defaults_tube) or []
    if img_image is not None: result["image"] = img_image
    return result

# =============================================================================
# SECTION: LoRA Extraction logic
# =============================================================================

def extract_loras_from_resources(resources: List[Dict], version_lookup: Optional[Dict] = None) -> tuple:
    names, syntaxes = [], []
    for r in resources:
        if not isinstance(r, dict) or str(r.get("type", "")).lower() != "lora": continue
        w = r.get("weight") or r.get("strength") or 1.0
        try: w = float(w)
        except: w = 1.0
        raw = str(r.get("name") or "")
        if not raw and version_lookup:
            vid = r.get("modelVersionId")
            if vid in version_lookup:
                raw = version_lookup[vid].get("model_name") or version_lookup[vid].get("version_name") or ""
        if not raw: continue
        for ext in (".safetensors", ".ckpt", ".pt", ".bin"):
            if raw.lower().endswith(ext):
                raw = raw[:-len(ext)]
                break
        names.append(raw)
        syntaxes.append(f"<lora:{raw}:{w}>")
    return names, syntaxes

def extract_loras_from_hashes(hashes: Dict) -> tuple:
    n, s = [], []
    if not isinstance(hashes, dict): return n, s
    for k in hashes.keys():
        if k.startswith("LORA:"):
            name = k[5:]
            if name:
                n.append(name)
                s.append(f"<lora:{name}:1.0>")
    return n, s

def extract_loras_from_prompt(prompt: str) -> tuple:
    n, s = [], []
    if not prompt: return n, s
    matches = re.findall(r'<lora:([^:>]+):([0-9.]+)(?::([0-9.]+))?>', prompt)
    for m in matches:
        name = m[0].strip()
        try: w = float(m[1])
        except: w = 1.0
        if name:
            n.append(name)
            s.append(f"<lora:{name}:{w}>")
    return n, s

def format_lora_outputs(n: List[str], s: List[str]) -> tuple:
    if not n: return "", ""
    if len(n) == 1: return n[0], s[0]
    return str(n), "".join(s)

# =============================================================================
# SECTION: Metadata Parsing
# =============================================================================

def extract_prompt(meta: Dict, item_data: Optional[Dict] = None) -> str:
    if item_data and item_data.get("prompt"): return str(item_data.get("prompt"))
    return str(meta.get("prompt") or meta.get("Prompt") or meta.get("positive") or meta.get("textPrompt") or "")

def extract_negative_prompt(meta: Dict) -> str:
    return str(meta.get("negativePrompt") or meta.get("NegativePrompt") or meta.get("negative") or "")

def extract_dimensions(meta: Dict, item_data: Dict) -> tuple:
    w = safe_int(meta.get("width") or item_data.get("width"))
    h = safe_int(meta.get("height") or item_data.get("height"))
    if (w is None or h is None) and meta.get("Size"):
        try:
            parts = str(meta.get("Size")).split("x")
            if len(parts) == 2:
                if w is None: w = safe_int(parts[0])
                if h is None: h = safe_int(parts[1])
        except: pass
    return w, h

def extract_model_name(meta: Dict, item_data: Dict) -> Optional[str]:
    m = meta.get("Model") or meta.get("model")
    if not m:
        hashes = meta.get("hashes") or {}
        if isinstance(hashes, dict):
            for k in hashes.keys():
                if k.startswith("Model:"):
                    m = k[6:]
                    break
    if not m: m = item_data.get("baseModel") or item_data.get("base_model")
    return m

INFO_EXCLUDE_KEYS = {
    "prompt",
    "Prompt",
    "positive",
    "textPrompt",
    "negativePrompt",
    "NegativePrompt",
    "negative",
    "Size",
    "draft",
    "engine",
    "process",
    "quantity",
    "workflow",
    "disablePoi",
}

def build_info_string(meta: Dict) -> str:
    info = {k: v for k, v in meta.items() if k not in INFO_EXCLUDE_KEYS}
    try: return json.dumps(info, indent=4, ensure_ascii=False)
    except: return "{}"

def build_raw_json(data: Dict) -> str:
    try: return json.dumps(data, indent=4, ensure_ascii=False)
    except: return "{}"
