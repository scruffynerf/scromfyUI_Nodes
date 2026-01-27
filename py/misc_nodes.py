"""
Miscellaneous Utility Nodes - UUID generation.
"""

import uuid
import shortuuid

class ComfyUUID:
    """Generates a standard UUID and a compact shortuuid."""
    @classmethod
    def INPUT_TYPES(cls): return {"required": {}}

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("uuid", "shortuuid")
    FUNCTION = "execute"
    CATEGORY = "Scromfy/Misc"

    def execute(self):
        new_uuid = uuid.uuid4()
        return (str(new_uuid), shortuuid.encode(new_uuid))
    
    @classmethod
    def IS_CHANGED(cls):
        # always update
        return float("nan")

NODE_CLASS_MAPPINGS = {"ComfyUUID": ComfyUUID}
NODE_DISPLAY_NAME_MAPPINGS = {"ComfyUUID": "Generate UUID"}
