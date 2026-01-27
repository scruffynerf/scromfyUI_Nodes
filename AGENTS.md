# AGENTS.md

This document serves as the "Source of Truth" for AI agents and humans contributing to this repository. It defines the architectural standards and the "Scromfy Way" of building ComfyUI nodes.

## Repository Structure

- `/py`: All Python node code. Each file should represent a single node or a small, related set of nodes.
  - *Support Logic*: Complex logic or dependencies that aren't nodes themselves should live in subdirectories within `/py` (e.g., `/py/utils/` or `/py/logic/`) to prevent the dynamic loader from attempting to register them as nodes.
- `/js`: Frontend extensions for ComfyUI.
- `/docs`: Detailed documentation for specific nodes or systems. Every new node package should include a dedicated `readme.md` here.
- `/favorites`: User favorites JSON files (gitignored).
- `/auth`: User credentials and auth tokens (gitignored).
- `/sites`: Site configuration files (e.g., `danbooru_sites.json`).
- `__init__.py`: Dynamic loader that scans `/py` and collects mappings.

## Principle for Documentation

1. **Node Readmes**: Each set of nodes MUST have a descriptive `readme.md` in the `/docs` directory. This applies to newly created nodes and migrated legacy components.
2. **Central Linking**: The main root `README.md` must be updated to link to these specific node documentations, optionally including a brief summary of the node's purpose.

## Principles for Node Development

- **Safety and Functional Parity**: NEVER remove existing functionality, logic, parameters, or edge-case handlers during a migration or refactor without discussing it first and getting explicit approval. Maintaining factual correctness and functional integrity is the highest priority.
- **Zero-Truncation Migration Protocol**:
    - Perform a side-by-side logical audit of the original file vs. the new file.
    - Account for every helper function, conditional branch, and error handler from the source.
    - "Skipping for skeleton" or "Simplified for migration" is strictly PROHIBITED.
- **Never Truncate Data**: DO NOT truncate lists, presets, or metadata for "brevity" in code files. Large lists of resolutions, settings, or mappings are functional code and must be preserved or expanded.
- **No Vertical Compression**: DO NOT compress lists, dictionaries, or multi-line code into a single line or horizontally dense format for "brevity". Use long, readable, vertically expanded lists (one item per line) for clarity and easier review.
- **Isolation**: Do NOT create a monolithic `nodes.py`. Keep nodes in separate files within `/py`.
2. **Local Mappings**: Define `NODE_CLASS_MAPPINGS` and `NODE_DISPLAY_NAME_MAPPINGS` within the `.py` file they belong to. The global `__init__.py` will find and merge them.
3. **Universal Nodes**: Design nodes to be model-agnostic and input-resilient. Avoid "SD15-only" or "XL-only" nodes when a single node can handle both.
4. **Dictionary-based Data (The Scromfy Way)**:
   - Prefer passing data via Python dictionaries using named keys over rigid "Pipes" or "Buses".
   - This allows for extensible data packets without breaking existing connections.
5. **Licensing**: MIT is the primary license for this repository. New code should be MIT licensed and specify so in the file. Existing code migrated into this framework MUST retain its original license, and that license file MUST be saved in the `LICENSES/` directory and referenced in the source files.

## Dynamic Loading Mechanism

The root `__init__.py` automatically imports every `.py` file in the `/py` directory. It then looks for the following constants in each module:
- `NODE_CLASS_MAPPINGS`
- `NODE_DISPLAY_NAME_MAPPINGS`

If found, they are merged into the master mappings exported to ComfyUI.

## Adding a New Node

1. Create a new file in `/py/my_new_node.py`.
2. Implement your node class.
3. Define the local mappings:
   ```python
   NODE_CLASS_MAPPINGS = { "MyNewNode": MyNewNode }
   NODE_DISPLAY_NAME_MAPPINGS = { "MyNewNode": "My New Node 🚀" }
   ```
4. The loader will handle the rest.
