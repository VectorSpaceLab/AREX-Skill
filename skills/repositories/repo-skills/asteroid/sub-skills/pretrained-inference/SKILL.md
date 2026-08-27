---
name: pretrained-inference
description: "Load Asteroid pretrained checkpoints and separate audio tensors,
  arrays, or files."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# Pretrained inference

Use this sub-skill when the user wants to apply an existing Asteroid model rather than build or train one.

## Typical triggers

- `asteroid-infer`
- `BaseModel.from_pretrained(...)`
- `model.separate(...)`, `separate(...)`, `numpy_separate(...)`, `torch_separate(...)`, or `file_separate(...)`
- Torch Hub, Hugging Face IDs, Zenodo URLs, or local `model.pth` files
- `available_models()` / `show_available_models()`
- long-file chunking with `LambdaOverlapAdd`

## What to do first

1. Identify the checkpoint source:
   - local serialized dict or `model.pth`
   - public URL
   - Hugging Face model ID
   - Torch Hub usage
2. Decide whether the user wants:
   - a tensor/numpy result
   - files written next to the inputs
   - a temporary smoke check only
3. Choose the device explicitly when ambiguity matters.
   - `asteroid-infer` defaults to CUDA if available, otherwise CPU.
   - Long file inference can optionally be wrapped in `LambdaOverlapAdd`.

## Standard workflow

- Read `references/pretrained-models.md` for the model-loading matrix and cache behavior.
- Read `references/cli-reference.md` for the public CLI flags and file-handling rules.
- Read `references/troubleshooting.md` when the model source, file type, or device choice looks suspicious.
- Use `scripts/smoke_pretrained_inference.py` for a tiny local round-trip on tensors and files.

## Common path choices

- **Local checkpoint**: call `BaseModel.from_pretrained(path_or_conf)`.
- **Public model name**: resolve through `BaseModel.from_pretrained(...)` or Torch Hub.
- **Audio files**: call `model.separate(path)` or the CLI with `--files`.
- **Long files**: wrap the model in `LambdaOverlapAdd` before separating.

## Output expectations

- Tensor or numpy inputs return separated arrays with a source dimension.
- File inputs create `*_estN.wav` outputs unless an output directory is set.
- The CLI should print or save separated waveforms without requiring the original repository checkout.

## Troubleshooting reminders

- `requests` missing usually means the bundled runtime bootstrap was skipped; run `python scripts/install_runtime.py` from the skill output.
- `librosa` missing usually means `asteroid.data` or audio-visual helpers were imported without the optional audio dependency.
- Sample-rate mismatches usually need `--resample` or a model whose `sample_rate` matches the input.
- Existing output files need `--force-overwrite`.

## Inputs to inspect

- checkpoint source and format
- sample rate and channel count
- whether the request is tensor, numpy, file, or folder based
- whether the user wants a one-off smoke or a reusable separation recipe

## Smoke sequence

1. Load or serialize a tiny model.
2. Round-trip it through `from_pretrained(...)`.
3. Run a tiny tensor separation call.
4. Run a tiny file separation call if files are involved.
5. Add overlap-add only when the request mentions long files or chunking.

## What to avoid

- Do not tell the user to rely on the original checkout at runtime.
- Do not imply that a remote model download is guaranteed to work offline.
- Do not hide a sample-rate mismatch behind a vague error message.
- Do not use model-sharing guidance unless the user is actually preparing an upload.

## Output shapes to remember

- tensor and numpy paths keep a source dimension in the output
- file paths write WAV files next to the input or in the requested output directory
- overlap-add should preserve the source dimension while chunking long signals

## Good questions to ask when unclear

- Is the checkpoint local or remote?
- Do you want files or in-memory arrays?
- Should the output be forced onto CPU or a specific CUDA device?
- Is this a short clip or a long-file inference problem?
