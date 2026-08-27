# Model and Runtime Notes for DiscoArt Generation

Use this reference when selecting diffusion models, CLIP models, CUDA/runtime settings, cache locations, W&B behavior, and memory trade-offs for `discoart.create()` and `go_big()`.

## Runtime assumptions

- Target package facts: DiscoArt `0.12.2`, `create(**kwargs)`, 49 default arguments.
- Practical generation is CUDA-oriented. DiscoArt can fall back to CPU, but its own warning says CPU generation is unbearably slow.
- Environment variables that affect output/cache/model behavior must be set before importing or running DiscoArt in the process.
- Config planning through `discoart.config.load_config` or `scripts/plan_create_request.py` does not download models. Calling `create()` can download and load large model files.

## Model load sequence in `create()`

A `create()` call performs these high-level runtime steps:

1. Normalize kwargs with DiscoArt defaults and generate/fill `seed` and `name_docarray`.
2. Choose device with `torch.cuda.is_available()`; CUDA uses `cuda:0`, otherwise CPU.
3. Load the selected diffusion model and diffusion config.
4. Load enabled CLIP models.
5. Load the secondary model when `use_secondary_model=True`.
6. Run denoising and persist images/protobuf during `save_rate` intervals and at completion.

Each model load can fail independently due to missing packages, cache permissions, unavailable CUDA, download failures, checksum mismatch, or VRAM exhaustion.

## Diffusion model selection

`diffusion_model` may be one of the catalog model names/prefixes or a local model file path. Prefix matching is supported: for example, `"512"` resolves to the default 512 model, `"portrait"` resolves to a portrait generator variant, and `"watercolor"` resolves to a watercolor model.

Common catalog entries distilled from the 0.12.2 package include:

- `512x512_diffusion_uncond_finetune_008100` — default model.
- `256x256_diffusion_uncond` — smaller base model.
- `PulpSciFiDiffusion`.
- `pixel_art_diffusion_hard_256` and `pixel_art_diffusion_soft_256`.
- `pixelartdiffusion4k`.
- `PADexpanded`.
- `watercolordiffusion` and `watercolordiffusion_2`.
- `portrait_generator_v1.5` and related portrait generator keys.
- Additional fine-tuned style models such as comic, isometric, and ukiyo-e variants.

Selection rules and cautions:

- You do not need the full name when a prefix is unambiguous.
- Some catalog models declare recommended `width_height`; DiscoArt warns when your size differs.
- A local `.pt` path is treated as a custom diffusion model. Provide `diffusion_model_config={...}` when the model architecture differs from the default fallback.
- Unknown names raise an error before generation can proceed.
- First use of a catalog model may download from configured sources into the cache.

## Diffusion config and sampling

| Setting | Guidance |
| --- | --- |
| `diffusion_model_config` | Dict override for architecture/runtime settings. Use for custom model files or known model variants only. Bad configs can fail deep in guided-diffusion loading. |
| `diffusion_sampling_mode` | `"ddim"` is the default/stable path; `"plms"` is an alternate sampler that can be tried for fewer-step experiments. |
| `steps` | Controls denoising iterations. More steps improve opportunity for detail but linearly increase runtime. |
| `skip_steps` | Must remain below `steps`. For `init_image`, around 50% of `steps` preserves more init structure; too high can leave insufficient denoising. |
| `eta` | DDIM noise amount. `0` can work with fewer steps; higher values often benefit from higher step counts. |
| `use_secondary_model` | Default `True`; loads a secondary model and can be faster/lower VRAM. `False` skips that download but may consume more VRAM and run slower. |

On non-CPU devices, DiscoArt enables fp16 for the diffusion model. CPU mode uses full precision and is very slow.

## Model cache and remote catalog controls

Set these before importing/running DiscoArt:

| Environment variable | Effect |
| --- | --- |
| `DISCOART_CACHE_DIR` | Directory for DiscoArt diffusion/secondary model downloads. Defaults to a user cache directory. Set it explicitly for reproducible jobs or shared caches. |
| `DISCOART_MODELS_YAML` | Local model catalog override. Use this for private mirrors or custom model lists. |
| `DISCOART_DISABLE_REMOTE_MODELS=1` | Disables remote model-list sync. Useful for offline/reproducible runs and to avoid network-sensitive startup warnings. |
| `DISCOART_REMOTE_MODELS_URL` | Custom remote model-list URL when remote sync is enabled. |
| `DISCOART_DISABLE_CHECK_MODEL_SHA=1` | Skips SHA verification. Use only as a last resort for trusted local mirrors because it removes corruption/tamper detection. |

First-run download planning:

- Diffusion model files are large. Ensure cache disk space and write permission before calling `create()`.
- CLIP/OpenCLIP weights may use their own package caches in addition to `DISCOART_CACHE_DIR`.
- `use_secondary_model=True` triggers a secondary model download unless cached.
- For air-gapped runs, pre-populate caches, set `DISCOART_DISABLE_REMOTE_MODELS=1`, and use a local `DISCOART_MODELS_YAML` if the default catalog points at unreachable URLs.

