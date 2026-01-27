"""
Civitai Base Models List - Shared list for accurate searching and filtering.
"""

# exhaustive list from Civitai interface (Jan 2026)
CIVITAI_BASE_MODELS = [
    "Any",
    "Aura Flow",
    "Chroma",
    "CogVideoX",
    "Flux.1 D",
    "Flux.1 Kontext",
    "Flux.1 Krea",
    "Flux.1 S",
    "Flux.2 D",
    "Flux.2 Klein 9B-base",
    "Flux.2 Klein 9B",
    "Flux.2 Klein 4B-base",
    "Flux.2 Klein 4B",
    "HiDream",
    "Hunyuan 1",
    "Hunyuan Video",
    "Illustrious",
    "Imagen 4",
    "Kolors",
    "LTXV",
    "LTXV2",
    "Lumina",
    "Mochi",
    "Nano Banana",
    "NoobAI",
    "Open AI",
    "Other",
    "PixArt Σ",
    "Playground v2",
    "Pony",
    "Pony V7",
    "Qwen",
    "SD 1.4",
    "SD 1.5",
    "SD 1.5 Hyper",
    "SD 1.5 LCM",
    "SD 2.0",
    "SD 2.0 768",
    "SD 2.1",
    "SD 2.1 768",
    "SD 3",
    "SD 3.5",
    "SD 3.5 Large",
    "SD 3.5 Large Turbo",
    "SD 3.5 Medium",
    "SDXL 0.9",
    "SDXL 1.0",
    "SDXL 1.0 LCM",
    "SDXL Distilled",
    "SDXL Hyper",
    "SDXL Lightning",
    "SDXL Turbo",
    "SVD",
    "SVD XT",
    "Seedream",
    "Sora 2",
    "Stable Cascade",
    "Veo 3",
    "WAN Video",
    "Wan Video 1.3B t2v",
    "Wan Video 14B i2v 480p",
    "Wan Video 14B i2v 720p",
    "Wan Video 14B t2v",
    "Wan Video 2.2 I2V-A14B",
    "Wan Video 2.2 T2V-A14B",
    "Wan Video 2.2 TI2V-5B",
    "Wan Video 2.5 I2V",
    "Wan Video 2.5 T2V",
    "ZImageTurbo",
]

def get_base_model(model_name: str) -> str:
    """Guess base model from name/hashes for internal filtering."""
    lower = model_name.lower()
    if any(x in lower for x in ["xl", "sdxl"]): return "SDXL"
    if any(x in lower for x in ["sd15", "v1.5"]): return "SD1.5"
    if "pony" in lower: return "Pony"
    if "flux" in lower: return "Flux.1 D"
    if "3.5" in lower: return "SD 3.5"
    return "Any"
