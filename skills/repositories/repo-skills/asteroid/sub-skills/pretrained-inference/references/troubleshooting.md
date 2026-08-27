# Pretrained inference troubleshooting

## Common failures

- **`ModuleNotFoundError: requests`**
  - Run `python scripts/install_runtime.py` from the skill output.
  - This is the most common missing extra for pretrained-model loading.

- **`File not found` or empty glob results**
  - Confirm the `--files` argument expands to real filenames.
  - Try a fully qualified path before using a directory or wildcard.

- **Sample-rate mismatch**
  - Use `--resample` when the file sample rate differs from the model's `sample_rate`.
  - If the model was serialized without a sample rate, inspect the checkpoint or register one only for legacy checkpoints.

- **Existing output files prevent overwrite**
  - Use `--force-overwrite`.

- **`soundfile` cannot read the file**
  - Prefer WAV/FLAC/OGG.
  - The runtime bootstrap helper installs `librosa` so the fallback loader is available.

- **Long-file outputs sound misaligned**
  - Wrap the model in `LambdaOverlapAdd`.
  - Tune `--ola-window`, `--ola-hop`, and `--ola-no-reorder`.

- **CUDA is unavailable unexpectedly**
  - Pass `--device cpu` to force CPU inference.
  - If you expected GPU support, confirm that `torch.cuda.is_available()` is true in the active environment.
