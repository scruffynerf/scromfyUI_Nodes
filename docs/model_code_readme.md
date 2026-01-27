# Model Utility Nodes 🔍📐⚡

A suite for model detection, latent generation, and noise schedule optimization.

## Nodes

### Detect Model Type
Analyzes the `MODEL` and returns a standardized architecture string.
- **Output Names**: Returns specific IDs like `FLUX.1`, `SD3`, `WAN2.1`, `WAN2.2`, `HYVid1.5`, etc.
- **Interoperability**: Designed to plug directly into the `latent_type` or `model_override` inputs of other nodes.

### Universal Empty Latent
The definitive empty latent generator. Restored to full functional parity with support for specialized sizing constraints and 20+ model families.
- **Sizing & Ratios**:
    - **Presets**: Dozens of high-res aspect ratios.
    - **Ratio Finding**: Use `ratio_x`/`ratio_y` or `altratio_xy` to find the largest fitting dimensions.
    - **Constraints**: Set `min_width/height` and `max_width/height` to keep generations within hardware limits.
    - **Precision**: `pixels_64` toggle for mod-64 alignment (required by some DiT models).
- **Architecture Support**:
    - Includes accurate channel counts (3 to 128) and noise constants (`0.1159` for Flux, `0.0609` for SD3).
    - Supports everything from SD1.5/XL to Wan 2.x, Hunyuan Video, Cosmos, Mochi, and LTXV.

### Model Shift (AutoCalc)
Optimizes the sampling shift for Diffusion Transformers (DiT).
- **Intelligence**: Automatically recognizes the native base shift for the detected model (e.g., Wan=8.0, HYVid=7.0, Flux.1=1.15).
- **Resolution Scaling**: Scale-aware heuristic that adjusts the shift logarithmicly as you move away from the model's base training resolution (1024p).

---

## Supported Architectures

| ID | Channels | Base Shift | Constant |
|----|----------|------------|----------|
| **Flux.1** | 16 | 1.15 | 0.1159 |
| **SD3** | 16 | 3.0 | 0.0609 |
| **Wan 2.1** | 16 | 8.0 | 0.0 |
| **Wan 2.2** | 48 | 8.0 | 0.0 |
| **HYVideo** | 16 | 7.0 | 0.0 |
| **LTXV** | 128 | 2.37 | 0.0 |
| **Mochi** | 12 | 6.0 | 0.0 |
| **ZImage** | 16 | 3.0 | 0.0 |
| **Cosmos** | 16 | 1.0 | 0.0 |
