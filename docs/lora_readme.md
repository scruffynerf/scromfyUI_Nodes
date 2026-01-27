# LoRA Utility Nodes 🧬

Advanced tools for managing and loading LoRAs via dynamic lists and prompt parsing.

## Nodes

### LoRA List (Dynamic)
Lists all installed LoRAs with powerful regex-based filtering.
- **Dynamic Syntax**: Generates `<lora:name:1.0>` syntax strings for every LoRA found.
- **Shortnames**: Extracts clean filenames without paths/extensions for easy reading.
- **1by1 Outputs**: Provides outputs for both batch processing and individual use.

### Extract LoRAs from Prompt
Parses `<lora:name:strength>` or `<lora:name:strength_m:strength_c>` tags directly from a prompt string.
- **Automatic Loading**: Automatically finds the best match in your LoRA folder and loads it.
- **Prompt Cleaning**: Returns a "clean" version of your prompt with all LoRA tags removed, ready for the CLIP text encoder.
- **Supports Triple Syntax**: Supports standard, double-colon weight splitting, and simplified tags.
