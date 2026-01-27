"""
Genur.art Image Browser - ComfyUI Custom Node
Migrated to Scromfy Framework with Tube integration.
"""

import json
import os
import re
import time
import urllib.request
from typing import Any, Dict, List, Optional

import aiohttp
from aiohttp import web
from server import PromptServer

# Import shared utilities from support
from .support.browser_common import (
    clamp_int,
    truthy,
    safe_int,
    safe_float,
    load_favorites,
    save_favorites,
    empty_image_tensor,
    download_image_to_tensor,
    build_tube_from_metadata,
    extract_prompt,
    extract_negative_prompt,
    extract_dimensions,
    extract_model_name,
    build_info_string,
    build_raw_json,
)

# Constants
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FAVORITES_FILE = os.path.join(ROOT_DIR, "favorites", "genur_favorites.json")
GENUR_API_BASE = "https://genur.art/api"

def _load_favorites() -> Dict[str, Any]:
    return load_favorites(FAVORITES_FILE)

def _save_favorites(data: Dict[str, Any]) -> None:
    save_favorites(FAVORITES_FILE, data)

class GenurImageBrowserNode:
    """Main ComfyUI node for the Genur.art Image Browser."""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "selection_data": ("STRING", {
                    "default": "{}",
                    "multiline": True,
                    "tooltip": "JSON payload set by the UI. Do not edit manually.",
                }),
            },
            "optional": {
                "tube": ("TUBE", {
                    "tooltip": "Optional TUBE with default values.",
                }),
                "download_image": ("BOOLEAN", {
                    "default": True,
                    "tooltip": "Download the selected image.",
                }),
            },
        }
    
    RETURN_TYPES = (
        "IMAGE",
        "TUBE",
        "STRING",
        "STRING",
        "STRING",
        "STRING",
        "STRING"
    )
    RETURN_NAMES = (
        "image",
        "tube",
        "positive",
        "negative",
        "info",
        "raw_json",
        "filename"
    )
    FUNCTION = "execute"
    CATEGORY = "Scromfy/ImageBrowser"

    @classmethod
    def IS_CHANGED(cls, selection_data, tube=None, download_image=True, **kwargs):
        return (selection_data, id(tube), download_image)

    def execute(self, selection_data: str, tube=None, download_image=True):
        try:
            node_selection = json.loads(selection_data or "{}")
        except Exception:
            node_selection = {}

        item_data = node_selection.get("item", {}) if isinstance(node_selection, dict) else {}
        should_download = download_image if download_image is not None else True

        meta = item_data.get("meta", {}) if isinstance(item_data, dict) else {}
        if not isinstance(meta, dict):
            meta = {}

        defaults_tube = tube if isinstance(tube, dict) else {}

        # ----- Extract Metadata -----
        img_positive = extract_prompt(meta, item_data)
        img_negative = extract_negative_prompt(meta)
        img_steps = safe_int(meta.get("steps"))
        img_cfg = safe_float(
            meta.get("cfgScale") or 
            meta.get("cfg") or 
            meta.get("CFG scale")
        )
        img_sampler = (
            meta.get("sampler") or 
            meta.get("Sampler") or 
            None
        )
        img_scheduler = (
            meta.get("scheduler") or 
            meta.get("Scheduler") or 
            None
        )
        img_width, img_height = extract_dimensions(meta, item_data)
        img_seed = safe_int(meta.get("seed"))
        img_modelname = extract_model_name(meta, item_data)
        img_clip_skip = safe_int(
            meta.get("clipSkip") or 
            meta.get("clip_skip") or 
            meta.get("Clip skip")
        )

        # ----- Extract LoRA Information -----
        lora_stack = []
        civitai_resources = meta.get("civitaiResources") or []
        model_versions = item_data.get("model_versions") or []
        version_lookup = {
            mv.get("id"): mv 
            for mv in model_versions 
            if isinstance(mv, dict)
        }
        
        if isinstance(civitai_resources, list) and civitai_resources:
            for resource in civitai_resources:
                if not isinstance(resource, dict):
                    continue
                if str(resource.get("type", "")).lower() != "lora":
                    continue
                name = str(resource.get("name") or "")
                if not name:
                    version_id = resource.get("modelVersionId")
                    if version_id and version_id in version_lookup:
                        mv = version_lookup[version_id]
                        name = mv.get("model_name") or mv.get("version_name") or ""
                if not name:
                    continue
                for ext in (".safetensors", ".ckpt", ".pt", ".bin"):
                    if name.lower().endswith(ext):
                        name = name[:-len(ext)]
                        break
                weight = float(
                    resource.get("weight") or 
                    resource.get("strength") or 
                    1.0
                )
                lora_stack.append((name, weight, weight))
        
        # Fallback: Try additionalResources
        if not lora_stack:
            additional_resources = (
                meta.get("additionalResources") or 
                meta.get("resources") or 
                []
            )
            if isinstance(additional_resources, list):
                for resource in additional_resources:
                    if not isinstance(resource, dict):
                        continue
                    if str(resource.get("type", "")).lower() != "lora":
                        continue
                    name = str(resource.get("name") or "")
                    if not name:
                        continue
                    for ext in (".safetensors", ".ckpt", ".pt", ".bin"):
                        if name.lower().endswith(ext):
                            name = name[:-len(ext)]
                            break
                    weight = float(
                        resource.get("weight") or 
                        resource.get("strength") or 
                        1.0
                    )
                    lora_stack.append((name, weight, weight))
        
        # Fallback: Parse from prompt
        if not lora_stack and img_positive:
            for match in re.finditer(r"<lora:([^:>]+)(?::([^>]*))?(?::([^>]*))?>", img_positive):
                name = match.group(1).strip()
                if name:
                    weight = float(match.group(2) or 1.0) if match.group(2) else 1.0
                    lora_stack.append((name, weight, weight))

        # ----- Download Image -----
        image_url = str(item_data.get("url") or "") if isinstance(item_data, dict) else ""
        if image_url and "img.genur.art" in image_url:
            full_url = item_data.get("full_url") or ""
            if full_url:
                image_url = full_url
        
        tensor = empty_image_tensor()
        if should_download and image_url:
            try:
                tensor = download_image_to_tensor(image_url, timeout_s=30)
            except Exception:
                tensor = empty_image_tensor()

        # ----- Build TUBE Output -----
        tube_out = build_tube_from_metadata(
            img_prompt=img_positive,
            img_neg_prompt=img_negative,
            img_steps=img_steps,
            img_cfg=img_cfg,
            img_sampler=img_sampler,
            img_scheduler=img_scheduler,
            img_model_name=img_modelname,
            img_width=img_width,
            img_height=img_height,
            img_seed=img_seed,
            img_loras=lora_stack,
            img_clip_skip=img_clip_skip,
            img_image=tensor,
            defaults_tube=defaults_tube
        )
        
        return (
            tensor,
            tube_out,
            img_positive,
            img_negative,
            build_info_string(meta),
            json.dumps(item_data, indent=4),
            f"genur_{item_data.get('id', 'unknown')}"
        )

