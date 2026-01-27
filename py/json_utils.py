"""
JSON Utility Nodes - Building, merging, and saving JSON data.
"""

import os
import json
from .support.constants import DEF_TRUEBOOL, ANY_
from .support.scromfy_utils import write_json_to_file

class AnyValuetoJSON:
    """Adds or updates a key-value pair in a JSON object."""
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {"key": ("STRING", {}), "value": (ANY_, {})},
            "optional": {"json_in": ("JSON", {})}
        }
    RETURN_TYPES = ("JSON",)
    FUNCTION = "execute"
    CATEGORY = "Scromfy/Text"

    def execute(self, key, value, json_in=None):
        res = json_in or {}
        res[key] = value
        return (res,)

class MergeMultipletoJSON:
    """Merges up to 5 JSON objects into one."""
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {"json_1": ("JSON", {})},
            "optional": {f"json_{i}": ("JSON", {}) for i in range(2, 6)}
        }
    RETURN_TYPES = ("JSON",)
    FUNCTION = "execute"
    CATEGORY = "Scromfy/Text"

    def execute(self, **kwargs):
        res = {}
        for i in range(1, 6): res.update(kwargs.get(f"json_{i}") or {})
        return (res,)

class SaveGridJson:
    """Saves a JSON object to a file for external tools or grids."""
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "file_path": ("STRING", {"default": "output/grid.json"}),
                "json_data": ("JSON", {}),
                "immediate_gen": DEF_TRUEBOOL
            }
        }
    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("File Path", "JSON String")
    FUNCTION = "execute"
    CATEGORY = "Scromfy/Text"

    def execute(self, file_path, json_data, immediate_gen):
        write_json_to_file(json_data, file_path)
        return (file_path, json.dumps(json_data))

class LoadJsonFromFile:
    """Loads a JSON object from a specified file path."""
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "file_path": ("STRING", {"default": "output/grid.json"}),
            }
        }
    RETURN_TYPES = ("JSON", "STRING")
    RETURN_NAMES = ("json_data", "json_string")
    FUNCTION = "execute"
    CATEGORY = "Scromfy/Text"

    def execute(self, file_path):
        if not os.path.exists(file_path):
            return ({}, "{}")
        with open(file_path, 'r') as f:
            data = json.load(f)
        return (data, json.dumps(data))

NODE_CLASS_MAPPINGS = {
    "AnyValuetoJSON": AnyValuetoJSON,
    "MergeMultipletoJSON": MergeMultipletoJSON,
    "SaveGridJson": SaveGridJson,
    "LoadJsonFromFile": LoadJsonFromFile
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "AnyValuetoJSON": "Any to JSON",
    "MergeMultipletoJSON": "Merge JSON Objects",
    "SaveGridJson": "Save JSON to File",
    "LoadJsonFromFile": "Load JSON from File"
}
