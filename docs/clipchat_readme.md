# ClipChat (Qwen3) 🤖💬

ClipChat is a powerful text generation node that leverages Qwen models to generate both descriptive text and standard ComfyUI `CONDITIONING` (embeddings).

## Features

- **Text Generation**: Use Qwen3 (or other compatible models) to generate creative prompts, descriptions, or general text.
- **Visual-Language (VL) Support**: Optional VL mode for image-to-text workflows (requires compatible VL model).
- **Direct Conditioning**: Extracts hidden states from the text encoder portion of the model to create `CONDITIONING` that can be fed directly into KSamplers.
- **Clean Output**: Automatically filters out "thinking" blocks (`<think>...</think>`) and other special tokens to provide a clean string output for your workflow.
- **Layer Output**: Returns both the second-to-last and third-to-last hidden state layers for advanced workflow experimentation.

## Performance Principles

- **Cached Loading**: The model and tokenizer are cached in memory. Switching prompts is fast, though switching models will require a reload.


## Usage Tips

- **System Prompt**: Use the system prompt to guide the model's persona or formatting (e.g., "Always reply in bullet points").
- **Embedding Filter**: Automatically applies an attention mask filter to ensure your conditioning doesn't include unwanted padding noise.
