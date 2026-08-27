# DiscoArt Artwork API Workflow

This reference is for Python API generation with DiscoArt `create(**kwargs)` and `go_big()`. It is self-contained for runtime use with an installed `discoart` package; it does not require reading the source checkout.

For prompt-schema, schedule grammar, config save/load/show/export, and YAML validation, route to `../configuration-and-prompts/SKILL.md`. For `python -m discoart`, Jina serving, Docker, or Jupyter launch workflows, route to `../cli-and-serving/SKILL.md`.

## `create(**kwargs)` at a glance

`create()` creates Disco Diffusion artwork and returns a DocArray `DocumentArray` containing final images and intermediate chunks. Although the runtime signature is `create(**kwargs)`, DiscoArt validates kwargs against its default parameter set before loading models; unknown keys fail through `discoart.config.load_config`.

Key behavior:

- First-generation calls may download the selected diffusion model, secondary model, and CLIP weights unless caches already contain them.
- `create()` chooses CUDA when `torch.cuda.is_available()` is true; CPU mode is possible but expected to be extremely slow.
- `n_batches` creates multiple serial image runs; `batch_size` creates multiple samples per denoising step and increases memory pressure.
- `create()` returns `None` if interrupted by `KeyboardInterrupt` before a successful return, but local/cloud persisted artifacts may still be recoverable.

## Plan a config without generation

Use `load_config` or the bundled helper before calling `create()`:

```python
from discoart.config import load_config

cfg = load_config(user_config={
    "text_prompts": "a small stone lighthouse at dawn, watercolor",
    "name_docarray": "lighthouse-plan-512",
    "width_height": [512, 512],
    "steps": 100,
    "n_batches": 1,
    "batch_size": 1,
})
print(cfg["name_docarray"], cfg["width_height"], cfg["seed"])
```

Command-line planning without generation:

```bash
# from this sub-skill directory
python scripts/plan_create_request.py --config my.yml --check-cuda
python scripts/plan_create_request.py --config my.yml --json
```

The helper calls `discoart.config.load_config`; it does **not** call `create()`, load models, start a server, or create output directories.

## Minimal Python generation recipe

Set DiscoArt environment variables before importing `discoart` if you need custom output/cache behavior.

```python
import os

os.environ.setdefault("DISCOART_OUTPUT_DIR", "./discoart-outputs")
os.environ.setdefault("DISCOART_CACHE_DIR", "./discoart-model-cache")
os.environ.setdefault("DISCOART_DISABLE_REMOTE_MODELS", "1")  # optional: avoid remote model-list sync
os.environ.setdefault("WANDB_MODE", "disabled")

from discoart import create

da = create(
    text_prompts="a small stone lighthouse at dawn, watercolor",
    name_docarray="lighthouse-512-demo",
    width_height=[512, 512],
    steps=100,
    skip_steps=0,
    n_batches=1,
    batch_size=1,
    diffusion_sampling_mode="ddim",
    clip_models=["ViT-B-32::openai", "RN50::openai"],
    save_rate=20,
    image_output=True,
)

# Save the first final image somewhere explicit.
da[0].save_uri_to_file("lighthouse-result.png")
```

This recipe still performs generation and may download models. For a first run on an unknown machine, use the planner and CUDA/cache checks first.

## Core parameters by task

### Run identity, batching, and artifacts

| Parameter | Use |
| --- | --- |
| `name_docarray` | Stable run/session id. Also names the local output directory and cloud DocArray id. Supports Python `.format()` substitution from config keys, e.g. `"demo-{steps}-{seed}"`. |
| `batch_name` | Used only when `name_docarray` is omitted; DiscoArt generates a random `discoart-...` id. |
| `n_batches` | Number of serial image runs. More batches cost more time but not much peak VRAM compared with `batch_size`. |
| `batch_size` | Number of samples per denoising step. Higher values can be faster than separate batches but can trigger OOM. |
| `seed` | Optional reproducibility anchor. DiscoArt increments the original seed per batch. |
| `save_rate` | Step interval for intermediate image/protobuf persistence. `-1` disables intermediate saves; final artifacts are still attempted at completion. |
| `image_output` | If `False`, PNG/GIF files are not written; protobuf persistence remains the recovery path. |
| `gif_fps`, `gif_size_ratio` | Control progress GIF generation. `gif_fps <= 0` disables GIF output. |
| `display_rate` | Notebook/IPython preview refresh rate; `0` disables preview refresh without disabling local files. |
| `visualize_cuts` | Writes cut-visualization PNGs and increases output volume. |

