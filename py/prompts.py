import json
import os
import glob
import random
from collections import Counter

class PromptSuiteLoader:
    """
    Prompt Suite Loader.
    Consolidates loading, filtering, and info display into a single node.
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        # Dynamically discover files and tags
        base_path = os.path.dirname(__file__)
        prompts_dir = os.path.join(base_path, "..", "prompts")
        
        file_list = ["all"]
        tag_counts = Counter()
        
        if os.path.exists(prompts_dir):
            files = glob.glob(os.path.join(prompts_dir, "*.json")) + glob.glob(os.path.join(prompts_dir, "*.txt"))
            file_list.extend([os.path.basename(f) for f in sorted(files)])
            
            # Scan files to get tags and counts for the dropdown
            for f_path in files:
                try:
                    if f_path.endswith(".json"):
                        with open(f_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            prompts = data if isinstance(data, list) else data.get("prompts", [])
                            for p in prompts:
                                # Use 'tags' if present, otherwise fallback to 'categories'
                                raw_tags = p.get("tags") or p.get("categories") or []
                                tags = [t.lower() for t in raw_tags]
                                tag_counts.update(tags)
                    elif f_path.endswith(".txt"):
                        # Filename tags apply to all lines in the file
                        # We should ideally scan the file to count how many prompts actually exist
                        f_tags = os.path.basename(f_path).replace(".txt", "").replace("_", "-").split("-")
                        try:
                            with open(f_path, 'r', encoding='utf-8') as f_text:
                                line_count = sum(1 for line in f_text if line.strip())
                                for t in f_tags:
                                    tag_counts[t.lower()] += line_count
                        except:
                            pass
                except:
                    pass

        # Sort tags by count (descending), then by name
        sorted_tags = sorted(tag_counts.items(), key=lambda x: (-x[1], x[0]))
        tag_dropdown = ["all", "manual"] + [f"{tag} ({count})" for tag, count in sorted_tags]

        return {
            "required": {
                "file_filter": (file_list, {
                    "default": "all",
                    "tooltip": "Specify a single file to load from, or 'all'"
                }),
                "tag_selection": (tag_dropdown, {
                    "default": "all",
                    "tooltip": "Select a specific tag to filter by, or 'manual' to use the field below."
                }),
                "tags_manual": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "tooltip": "Comma-separated tags. Used if tag_selection is set to 'manual'."
                }),
                "tag_logic": (["AND", "OR"], {
                    "default": "AND"
                }),
                "index": ("INT", {
                    "default": -1,
                    "min": -1,
                    "max": 9999,
                    "step": 1,
                    "tooltip": "Select prompt index. Use -1 for RANDOM selection."
                }),
                "seed": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 0xffffffffffffffff,
                    "tooltip": "Seed for random selection (used when index is -1)."
                }),
            },
            "optional": {
                "prefix": ("STRING", {"default": "", "multiline": False}),
                "suffix": ("STRING", {"default": "", "multiline": False}),
            }
        }
    
    RETURN_TYPES = ("STRING", "LIST", "STRING", "INT", "STRING")
    RETURN_NAMES = ("prompt", "prompt_list", "all_prompts_str", "count", "load_info")
    FUNCTION = "load_prompts"
    CATEGORY = "Scromfy/prompts"
    
    def load_prompts(self, file_filter, tag_selection, tags_manual, tag_logic, index, seed, prefix="", suffix=""):
        base_path = os.path.dirname(__file__)
        prompts_dir = os.path.join(base_path, "..", "prompts")
        
        all_loaded_prompts = []
        file_stats = {}
        
        if not os.path.exists(prompts_dir):
            return ("", [], "", 0, f"Error: Directory not found at {prompts_dir}")

        # 1. Determine files to load
        if file_filter == "all":
            files_to_load = glob.glob(os.path.join(prompts_dir, "*.json")) + glob.glob(os.path.join(prompts_dir, "*.txt"))
        else:
            files_to_load = [os.path.join(prompts_dir, file_filter)]

        # 2. Load data
        for file_path in files_to_load:
            if not os.path.exists(file_path): continue
            fname = os.path.basename(file_path)
            count_before = len(all_loaded_prompts)
            
            if file_path.endswith(".json"):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    prompts = data if isinstance(data, list) else data.get("prompts", [])
                    for p in prompts:
                        # Optimization: only store prompt and tags
                        raw_tags = p.get("tags") or p.get("categories") or []
                        all_loaded_prompts.append({
                            "tags": [t.lower() for t in raw_tags],
                            "prompt": p.get("prompt", "")
                        })
                except Exception as e:
                    print(f"[Scromfy] Error loading {fname}: {e}")
            elif file_path.endswith(".txt"):
                f_tags = fname.replace(".txt", "").replace("_", "-").split("-")
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        for line in f:
                            p_text = line.strip()
                            if p_text:
                                all_loaded_prompts.append({"tags": f_tags, "prompt": p_text})
                except Exception as e:
                    print(f"[Scromfy] Error loading {fname}: {e}")
            
            file_stats[fname] = len(all_loaded_prompts) - count_before

        # 3. Determine filtering tags
        if tag_selection == "manual":
            search_tags = [t.strip().lower() for t in tags_manual.split(",") if t.strip()]
        elif tag_selection == "all":
            search_tags = []
        else:
            # Parse "Tag Name (Count)" back to "tag name"
            search_tags = [tag_selection.rsplit(" (", 1)[0].lower()]

        # 4. Apply filter logic
        filtered = []
        for item in all_loaded_prompts:
            p_tags = [t.lower() for t in item.get("tags", [])]
            if not search_tags:
                filtered.append(item)
            else:
                if tag_logic == "AND":
                    if all(st in p_tags for st in search_tags):
                        filtered.append(item)
                else: # OR
                    if any(st in p_tags for st in search_tags):
                        filtered.append(item)

        total_count = len(filtered)
        if total_count == 0:
            return ("No prompts match filters", [], "", 0, "No matches found.")

        # 5. Formatting
        prefix_str = f"{prefix} " if prefix.strip() else ""
        suffix_str = f" {suffix}" if suffix.strip() else ""
        formatted_list = [f"{prefix_str}{p.get('prompt', '')}{suffix_str}".strip() for p in filtered]
        
        # 6. Selection
        if index == -1:
            # Use the provided seed for deterministic randomness
            prng = random.Random(seed)
            selected_idx = prng.randint(0, total_count - 1)
        else:
            selected_idx = index % total_count
            
        selected_prompt = formatted_list[selected_idx]
        
        # 7. Summary Info
        info_lines = [f"Loaded {len(file_stats)} files:"]
        for f, c in sorted(file_stats.items()):
            info_lines.append(f" - {f}: {c} prompts")
        info_lines.append(f"\nFiltered Total: {total_count}")
        if search_tags:
            info_lines.append(f"Filter: {' & '.join(search_tags) if tag_logic == 'AND' else ' | '.join(search_tags)}")
            
        return (
            selected_prompt, 
            formatted_list, 
            "\n".join(formatted_list), 
            total_count, 
            "\n".join(info_lines)
        )

NODE_CLASS_MAPPINGS = {
    "PromptSuiteLoader": PromptSuiteLoader,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PromptSuiteLoader": "📋 Prompt Suite Loader (Scromfy)",
}
