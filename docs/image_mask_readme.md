# Image & Mask Nodes 🖼️🎭

Nodes for geometric image analysis, mask manipulation, and stylized framing.

## Nodes

### Largest Rect in Mask
Uses the `largestinteriorrectangle` algorithm to find the single largest axis-aligned rectangle that fits entirely within a binary mask.
- **Auto-BBOX**: Generates a standard bounding box output compatible with cropping and masking nodes.
- **Preview**: Optionally provides a preview image with the detected rectangle highlighted.

### Split Mask by Grid
Splits a single large mask into a grid (Rows x Columns) of smaller masks.
- **Batch Output**: Returns a batch of masks for processing in loops or multi-sampler setups.

### Add Border
Adds a simple, customizable border to any image.
- **Style Control**: Adjust color and size independently.
