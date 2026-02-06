import os
import random
import re
import glob

class WildcardProcessor:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text": ("STRING", {"multiline": True, "default": ""}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff}),
            }
        }

    RETURN_TYPES = ("STRING",)
    FUNCTION = "process"
    CATEGORY = "Scromfy/Text"

    def process(self, text, seed):
        # Initialize internal PRNG with the provided seed
        rng = random.Random(seed)
        
        # Path to wildcards directory
        base_path = os.path.dirname(__file__)
        wildcards_dir = os.path.join(base_path, "..", "wildcards")
        
        # Regex for both [Wildcard] and {wildcard}
        # It matches anything inside [] or {} that doesn't contain the closing bracket
        pattern = re.compile(r'\[([^\]]+)\]|\{([^\}]+)\}')
        
        # Track recursion to avoid infinite loops
        max_depth = 10
        current_text = text
        
        # Cache for wildcard files to avoid many reads
        cache = {}

        def get_wildcard_lines(name):
            name = name.lower().strip()
            if name in cache:
                return cache[name]
            
            # Look for name.txt in the wildcards directory
            file_path = os.path.join(wildcards_dir, f"{name}.txt")
            if os.path.exists(file_path):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        lines = [line.strip() for line in f if line.strip() and not line.startswith("#")]
                        cache[name] = lines
                        return lines
                except Exception as e:
                    print(f"[Scromfy] Error reading wildcard file {name}.txt: {e}")
            
            return None

        # Recursive replacement
        # We loop until no more patterns are found or we hit max_depth
        for _ in range(max_depth):
            matches = list(pattern.finditer(current_text))
            if not matches:
                break
            
            # Process from end to start to maintain indices
            for match in reversed(matches):
                wc_name = match.group(1) or match.group(2)
                lines = get_wildcard_lines(wc_name)
                
                if lines:
                    replacement = rng.choice(lines)
                    start, end = match.span()
                    current_text = current_text[:start] + replacement + current_text[end:]
                else:
                    pass
        
        return (current_text,)

NODE_CLASS_MAPPINGS = {
    "WildcardProcessor": WildcardProcessor,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "WildcardProcessor": "🃏 Wildcard Processor (Scromfy)",
}
