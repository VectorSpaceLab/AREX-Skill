# Pretrained models and separation

## Loading sources

Asteroid pretrained checkpoints can come from:

- a local serialized model dictionary or `model.pth`
- a public URL
- a Hugging Face model ID
- a Torch Hub entry

The core pattern is `BaseModel.from_pretrained(...)`.

## What `from_pretrained` expects

A serialized checkpoint must include:

- `model_name`
- `model_args`
- `state_dict`

If the serialized dict comes from `model.serialize()`, it already has the right shape for round-tripping.

## Separation entry points

- `separate(model, wav, ...)` is the public helper.
- `model.separate(...)` is the convenience wrapper on `BaseModel`.
- `torch_separate(...)` handles tensors.
- `numpy_separate(...)` handles numpy arrays.
- `file_separate(...)` handles filenames and writes `*_estN.wav` files.

## File and tensor rules

- Tensor inputs may be 1D, 2D, or 3D with time last.
- File inputs are read with `soundfile` first and `librosa` as a fallback when needed.
- Multi-channel files are currently treated conservatively; file separation warns and typically uses the first channel.
- If the file sample rate does not match the model, pass `--resample` or load a model with the correct `sample_rate`.

## Long-file inference

Asteroid's CLI can optionally wrap the model in `LambdaOverlapAdd`.

Use overlap-add when:

- the file is longer than the model's natural receptive field
- you want chunked inference with a controlled window and hop size
- you need a safer path for very long audio files

## Cache behavior

Pretrained downloads use the Asteroid cache directory, which defaults to `~/.cache/torch/asteroid` unless `ASTEROID_CACHE` is set.

## Model lists

`show_available_models()` prints the known public IDs.
`available_models()` returns the full mapping of public names to download URLs.

## When to prefer the CLI

Use `asteroid-infer` when the user wants:

- file-based separation
- output files on disk
- a safe command-line smoke check
- explicit flags such as `--device`, `--resample`, `--ola-window`, or `--force-overwrite`

Use Python APIs when the caller already has tensors or numpy arrays in memory.
