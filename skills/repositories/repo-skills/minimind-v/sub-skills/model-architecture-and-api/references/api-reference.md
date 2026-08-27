# MiniMind-V API Reference

## Verified public classes and functions

| Object | Signature / key defaults | Notes |
| --- | --- | --- |
| `VLMConfig` | `(image_special_token='<|image_pad|>', image_ids=[12], **kwargs)` | Inherits `MiniMindConfig`; adds image token metadata. Defaults include `image_hidden_size=768`, `image_token_len=64`. |
| `MiniMindVLM.__init__` | `(config=None, vision_model_path='./model/siglip2-base-p32-256-ve')` | Builds MiniMind causal LM, attaches SigLIP2 if the local path exists and loads, then creates `vision_proj`. |
| `MMVisionProjector` | `(in_dim, out_dim, source_tokens=64, target_tokens=64)` | LayerNorm + two Linear layers with GELU; token-count arguments are not used for resampling. |
| `MiniMindVLM.image2tensor` | `(image, processor)` | Converts RGBA/LA images to RGB, then calls the SigLIP processor. Requires a non-`None` processor. |
| `MiniMindVLM.get_image_embeddings` | `(image_inputs, vision_model)` | Runs frozen vision model and returns `last_hidden_state`; requires local SigLIP2. |
| `MiniMindVLM.forward` | `(input_ids=None, attention_mask=None, past_key_values=None, use_cache=False, logits_to_keep=0, labels=None, pixel_values=None, **args)` | Inserts projected image features only when `pixel_values` is not `None` and decoding starts at position 0. |
| `MiniMindVLM.generate` | `(*args, num_return_sequences=1, **kwargs)` | Repeats `pixel_values` along batch dimension when `num_return_sequences > 1`. |
| `MiniMindConfig` | defaults `hidden_size=768`, `num_hidden_layers=8`, `vocab_size=6400`, `use_moe=False` | MoE fields include `num_experts=4`, `num_experts_per_tok=1`. |

## Important tensor shapes

- Processor dictionary for one image: `{'pixel_values': [batch, channels, height, width]}`.
- Processor dictionary for multiple images: `{'pixel_values': [batch, num_images, channels, height, width]}`.
- Raw multi-image tensor: `[batch, num_images, channels, height, width]`.
- Accepted raw special case: `[batch, num_images, 1, channels, height, width]`, squeezed before processing.
- Projected visual tokens: `[batch, num_images, image_token_len, hidden_size]` for multiple images.

## Prompt/token contract

For the default tokenizer/config, one image is represented by a contiguous run of 64 `<|image_pad|>` tokens. The replacement loop scans `input_ids` for runs whose token id equals `config.image_ids[0]` and replaces each run with projected vision features in order.

Do not assume the source validates semantic alignment between the number of image-byte entries and placeholder runs. Future agents should validate this invariant in data/prompt construction.

## Runtime caveats

- If `vision_model_path` is missing or incompatible, `MiniMindVLM.get_vision_model()` returns `(None, None)` rather than downloading resources.
- `source_tokens` and `target_tokens` arguments to `MMVisionProjector` do not resample token count.
- MoE checkpoints require `use_moe=True`; dense checkpoints require `use_moe=False`.
- `strict=False` loads elsewhere should not be treated as proof of compatible architecture.
