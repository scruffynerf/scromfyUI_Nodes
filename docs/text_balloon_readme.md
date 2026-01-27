# Text Balloon Node 🗨️🎨

Stylized SVG-based speech balloons and word-art generators for comic book effects.

## Node COMING SOON - Under reconstruction

### Speech Balloon
Generates a vector-sharp speech balloon with highly customizable shapes and tails.
- **Dynamic Tails**: Move the tail to any angle (0-360) and adjust its size/curve.
- **Diamond Text**: Includes specialized text wrapping logic (`split_text_diamond`) to ensure text fits perfectly inside oval and cloud shapes.
- **Balloon Types**: `round`, `rectangle`, `cloud`, `spiky`, `wavy`.
- **Styling**: Complete control over font colors, background colors, and stroke hex values.

## Fonts
The node looks for TrueType fonts in the modules' root `/fonts` directory. 
**Note**: Only `comic.ttf` and `Roboto-Regular.ttf` are included by default.