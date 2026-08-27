# Troubleshooting: Interfaces and Deployment

Use this guide for command-line, notebook, Tkinter, and Replicate/Cog interface failures. For the underlying Python generation API, route to `../text-to-image-generation/SKILL.md`; for cache, dtype, backend, and weight download details, route to `../model-assets-and-runtime/SKILL.md`.

## `min-dalle` command not found

Symptoms:

- Running `min-dalle` or `min_dalle` in a shell fails with command-not-found.
- Package import works but no CLI entry point is installed.

Cause:

- Package metadata does not define console scripts. The repository's command-line behavior came from a source script, not an installed executable.

Recovery:

- Use this sub-skill's bundled helper:

```bash
python scripts/min_dalle_cli_template.py --help
python scripts/min_dalle_cli_template.py --text "artificial intelligence" --no-mega --top-k 256
```

- Add `--run` only after accepting model downloads and compute cost.

## CLI run downloads weights or takes too long

Symptoms:

- A command starts printing model initialization messages and appears stuck.
- Network traffic starts before an image is produced.
- A CI or automated agent unexpectedly downloads large files.

Recovery:

1. Run the bundled CLI template without `--run` first. Dry-run mode validates arguments and prints the plan without importing `MinDalle`.
2. Confirm `models_root`, network access, and available CPU/GPU memory before adding `--run`.
3. Use `--no-mega --grid-size 1 --device cpu --dtype float32` for the smallest compatibility run if downloads are approved.
4. Use the runtime sub-skill to diagnose partial or corrupt cache files.

## `--fp16` or low precision fails

Symptoms:

- The CLI fails on CPU with fp16/bfloat16 errors.
- CUDA autocast or dtype warnings appear.

Recovery:

- Use `--dtype float32` for CPU and initial debugging.
- Use `--fp16`/`--dtype float16` only on CUDA when memory savings are needed.
- Use `--dtype bfloat16` only on hardware and PyTorch builds that support it.

## `--top_k` versus `--top-k`

Symptoms:

- A command copied from older examples uses `--top_k` and fails with the bundled helper.
- A command copied from the bundled helper uses `--top-k` but does not match the source script spelling.

Recovery:

- The upstream source script used underscore spelling: `--top_k`.
- The bundled helper intentionally uses conventional hyphen spelling: `--top-k`.
- When adapting old commands, translate `--top_k 256` to `--top-k 256`.

## Output path surprises

Symptoms:

- The output filename has `.png` appended.
- A directory path writes `generated.png` inside the directory.
- Replicate output uses a sanitized prompt instead of the requested raw text.

Recovery:

- For CLI template output, pass an explicit `--image-path result.png` or directory.
- For Replicate-style basenames, preview with:

```bash
python scripts/replicate_filename_sanitize.py --text "your prompt"
```

- Remember that Replicate intermediate frames append `-iter-N`; final PNG is used only when `save_as_png=True`.

## Notebook/Colab CUDA is missing

Symptoms:

- Notebook setup chooses `device="cuda"` but PyTorch reports no GPU.
- `nvidia-smi` is unavailable or shows no device.

Recovery:

1. Switch the notebook runtime to a GPU-backed accelerator.
2. Reinstall a CUDA-compatible PyTorch/min-dalle environment if needed.
3. If GPU is unavailable, route to CPU-compatible settings: Mini, `grid_size=1`, `dtype=torch.float32`, and expect slow generation.

## Tkinter GUI fails in automation

Symptoms:

- `_tkinter.TclError: no display name and no $DISPLAY environment variable`.
- The UI blocks waiting for button clicks.
- Save fails because `generated/` does not exist.

Recovery:

- Do not run the GUI in headless automation. Use the bundled CLI template or direct API recipes.
- If the user explicitly wants GUI behavior, provide a display server and ensure the output directory exists before saving.
- Treat GUI generation as an interactive, model-downloading workflow rather than a smoke test.

## Cog or Replicate setup fails

Symptoms:

- Missing `cog` package or `BasePredictor` import.
- CUDA/PyTorch wheel mismatch.
- Cog image build fails on CUDA version or Python version.
- Predictor setup fails because `device="cuda"` is unavailable.

Recovery:

1. Do not verify Cog deployment in the base CPU package environment.
2. Use the deployment evidence as a starting point: Python 3.10, CUDA-enabled Cog image, compatible PyTorch CUDA wheel, and package pins from the Cog configuration when reproducing that exact deployment.
3. If using current package version instead of the older deployment pin, rebuild and test the Cog image explicitly.
4. Run filename helper self-tests locally only for pure string behavior; they do not prove model-serving readiness.

## Progressive output count seems wrong

Symptoms:

- Replicate emits several intermediate files and one final file.
- Notebook display updates around 8 times.

Cause:

- Generation has 256 image-token steps and progressive output yields every 32 tokens plus the final result. The Replicate wrapper labels intermediate frames until the eighth frame is considered final.

Recovery:

- Set `progressive_outputs=False` when only a final image is needed.
- In custom scripts, count yielded stream items rather than hard-coding file names unless matching the Replicate predictor behavior intentionally.
