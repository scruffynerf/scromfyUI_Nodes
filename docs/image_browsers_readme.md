# Image Browsers 🖼️

A collection of interactive browsers for popular image sharing platforms, integrated directly into your ComfyUI workflow via the **Tubes** system.

## Features

- **Infinite Scroll**: Browse thousands of images without leaving ComfyUI.
- **Metadata Extraction**: Click an image to automatically fill your `TUBE` with the original prompts, seeds, samplers, and model names.
- **Favorites**: Save your favorite discoveries locally.
- **Download Check**: Optionally skip downloading the image if you only want the metadata.

## Common Usage Notes

### `download_image` Boolean
This input controls whether the actual image pixel data is fetched.
- **True (default)**: The image is downloaded **to memory** and returned as a standard ComfyUI `IMAGE` tensor.
- **False**: Returns an empty black tensor. This is useful for saving bandwidth if you only want to extract the metadata (prompts, seeds, etc.) without transferring the large image file.

*Note: This download happens entirely in memory. It does **not** save the file to any folder on your disk.*

### Outputs
All browsers provide standardized outputs:
- **IMAGE**: The image tensor (or empty if download is disabled).
- **TUBE**: A Scromfy Tube containing all extracted metadata (params, models, LoRAs, etc.).
- **positive / negative**: The prompt strings.
- **filename**: A bare filename string (e.g., `civitai_12345` or `danbooru_9876`).
    - Contains **NO path** and **NO extension**.
    - Intended to be used as a filename prefix if you feed this into a "Save Image" node.
- **info / raw_json**: Raw metadata for debugging or custom parsing.

## Available Browsers

### Civitai Browser
Browse the massive Civitai gallery. Supports filtering by NSFW level, sorting, and base model (SD 1.5, SDXL, etc.).

### CivSearch Browser
A specialized search interface for Civitai images.

### Danbooru Browser
The ultimate tool for anime and stylized reference browsing. If you find another site that works (you can add sites into the `/sites/danbooru_sites.json` config), let me know!

### Genur.art Browser
Explore high-quality generations from the Genur.art platform. Similar to Civitai. Used as backup for Civarchive.com's image sourcing.
