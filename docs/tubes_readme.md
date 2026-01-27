# The Tube System 🧪 

Tubes are the "Scromfy Way" of avoiding noodle soup. They are a dictionary-based data passing system that allows you to bundle all your generation parameters—images, models, prompts, masks, latents—into a single connection line.

## Core Philosophy

Instead of wiring 20 different lines across your workflow (Model -> Sampler, VAE -> Decode, Positive -> Sampler, etc.), you wire a single **TUBE**. 

- **Tube In**: Collects loose parameters into a Tube.
- **Tube Out**: Extracts parameters from a Tube back into standard ComfyUI types.
- **Tube Merge**: Combines two Tubes, allowing you to layer settings (e.g., a "Style" tube merging into a "Content" tube).

## Available Nodes

### Core Nodes

#### Tube In
The starting point. Takes standard ComfyUI inputs (positive, negative, image, latent, etc.) and bundles them into a `TUBE`.
- **Inputs**: `tube_in` (optional input tube to modify), plus all standard fields (positive, negative, image, mask, latent, model, vae, clip, prompt, seed, steps, cfg, etc.).
- **Logic**: Only non-null/non-default inputs are added. If you provide a `tube_in`, it copies that tube and overrides only the fields you connected.

#### Tube Out
The ending point. Takes a `TUBE` and outputs all standard ComfyUI types.
- **Outputs**: All standard fields + the original `tube` (passthrough).
- **Usage**: Connect this to your nontube supporting KSampler, VAE Decode, and/or Save Image nodes.

#### Tube Save Images
A powerful "Save Image" replacement that reads metadata directly from the Tube.
- **Features**:
    - Saves standard ComfyUI PNG metadata (**Process, Version, Hashes**).
    - Includes **Civitai-compatible metadata** (making your generations auto-detectable by Civitai).
    - Embeds the entire workflow (optional).
    - Can save `json` generation data (`.txt` sidecar).
- **Inputs**: `images`, `tube` (for metadata), `output_path`, `filename_prefix`, `extension` (png/jpg/webp).

### Manipulation & Logic

#### Tube Merge
Combines two Tubes (`tube_a` and `tube_b`).
- **Strategy**:
    - `override`: Values in B overwrite A.
    - `only if empty/none`: B only fills missing values in A.
    - `combine`: Lists are concatenated; single values become lists.

#### Tube Set Value / Tube Get Value
- **Set Value**: Manually inject a specific key/value pair into a Tube.
- **Get Value**: Extract a single specific key from a Tube (returns `*` wildcard type).

#### Tube Set JSON / Tube Get JSON
- **Set JSON**: Inject multiple values using a JSON string.
- **Get JSON**: Extract multiple keys at once, returned as a JSON dictionary.

#### Tube Modify String
Append prefixes or suffixes to a string field (usually `prompt`) within a Tube.
- **Usage**: Great for adding LoRA triggers or quality tags to a prompt passing through the tube.
- **Delimiters**: Custom delimiter support (default `, `).

#### Tube Rename Key
Moves a value from `old_key` to `new_key` (e.g., rename `prompt` to `user_input` for storage).

### Utilities & Inspection

#### Tube Inspector
Debugging tool. Connect a Tube to see its contents in a text box.
- **Outputs**: Formatted text summary, JSON string, and raw JSON object.

#### Tube Filter
Whitelist or Blacklist keys to clean up a Tube before passing it on.
- **Usage**: Remove massive images or latents before saving a preset to disk.

#### Tube Prune
Removes all keys with `None`, empty string, or empty list values. Keeps the Tube clean.

#### Tube Diff
Compares `tube_a` and `tube_b`. Returns a new Tube containing only the items that are different or new in B.

#### Tube Contains
Returns a boolean `True` if a specific key exists in the Tube.

### File I/O

#### Tube to File
Saves the entire Tube dictionary to a `.json` file on disk.

#### File to Tube
Loads a `.json` file from disk and outputs it as a **TUBE**.
- **Power User Tip**: Use this to load "Presets" or "Styles" stored as JSON files.
