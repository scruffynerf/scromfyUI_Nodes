from transformers import AutoModelForCausalLM, AutoTokenizer
from transformers import AutoProcessor
from transformers import TextStreamer
import torch
import re
import os
import json
import shutil

DEBUG = False  # Set to True for debug output

def filter_embeddings_by_mask(conditioning):
    """
    Filter padding tokens from embeddings using attention mask.
    Matches DiffSynth/diffusers reference implementation.
    """
    if not conditioning or len(conditioning) == 0:
        return conditioning

    filtered_conditioning = []
    
    for embeddings, extra_dict in conditioning:
        attention_mask = extra_dict.get("attention_mask")
        
        if attention_mask is None:
            filtered_conditioning.append((embeddings, extra_dict))
            continue
        
        mask_bool = attention_mask.bool()
        batch_size = embeddings.shape[0]
        
        filtered_embeds_list = []
        for b in range(batch_size):
            valid_mask = mask_bool[b] if mask_bool.dim() > 1 else mask_bool
            valid_embeds = embeddings[b][valid_mask]
            filtered_embeds_list.append(valid_embeds)
        
        if len(filtered_embeds_list) == 1:
            filtered_embeds = filtered_embeds_list[0].unsqueeze(0)
        else:
            max_len = max(e.shape[0] for e in filtered_embeds_list)
            padded = []
            for e in filtered_embeds_list:
                if e.shape[0] < max_len:
                    pad = torch.zeros(max_len - e.shape[0], e.shape[1], device=e.device, dtype=e.dtype)
                    padded.append(torch.cat([e, pad], dim=0))
                else:
                    padded.append(e)
            filtered_embeds = torch.stack(padded, dim=0)
        
        # Remove mask from dict since padding is gone
        new_extra = {k: v for k, v in extra_dict.items() if k != "attention_mask"}
        filtered_conditioning.append((filtered_embeds, new_extra))
    
    return filtered_conditioning

