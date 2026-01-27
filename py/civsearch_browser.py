"""
CivSearch Image Browser - ComfyUI Custom Node
Migrated to Scromfy Framework with Tube integration.
"""

import os
import json
import asyncio
import aiohttp
from typing import Dict, List, Any, Optional
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
    extract_loras_from_prompt,
    build_info_string,
    build_raw_json,
)

from .support.base_models import CIVITAI_BASE_MODELS

# =============================================================================
# CONSTANTS
# =============================================================================

SEARCH_API_URL = "https://search-new.civitai.com/multi-search"
IMAGE_CDN_BASE = "https://image.civitai.com/xG1nkqKTMzGDvpLrqFT7WA"

# Cookie file path (Netscape format)
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COOKIE_FILE = os.path.join(ROOT_DIR, "auth", "cookies-civitai-com.txt")

# Favorites file
FAVORITES_FILE = os.path.join(ROOT_DIR, "favorites", "civsearch_favorites.json")

SORT_OPTIONS = {
    "Relevancy": None,
    "Most Reactions": "stats.reactionCountAllTime:desc",
    "Most Discussed": "stats.commentCountAllTime:desc",
    "Most Collected": "stats.collectedCountAllTime:desc",
    "Most Buzz": "stats.tippedAmountCountAllTime:desc",
    "Newest": "createdAt:desc",
}

NSFW_LEVELS = {
    "None (SFW only)": [1],
    "Soft": [1, 2],
    "Mature": [1, 2, 4],
    "X": [1, 2, 4, 8, 16, 32],
}

ASPECT_RATIOS = [
    "Any",
    "Landscape",
    "Portrait",
    "Square"
]

MEDIA_TYPES = [
    "Any",
    "image",
    "video"
]

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def load_cookies_from_file(filepath: str) -> Dict[str, str]:
    """Load cookies from a Netscape-format cookies file."""
    cookies = {}
    if not os.path.exists(filepath):
        return cookies
    try:
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                parts = line.split('\t')
                if len(parts) >= 7:
                    cookies[parts[5]] = parts[6]
    except Exception as e:
        print(f"[CivSearch] Error loading cookies: {e}")
    return cookies

def get_cookie_header() -> str:
    """Get cookie header string from loaded cookies."""
    cookies = load_cookies_from_file(COOKIE_FILE)
    if not cookies:
        return ""
    return "; ".join([f"{k}={v}" for k, v in cookies.items()])

def build_filter_string(field: str, value: str) -> str:
    """Build a single filter condition."""
    return f'"{field}"="{value}"'

def build_nsfw_filter(levels: List[int]) -> str:
    """Build NSFW level filter."""
    conditions = " OR ".join([f"nsfwLevel={level}" for level in levels])
    return f"({conditions})"

def build_search_query(
    q: str = "",
    base_model: str = "Any",
    media_type: str = "Any",
    tool: str = "",
    technique: str = "",
    aspect_ratio: str = "Any",
    username: str = "",
    tag: str = "",
    nsfw: str = "None (SFW only)",
    sort: str = "Most Collected",
    limit: int = 50,
    offset: int = 0,
) -> Dict[str, Any]:
    """Build the multi-search query object."""
    filters = []
    if base_model != "Any":
        filters.append(build_filter_string("baseModel", base_model))
    if media_type != "Any":
        filters.append(build_filter_string("type", media_type))
    if tool.strip():
        filters.append(build_filter_string("toolNames", tool.strip()))
    if technique.strip():
        filters.append(build_filter_string("techniqueNames", technique.strip()))
    if aspect_ratio != "Any":
        filters.append(build_filter_string("aspectRatio", aspect_ratio))
    if username.strip():
        filters.append(build_filter_string("user.username", username.strip()))
    if tag.strip():
        filters.append(build_filter_string("tagNames", tag.strip()))
    
    nsfw_levels = NSFW_LEVELS.get(nsfw, [1])
    filters.append(build_nsfw_filter(nsfw_levels))
    
    sort_value = SORT_OPTIONS.get(sort)
    
    query = {
        "q": q,
        "indexUid": "images_v6",
        "facets": [
            "aspectRatio",
            "baseModel", 
            "tagNames",
            "techniqueNames",
            "toolNames",
            "type",
            "user.username"
        ],
        "attributesToHighlight": [],
        "limit": limit,
        "offset": offset,
        "filter": filters,
    }
    if sort_value:
        query["sort"] = [sort_value]
    return query

def transform_hit_to_item(hit: Dict) -> Dict:
    """Transform a search hit into standard format."""
    url_id = hit.get("url", "")
    is_video = (
        hit.get("type") == "video" or 
        hit.get("mimeType", "").startswith("video")
    )
    suffix = ".mp4" if is_video else ".jpeg"
    prefix = "original=true/" if is_video else ""
    full_url = f"{IMAGE_CDN_BASE}/{url_id}/{prefix}{url_id}{suffix}"
    
    return {
        "id": hit.get("id"),
        "postId": hit.get("postId"),
        "url": full_url,
        "fullUrl": full_url,
        "thumbUrl": f"{IMAGE_CDN_BASE}/{url_id}/width=450/{url_id}.jpeg",
        "width": hit.get("width", 0),
        "height": hit.get("height", 0),
        "type": "video" if is_video else "image",
        "baseModel": hit.get("baseModel", ""),
        "username": (
            hit.get("user", {}).get("username") or 
            hit.get("user", {}).get("name") or 
            ""
        ),
        "nsfwLevel": hit.get("nsfwLevel", 1),
        "hash": hit.get("hash", ""),
        "prompt": hit.get("prompt", ""),
        "negativePrompt": hit.get("negativePrompt", ""),
        "tagNames": hit.get("tagNames", []),
        "stats": hit.get("stats", {}),
        "createdAt": hit.get("createdAt", ""),
        "_raw": hit,
    }

