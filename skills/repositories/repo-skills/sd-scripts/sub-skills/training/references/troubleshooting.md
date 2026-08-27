# Training Troubleshooting

Use this file to diagnose sd-scripts training command failures before asking the user to run expensive jobs again.

## Missing `accelerate` or Configuration

Symptoms:
- `accelerate: command not found`
- launch asks for distributed settings unexpectedly
- process starts with wrong device count or precision

Fixes:
- Install the package extras required by the user's environment.
- Run `accelerate config` or use explicit launch flags such as `--num_cpu_threads_per_process 1`.
- Keep precision consistent between accelerate config and command flags.

## Torch, CUDA, or Wheel Mismatch

Symptoms:
- CUDA unavailable despite GPU
- illegal instruction or missing CUDA symbols
- xformers import errors after changing PyTorch

Fixes:
- Verify PyTorch sees CUDA before training.
- Match PyTorch, CUDA runtime, xformers, bitsandbytes, and GPU driver versions.
- Temporarily remove `--xformers` and use `--sdpa` on PyTorch 2.x if xformers is broken.

## Missing Model Files

Symptoms:
- file-not-found for base model, text encoder, VAE, AE, or DiT
- FLUX/SD3 load fails because a Diffusers directory was passed where `.safetensors` is expected

Fixes:
- Confirm every placeholder path was replaced.
- For FLUX/Chroma, pass the model `.safetensors`, T5XXL `.safetensors`, and AE `.safetensors`; FLUX also needs CLIP-L, while Chroma omits CLIP-L.
- For SD3, separate `--clip_l`, `--clip_g`, `--t5xxl`, and `--vae` are only needed when not embedded in the base checkpoint.

## Wrong Model-Family Flags

Symptoms:
- parser rejects `--v2`, `--v_parameterization`, `--clip_skip`, or `--max_token_length`
- command trains but results look wrong because v-prediction was omitted or added incorrectly

Fixes:
- Use `--v2 --v_parameterization` only for SD2 v-prediction checkpoints.
- Do not use SD1/2 flags on SDXL, SD3, FLUX, Chroma, Lumina, HunyuanImage, or Anima.
- For FLUX/SD3 token length, use `--t5xxl_max_token_length`.

## FLUX and Chroma Asset Confusion

Symptoms:
- FLUX command fails loading text encoders or AE
- Chroma command expects CLIP-L or produces guidance-related errors

Fixes:
- FLUX.1 requires `--clip_l`, `--t5xxl`, and `--ae`.
- Chroma uses `flux_train_network.py --model_type chroma`, omits `--clip_l`, and still needs `--t5xxl` and `--ae`.
- Chroma should use `--guidance_scale 0.0` and `--apply_t5_attn_mask`; FLUX.1 typically uses `--guidance_scale 1.0`.
- For FLUX memory pressure, consider fp8 T5XXL, `--fp8_base`, `--blocks_to_swap`, and frozen text encoder output caching.

## Optimizer Optional Dependencies

Symptoms:
- `AdamW8bit`, `Lion`, `Prodigy`, or DAdapt optimizer import/selection fails
- optimizer state causes immediate OOM

Fixes:
- `AdamW8bit` requires bitsandbytes and a compatible platform.
- Lion/Prodigy/DAdapt variants require their optional packages or supported implementations.
- Fall back to `AdamW` or `Adafactor` when optional optimizer dependencies are unavailable.
- For Adafactor-style FLUX memory reduction, include compatible scheduler and optimizer args such as disabling relative step/scale parameter where needed.

## Attention Backend Problems

Symptoms:
- xformers import failure
- unsupported attention mode
- slower-than-expected training after changing backend

Fixes:
- Use `--sdpa` on PyTorch 2.x when xformers is unavailable.
- Use `--xformers` only when the installed xformers wheel matches the PyTorch/CUDA stack.
- HunyuanImage `--attn_mode sageattn` is inference-only; do not use it for training.
- Some family scripts have special constraints such as HunyuanImage xformers requiring split attention.

## Out of Memory

Symptoms:
- CUDA OOM during model load, latent caching, text encoder caching, or first backward pass
- process killed by system memory pressure