class ClipChat:
    """
    Generate text with Qwen and return both text content and conditioning.
    
    Args:
        model_name: Path to Qwen model
        max_tokens: Max tokens to generate
        prompt: User prompt
        system_prompt: Optional system prompt
    
    Returns:
        Tuple of (content_text, conditioning, formatted_prompt)
    """
    @classmethod
    def INPUT_TYPES(cls):
        # Path setup
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # scromfyUI_Nodes root
        user_config_dir = os.path.join(base_dir, "userconfig")
        user_config_path = os.path.join(user_config_dir, "user_clipchat_settings.json")
        default_config_path = os.path.join(base_dir, "py", "support", "default_clipchat_settings.json")
        
        # Ensure user config exists
        if not os.path.exists(user_config_path):
            try:
                os.makedirs(user_config_dir, exist_ok=True)
                if os.path.exists(default_config_path):
                    shutil.copy(default_config_path, user_config_path)
            except Exception as e:
                print(f"[ClipChat] Warning: Could not create user config: {e}")
        
        # Load models
        models = []
        if os.path.exists(user_config_path):
            try:
                with open(user_config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    models = config.get("models", [])
            except Exception as e:
                print(f"[ClipChat] Error loading user config: {e}")
        
        # Fallback if empty or failed
        if not models:
            models = ['Qwen/Qwen3-4B-Instruct-2507']
            
        return {
            "required": {
                "model_name": (models,),
                "prompt": ("STRING", {"default": "", "multiline": True}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff}),
            },
            "optional": {
                "system_prompt": ("STRING", {"default": "", "multiline": True}),
                "max_tokens": ("INT", {"default": 512, "min": 64, "max": 16384, "step": 64}),
                "temperature": ("FLOAT", {"default": 0.3, "min": 0.0, "max": 2.0, "step": 0.05}),
                "top_p": ("FLOAT", {"default": 0.85, "min": 0.0, "max": 1.0, "step": 0.05}),
                "top_k": ("INT", {"default": 30, "min": 0, "max": 100, "step": 1}),
                "repetition_penalty": ("FLOAT", {"default": 1.8, "min": 1.0, "max": 3.0, "step": 0.1}),
                "no_repeat_ngram_size": ("INT", {"default": 4, "min": 0, "max": 10, "step": 1}),
                "qwen3vl": ("BOOL", {"default": False}),
                "image": ("IMAGE", {}),

            },
        }
    RETURN_TYPES = ("STRING", "STRING", "CONDITIONING", "CONDITIONING")
    RETURN_NAMES = ("content", "formatted_prompt", "conditioning", "conditioning-layer-1", )
    FUNCTION = 'clipchat'
    CATEGORY = "Scromfy/ClipChat"
    
    # Class-level cache for model/tokenizer
    _cached_model = None
    _cached_tokenizer = None
    _cached_model_name = None
    
    def clipchat(self, model_name, prompt, seed, system_prompt=None, max_tokens=512, 
                   temperature=0.3, top_p=0.85, top_k=30, repetition_penalty=1.8, 
                   no_repeat_ngram_size=4, qwen3vl=False, image={}):
        # TODO: Move heavy transformers/torch imports inside the function or use a lazy loader to speed up ComfyUI startup.
        # TODO: Refactor VL vs text-only loading into a clean helper function.
    
      if DEBUG:
        print(f"\n[ClipChat] Starting generation...")
        prompt_preview = prompt[:100] + "..." if len(prompt) > 100 else prompt
        print(f"[ClipChat] Prompt: {prompt_preview}")
        print(f"[ClipChat] System prompt: {'Yes' if system_prompt else 'No'}")
        print(f"[ClipChat] Seed: {seed}")
        print(f"[ClipChat] Generation params: temp={temperature}, top_p={top_p}, top_k={top_k}, rep_pen={repetition_penalty}, ngram={no_repeat_ngram_size}, max_tokens={max_tokens}")
      
      # Check if we can reuse cached model
      if (ClipChat._cached_model is not None and 
          ClipChat._cached_model_name == model_name):
          tokenizer = ClipChat._cached_tokenizer
          processor = ClipChat._cached_processor
          model = ClipChat._cached_model
          if DEBUG:
              print(f"[ClipChat] Reusing cached model")
      else:
          if DEBUG:
              print(f"[ClipChat] Loading tokenizer from {model_name}...")
              print(f"[ClipChat] Loading model...")
          
           # --- VL mode loading ---
          if qwen3vl:
               tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True, use_safetensors=True)
               processor = AutoProcessor.from_pretrained(model_name, trust_remote_code=True, use_safetensors=True)
               model = AutoModelForCausalLM.from_pretrained(
                    model_name,
                    dtype="auto",
                    device_map="auto",
                    trust_remote_code=True,
                    use_safetensors=True
               )

               ClipChat._cached_tokenizer = tokenizer
               ClipChat._cached_model = model
               ClipChat._cached_processor = processor
               ClipChat._cached_model_name = model_name
          else:
               tokenizer = AutoTokenizer.from_pretrained(model_name,trust_remote_code=True,use_safetensors=True)
               model = AutoModelForCausalLM.from_pretrained(
                    model_name,
                    dtype="auto",
                    device_map="auto",
                    trust_remote_code=True,
                    use_safetensors=True
               )

               ClipChat._cached_tokenizer = tokenizer
               ClipChat._cached_model = model
               ClipChat._cached_processor = None
               ClipChat._cached_model_name = model_name 
          
      if DEBUG:
         print(f"[ClipChat] Model loaded on {model.device}")

      # Set seed for reproducibility
      torch.manual_seed(seed)
      if torch.cuda.is_available():
          torch.cuda.manual_seed_all(seed)

      # Build messages with system prompt in user message
      if system_prompt:
          user_content = f"<|im_start|>system\n{system_prompt}<|im_end|>\n<|im_start|>user\n{prompt}<|im_end|>"
      else:
          user_content = f"<|im_start|>user\n{prompt}<|im_end|>"
    
      messages = [{"role": "user", "content": user_content}]

      # Apply chat template - try to disable thinking mode
      try:
          text = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=False,  # Qwen3 thinking mode off
          )
      except TypeError:
          # Fallback if enable_thinking not supported
          text = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
          )
          
          
      # ==========================
      # VL vs text-only path
      # ==========================
      if qwen3vl:
          if image is None:
              raise ValueError("VL mode enabled but no image provided.")

          model_inputs = processor(
              text=text,
              images=[image],
              return_tensors="pt"
          ).to(model.device)
      else:
          model_inputs = tokenizer(
              [text],
              return_tensors="pt"
          ).to(model.device)
          
      if DEBUG:
         print(f"[ClipChat] Input tokens: {model_inputs.input_ids.shape[1]}")
         print(f"[ClipChat] Input text preview (first 300 chars):")
         print("-" * 40)
         print(text[:300])
         print("-" * 40)
         print(f"[ClipChat] Generating (max {max_tokens} tokens)...")
         print("-" * 40)
    
      # Create streamer for live output
      streamer = TextStreamer(tokenizer, skip_prompt=True, skip_special_tokens=True)
    
      # Generate with streaming
      # Note: Qwen3 may have "thinking" mode - we want just the response
      generated_ids = model.generate(
        **model_inputs,
        streamer=streamer,
        # Sampling strategy
        do_sample=True,
        temperature=temperature,
        top_p=top_p,
        top_k=top_k,

        # Repetition control
        repetition_penalty=repetition_penalty,
        no_repeat_ngram_size=no_repeat_ngram_size,

        # Length control
        min_new_tokens=1,
        max_new_tokens=max_tokens,

        # Stopping conditions
        eos_token_id=tokenizer.eos_token_id,
        pad_token_id=tokenizer.pad_token_id,

        # Misc
        use_cache=True,
      )
    
      if DEBUG:
         print("-" * 40)
         print(f"[ClipChat] Total output tokens: {generated_ids.shape[1]}")
         print(f"[ClipChat] Input tokens: {len(model_inputs.input_ids[0])}")
    
      # Extract only the generated portion (keep as tensor)
      output_ids = generated_ids[0][len(model_inputs.input_ids[0]):]

      if DEBUG:
         print(f"[ClipChat] Generated tokens (output - input): {output_ids.shape[0]}")
    
      # Decode to text - first with special tokens to see structure
      content_with_special = tokenizer.decode(output_ids, skip_special_tokens=False)
      content = tokenizer.decode(output_ids, skip_special_tokens=True)
    
      if DEBUG:
         print(f"[ClipChat] Raw content WITH special tokens (first 500 chars):")
         print("-" * 40)
         print(content_with_special[:500])
         print("-" * 40)
         print(f"[ClipChat] Raw content WITHOUT special tokens (first 500 chars):")
         print("-" * 40)
         print(content[:500])
         print("-" * 40)
    
      # Clean up stray tags from generation
      # Use version WITH special tokens so we can properly strip thinking blocks
      clean_content = content_with_special
    
      # Strip thinking block content (model may have output reasoning)
      clean_content = re.sub(r'<think>.*?</think>', '', clean_content, flags=re.DOTALL)
      # Strip other stray tags
      clean_content = re.sub(r'</?tool_call>', '', clean_content)
      clean_content = re.sub(r'</?tool>', '', clean_content)
      clean_content = re.sub(r'</?function>', '', clean_content)   
      # Strip any remaining special tokens
      clean_content = re.sub(r'<\|im_start\|>', '', clean_content)
      clean_content = re.sub(r'<\|im_end\|>', '', clean_content)
      clean_content = re.sub(r'<\|endoftext\|>', '', clean_content)
      clean_content = clean_content.strip()

      if DEBUG:
         print(f"[ClipChat] Clean content length: {len(clean_content)} chars")
         print(f"[ClipChat] Clean content preview (first 300 chars):")
         print("-" * 40)
         print(clean_content[:300])
         print("-" * 40)

      # Wrap in chat template format (matches z_image encoder)
      wrapped_text = f"<|im_start|>user\n{clean_content}<|im_end|>\n<|im_start|>assistant\n<think>\n</think>\n\n"
    
      if DEBUG:
         # Log formatted prompt (like z_image encoder does)
         print(f"\n[ClipChat] Formatted prompt:\n{wrapped_text}\n")
    
      # Re-tokenize the wrapped text
      wrapped_ids = tokenizer(wrapped_text, return_tensors="pt").input_ids.to(model.device)
    
      if DEBUG:
         print(f"[ClipChat] Encoding {wrapped_ids.shape[1]} tokens to conditioning...")

      # === DIRECT PATH: Get hidden states from our model ===
      with torch.no_grad():
      
          # Correct: compute embeddings for the wrapped prompt, not generated tokens
          #outputs = model(
          #    input_ids=wrapped_ids,
          #    output_hidden_states=True,
          #    return_dict=True
          #)

          # was
          outputs = model(
              output_ids.unsqueeze(0),  # Add batch dimension: [seq_len] -> [1, seq_len]
              output_hidden_states=True
          )
          
          # Use second-to-last layer (matches CLIP encoder behavior)
          hidden_states = outputs.hidden_states[-2].float().cpu()
          hidden_states1 = outputs.hidden_states[-3].float().cpu()

      # Build attention mask (all 1s - no padding in our output)
      attention_mask = torch.ones(1, output_ids.shape[0], dtype=torch.long)  # shape[0] since output_ids is 1D

      # Build conditioning in ComfyUI format
      conditioning = [[
        hidden_states,
        {"pooled_output": None, "attention_mask": attention_mask}
      ]]

      conditioning1 = [[
        hidden_states1,
        {"pooled_output": None, "attention_mask": attention_mask}
      ]]
    
      # Apply padding filter (matches DiffSynth/diffusers)
      conditioning = filter_embeddings_by_mask(conditioning)
      conditioning1 = filter_embeddings_by_mask(conditioning1)

      # === DEBUG: Print direct path info ===
      if DEBUG:
        print("\n" + "="*60)
        print("QWEN DIRECT PATH DEBUG (POST-FILTER)")
        print("="*60)
        print(f"\n--- Generated Content ---")
        print(f"Raw output tokens: {output_ids.shape[0]}")
        print(f"Wrapped tokens: {wrapped_ids.shape[1]}")
        print(f"Clean text length: {len(clean_content)} chars")
        print(f"Text preview: {clean_content[:200]}..." if len(clean_content) > 200 else f"Text: {clean_content}")
        print(f"\n--- Direct Conditioning ---")
        print(f"Shape: {conditioning[0][0].shape}")
        print(f"Range: min={conditioning[0][0].min().item():.2f}, max={conditioning[0][0].max().item():.2f}")
        print(f"Mean: {conditioning[0][0].mean().item():.4f}")
        print(f"Device: {conditioning[0][0].device}")
        print(f"Dtype: {conditioning[0][0].dtype}")
        print(f"Extra dict keys: {conditioning[0][1].keys()}")
        print(f"\n--- First Token Embedding (first 10 dims) ---")
        print(f"Values: {conditioning[0][0][0, 0, :10]}")
        print(f"\n--- Last Token Embedding (first 10 dims) ---")
        print(f"Values: {conditioning[0][0][0, -1, :10]}")
        print("="*60)
        print(f"[ClipChat] Done! Conditioning shape: {conditioning[0][0].shape}")
    
      return (content, wrapped_text, conditioning, conditioning1)

NODE_CLASS_MAPPINGS = {
    "ClipChat": ClipChat,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ClipChat": "Clip Chat",
}
