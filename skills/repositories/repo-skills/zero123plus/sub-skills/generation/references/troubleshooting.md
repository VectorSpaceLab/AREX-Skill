# Zero123Plus generation troubleshooting

This reference covers generation-specific failures. If the issue is about demo
serving, Docker, Gitpod, or Cog startup, use the deployment sub-skill.

## Fast triage checklist

1. Confirm the runtime has a CUDA GPU and a CUDA-enabled PyTorch build for real
   generation.
2. Confirm the requested model/ControlNet checkpoints are available in cache
   and the checked-in `diffusers-support/` custom pipeline directory is
   present, or pass `--allow-download` if network access is approved.
3. Confirm the input image is square or that the bundled script can safely pad
   it to square.
4. Confirm you are using the right workflow for the model family and control
   branch.
5. For normal generation, confirm `pymatting` and `scipy` are installed before
   enabling postprocess.

## CUDA and memory issues

**Symptom:** The script fails at `.to("cuda:0")`, crashes with an OOM error, or
runs much slower than expected.

**What to check:**

- The base README example needs roughly `5 GB` VRAM.
- The depth ControlNet example needs roughly `5.7 GB` VRAM.
- The normal-generation path uses both a base model and a ControlNet, so it is
  the heaviest bundled generation workflow.

**Fixes:**

- Reduce image size before running.
- Lower inference steps if the scene allows it.
- Run only one generation job at a time on the GPU.
- Do not expect CPU-only execution to be a practical substitute for the real
  CUDA path.

## Diffusers / huggingface-hub version drift

**Symptom:** Import errors, scheduler problems, or custom-pipeline loading
failures appear after upgrading packages.

**What to check:**

- The repository evidence uses `diffusers==0.20.2`.
- The Cog evidence uses `huggingface-hub==0.18.0`.
- The README explicitly notes that `timestep_spacing='trailing'` is not
  supported in older `diffusers` versions.

**Fixes:**

- Align to the versions in the repository requirements/evidence when debugging.
- If the scheduler warning is the issue, keep the trailing Euler ancestral
  config only on a compatible diffusers release.
- Avoid guessing new APIs from newer library versions unless you have verified
  them locally.

## Local cache failures

**Symptom:** Model loading fails immediately when the script starts, often with a
local-files-only or cache-miss error.

**What to check:**

- The bundled scripts default to local-only loading.
- The bundled generation wrappers use the checked-in `diffusers-support/`
  directory by default. Only use `sudo-ai/zero123plus-pipeline` if you
  intentionally override the local copy.
- The base and ControlNet checkpoints must already be in the Hugging Face cache
  unless `--allow-download` is passed.

**Fixes:**

- Pre-populate the cache and rerun.
- Pass `--allow-download` only if network access is approved.
- If a bundled script complains about missing skill files, verify that the
  generated skill tree was copied intact and not truncated.

## Input image shape / mode problems

**Symptom:** The pipeline raises a `ValueError`, the output looks badly padded,
or the six views are visually inconsistent.

**What to check:**

- `Zero123PlusPipeline.__call__` expects a PIL image.
- `to_rgb_image` accepts only `RGB` and `RGBA`.
- The README recommends square inputs and at least `320 x 320` resolution.

**Fixes:**

- Convert grayscale or palette images to RGB before generation.
- Pad non-square images to a square canvas before calling the pipeline.
- For depth ControlNet, keep the depth map aligned with the conditioning image;
  the bundled wrapper raises if the padded depth image and padded conditioning
  image differ in size.
- If the subject occupies only a tiny region, crop or recenter it before
  generation.

## Matting dependency gaps

**Symptom:** Normal generation fails only when postprocess is enabled, or the
matting helper import fails.

**What to check:**

- `matting_postprocess.py` depends on `pymatting` and `scipy`.
- The live smoke test for `postprocess` succeeded with the expected output
  modes.

**Fixes:**

- Install `pymatting` and `scipy`.
- If you only need raw normal and color grids, rerun with `--skip-postprocess`.
- If the helper import still fails, verify that `numpy` and `Pillow` are
  present too.

## Wrong output interpretation

**Symptom:** The six-view grid appears to be in the wrong order.

**What to check:**

- The bundled scripts treat the grid as a `2 x 3` montage.
- The correct row-major tile order is top-left, top-right, middle-left,
  middle-right, bottom-left, bottom-right.

**Fixes:**

- Split the saved montage row-major if you need individual tiles.
- Do not treat the montage as six separate files unless you split it first.

## Optional background cleanup

**Symptom:** `--remove-background` fails or refuses to run on the base runner.

**What to check:**

- The base runner can call `rembg` only when `--remove-background` is passed.
- The script also requires `--allow-download` for this cleanup path because
  `rembg` may need its own first-run model cache.
- The bundled matting helper is a separate normal-grid cleanup path and does not
  replace `rembg` for arbitrary base outputs.

**Fixes:**

- Install `rembg` and its runtime dependencies if you need inline cleanup.
- Re-run with `--remove-background --allow-download` only after the user
  approves the possible first-time cleanup-model fetch.
- If background cleanup is not needed, omit `--remove-background` and keep the
  core generation path only.

## Helpful messages to surface in code or docs

- "CUDA is not available; this run will use CPU float32 for inspection only."
- "The requested Zero123Plus model is not in local cache; downloads are disabled."
- "The normal matting helper requires pymatting and scipy."
- "The bundled script padded the input image to square RGB before generation."
- "The output is a six-view montage, not six separate files."
- "Use `--skip-postprocess` if you only need the raw normal-grid outputs."

## When to stop and ask the user

Stop instead of guessing when:

- the task requires a real GPU run but no CUDA device is available;
- the user has not approved downloads for Hugging Face or rembg;
- the cache is missing and you do not know whether the model id or the custom
  pipeline is the blocker;
- the requested work is really about demo serving or deployment rather than the
  generation path.
