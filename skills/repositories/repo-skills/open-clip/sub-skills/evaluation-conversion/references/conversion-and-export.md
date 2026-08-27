# Conversion and Export

Use this reference to choose checkpoint payloads, diagnose state-dict keys, apply OpenCLIP conversion helpers, and plan Hugging Face export/push work.

## Checkpoint Payloads

Common payload shapes:

- Flat raw state dict: `{parameter_name: tensor}`.
- Factory-loadable dict with `state_dict`.
- Task-era training checkpoint with `epoch`, `state_dict`, optional `state_dict_ema`, `optimizer`, `scaler`, `global_step`, and `samples_seen`.
- Sharded DCP checkpoint directory plus `_metadata_extra.pt` for epoch/scaler/counters.
- `safetensors` files for HF-style model weights.
- big_vision SigLIP `.npz` or `.npy` files.

For inference/export from a task checkpoint, prefer `state_dict_ema` when it exists and the user wants EMA evaluation; otherwise use `state_dict`. `TrainingTask.state_dict_for_inference()` follows the same preference when the live task object is available.

Use `scripts/checkpoint_key_report.py` before destructive or side-effecting conversion. It reports nested state-dict payloads, prefix patterns, tensor shapes, and optional random-model key comparison.

## Safe Loading

OpenCLIP now loads PyTorch checkpoint files with `weights_only=True` in core paths. Keep this default for local inspection and model loading.

Only consider `weights_only=False` when all are true:

1. The checkpoint is trusted.
2. `weights_only=True` fails because the payload uses non-tensor Python objects.
3. The user explicitly accepts arbitrary pickle execution risk.
4. The load happens in the narrowest possible diagnostic context.

Do not make generated helpers default to unsafe pickle loading.

## Prefix and Wrapper Diagnosis

Common prefixes and wrappers:

- `module.`: usually DDP. Factory load strips a leading `module` prefix; task checkpoint loading strips `module.` when `is_distributed=False`.
- `_orig_mod.`: often from a compiled module state dict; unwrap or strip before comparing against an uncompiled model.
- `trainable_module.`: task wrapper namespace; usually indicates the checkpoint came from a wrapper rather than the raw model.
- Nested `state_dict`: task/full checkpoint payload.
- Nested `state_dict_ema`: EMA payload; often preferred for evaluation/export.

Scalar mismatch at FSDP/non-FSDP boundaries is expected for `logit_scale` and SigLIP `logit_bias`: FSDP may use shape `[1]`, while standard models use 0-D scalars. OpenCLIP reconciles these in task and factory load paths.

## Factory Load Path

`open_clip.factory.load_checkpoint(model, checkpoint_path, strict=True, weights_only=True, device="cpu")` handles:

- `.safetensors` via safetensors.
- `.npz`/`.npy` big_vision SigLIP weights through `open_clip.convert.load_big_vision_weights`.
- Flat or nested `state_dict` payloads.
- Leading `module` prefix stripping.
- Third-party state-dict conversion through `open_clip.convert.convert_state_dict`.
- NaFlex state-dict conversion through `open_clip.naflex_convert.convert_naflex_state_dict`.
- Old custom-text layout migration.
- Positional embedding resize.
- `logit_scale`/`logit_bias` scalar shape reconciliation.

Use `strict=False` only when missing/unexpected keys are understood and documented.

## Conversion Helpers

`open_clip.convert`:

- `load_big_vision_weights(model, checkpoint_path)` loads Google big_vision image-text `.npz` weights, currently for SigLIP-style `CustomTextCLIP` destinations with timm image encoders, including NaFlexVit trunk handling.
- `convert_mobile_clip_state_dict(model, state_dict, fastvit=True)` maps Apple MobileCLIP state dicts into OpenCLIP/timm/text keys.
- `convert_state_dict(model, state_dict)` detects MobileCLIP key signatures and converts supported variants.

`open_clip.naflex_convert`:

- `apply_naflex_vision_config(model_cfg)` rewrites compatible native OpenCLIP ViT or timm EVA/ViT vision configs to use NaFlexVit.
- `convert_naflex_state_dict(model, state_dict)` converts native ViT or timm NaFlex-compatible keys into NaFlexVit trunk keys when the destination model uses NaFlexVit.
- Native conversion folds class and positional embeddings, maps `visual.conv1.weight` to linear patch embedding, maps transformer block names, and requires square positional grids.

Audio-specific Transformers CLAP conversion lives in `open_clip.audio.convert`; route details to `../audio-clap/SKILL.md`.

## Pretrained Registry and Remote Checkpoints

Use `open_clip.list_pretrained()` to validate `(model, tag)` pairs before giving users a hosted pretrained command. The README states that `pretrained` also accepts local checkpoint paths, and OpenAI weights now route through Hugging Face Hub instead of the removed JIT loader path.

When a task mentions remote or hosted weights:

- Validate model/tag availability with `list_pretrained()` when possible.
- Prefer local checkpoint paths for reproducible conversion diagnostics.
- Avoid implicit downloads in helper scripts; make downloads an explicit user step.
- Treat checksum failures from pretrained download helpers as a hard stop, not a warning.

## Hugging Face Export and Push

`open_clip.push_to_hf_hub` provides two public entry points:

- `push_to_hf_hub(model, tokenizer, model_config, repo_id, ...)` for an already-created model.
- `push_pretrained_to_hf_hub(model_name, pretrained, repo_id, precision="fp32", ..., hf_tokenizer_self=False, **kwargs)` for loading a named model/checkpoint and pushing it.

Export behavior:

- `save_for_hf` writes model weights, tokenizer files, and `open_clip_config.json`-style config.
- Safe serialization can save safetensors, PyTorch `.bin`, or both depending on `safe_serialization`.
- If the tokenizer is not an `HFTokenizer` or `SigLipTokenizer`, push falls back to the default CLIP HF tokenizer.
- `push_pretrained_to_hf_hub` can set `model_config["text_cfg"]["hf_tokenizer_name"] = repo_id` when `hf_tokenizer_self=True`.

Push behavior is side-effecting and can create repos/upload files. Confirm:

1. `repo_id`, visibility, revision, and PR behavior.
2. HF token/auth availability.
3. Whether safetensors is installed when safe serialization is requested.
4. Model card metadata and license.
5. That local inference/evaluation checks passed before upload.
