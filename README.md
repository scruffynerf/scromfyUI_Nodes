# scromfyUI_Nodes

A collection of custom nodes for [ComfyUI](https://github.com/comfy-org/ComfyUI) designed with a focus on flexibility, modularity, and clean workflow management.

## Core Principles

### 1. Universal Nodes (One Node to rule them all)
I believe in **Universal Nodes** whenever possible and feasible.
- **One Node to rule them all**: You shouldn't have to switch out a key node just because you change a model type or input format.  I hate rebuilding a good workflow just so I can use a different thing in one place, but it cascades into a half dozen changes.
- **Flexibility**: Workflows should be adaptable and resilient to changes in the underlying stack.

### 2. Forking Innovation (We stand on the shoulders of giants)
This repository serves as a hub for both original ideas and refined forks.
- **Standing on Shoulders**: I often copy and fork other people's code.
- **New Directions**: Sometimes I contribute back to the original source; other times, I take the code in a completely new direction. This is where those "new direction" nodes live.
- **License**: All of my own code is released under the MIT license.  Not all of the code here originates with me, so some of the code might be covered under other licenses.  Please check the individual node files for license information and attribution.

### 3. Clean Data Management (The Scromfy Way)
Moving beyond the limitations of traditional ComfyUI data passing.
- **Beyond Spaghetti**: While Comfy Set/Get nodes can help reduce wire clutter, they can quickly lead to a different kind of mess - piles of set/gets all over the place, and then people tuck them away for a cleaner looking workflow.  This is still a mess.
- **Better than leaky pipes or squeaky buses**: Existing "Bus" or "Pipe" implementations often fall short, or limit you in too many ways.
- **Dictionary-based Flow**: This project builds toward a better method: using **named items in a Python dictionary**. This keeps data organized with just one 'noodle', making it more accessible (dict, json, etc.), and the workflow that much cleaner.  It's all just a "series of tubes," man... like the Internet. Or Futurama.  In light of needing to come up with another name to avoid confusion, I went with the name "Tubes".  Cause I'm old.. (cough) school, and I remember the September that never ended.

### 4. Nodes 1.0 

While I respect the intent of the Nodes 2.0 + Comfy API v3 stuff, it's raw and broken, lots of better devs than me have found it impossible to do things they do now.  So I'm sticking with the tried and true for now.  If ports or upgrades happen, that'll be a new repo.  Consider this stuff Nodes 1.0 centric.

## Available Nodes

See the individual readme files for more details.
 
- **[ClipChat](docs/clipchat_readme.md)**: Generate both creative text and high-quality conditioning using Qwen3 models for ZImage + Flux Klein.
- **[Model Utilities](docs/model_code_readme.md)**: Architecture detection, universal latent initialization, and intelligent sampling shifts.
- **[LoRA Utilities](docs/lora_readme.md)**: Dynamic LoRA listing and prompt-based <lora:...> parsing.
- **[Tubes](docs/tubes_readme.md)**: The core of the Scromfy Way. A dictionary-based (pythonic) data management system.  It's all just a "series of tubes".
- **[Image Browsers](docs/image_browsers_readme.md)**: Interactive galleries for Civitai, Danbooru, and more.
- **[VAE Decode PLUSPLUS](docs/vae_decode_plusplus_readme.md)**: Switch between standard and tiled VAE decoding, fix UltraVAE shift
- **[Image & Mask](docs/image_mask_readme.md)**: Geometric analysis (Largest Interior Rect) and grid splitting.
- **[Logic & Utils](docs/logic_misc_readme.md)**: Integer-to-bit conversion and UUID generation.
- **[Utility Nodes](docs/text_json_utils_readme.md)**: Flexible string list combining and JSON manipulation.
- **[Moiré Nodes](docs/moire_nodes_readme.md)**: Tools for generating complex patterns and distortions.
- **[Prompt Suite](docs/prompt_node.md)**: Structured prompt management and selection from JSON suites.

## Thanks and Kudos

- [ComfyUI](https://github.com/comfy-org/ComfyUI)
- [Banodoco](https://banodoco.ai) discord and all of the good folks there, especially Kijai.