## CLIP model selection

`clip_models` accepts selectors in the form `model::pretrained`. Defaults are:

```python
["ViT-B-32::openai", "ViT-B-16::openai", "RN50::openai"]
```

Useful guidance:

- Start with one or two default CLIP models for memory-constrained runs.
- More CLIP models can improve guidance diversity but increase VRAM and load time.
- Larger selectors such as `RN50x16`, `RN50x64`, `ViT-L-14`, and `ViT-L-14-336` are memory-heavy.
- Non-OpenAI or quickgelu variants use OpenCLIP loading and may download separate weights.
- `clip_models_schedules` only affects models listed in `clip_models`; otherwise the schedule entry is ignored.
- Schedule syntax and prompt-level `clip_guidance` routing belong to `configuration-and-prompts`.

VRAM helpers:

- `text_clip_on_cpu=True` loads text transformers on CPU while keeping visual CLIP on GPU. This can save VRAM with little speed penalty on common GPUs.
- Reduce `clip_models` before reducing prompt quality or canvas size when OOM occurs during CLIP loading.

## Canvas, batching, and memory trade-offs

| Lever | Peak memory impact | Runtime impact | Notes |
| --- | --- | --- | --- |
| `width_height` | High | High | Pixel count dominates memory. Use multiples of 64; start at 512-ish sizes and scale up cautiously. |
| `batch_size` | High | Moderate/high | Multiple samples per step. Faster than separate runs in some cases but a common OOM trigger. |
| `n_batches` | Low peak, high total | High total | Runs serially; increases total time more than peak memory. |
| `clip_models` count/size | High | High | Heavy CLIP models can OOM before diffusion starts. |
| `cutn_batches` | Can lower peak for cuts | Slower | More sequential cut batches reduce per-step memory for cuts but increase per-step time. |
| `use_secondary_model=False` | Can increase | Can slow | Higher-quality path may consume more VRAM. |
| `text_clip_on_cpu=True` | Lowers GPU memory | Small | Helpful on many GPUs; if a specific GPU behaves badly, switch back. |
| `visualize_cuts=True` | Output/storage | Slower I/O | Writes extra cut visualization images. |

`go_big()` multiplies generation cost by the number of sliding windows. To control it: increase `window_size`, increase `skip_rate`, decrease `upscale_factor`, or increase `stride_size` to reduce overlap.

## Output, display, and process environment

| Environment variable | Effect |
| --- | --- |
| `DISCOART_OUTPUT_DIR` | Root directory for `<name_docarray>/` outputs. Defaults to the current working directory. |
| `DISCOART_LOG_LEVEL` | Logging verbosity such as `DEBUG` or `INFO`. |
| `DISCOART_DISABLE_IPYTHON=1` | Disables IPython/Jupyter integration paths; useful for headless scripts. |
| `DISCOART_DISABLE_RESULT_SUMMARY=1` | Suppresses final result summary display. `go_big()` may set this temporarily while it runs internal chunk generations. |
| `DISCOART_DISABLE_TQDM=1` | Disables diffusion progress bars. |
| `DISCOART_OPTOUT_CLOUD_BACKUP=1` | Prevents DocArray cloud backup. Local `da.protobuf.lz4` remains the recovery target. |

Output-related create kwargs:

- `image_output=True`: write PNG/GIF artifacts.
- `image_output=False`: persist protobuf only; no PNG/GIF output.
- `save_rate`: controls intermediate save interval.
- `gif_fps <= 0`: disables GIF generation.
- `display_rate=0`: disables notebook preview refresh only.

## W&B behavior

DiscoArt initializes W&B around each `n_batches` item. By default, `WANDB_MODE` is treated as `disabled` and DiscoArt logs a message explaining how to enable online tracking.

Set before import/run:

```python
import os
os.environ["WANDB_MODE"] = "disabled"  # or "offline" / "online"
```

Guidance:

- Use `disabled` for deterministic local automation and CI-like runs.
- Use `offline` when you want local W&B logs without network sync.
- Use `online` only when credentials/network are configured; one `create()` maps to a W&B project named after `name_docarray`, and each batch maps to a run.

## Safe preflight commands

Summarize a YAML config without generation:

```bash
# from this sub-skill directory
python scripts/plan_create_request.py --config my.yml --json
```

Check CUDA availability without running DiscoArt diffusion:

```bash
# from this sub-skill directory
python scripts/plan_create_request.py --config my.yml --check-cuda
```

Minimal inline CUDA probe:

```python
import torch
print(torch.__version__)
print(torch.cuda.is_available())
if torch.cuda.is_available():
    print(torch.cuda.get_device_name(0))
```

A CUDA check only proves PyTorch can see a GPU; it does not prove model files, package versions, cache permissions, or VRAM headroom are sufficient for the chosen `create()` config.
