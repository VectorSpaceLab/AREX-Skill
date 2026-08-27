# API reference

## Legacy delta extraction

`get_deltas.main(path, newtoken=0)` scans a checkpoint folder, keeps the attention K/V tensors, optionally stores the last `newtoken` embeddings, writes `delta_epoch=...ckpt`, and the original source script deletes the checkpoint after saving.

Bundled helper behavior:

- keeps the original checkpoint unless `--delete-source` is set
- defaults to CPU-safe loading
- can write to a separate output directory

## Compression

`compress.compress(delta_ckpt, ckpt, diffuser=False, compression_ratio=0.6, device='cuda')`

- compares the delta checkpoint to the pretrained model
- computes an SVD for each `attn2.to_k` / `attn2.to_v` tensor
- stores `u` and `v` factors for the low-rank approximation
- preserves `embed` in legacy mode and `modifier_token` in diffusers mode
- keeps the legacy output under `state_dict` and the diffusers output under `unet`

## Composition

`compose(paths, category, outpath, pretrained_model_path, regularization_prompt, prompts, save_path, device='cuda')`

- loads multiple diffusers deltas
- aligns concept names with category strings
- updates the target K/V weights
- writes a composed `delta.bin`
- may optionally sample if prompts are provided

## Layout expectations

### Legacy extracted delta

- top-level `state_dict`
- attention K/V keys such as `attn2.to_k` and `attn2.to_v`
- optional `embed` tensor for optimized tokens
- compressed K/V entries, when present, are dictionaries with `u` and `v`

### Diffusers delta

- top-level `unet`
- optional `modifier_token`
- uncompressed K/V entries are tensors
- compressed K/V entries are dictionaries with `u` and `v`

## Validator contract

The bundled delta-layout checker should be able to answer three questions:

1. Is this a legacy or diffusers-style delta?
2. Is it compressed or uncompressed?
3. Does it contain the expected learned-token payload (`embed` for legacy extracted deltas or `modifier_token` for diffusers deltas) and the expected K/V layout?