### Canvas and diffusion loop

| Parameter | Use |
| --- | --- |
| `width_height` | Final canvas as `[width, height]`. Use multiples of 64. For practical art, start at 512-ish dimensions before increasing. |
| `steps` | Denoising iterations. More steps are slower; many workflows start near 100-250. |
| `skip_steps` | Skips early denoising. For pure text-to-image, keep low; for `init_image`, values around half of `steps` preserve more of the init image. Must be less than `steps`. |
| `diffusion_sampling_mode` | `"ddim"` is the established default; `"plms"` can work with fewer steps but is less proven in this codebase. |
| `eta` | DDIM noise amount. Lower values can work with fewer steps; higher values often need more steps. |
| `use_secondary_model` | Default `True`. Faster and usually lower VRAM, but requires the secondary model file. `False` can improve fidelity but may consume more VRAM. |
| `diffusion_model` | Catalog model name or prefix, or a local `.pt` path. See `model-and-runtime.md`. |
| `diffusion_model_config` | Dict overrides for custom diffusion model configs. Use only when you know the model architecture. |

### CLIP guidance and cut settings

| Parameter | Use |
| --- | --- |
| `text_prompts` | A string/list or structured prompt config. This sub-skill shows simple strings/lists only; use `configuration-and-prompts` for full prompt schema. |
| `clip_models` | CLIP selectors such as `"ViT-B-32::openai"`, `"ViT-B-16::openai"`, `"RN50::openai"`. More/heavier models increase memory. |
| `clip_models_schedules` | Enables/disables selected CLIP models by step. The model must also appear in `clip_models`; schedule grammar belongs to `configuration-and-prompts`. |
| `clip_guidance_scale` | Strong prompt pull. If outputs overshoot into harsh/solid colors, reduce it or adjust `skip_steps`/clamp settings. |
| `cutn_batches` | Splits cut evaluation into sequential batches. Higher values can reduce peak memory for many cuts but make each step slower. |
| `cut_overview`, `cut_innercut`, `cut_icgray_p`, `cut_ic_pow` | Cut schedules. Use `configuration-and-prompts` for grammar and validation. |
| `text_clip_on_cpu` | Keeps text transformers on CPU while visual CLIP moves to GPU; can save VRAM with little speed cost on common GPUs. |
| `truncate_overlength_prompt` | Truncates prompts to CLIP context length instead of failing/overrunning. |
| `clip_denoised` | Selects whether CLIP evaluates noisy or denoised images. |

### Initial state and reuse

| Parameter | Use |
| --- | --- |
| `init_image` | Local path or URL used as starting image. Increase `skip_steps` to preserve more structure. |
| `init_document` | `Document`, `DocumentArray`, or DocArray id string. DiscoArt uses document `.tags` as starting config and `.uri` as `init_image`; explicit kwargs override tags. |
| `init_scale` | Strength of matching the init image relative to CLIP prompt guidance. |
| `perlin_init`, `perlin_mode` | Use Perlin noise instead of random noise as starting point. `perlin_init` overrides `init_image`. |

### Stop/skip controls

`skip_event` and `stop_event` may be `multiprocessing.Event`, `threading.Event`, or `asyncio.Event`-like objects:

- When `skip_event` is set, the current batch is skipped and generation proceeds to the next `n_batches` item; the event is cleared.
- When `stop_event` is set, all remaining batches are skipped; the event is cleared before return.
- Partial images and protobuf data may still be available if a save occurred before the event took effect.

Example:

```python
import threading
from discoart import create

skip_event = threading.Event()
stop_event = threading.Event()

da = create(
    text_prompts="a neon library under rain",
    name_docarray="interruptible-demo",
    n_batches=2,
    batch_size=1,
    skip_event=skip_event,
    stop_event=stop_event,
)
```

## Output directory and filenames

By default, DiscoArt writes under the current working directory. If `DISCOART_OUTPUT_DIR` is set before the run, outputs go there instead.

```text
<output-root>/<name_docarray>/
  da.protobuf.lz4
  0-done-0.png
  0-step-20-0.png
  0-progress-0.png
  0-progress-0.gif
```

Index meanings in DiscoArt 0.12.2:

