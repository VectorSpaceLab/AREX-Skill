# MAGI-1 cross-cutting troubleshooting

Use this root troubleshooting guide for install/import, dependency, asset, and routing problems that cut across source inference and ComfyUI. For workflow-specific failures, also read the nearest sub-skill troubleshooting page.

## Which troubleshooting page should I use?

| Symptom | Read |
| --- | --- |
| CLI argument, config, checkpoint, distributed, or source API failure | [../sub-skills/inference/references/troubleshooting.md](../sub-skills/inference/references/troubleshooting.md) |
| ComfyUI node missing, workflow placeholders, node wiring, or save-node failure | [../sub-skills/comfyui/references/troubleshooting.md](../sub-skills/comfyui/references/troubleshooting.md) |
| General Python/CUDA/package/runtime setup problem | This page plus [installation-and-assets.md](installation-and-assets.md) |
| Prompt enhancement workflow import problem | This page plus [dify-prompt-enhancement.md](dify-prompt-enhancement.md) |

## Package import failures

### `ModuleNotFoundError: inference`

Cause: the MAGI source root is not on `PYTHONPATH`, or the ComfyUI plugin root does not contain the full source tree.

Fix:

- For source CLI/API, run from the MAGI source root or export `PYTHONPATH="$PWD:${PYTHONPATH:-}"`.
- For ComfyUI, keep `inference/` below the MAGI plugin root and ensure the root `__init__.py` appends that root to `sys.path`.

### `ModuleNotFoundError` for `flash_attn`, `flashinfer`, `diffusers`, `transformers`, or media packages

Cause: dependencies were not installed into the runtime Python that actually launches MAGI or ComfyUI.

Fix:

- Run `python scripts/magi_runtime_preflight.py --run-cuda-smoke` in the runtime Python.
- Install requirements into that same isolated environment.
- Match `flashinfer-python` to PyTorch 2.4 and CUDA 12.4 when following the verified stack.
- Avoid mutating shared or base environments unless the user explicitly approves.

### `torch.cuda.is_available()` is false

Cause: CPU-only PyTorch, missing driver/runtime, hidden GPUs, or wrong container flags.

Fix:

- Use a CUDA-capable PyTorch build and compatible NVIDIA driver.
- In Docker, run with GPU access and sufficient shared memory as recommended by the README.
- Check `CUDA_VISIBLE_DEVICES`; the ComfyUI node sets it internally to `0` before generation.

## Asset and path failures

### Missing weights or empty checkpoint directory

Full generation requires all of these local assets: MAGI DiT weights, T5 weights, VAE weights, and `special_tokens.npz`. The DiT loader appends a variant-specific subdirectory below `runtime_config.load`.

Fix:

- Download the intended model family from the public model zoo or another approved source.
- Edit a copied config so `load`, `t5_pretrained`, and `vae_pretrained` point to local directories.
- Run the inference config checker with `--check-paths` before launching.

### Relative paths work in one shell but fail elsewhere

Cause: MAGI configs and ComfyUI node fields are often interpreted relative to the process working directory, which may differ between shell, `torchrun`, and ComfyUI.

Fix:

- Prefer absolute paths in user-owned runtime configs and ComfyUI fields.
- If using relative paths for source CLI experiments, run from the MAGI source root and document that assumption.

### `special_tokens.npz` missing at import time

Cause: prompt processing imports the NPZ at module import time.

Fix:

- Keep `example/assets/special_tokens.npz` available in source or plugin layouts.
- Set `SPECIAL_TOKEN_PATH` before import if the file lives elsewhere.

## ffmpeg and media failures

Symptoms include input decode errors, output MP4 not created, unsupported codec, or empty output file.

Fix:

- Install ffmpeg executable, not only `ffmpeg-python`.
- Use common image formats for image-to-video and simple MP4/H.264 input for video continuation.
- Pre-create the output directory and use an `.mp4` filename.
- If ComfyUI save fails after generation, inspect the ComfyUI terminal log for ffmpeg stderr.

## Long downloads or expensive generation

MAGI weights and full video generation can be large and slow. Before starting network downloads or long generation:

- Confirm the user's model family, target hardware, and time/bandwidth budget.
- Prefer preflight checks first.
- Use short prompts and smaller resolution/frame counts for initial runs when the user approves a real generation smoke test.

## Dify DSL import problems

If the prompt enhancement DSL does not import into Dify:

- Verify the Dify version supports importing workflow DSL/YAML files.
- Configure provider plugins and credentials referenced by the DSL.
- Replace provider/model names if the user's Dify deployment uses different LLM backends.
- Keep prompt-enhancement debugging separate from MAGI inference debugging; a valid enhanced prompt does not validate model weights or CUDA.
