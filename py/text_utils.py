"""
Text Utility Nodes - String manipulation and combining.
"""

from .support.constants import DEF_STRING_ML, DEF_FALSEBOOL, DEF_TRUEBOOL, DEF_ANYINPUT

class FlexListString:
    """Combines up to 10 strings with optional delimiters."""
    @classmethod
    def INPUT_TYPES(cls):
        inputs = {"required": {}, "optional": {"delimiter": DEF_STRING_ML, "separate_lines": DEF_TRUEBOOL}}
        for i in range(1, 11):
            inputs["optional"][f"string_{i}"] = DEF_STRING_ML
            inputs["optional"][f"enable_{i}"] = DEF_FALSEBOOL
        return inputs

    RETURN_TYPES = ("STRING", "LIST", "LIST")
    RETURN_NAMES = ("TextBlock", "TextBlock IN LIST", "LIST OF STRINGS")
    OUTPUT_IS_LIST = (False, True, True)
    FUNCTION = "execute"
    CATEGORY = "Scromfy/Text"

    def execute(self, delimiter="", separate_lines=False, **kwargs):
        res = [kwargs.get(f"string_{i}") for i in range(1, 11) if kwargs.get(f"enable_{i}") and kwargs.get(f"string_{i}")]
        out = ('\n' if separate_lines else delimiter).join(res)
        return (out, [out], res)

class FirstStringWins:
    """Returns the first non-empty string from a list of inputs."""
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {"fallback": DEF_STRING_ML},
            "optional": {"prefix": DEF_STRING_ML, "suffix": DEF_STRING_ML, "try_1": DEF_ANYINPUT, "try_2": DEF_ANYINPUT}
        }
    RETURN_TYPES = ("STRING",)
    FUNCTION = "execute"
    CATEGORY = "Scromfy/Text"

    def execute(self, fallback, prefix="", suffix="", **kwargs):
        for k in ["try_1", "try_2"]:
            val = str(kwargs.get(k)) if kwargs.get(k) is not None else ""
            if val.strip(): return (prefix + val + suffix,)
        return (fallback,)

class MultilinesToList:
    """Splits multi-line text into a list of strings."""
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"text": DEF_STRING_ML}}
    RETURN_TYPES = ("STRING", "STRING", "INT")
    RETURN_NAMES = ("Strings 1by1", "Strings List", "Count")
    OUTPUT_IS_LIST = (True, False, False)
    FUNCTION = "execute"
    CATEGORY = "Scromfy/Text"

    def execute(self, text):
        lines = [l for l in text.splitlines() if l.strip()]
        return (lines, lines, len(lines))

NODE_CLASS_MAPPINGS = {
    "FlexListString": FlexListString,
    "FirstStringWins": FirstStringWins,
    "MultilinesToList": MultilinesToList
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "FlexListString": "Flexible String List",
    "FirstStringWins": "First String Wins (Selector)",
    "MultilinesToList": "Text Lines to List"
}
