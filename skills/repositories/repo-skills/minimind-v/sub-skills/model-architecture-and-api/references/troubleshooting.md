# Architecture/API Troubleshooting

## Missing vision encoder

Symptoms: `model.processor is None`, `model.vision_encoder is None`, or `image2tensor` fails because the processor is missing.

Cause: `MiniMindVLM.get_vision_model(model_path)` returns `(None, None)` when the path does not exist or SigLIP2 loading raises an error. It does not download a model.

Recovery: verify the local SigLIP2 directory and route setup to `data-and-resources`. Use the API helper with `--check-vision-path` for a non-loading path check.

## Image placeholder mismatch

Symptoms: text-only answers, poor image grounding, wrong image bound to prompt text, or custom tokenizer mismatch.

Checks:

- Default `image_special_token` is `<|image_pad|>`.
- Default `image_ids` is `[12]`.
- Default `image_token_len` is `64`.
- One contiguous placeholder run should correspond to one image tensor entry.

Recovery: expand `<image>` to `model.config.image_special_token * model.config.image_token_len`, verify tokenizer id, and keep placeholder runs/images in order.

## `pixel_values` shape issues

Use processor dictionaries or shaped raw tensors documented in `api-reference.md`. Add batch/image dimensions for single raw tensors. Do not manually repeat `pixel_values` for `num_return_sequences`; `MiniMindVLM.generate` does this.

## Cache and image changes

Visual features are inserted only when generation starts at position 0. If the image changes, restart generation without old `past_key_values`.

## MoE mismatch

MoE changes every block's feed-forward key layout. Align `use_moe`, hidden size, layer count, and checkpoint filename. Treat `strict=False` loading as a warning, not proof.

## Projector token-count assumptions

The projector does not resample token count. Keep `image_token_len=64` unless changing the vision encoder and replacement logic deliberately.
