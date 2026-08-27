# Zero123Plus generation workflows

These recipes cover the core generation path only. For serving, demo launch,
Docker, or Cog behavior, use the sibling deployment sub-skill. For exact
callable signatures, see [`api-reference.md`](api-reference.md).

## Shared rules

- Use a CUDA GPU for real generation runs.
- Keep local cache loading on by default.
- Pass `--allow-download` only when network fetches are approved.
- The bundled wrappers use the checked-in `diffusers-support/` custom pipeline
  by default; `--allow-download` only affects checkpoint and optional cleanup
  model fetching.
- Use `--dry-run` first when you want to verify file paths, model ids, or device
  selection without loading weights.
- Treat the raw base and depth outputs as a single `640 x 960` six-view montage.
- Treat the six-view montage as a `2 x 3` grid and split it row-major if you
  need individual tiles.
- Use PIL images, not tensors, as inputs.

## 1) Base v1.1 multiview path

**What it does:** Runs the base `sudo-ai/zero123plus-v1.1` model and writes the
six-view grid.

**Typical command:**

```bash
python scripts/run_img_to_mv.py \
  --input-image path/to/input.png \
  --output output.png \
  --steps 28 \
  --guidance-scale 4.0
```

**What the bundled script does:**

- loads `sudo-ai/zero123plus-v1.1` from local cache by default;
- uses the checked-in `diffusers-support/` custom pipeline by default;
- applies the trailing Euler ancestral scheduler when available;
- converts RGBA input onto a gray background and pads non-square input to a
  square canvas;
- uses `num_images_per_prompt=1`, `prompt=''`, `output_type='pil'`,
  `width=640`, and `height=960`;
- keeps the saved montage as the raw model output unless you postprocess it
  separately with the bundled matting helper or an external image tool.

**When to use it:**

- you want the default one-image-to-six-view flow;
- you want the base model without ControlNet conditioning;
- you need a local-only run for a cached model.

**Helpful variants:**

- `--dry-run` to check the plan without loading models;
- `--steps 75` or higher for delicate details;
- `--allow-download` when the cache is incomplete and network access is
  approved;
- `--remove-background --allow-download` when you explicitly approve rembg
  cleanup and its possible first-run model fetch;
- split or postprocess the saved montage separately if you need individual
  tiles or a custom cleanup path.

## 2) Depth ControlNet path

**What it does:** Runs the v1.1 base model with the depth ControlNet attached.

**Typical command:**

```bash
python scripts/run_depth_controlnet.py \
  --input-image path/to/input.png \
  --depth-image path/to/depth.png \
  --output depth_grid.png \
  --conditioning-scale 0.75 \
  --steps 36 \
  --guidance-scale 4.0
```

**What the bundled script does:**

- loads `sudo-ai/zero123plus-v1.1` and
  `sudo-ai/controlnet-zp11-depth-v1` from local cache by default;
- calls `Zero123PlusPipeline.add_controlnet(..., conditioning_scale=0.75)`;
- center-pads the conditioning image to a square RGB image;
- center-pads the depth image to a square RGB image and requires it to match
  the conditioning image after padding;
- keeps the same six-view montage output;
- uses the same trailing Euler ancestral scheduler fallback as the base path.

**When to use it:**

- you already have a depth map for the input view;
- you want tighter geometric guidance than the base model alone;
- you need a direct analogue of the repository's depth example.

**Helpful variants:**

- `--dry-run` to confirm the paths and model ids;
- `--allow-download` when the cache is incomplete and network access is
  approved.

## 3) Normal ControlNet path

**What it does:** Runs the v1.2 base model, then the v1.2 normal ControlNet, and
optionally postprocesses the paired outputs.

**Typical command:**

```bash
python scripts/run_normal_gen.py \
  --input-image path/to/input.png \
  --color-output colors.png \
  --normal-output normals.png \
  --steps 75 \
  --guidance-scale 4.0
```

**What the bundled script does:**

- loads `sudo-ai/zero123plus-v1.2` and
  `sudo-ai/controlnet-zp12-normal-gen-v1` from local cache by default;
- uses the checked-in `diffusers-support/` custom pipeline by default;
- first generates the six-view color grid, then feeds that grid into the
  normal-generator ControlNet;
- calls the bundled `matting_postprocess.py` helper unless you pass
  `--skip-postprocess`;
- writes the postprocessed color cutout and matted normal image by default;
- preserves the raw grids when `--skip-postprocess` is used;
- keeps the same `640 x 960` output size and six-view montage layout.

**When to use it:**

- you want the v1.2 normal-generation path;
- you want a color cutout plus a matted normal image;
- you want the repo's normal-generator analogue without reopening the source
  checkout.

**Helpful variants:**

- `--dry-run` to confirm the plan without loading models;
- `--skip-postprocess` when `pymatting` or `scipy` is unavailable and you only
  want the raw grids;
- `--allow-download` when the cache is incomplete and network access is
  approved.

## 4) Matting-only postprocess

**What it does:** Converts a matching color grid and normal grid into a cutout
and a matted normal image.

**Typical command:**

```bash
python scripts/matting_postprocess.py \
  --rgb colors.png \
  --normal normals.png \
  --output-rgb cutout.png \
  --output-normal normal-matted.png
```

**What the bundled helper does:**

- uses the normal-grid magnitude to build a trimap;
- estimates alpha and foreground on CPU;
- returns a color cutout plus a normal visualization with the alpha applied;
- raises a clear error if `pymatting` or `scipy` is missing.

**When to use it:**

- you already have the paired color and normal grids from the normal workflow;
- you want to rerun matting after changing only the outputs;
- you want a CPU-safe cleanup step with no model loading.

## 5) Optional text-to-image input prep

If you need a synthetic conditioning image before Zero123Plus, create it with a
separate text-to-image tool, then feed the finished square image into the base
or normal workflow.

The repository evidence also includes a source-only SDXL helper for this purpose,
but it is intentionally treated as reference-only here because it is not part of
the core Zero123Plus generation path and it downloads a large model.

Recommended pattern:

1. Create a single isolated subject image.
2. Ensure the image is square and reasonably large.
3. Optionally remove its background in that external tool if you need a clean
   conditioning crop.
4. Pass the resulting image to `run_img_to_mv.py` or `run_normal_gen.py`.
