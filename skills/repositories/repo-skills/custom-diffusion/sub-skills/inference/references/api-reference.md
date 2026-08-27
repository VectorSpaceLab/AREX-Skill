# API reference

## Sampling contract

`sample(ckpt, delta_ckpt, from_file, prompt, compress, batch_size, freeze_model, sdxl=False)` is the public sampling contract used by the repo.

Behavior to remember:

- loads the base pipeline on CUDA
- loads the delta with `load_model`
- uses seed 42
- uses 200 inference steps
- uses guidance scale 6
- uses `eta=1`
- treats `prompt` as the single-prompt path and `from_file` as the line-delimited prompt-file path
- writes a prompt montage alongside per-sample images under the delta directory

## Pipeline load behavior

### `CustomDiffusionPipeline.load_model(save_path, compress=False)`

- restores text-encoder state when `text_encoder` is present
- restores learned modifier-token embeddings when `modifier_token` is present
- restores `unet` attention weights
- reconstructs compressed K/V weights from `u @ v` when `compress=True`

### `CustomDiffusionPipeline.save_pretrained(save_path, freeze_model=...)`

- stores a delta dictionary rather than a full pipeline when `all=False`
- saves modifier-token embeddings when they were learned
- saves text-encoder weights only when requested
- stores `attn2.to_k` and `attn2.to_v` for the default freeze mode
- stores all `attn2` weights when `freeze_model='crossattn'`

### `CustomDiffusionXLPipeline`

The XL pipeline mirrors the same delta logic but keeps two text encoders, two tokenizers, and paired modifier-token embeddings.

## Delta layout expectations

### Uncompressed diffusers delta

- top-level `unet`
- optional `modifier_token`
- `unet` values for K/V entries are tensors

### Compressed diffusers delta

- top-level `unet`
- optional `modifier_token`
- `unet` values for K/V entries are dictionaries with `u` and `v`

## Freeze-mode semantics

- `crossattn_kv` keeps the K/V matrices as the default training target.
- `crossattn` updates all cross-attention weights.
- The sampler should match the freeze mode that produced the delta.
