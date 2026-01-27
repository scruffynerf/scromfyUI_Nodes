"""
Civitai Image Browser - ComfyUI Custom Node
Migrated to Scromfy Framework with Tube integration.
"""

import json
import os
import re
import time
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
    build_info_string,
    build_raw_json,
)
from .support.base_models import CIVITAI_BASE_MODELS

# Constants
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FAVORITES_FILE = os.path.join(ROOT_DIR, "favorites", "civitai_favorites.json")

def _load_favorites() -> Dict[str, Any]:
    return load_favorites(FAVORITES_FILE)

def _save_favorites(data: Dict[str, Any]) -> None:
    save_favorites(FAVORITES_FILE, data)

def item_is_video(it: Dict[str, Any]) -> bool:
    """Determine if a Civitai item is a video (mp4/webm) rather than an image."""
    u = str(it.get("url") or "").lower()
    if u.endswith(".mp4") or u.endswith(".webm"):
        return True
    m = it.get("meta") or {}
    mv = str(
        m.get("video") or 
        m.get("videoUrl") or 
        m.get("mp4") or 
        m.get("mp4Url") or 
        ""
    ).lower()
    return mv.endswith(".mp4") or mv.endswith(".webm")

def item_has_positive_prompt(it: Dict[str, Any]) -> bool:
    """Check if an item has a non-empty positive prompt in its metadata."""
    m = it.get("meta") or {}
    for k in (
        "prompt",
        "Prompt",
        "positive",
        "textPrompt"
    ):
        if str(m.get(k) or "").strip():
            return True
    return False

def item_matches_query_local(it: Dict[str, Any], q: str) -> bool:
    """Client-side text search across multiple fields of an item."""
    if not q:
        return True
    q = q.lower().strip()
    m = it.get("meta") or {}
    buf = " | ".join(
        str(x or "")
        for x in [
            it.get("id"),
            it.get("url"),
            m.get("prompt"),
            m.get("Prompt"),
            m.get("textPrompt"),
            m.get("negativePrompt"),
            m.get("NegativePrompt"),
            (it.get("user") or {}).get("username") or (it.get("user") or {}).get("name") or "",
            m.get("Model") or m.get("model") or "",
        ]
    ).lower()
    return q in buf

