"""
Logic Nodes - Boolean and flow control utilities.
"""

class InttoBooleans:
    """Converts an integer (0-255) into 8 individual boolean outputs."""
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"number": ("INT", {"default": 0, "min": 0, "max": 255})}}

    RETURN_TYPES = ("BOOLEAN", "BOOLEAN", "BOOLEAN", "BOOLEAN", "BOOLEAN", "BOOLEAN", "BOOLEAN", "BOOLEAN")
    RETURN_NAMES = ("bit0", "bit1", "bit2", "bit3", "bit4", "bit5", "bit6", "bit7")
    FUNCTION = "execute"
    CATEGORY = "Scromfy/Logic"

    def execute(self, number: int):
        binary_str = f'{number:08b}'
        bools = [bool(int(bit)) for bit in binary_str][::-1] # Reverse to get bits 0-7
        return tuple(bools)

NODE_CLASS_MAPPINGS = {"InttoBooleans": InttoBooleans}
NODE_DISPLAY_NAME_MAPPINGS = {"InttoBooleans": "Int to 8-Bits"}