Fixes, in order:
1. Lower batch size and resolution.
2. Enable `--gradient_checkpointing`.
3. Use `--mixed_precision bf16` or `fp16` supported by hardware.
4. Use `--sdpa` or a working `--xformers` install.
5. Enable `--cache_latents` where compatible; avoid it for inpainting.
6. Enable `--cache_text_encoder_outputs` when text encoders are frozen.
7. Use family fp8 options: FLUX/SD3/Lumina `--fp8_base`, HunyuanImage `--fp8_scaled`; do not use unsupported fp8 flags on Anima.
8. Use `--blocks_to_swap`; expect slower training and avoid conflicting CPU checkpoint offload flags.
9. Switch optimizer to an 8-bit or lower-memory option if installed.

## Invalid `network_module`

Symptoms:
- `ModuleNotFoundError` for a network module
- network creation fails because the module is for a different family

Fixes:
- Standard LoRA: `networks.lora`.
- FLUX/Chroma LoRA: `networks.lora_flux`.
- LoHa: `networks.loha`.
- LoKr: `networks.lokr`.
- ControlNet-LLLite does not require `--network_module`; use its dedicated script and `--cond_emb_dim` / `--network_dim`.

## Text Encoder Caching Conflicts

Symptoms:
- error says T5XXL or text encoder is being trained while outputs are cached
- caption shuffle/dropout seems ignored

Fixes:
- Do not use `--cache_text_encoder_outputs` when training the same text encoder.
- For FLUX/SD3, if `network_args` trains T5XXL, remove text encoder caching.
- Caption augmentations such as shuffle/dropout do not work after text encoder outputs are cached.

## Validation Loss Confusion

Symptoms:
- validation does not run
- validation split differs from expectation
- user expects generation quality metric instead of loss

Fixes:
- Ensure dataset TOML has validation subsets or CLI `--validation_split` is provided.
- TOML `validation_split` takes precedence over CLI global `--validation_split`.
- Add `--validate_every_n_steps` or `--validate_every_n_epochs` to control cadence.
- Look for `loss/validation` in TensorBoard or the chosen logger; it is not an image-quality score.
- Use `--max_validation_steps` for cheaper deterministic validation.

## Inpainting Mask and Cache Issues

Symptoms:
- error or bad behavior when combining inpainting with latent caching
- sample prompts skipped during inpainting training
- confusion between alpha masks and inpainting masks

Fixes:
- `--train_inpainting` cannot be combined with `--cache_latents` or `--cache_latents_to_disk`.
- Training masks are generated procedurally per step from source images; no special mask dataset is required.
- For inpainting sample previews, every prompt line needs an `--i path/to/reference_image` directive.
- `--alpha_mask` is loss masking from image alpha and is separate from 9-channel inpainting training.

## ControlNet-LLLite Dataset Issues

Symptoms:
- conditioning images not found
- random crop errors
- training runs but controls do not line up with images

Fixes:
- Use `sdxl_train_control_net_lllite.py` for SDXL only.
- Add `conditioning_data_dir` to each dataset subset that needs control images.
- Conditioning image basenames must match training image basenames.
- Do not use random crop for LLLite datasets.
- Tune `--cond_emb_dim` and `--network_dim` for control complexity; high values cost more VRAM.

## Anima Compile Conflicts

Symptoms:
- parser/assertion error involving `--compile`, `--torch_compile`, `--compile_fullgraph`, or `--split_attn`
- compile run fails after block swapping/offload changes

Fixes:
- Use `--compile` for Anima per-block compile.
- Do not combine `--compile` and `--torch_compile`.
- Do not combine `--compile_fullgraph` with `--split_attn`.
- Avoid incompatible offload combinations: block swapping conflicts with CPU offload checkpointing and unsloth offload checkpointing.

## Safe Native Checks

Safe-ish checks when dependencies are installed:

```bash
python train_leco.py --help
python sdxl_train_leco.py --help
python train_network.py --help
python sdxl_train_network.py --help
```

Parser/unit candidates that do not require full model weights are `tests/test_train_leco.py`, `tests/test_sdxl_train_leco.py`, and parts of `tests/test_lumina_train_network.py`, but they still depend on the repository's Python dependency stack. Treat full training and manual GPU scripts as skip-expensive unless explicitly authorized.