class CivitaiImageBrowserNode:
    """Main ComfyUI node for the Civitai Image Browser."""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "selection_data": ("STRING", {
                    "default": "{}",
                    "multiline": True,
                    "tooltip": "JSON payload set by the UI (selected item + flags). Do not edit manually.",
                }),
            },
            "optional": {
                "tube": ("TUBE", {
                    "tooltip": "Optional TUBE with default values to use when image metadata is missing.",
                }),
                "download_image": ("BOOLEAN", {
                    "default": True,
                    "tooltip": "Download the selected image. Set to False to skip download.",
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
        # ----- Parse Input JSON -----
        try:
            node_selection = json.loads(selection_data or "{}")
        except Exception:
            node_selection = {}

        item_data = node_selection.get("item", {}) if isinstance(node_selection, dict) else {}
        should_download = download_image if download_image is not None else True

        meta = item_data.get("meta", {}) if isinstance(item_data, dict) else {}
        if not isinstance(meta, dict):
            meta = {}

        # ----- Tube Input (TUBE is a dict) -----
        defaults_tube = tube if isinstance(tube, dict) else {}

        # ----- Extract Image Metadata -----
        img_positive = extract_prompt(meta)
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

        # ----- Extract LoRA Information as LORA_STACK -----
        lora_stack = []
        
        # Try additionalResources/resources array first
        additional_resources = (
            meta.get("additionalResources") or 
            meta.get("resources") or 
            []
        )
        if isinstance(additional_resources, list) and additional_resources:
            for resource in additional_resources:
                if not isinstance(resource, dict):
                    continue
                if str(resource.get("type", "")).lower() != "lora":
                    continue
                name = str(resource.get("name") or "")
                if not name:
                    continue
                # Strip extensions
                for ext in (".safetensors", ".ckpt", ".pt", ".bin"):
                    if name.lower().endswith(ext):
                        name = name[:-len(ext)]
                        break
                weight = float(
                    resource.get("weight") or 
                    resource.get("strength") or 
                    1.0
                )
                # (name, model_weight, clip_weight)
                lora_stack.append((name, weight, weight))
        
        # Try hashes if no LoRAs found
        if not lora_stack:
            hashes = meta.get("hashes") or {}
            for key, hash_val in hashes.items():
                if key.lower().startswith("lora:"):
                    name = key[5:].strip()
                    if name:
                        lora_stack.append((name, 1.0, 1.0))
        
        # Try prompt parsing if still no LoRAs
        if not lora_stack and img_positive:
            for match in re.finditer(r"<lora:([^:>]+)(?::([^>]*))?(?::([^>]*))?>", img_positive):
                name = match.group(1).strip()
                if name:
                    weight = float(match.group(2) or 1.0) if match.group(2) else 1.0
                    lora_stack.append((name, weight, weight))

        # ----- Download Image (if needed) -----
        image_url = str(item_data.get("url") or "") if isinstance(item_data, dict) else ""
        tensor = empty_image_tensor()

        if should_download and image_url:
            try:
                tensor = download_image_to_tensor(image_url, timeout_s=30)
            except Exception:
                tensor = empty_image_tensor()

        # ----- Build TUBE Output (includes image) -----
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
        
        info_string = build_info_string(meta)
        raw_json = build_raw_json(item_data)

        # ----- Return All Outputs -----
        return (
            tensor,
            tube_out,
            img_positive,
            img_negative,
            info_string,
            raw_json,
            f"civitai_{item_data.get('id', 'unknown')}"
        )

# HTTP Server Routes
prompt_server = PromptServer.instance

@prompt_server.routes.get("/scromfy/base_models")
async def get_base_models(request):
    """Return the centralized list of base models."""
    return web.json_response(CIVITAI_BASE_MODELS)

@prompt_server.routes.get("/civitai_images/get_all_favorites_data")
async def get_all_favorites_data(request):
    """Return all favorites as a dictionary."""
    return web.json_response(_load_favorites())

@prompt_server.routes.post("/civitai_images/toggle_favorite")
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

@prompt_server.routes.get("/civitai_images/images_stream")
async def images_stream(request):
    """
    Aggregating proxy for Civitai /api/v1/images with client-side baseModel filtering.
    """
    try:
        # Parse query parameters
        cursor = request.query.get("cursor") or None
        min_batch = clamp_int(request.query.get("min_batch", 24), 1, 500, 24)
        time_budget_ms = clamp_int(request.query.get("time_budget_ms", 0), 0, 30000, 0)
        
        sort_map = {
            "newest": "Newest",
            "most reactions": "Most Reactions",
            "most comments": "Most Comments"
        }
        sort = sort_map.get(request.query.get("sort", "Newest").lower(), "Newest")
        
        period_map = {
            "alltime": "AllTime",
            "year": "Year",
            "month": "Month",
            "week": "Week",
            "day": "Day"
        }
        period = period_map.get(request.query.get("period", "AllTime").lower(), "AllTime")
        
        nsfw_map = {
            "none": "None",
            "soft": "Soft",
            "mature": "Mature",
            "x": "X"
        }
        nsfw = nsfw_map.get(request.query.get("nsfw", "None").lower(), "None")
        
        username = request.query.get("username", "").strip() or None
        tags = request.query.get("tags", "").strip() or None
        include_videos = truthy(request.query.get("include_videos", "false"))
        videos_only = truthy(request.query.get("videos_only", "false"))
        hide_no_prompt = truthy(request.query.get("hide_no_prompt", "false"))
        base_model_filter = request.query.get("baseModel", "").strip()
        query_q = request.query.get("q", "").strip()

        needs_client_filter = bool(base_model_filter)
        deadline = (time.monotonic() + time_budget_ms / 1000.0) if time_budget_ms > 0 else None

        base_url = "https://civitai.com/api/v1/images"

        def build_params(cur: Optional[str]) -> Dict[str, str]:
            p = {
                "limit": "200",
                "sort": sort,
                "period": period,
                "nsfw": nsfw
            }
            if cur:
                p["cursor"] = cur
            if username:
                p["username"] = username
            if tags:
                p["tags"] = tags
            return p

        def item_matches_base_model(it: Dict[str, Any]) -> bool:
            if not base_model_filter:
                return True
            img_base_model = str(it.get("baseModel") or "").strip()
            return img_base_model.lower() == base_model_filter.lower()

        async def fetch_once(session: aiohttp.ClientSession, cur: Optional[str]) -> Dict[str, Any]:
            params = build_params(cur)
            async with session.get(base_url, params=params) as resp:
                text = await resp.text()
                if resp.status != 200:
                    return {
                        "items": [],
                        "metadata": {
                            "error": f"upstream {resp.status}",
                            "detail": text[:400]
                        },
                        "next": None
                    }
                try:
                    data = json.loads(text)
                except Exception:
                    return {
                        "items": [],
                        "metadata": {"error": "bad json"},
                        "next": None
                    }

                md = data.get("metadata", {}) if isinstance(data, dict) else {}
                nxt = md.get("nextCursor") or md.get("cursor") or md.get("next") or None
                items = data.get("items", []) if isinstance(data, dict) else []
                if not isinstance(items, list):
                    items = []
                return {
                    "items": items,
                    "metadata": md,
                    "next": nxt
                }

        started = time.monotonic()
        kept: List[Dict[str, Any]] = []
        dropped = 0
        next_cursor = None
        total_scanned = 0
        api_calls = 0

        async with aiohttp.ClientSession() as session:
            cur = cursor
            for _ in range(50):
                api_calls += 1
                res = await fetch_once(session, cur)
                rec_items = res.get("items", [])
                next_cursor = res.get("next", None)
                total_scanned += len(rec_items)

                for it in rec_items:
                    if not isinstance(it, dict):
                        dropped += 1
                        continue

                    if needs_client_filter and not item_matches_base_model(it):
                        dropped += 1
                        continue

                    if videos_only:
                        if not item_is_video(it):
                            dropped += 1
                            continue
                    else:
                        if not include_videos and item_is_video(it):
                            dropped += 1
                            continue

                    if hide_no_prompt and not item_has_positive_prompt(it):
                        dropped += 1
                        continue
                    
                    if query_q and not item_matches_query_local(it, query_q):
                        dropped += 1
                        continue

                    kept.append(it)

                if len(kept) >= min_batch:
                    break

                if deadline is not None and time.monotonic() >= deadline and len(kept) > 0:
                    break

                if not next_cursor:
                    break

                cur = next_cursor

        served = kept[:min_batch] if min_batch > 0 else kept

        meta_out = {
            "aggregated": True,
            "nextCursor": next_cursor,
            "served": len(served),
            "totalScanned": total_scanned,
            "apiCalls": api_calls,
            "droppedByFilters": dropped,
            "hasMore": bool(next_cursor),
            "nsfw": nsfw,
            "sort": sort,
            "period": period,
            "videosOnly": videos_only,
            "elapsedMs": int((time.monotonic() - started) * 1000),
            "timeBudgetMs": time_budget_ms,
            "clientSideBaseModelFilter": needs_client_filter,
            "baseModelFilter": base_model_filter,
        }
        return web.json_response({"items": served, "metadata": meta_out})
    except Exception as e:
        return web.json_response(
            {"error": f"Unhandled: {e}"},
            status=500
        )

@prompt_server.routes.post("/civitai_images/check_video_workflow")
async def check_video_workflow(request):
    """Check if a video file contains embedded workflow data."""
    data = await request.json()
    video_url = data.get("url")
    if not video_url:
        return web.json_response(
            {"has_workflow": False, "error": "URL is missing"},
            status=400
        )
    try:
        headers = {"Range": "bytes=0-4194304"}
        async with aiohttp.ClientSession() as session:
            async with session.get(video_url, headers=headers) as response:
                if response.status >= 400 and response.status != 416:
                    return web.json_response(
                        {"has_workflow": False, "error": f"Failed to fetch video chunk, status: {response.status}"}
                    )
                chunk = await response.content.read()
                has_workflow = b'"workflow":' in chunk or b'"prompt":' in chunk
                return web.json_response({"has_workflow": has_workflow})
    except Exception as e:
        return web.json_response(
            {"has_workflow": False, "error": str(e)},
            status=500
        )

@prompt_server.routes.get("/civitai_images/get_video_for_workflow")
async def get_video_for_workflow(request):
    """Proxy endpoint to download a video file."""
    video_url = request.query.get("url")
    if not video_url:
        return web.Response(status=400, text="Missing video URL")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(video_url) as response:
                if response.status != 200:
                    return web.Response(
                        status=response.status,
                        text=f"Failed to fetch video from source: {response.reason}"
                    )
                data = await response.read()
                filename = video_url.split("/")[-1].split("?")[0] or "video_with_workflow.mp4"
                return web.Response(
                    body=data,
                    content_type=response.content_type,
                    headers={"Content-Disposition": f"attachment; filename=\"{filename}\""},
                )
    except Exception as e:
        return web.Response(status=500, text=str(e))

NODE_CLASS_MAPPINGS = {
    "CivitaiImageBrowser": CivitaiImageBrowserNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "CivitaiImageBrowser": "Civitai"
}
