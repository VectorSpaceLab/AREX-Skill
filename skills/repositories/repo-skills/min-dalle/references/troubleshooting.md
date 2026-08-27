# Troubleshooting: min(DALL·E) Package Setup

Use this root guide for package installation, imports, and cross-cutting runtime triage. Route workflow-specific issues to the nearest sub-skill.

## Package import fails

Symptoms:

- `ModuleNotFoundError: No module named 'min_dalle'`.
- `from min_dalle import MinDalle` fails.

Recovery:

1. Install the distribution package:

   ```bash
   python -m pip install min-dalle
   ```

2. Verify the import without constructing a model:

   ```bash
   python - <<'PY'
   from min_dalle import MinDalle
   print(MinDalle)
   PY
   ```

3. If the installed package is editable or local, ensure the active Python environment is the one where dependencies are installed.

## Dependency import fails

The package metadata requires these runtime dependencies: `torch>=1.11`, `typing_extensions>=4.1`, `numpy>=1.21`, `pillow>=7.1`, `requests>=2.23`, and `emoji`.

Symptoms:

- Missing `torch`, `PIL`, `requests`, `emoji`, `numpy`, or `typing_extensions`.
- `pip check` reports incompatible packages.

Recovery:

```bash
python -m pip install --upgrade "torch>=1.11" "typing_extensions>=4.1" "numpy>=1.21" "pillow>=7.1" "requests>=2.23" emoji
python -m pip check
python scripts/inspect_min_dalle_api.py
```

Choose a CPU or CUDA PyTorch build deliberately. A CPU-only PyTorch install can import the package but does not verify CUDA generation.

## Model construction downloads assets

Symptoms:

- A simple-looking script hangs or downloads during `MinDalle(...)` construction.
- Offline runs fail before generation starts.

Cause:

- The constructor always initializes tokenizer assets, and `is_reusable=True` can initialize/download all major weights immediately.

Recovery:

- For no-download checks, run `scripts/inspect_min_dalle_api.py` or the runtime sub-skill's tokenizer smoke instead of constructing `MinDalle`.
- Before full generation, use [../sub-skills/model-assets-and-runtime/SKILL.md](../sub-skills/model-assets-and-runtime/SKILL.md) to inspect cache layout and backend constraints.

## CUDA expectations are unclear

Symptoms:

- Generation is too slow on CPU.
- CUDA is requested but unavailable.
- A CUDA machine imports `torch`, but `torch.cuda.is_available()` is false.

Recovery:

1. Run:

   ```bash
   python scripts/inspect_min_dalle_api.py --check-cuda
   ```

2. If CUDA is unavailable, use CPU/Mini/small-grid settings for compatibility checks only.
3. If CUDA generation is required, install a CUDA-enabled PyTorch build compatible with the host driver and verify a tiny CUDA tensor allocation before running min(DALL·E).
4. Do not treat CPU import success as proof that CUDA generation or Replicate deployment works.

## CLI assumptions are wrong

Symptoms:

- The shell command `min-dalle` does not exist.
- A copied command uses `--top_k`, but a bundled helper expects `--top-k`.

Recovery:

- Use [../sub-skills/deployment-and-interfaces/SKILL.md](../sub-skills/deployment-and-interfaces/SKILL.md). The package has no installed console entry point; use the bundled CLI template and translate source-script `--top_k` to helper `--top-k`.

## Generation code returns the wrong output type

Symptoms:

- Code expects `generate_images()` to return a PIL image but receives a tensor.
- `Image.fromarray()` fails on a GPU float tensor.

Recovery:

- Use [../sub-skills/text-to-image-generation/SKILL.md](../sub-skills/text-to-image-generation/SKILL.md) for exact output contracts. Convert tensor batches with `.detach().clamp(0, 255).to(torch.uint8).cpu().numpy()` before `PIL.Image.fromarray()`.

## When to stop and ask for approval

Ask before:

- Downloading full model weights or running generation in constrained automation.
- Installing a CUDA PyTorch build, Cog image, or other large backend-specific dependency.
- Running GUI/Tkinter workflows in a headless environment.
- Treating optional Replicate/Cog deployment as verified.
