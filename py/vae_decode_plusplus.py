# VAE Decode PLUSPLUS
# Original code licensed under GNU GPL v3.
# License available at LICENSES/LICENSE_GPLv3

try:
    import torch
except ImportError:
    print("[Warning] VAE Decode PlusPlus: PyTorch is not installed. Error handling will be limited.")
    torch = None

from nodes import VAEDecode, VAEDecodeTiled

class VAEDecodePlusPlus:
    """
    A custom node that allows switching between the standard VAE decoder
    and the tiled VAE decoder without changing workflow connections.
    """

    @classmethod
    def INPUT_TYPES(s):
        """
        Defines all possible input types for the node.
        The frontend will hide/show them as needed.
        """
        return {
            "required": {
                "samples": ("LATENT",),
                "vae": ("VAE",),
                "select_decoder": (["default", "tiled"],),
                "pixel_shift_down_right": ("BOOLEAN", {"default": False}),
            },
            "optional": {
                "tile_size": ("INT", {"default": 512, "min": 64, "max": 4096, "step": 64}),
                "overlap": ("INT", {"default": 64, "min": 0, "max": 4096, "step": 8}),
                "temporal_size": ("INT", {"default": 64, "min": 1, "max": 4096, "step": 1}),
                "temporal_overlap": ("INT", {"default": 8, "min": 0, "max": 4096, "step": 1}),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "switch_and_decode"
    CATEGORY = "Scromfy/VAE"

    def switch_and_decode(self, samples, vae, select_decoder, pixel_shift_down_right=False, **kwargs):
        # TODO: Add support for more decoder types (e.g., UltraVAE specific optimizations).
        print("\n--- VAE Decode PLUSPLUS ---")
        print(f"Selected Decoder: {select_decoder}")
        
        result = None
        if select_decoder == "tiled":
            print("Executing Tiled VAE Decode.")
            tiled_decoder = VAEDecodeTiled()
            try:
                result = tiled_decoder.decode(
                    vae, 
                    samples, 
                    tile_size=kwargs.get('tile_size', 512),
                    overlap=kwargs.get('overlap', 64),
                    temporal_size=kwargs.get('temporal_size', 64),
                    temporal_overlap=kwargs.get('temporal_overlap', 8)
                )
                print("Tiled decoding successful.")
            except TypeError as e:
                print(f"\n[ERROR] VAE Decode PLUSPLUS: 'tiled' decoder failed: {e}\n")
                if torch:
                    # Return a blank tensor if torch is available, otherwise re-raise
                    # Note: We return early here, ignoring pixel shift if decoding failed
                    return (torch.zeros(1, 64, 64, 3, dtype=torch.float32, device="cpu"), )
                else:
                    raise e
        else:
            print("Executing Default VAE Decode.")
            default_decoder = VAEDecode()
            result = default_decoder.decode(vae, samples)
            print("Default decoding successful.")

        if result is None:
             # Should practically not happen unless we hit the exception block above
             return (torch.zeros(1, 64, 64, 3, dtype=torch.float32, device="cpu"), )

        # --- Pixel Shift Logic ---
        if pixel_shift_down_right:
            print("Applying 1-pixel shift (Down-Right).")
            # result is a tuple (image_tensor, )
            img_tensor = result[0]
            
            # Ensure we are working with torch tensor
            if hasattr(img_tensor, "clone"):
                shifted = torch.zeros_like(img_tensor)
                # Shift: move pixels at [:-1, :-1] to [1:, 1:]
                # Assuming BHWC format (Batch, Height, Width, Channels)
                shifted[:, 1:, 1:, :] = img_tensor[:, :-1, :-1, :] 
                return (shifted, )
            else:
                print("[Warning] Result is not a torch tensor, skipping pixel shift.")
                return result
        
        return result

NODE_CLASS_MAPPINGS = {
    "VAEDecodePlusPlus": VAEDecodePlusPlus
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "VAEDecodePlusPlus": "VAE Decode PLUSPLUS"
}
