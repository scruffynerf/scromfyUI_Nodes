"""
Danbooru Image Browser - ComfyUI Custom Node
Migrated to Scromfy Framework with Tube integration.
"""

import os
import json
import logging
from aiohttp import web
import aiohttp
from server import PromptServer

# Import shared utilities from support
from .support.browser_common import (
    empty_image_tensor,
    download_image_to_tensor,
    build_tube_from_metadata,
    load_favorites,
    save_favorites,
)

# =============================================================================
# CONSTANTS & CONFIG
# =============================================================================

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FAVORITES_FILE = os.path.join(ROOT_DIR, "favorites", "danbooru_favorites.json")
AUTH_FILE = os.path.join(ROOT_DIR, "auth", "danbooru_auth.json")
SITES_FILE = os.path.join(ROOT_DIR, "sites", "danbooru_sites.json")

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _load_favs():
    if not os.path.exists(FAVORITES_FILE):
        return []
    try:
        with open(FAVORITES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []

def _save_favs(data):
    try:
        with open(FAVORITES_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Error saving favorites: {e}")

def _load_auth():
    if not os.path.exists(AUTH_FILE):
        return {}
    try:
        with open(AUTH_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def _save_auth(data):
    try:
        with open(AUTH_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Error saving auth: {e}")

# =============================================================================
# NODE DEFINITION
# =============================================================================

class DanbooruImageBrowserNode:
    """A ComfyUI node for browsing Danbooru images via a custom UI."""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "selection_data": ("STRING", {
                    "default": "{}",
                    "multiline": True,
                    "hidden": True,
                }),
                "url": ("STRING", {
                    "default": "",
                    "multiline": False
                }),
            },
            "optional": {
                "tube": ("TUBE",),
            },
            "hidden": {
                "unique_id": "UNIQUE_ID",
                "extra_pnginfo": "EXTRA_PNGINFO",
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

    def execute(self, selection_data, url, tube=None, unique_id=None, extra_pnginfo=None):
        defaults_tube = tube if tube is not None else {}
        
        try:
            item_data = json.loads(selection_data or "{}")
        except:
            item_data = {}

        # ----- Extract Metadata -----
        tags = item_data.get("tag_string", "").replace(" ", ", ")
        width = item_data.get("image_width", 512)
        height = item_data.get("image_height", 512)
        
        # ----- Download Image -----
        image_url = (
            item_data.get("url") or 
            item_data.get("file_url") or 
            item_data.get("large_file_url") or 
            url
        )
        
        tensor = empty_image_tensor()
        if image_url:
             try:
                tensor = download_image_to_tensor(image_url, timeout_s=30)
             except Exception as e:
                print(f"Error downloading image: {e}")
                tensor = empty_image_tensor()

        # ----- Build TUBE -----
        tube_out = build_tube_from_metadata(
            img_prompt=tags,
            img_neg_prompt="",
            img_steps=20,
            img_cfg=7.0,
            img_sampler="euler",
            img_scheduler="normal",
            img_model_name="unknown",
            img_width=width,
            img_height=height,
            img_seed=0,
            img_loras=[],
            img_clip_skip=1,
            img_image=tensor,
            defaults_tube=defaults_tube
        )

        info_string = tags
        raw_json = json.dumps(item_data if item_data else {"url": url}, indent=4)

        return (
            tensor,
            tube_out,
            tags,
            "",
            info_string,
            raw_json,
            f"danbooru_{item_data.get('id', 'unknown')}"
        )

# =============================================================================
# SERVER ROUTES
# =============================================================================

prompt_server = PromptServer.instance

@prompt_server.routes.get("/danbooru_images/proxy")
async def proxy_request(request):
    """Generic proxy to fetch data from image boards to avoid CORS."""
    target_url = request.query.get("url")
    if not target_url:
        return web.json_response(
            {"error": "Missing 'url' parameter"},
            status=400
        )

    try:
        # 1. Validate Protocol
        if not target_url.startswith("http"):
             return web.json_response(
                 {"error": "Invalid URL protocol"},
                 status=400
             )

        # 2. Validate Domain against Allowlist
        allowed_domains = []
        if os.path.exists(SITES_FILE):
             try:
                 with open(SITES_FILE, 'r', encoding='utf-8') as f:
                     sites_data = json.load(f)
                     for key, site in sites_data.items():
                         if isinstance(site, dict) and "domain" in site:
                             allowed_domains.append(site["domain"])
                         elif isinstance(site, dict) and "url" in site:
                             from urllib.parse import urlparse
                             allowed_domains.append(urlparse(site["url"]).netloc)
             except Exception as e:
                 print(f"Error reading sites file: {e}")
        
        default_domains = [
            "danbooru.donmai.us",
            "safebooru.donmai.us",
            "konachan.net",
            "yande.re",
            "gelbooru.com"
        ]
        allowed_domains.extend(default_domains)
        
        from urllib.parse import urlparse
        target_netloc = urlparse(target_url).netloc
        
        is_allowed = False
        for d in allowed_domains:
            if target_netloc == d or target_netloc.endswith("." + d):
                is_allowed = True
                break
        
        if not is_allowed:
             return web.json_response(
                 {"error": f"Domain {target_netloc} blocked"},
                 status=403
             )

        auth_data = _load_auth()
        headers = {
            "User-Agent": "ScromfyDanbooru/1.0 (ComfyUI)",
            "Accept": "application/json"
        }

        matching_auth = auth_data.get(target_netloc)
        auth = None
        if matching_auth and matching_auth.get("username") and matching_auth.get("api_key"):
            auth = aiohttp.BasicAuth(
                matching_auth["username"],
                matching_auth["api_key"]
            )

        async with aiohttp.ClientSession(auth=auth) as session:
            async with session.get(target_url, headers=headers) as resp:
                if resp.status >= 400:
                    return web.json_response(
                        {"error": f"Upstream error {resp.status}"},
                        status=resp.status
                    )
                try:
                    return web.json_response(await resp.json())
                except:
                    return web.json_response(
                        {"error": "Non-JSON response"},
                        status=502
                    )
    except Exception as e:
        return web.json_response(
            {"error": str(e)},
            status=500
        )

@prompt_server.routes.get("/danbooru_images/sites")
async def get_sites(request):
    """Serve the danbooru_sites.json file"""
    if os.path.exists(SITES_FILE):
        try:
            with open(SITES_FILE, 'r', encoding='utf-8') as f:
                return web.json_response(json.load(f))
        except Exception as e:
            return web.json_response(
                {"error": str(e)},
                status=500
            )
    return web.json_response(
        {"error": "sites.json not found"},
        status=404
    )

@prompt_server.routes.get("/danbooru_images/favorites")
async def get_favorites_route(request):
    """Get all favorites"""
    return web.json_response(_load_favs())

@prompt_server.routes.post("/danbooru_images/favorites")
async def save_favorite_route(request):
    """Add/Remove favorite"""
    try:
        data = await request.json()
        item = data.get("item")
        action = data.get("action", "add")
        
        if not item or not item.get("id"):
             return web.json_response(
                 {"error": "Invalid item"},
                 status=400
             )
             
        favs = _load_favs()
        if not isinstance(favs, list):
            favs = []
        
        existing_idx = next(
            (i for i, x in enumerate(favs) if str(x.get("id")) == str(item.get("id"))),
            -1
        )
        
        if action == "add":
            if existing_idx == -1:
                favs.append(item)
                _save_favs(favs)
            return web.json_response({"status": "added", "count": len(favs)})
        elif action == "remove":
            if existing_idx != -1:
                favs.pop(existing_idx)
                _save_favs(favs)
            return web.json_response({"status": "removed", "count": len(favs)})
        return web.json_response({"error": "Unknown action"}, status=400)
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)

@prompt_server.routes.get("/danbooru_images/auth")
async def get_auth_route(request):
    auth = _load_auth()
    return web.json_response({"domains": list(auth.keys())})

@prompt_server.routes.post("/danbooru_images/auth")
async def set_auth_route(request):
    try:
        data = await request.json()
        domain = data.get("domain")
        user = data.get("username")
        key = data.get("api_key")
        if not domain:
            return web.json_response({"error": "Missing domain"}, status=400)
        auth = _load_auth()
        if user and key:
            auth[domain] = {"username": user, "api_key": key}
        else:
            if domain in auth:
                del auth[domain]
        _save_auth(auth)
        return web.json_response({"status": "ok"})
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)

NODE_CLASS_MAPPINGS = {
    "DanbooruImageBrowser": DanbooruImageBrowserNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "DanbooruImageBrowser": "Danbooru"
}