# HTTP Server Routes
prompt_server = PromptServer.instance

@prompt_server.routes.get("/genur_images/get_all_favorites_data")
async def get_all_favorites_data(request):
    """Return all favorites as a dictionary."""
    return web.json_response(_load_favorites())

@prompt_server.routes.post("/genur_images/toggle_favorite")
async def toggle_favorite(request):
    """Toggle favorite status for an image."""
    try:
        data = await request.json()
        item = data.get("item")
        if not item or "id" not in item:
            return web.json_response(
                {"error": "Invalid item"},
                status=400
            )
        favs = _load_favorites()
        key = str(item["id"])
        if key in favs:
            del favs[key]
            _save_favorites(favs)
            return web.json_response({"status": "removed", "id": key})
        else:
            favs[key] = item
            _save_favorites(favs)
            return web.json_response({"status": "added", "id": key})
    except Exception as e:
        return web.json_response(
            {"error": str(e)},
            status=500
        )

@prompt_server.routes.get("/genur_images/images_stream")
async def genur_images_stream(request):
    """Fetch images from Genur.art API with filtering."""
    try:
        page = clamp_int(request.query.get("page", 1), 1, 1000, 1)
        sort = request.query.get("sort", "top")
        query = request.query.get("q", "").strip()
        base_model_filter = request.query.get("baseModel", "").strip()
        
        params = {
            "sort": sort,
            "page": page
        }
        if query:
            params["q"] = query
        
        query_string = "&".join(
            f"{k}={urllib.request.quote(str(v))}" 
            for k, v in params.items()
        )
        api_url = f"{GENUR_API_BASE}/search?{query_string}"
        
        started = time.monotonic()
        cookies = {"nsfw_enabled": "true"}
        
        async with aiohttp.ClientSession(cookies=cookies) as session:
            async with session.get(api_url) as resp:
                if resp.status != 200:
                    return web.json_response(
                        {"error": f"upstream {resp.status}"},
                        status=resp.status
                    )
                try:
                    data = await resp.json()
                except:
                    return web.json_response(
                        {"error": "Invalid JSON response"},
                        status=500
                    )
        
        results = data.get("results", []) if isinstance(data, dict) else []
        kept = []
        dropped = 0
        
        for item in (results if isinstance(results, list) else []):
            if not isinstance(item, dict):
                dropped += 1
                continue
            
            if "nsfw" in item and "is_nsfw" not in item:
                item["is_nsfw"] = item["nsfw"]
            
            if base_model_filter:
                item_base = str(item.get("base_model") or "").strip()
                if item_base.lower() != base_model_filter.lower():
                    dropped += 1
                    continue
            kept.append(item)
        
        hits = data.get("hits", 0)
        current_page = data.get("page", page)
        total_pages = data.get("totalPages", 1)
        has_more = current_page < total_pages
        
        meta_out = {
            "page": current_page,
            "totalPages": total_pages,
            "hits": hits,
            "hasMore": has_more,
            "nextPage": current_page + 1 if has_more else None,
            "served": len(kept),
            "droppedByFilters": dropped,
            "sort": sort,
            "query": query,
            "baseModelFilter": base_model_filter,
            "elapsedMs": int((time.monotonic() - started) * 1000),
        }
        return web.json_response({"items": kept, "metadata": meta_out})
    except Exception as e:
        return web.json_response(
            {"error": f"Unhandled: {e}"},
            status=500
        )

@prompt_server.routes.get("/genur_images/get_post_details")
async def get_post_details(request):
    """Fetch detailed post data from Genur.art API."""
    try:
        post_id = request.query.get("id")
        if not post_id:
            return web.json_response(
                {"error": "Missing post ID"},
                status=400
            )
        api_url = f"{GENUR_API_BASE}/posts/{post_id}"
        cookies = {"nsfw_enabled": "true"}
        async with aiohttp.ClientSession(cookies=cookies) as session:
            async with session.get(api_url) as resp:
                if resp.status != 200:
                    return web.json_response(
                        {"error": f"upstream {resp.status}"},
                        status=resp.status
                    )
                return web.json_response(await resp.json())
    except Exception as e:
        return web.json_response(
            {"error": f"Unhandled: {e}"},
            status=500
        )

NODE_CLASS_MAPPINGS = {
    "GenurImageBrowser": GenurImageBrowserNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "GenurImageBrowser": "Genur.art"
}
