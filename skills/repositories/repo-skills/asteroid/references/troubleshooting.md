# Troubleshooting

## Import and install issues

- **`ModuleNotFoundError: requests` when importing `asteroid`**
  - Run `python scripts/install_runtime.py` again or install `scripts/runtime_requirements.txt` directly.
  - The generated runtime bootstrap installs `requests` explicitly because the public package metadata does not always cover that hub path.

- **`ModuleNotFoundError: librosa` when importing `asteroid.data`**
  - Run `python scripts/install_runtime.py` again or install `scripts/runtime_requirements.txt` directly.
  - `asteroid.data.avspeech_dataset` imports it at module import time.

- **`soundfile` cannot open an audio file**
  - Prefer WAV/FLAC/OGG for the built-in inference paths.
  - Run `python scripts/install_runtime.py` from the skill output so the `librosa` fallback loader is available for formats that `soundfile` cannot handle directly.
  - Make sure libsndfile is available if your platform does not bundle it with the wheel.

- **`pip check` passes but an import still fails**
  - Some dependencies are runtime-imported by the package but not declared in setup metadata.
  - Run `python scripts/install_runtime.py` from the skill output first; it installs the missing hub and dataset-import extras from `scripts/runtime_requirements.txt`.

## Inference and pretrained-model issues

- **`asteroid-infer` cannot find files**
  - Use `--files` with explicit filenames, directory names, or globs.
  - Add `--resample` if the file sample rate does not match the model.

- **Model output files already exist**
  - Pass `--force-overwrite`.

- **Unexpected device choice**
  - `asteroid-infer` defaults to CUDA when available, otherwise CPU.
  - Pass `--device cpu` or `--device cuda:0` explicitly to avoid ambiguity.

- **Long files sound wrong when chunked**
  - Use `--ola-window` and `--ola-hop` together.
  - If reordering is not wanted, add `--ola-no-reorder`.

- **HF or Zenodo model download problems**
  - Inspect the model ID/path first and prefer cached local files when possible.
  - If network access is unavailable, use a local `model.pth` or serialized dict.

## Training and recipe issues

- **Recipe scripts want missing dataset packages**
  - Some dataset helpers are external (`sms_wsj`, `lazy_dataset`, `opencv-python`, etc.).
  - Install only the package needed by the selected recipe instead of broad extras.

- **Recipe stages or storage directories are confusing**
  - Most `run.sh` recipes are stage-based.
  - Set the required storage/data path before starting from stage 0.
  - Resume from a later stage when the data has already been prepared.

- **GPU is unavailable**
  - Many Asteroid workflows still work on CPU.
  - The recipes and tests often branch on `torch.cuda.is_available()`.

## Publishing issues

- **`asteroid-upload` or `upload_publishable` asks for credentials**
  - Provide `ACCESS_TOKEN`, `uploader`, and usually `git_username`.
  - Never treat the upload helper as a safe default smoke check.

- **Legacy checkpoints need a sample rate**
  - Use `asteroid-register-sr` only for older checkpoints that were saved without `sample_rate`.

## Known inspection gotchas

- `asteroid.data` is more fragile to missing optional dependencies than the top-level `asteroid` import.
- Some music or audio-visual recipes are memory heavy or data heavy; keep them reference-only unless the user specifically wants recipe execution guidance.