class CivSearchImageBrowserNode:
    """Main node for CivSearch Image Browser."""
    
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
        if not item_data:
            return (
                empty_image_tensor(),
                tube or {},
                "",
                "",
                "{}",
                "{}",
                ""
            )
        
        meta = item_data.get("_raw", {}) if isinstance(item_data, dict) else {}
        image_url = item_data.get("url", "")
        image_id = item_data.get("id", "")
        media_type = item_data.get("type", "image")
        
        tensor = empty_image_tensor()
        if download_image and media_type != "video" and image_url:
            try:
                tensor = download_image_to_tensor(image_url)
            except:
                pass
        
        img_pos = item_data.get("prompt", "")
        img_neg = item_data.get("negativePrompt", "")
        
        # Extract LoRAs from prompt text
        _, lora_syntax = extract_loras_from_prompt(img_pos)
        # Convert syntax string to stack format
        # TODO: This is a bit heuristic, build_tube_from_metadata expects list of (name, model, clip)
        lora_stack = []
        if lora_syntax:
            matches = re.findall(r'<lora:([^:>]+):([0-9.]+)', lora_syntax)
            for n, w in matches:
                fw = float(w)
                lora_stack.append((n, fw, fw))

        tube_out = build_tube_from_metadata(
            img_prompt=img_pos,
            img_neg_prompt=img_neg,
            img_steps=meta.get("steps"),
            img_cfg=meta.get("cfgScale") or meta.get("cfg"),
            img_sampler=meta.get("sampler"),
            img_scheduler=meta.get("scheduler"),
            img_model_name=item_data.get("baseModel"),
            img_width=item_data.get("width"),
            img_height=item_data.get("height"),
            img_seed=meta.get("seed"),
            img_loras=lora_stack,
            img_image=tensor,
            defaults_tube=tube
        )
        
        return (
            tensor,
            tube_out,
            img_pos,
            img_neg,
            build_info_string(meta),
            json.dumps(item_data, indent=4),
            f"civsearch_{image_id}"
        )

# HTTP Server Routes
prompt_server = PromptServer.instance

@prompt_server.routes.get("/civsearch/debug_cookies")
async def civsearch_debug_cookies(request):
    cookies = load_cookies_from_file(COOKIE_FILE)
    return web.json_response({
        "cookie_file": COOKIE_FILE,
        "file_exists": os.path.exists(COOKIE_FILE),
        "cookie_count": len(cookies),
        "cookie_names": list(cookies.keys()),
    })

@prompt_server.routes.get("/civsearch/search")
async def civsearch_search(request):
    params = request.rel_url.query
    MEILISEARCH_API_KEY = "8c46eb2508e21db1e9828a97968d91ab1ca1caa5f70a00e88a2ba1e286603b61"
    
    query = build_search_query(
        q=params.get("q", ""),
        base_model=params.get("baseModel", "Any"),
        media_type=params.get("mediaType", "Any"),
        tool=params.get("tool", ""),
        technique=params.get("technique", ""),
        aspect_ratio=params.get("aspectRatio", "Any"),
        username=params.get("username", ""),
        tag=params.get("tag", ""),
        nsfw=params.get("nsfw", "None (SFW only)"),
        sort=params.get("sort", "Most Collected"),
        offset=safe_int(params.get("offset", "0")) or 0,
    )
    
    headers = {
        "Content-Type": "application/json",
        "Origin": "https://civitai.com",
        "Referer": "https://civitai.com/",
        "Authorization": f"Bearer {MEILISEARCH_API_KEY}",
    }
    cookie_str = get_cookie_header()
    if cookie_str:
        headers["Cookie"] = cookie_str

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                SEARCH_API_URL,
                json={"queries": [query]},
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                if resp.status != 200:
                    return web.json_response(
                        {"error": f"Search API error: {resp.status}"},
                        status=resp.status
                    )
                data = await resp.json()
                results = data.get("results", [])
                if not results:
                    return web.json_response({"items": [], "total": 0})
                
                first = results[0]
                hits = first.get("hits", [])
                total = first.get("estimatedTotalHits", 0)
                items = [transform_hit_to_item(h) for h in hits]
                return web.json_response({"items": items, "total": total})
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)

@prompt_server.routes.get("/civsearch/get_all_favorites_data")
async def civsearch_get_favorites(request):
    return web.json_response(load_favorites(FAVORITES_FILE))

@prompt_server.routes.post("/civsearch/toggle_favorite")
async def civsearch_toggle_favorite(request):
    try:
        data = await request.json()
        image_id = str(data.get("id", ""))
        if not image_id:
            return web.json_response({"error": "Missing id"}, status=400)
        favs = load_favorites(FAVORITES_FILE)
        is_favorite = False
        if image_id in favs:
            del favs[image_id]
        else:
            favs[image_id] = data
            is_favorite = True
        save_favorites(FAVORITES_FILE, favs)
        return web.json_response({"id": image_id, "isFavorite": is_favorite})
    except:
        return web.json_response({"error": "Failed to toggle"}, status=500)

NODE_CLASS_MAPPINGS = {
    "CivSearchImageBrowser": CivSearchImageBrowserNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "CivSearchImageBrowser": "CivSearch"
}
