# Scromfy Prompt Suite Loader

The `PromptSuiteLoader` is a powerful, consolidated node for managing, filtering, and selecting prompts from multiple sources within the `prompts/` directory.

## Core Features

- **Dynamic Tag Discovery**: Automatically scans all `.json` and `.txt` files in the `prompts/` folder to build a dropdown of unique tags.
- **Flexible Filtering**:
    - Select a specific tag from a dropdown.
    - Or use a manual freeform field for multiple tags.
    - Choose between **AND** (all tags must match) or **OR** (at least one tag must match) logic.
- **Intelligent Selection**:
    - Provide a specific index to select a prompt.
    - Use index **-1** for a random selection on every execution.
- **Consolidated Outputs**: A single node now provides the selected prompt, the filtered list, and loading statistics.

## Inputs

*   **file_filter**: Load from a specific file or "all" files in the directory.
*   **tag_selection**: 
    - `all`: No tag filtering.
    - `manual`: Use the `tags_manual` text field.
    - `(tag name)`: Quickly filter by a specific discovered tag.
*   **tags_manual**: A comma-separated list of tags (used only if `tag_selection` is `manual`).
*   **tag_logic**: Switch between `AND` and `OR` for filtering when multiple tags are involved.
*   **index**: The index of the prompt to select. **-1** triggers random selection.
*   **prefix / suffix**: Text to wrap around the selected prompt(s).

## Outputs

*   **prompt**: The single selected prompt string.
*   **prompt_list**: The full list of filtered prompts (as a Python list). Excellent for downstream list processing.
*   **all_prompts_str**: The full list of filtered prompts as a single newline-separated string. (Replaces the need for the legacy Iterator input).
*   **count**: Total number of prompts that matched the current filters.
*   **load_info**: Detailed text summary of which files were loaded and how many prompts each contributed. (Replaces the legacy Info node).

## File Formats

### Simplified JSON
```json
[
  {
    "tags": ["portrait", "cinematic"],
    "prompt": "portrait of a wizard, cinematic lighting"
  }
]
```

### Text Files
Create simple `.txt` files with one prompt per line. The tags are automatically derived from the filename:
- `scifi-interiors.txt` -> Tags: `scifi`, `interiors`

## Installation & Setup

Place your prompt files in the `prompts/` folder at the root of the custom node directory. The node will automatically detect new files and tags on restart or graph refresh.
