# VAE Decode Plus Plus for ComfyUI

A simple but powerful utility node for ComfyUI 
(based on VAE Decode Switch, but now with more options, ok 1 more...so far)

It allows you to switch between the standard `VAE Decode` and the `VAE Decode (Tiled)` nodes without rewiring your workflow, and use UltraVAE but fix the pixel shift.

This node is designed to keep your graphs clean and make A/B testing different decoding methods quick and easy.

---

## Features

* **Adds "Down and to the Right" shift:** UltraVAE has a noticable 1 pixel shift 'up and to the left' so this fixes that, bringing it into alignment with other VAEs.
* **Seamless Switching:** A simple dropdown menu lets you select either the "default" or "tiled" VAE decoder on the fly.
* **Dynamic UI:** The node's interface is dynamic. When "default" is selected, the extra settings for the tiled decoder (like `tile_size`, `overlap`, etc.) are completely hidden, keeping the node compact and clean.
* **Clean Workflows:** Avoid messy rerouting nodes or having to manually disconnect and reconnect pipelines when you want to try a different decoder.
* **Preserves Inputs:** All standard inputs (`samples`, `vae`) are maintained, and the node correctly passes the required parameters to the selected decoder.


## Usage

1. Connect your `samples` (LATENT) and `vae` (VAE) inputs as you would with a standard decoder.
2. Use the `select_decoder` dropdown to choose your desired method.
   * **default:** Uses the standard `VAEDecode`. The node will shrink to hide the other settings.
   * **tiled:** Uses the `VAEDecodeTiled`. The node will expand to show the tiled-specific settings.
3. * If needed, turn on the pixel shift (mostly when using UltraVAE)