- First number: batch index from `0` to `n_batches - 1`.
- `done`: final image at completion.
- `step-<j>`: intermediate image saved according to `save_rate`.
- Last number: minibatch/sample index from `0` to `batch_size - 1`.
- `progress`: sprite/GIF containing intermediate chunks for that batch/sample.
- `da.protobuf.lz4`: compressed DocArray backup updated during saves and on completion.

If `image_output=False`, expect protobuf but not PNG/GIF files. If `gif_fps <= 0`, expect no progress GIF. If `save_rate < 0`, intermediate step files are disabled, but final files are still attempted at completion when `image_output=True`.

## DocArray result recipes

Save final images from the returned `DocumentArray`:

```python
for idx, doc in enumerate(da):
    doc.save_uri_to_file(f"discoart-result-{idx}.png")
```

Display final images in notebook-capable environments:

```python
da.plot_image_sprites(skip_empty=True, show_index=True, keep_aspect_ratio=True)
for doc in da:
    doc.display()
```

Inspect or save intermediate chunks:

```python
first = da[0]
first.chunks.plot_image_sprites(
    "first-run-steps.png",
    skip_empty=True,
    show_index=True,
    keep_aspect_ratio=True,
)
first.chunks.save_gif("first-run-steps.gif", show_index=True, size_ratio=0.5)
```

Recover from local protobuf:

```python
from docarray import DocumentArray

da = DocumentArray.load_binary("./discoart-outputs/lighthouse-512-demo/da.protobuf.lz4")
da[0].save_uri_to_file("recovered-final.png")
```

Pull from DocArray cloud backup when the run was pushed and network/auth allow it:

```python
from docarray import DocumentArray

da = DocumentArray.pull("lighthouse-512-demo")
da[0].display()
```

Cloud backup is skipped when `DISCOART_OPTOUT_CLOUD_BACKUP=1`; local protobuf is then the primary recovery path.

## Reuse a previous result as `init_document`

Use a pulled/local document as the initial state for a new run. DiscoArt copies the document tags into the new config and uses the document URI as the init image if present.

```python
from docarray import DocumentArray
from discoart import create

previous = DocumentArray.pull("lighthouse-512-demo")

refined = create(
    init_document=previous[0],
    text_prompts="the same lighthouse, calmer sea, more sunrise glow",
    name_docarray="lighthouse-refined",
    steps=150,
    skip_steps=75,
    n_batches=1,
    batch_size=1,
)
```

Shortcut by id:

```python
from discoart import create

refined = create(init_document="lighthouse-512-demo", name_docarray="lighthouse-refined")
```

Notes:

- If `init_document` has no `.tags`, DiscoArt falls back to defaults.
- If it has no `.uri`, generation proceeds without an init image.
- Explicit kwargs override tags copied from the document.

## `go_big()` workflow

`go_big()` is a creative fractal-style upscale, not a high-fidelity super-resolution tool. It slides windows over a generated document, calls `create()` on each window, and stitches the results.

```python
from discoart import create, go_big

base = create(
    text_prompts="an ornate isometric city carved from crystal",
    name_docarray="crystal-city-base",
    width_height=[512, 512],
    steps=100,
    n_batches=1,
    batch_size=1,
)

big_doc = go_big(
    base[0],
    window_size=256,
    upscale_factor=2,
    skip_rate=0.85,
    stride_size=None,
    steps=80,
)
big_doc.save_uri_to_file("crystal-city-gobig.png")
```

Controls:

- `window_size`: larger windows mean fewer chunks and usually faster runs, but each chunk uses more memory.
- `upscale_factor`: final size multiplier; larger values can become very expensive.
- `skip_rate`: high values skip more diffusion, run faster, and preserve more of the original; low values add more detail/fractal variation but are slower and more disruptive.
- Extra `**kwargs` pass through to the internal `create()` calls.
- Internal chunk runs use names like `<old-name>-gobig-<idx>-<chunk-count>`.

## Later verification candidates

This sub-skill is designed to support these later checks, but do not run full native generation while drafting:

- `tiny-create-smoke`: bounded `create(**mini_config)` expectation from tests; requires CUDA/model cache/time allowance for practical execution.
- `readme-api-workflows`: documentation-backed recipes for one-line create, parameter overrides, result display, config reuse, DocArray pull/recovery, `init_document`, and `go_big()`.
