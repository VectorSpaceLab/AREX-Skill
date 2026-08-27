# EasyOCR Troubleshooting

This is the cross-cutting troubleshooting page for EasyOCR. Use the sub-skill
troubleshooting pages for workflow-specific fixes.

## Import and install failures

### `ModuleNotFoundError` for `torch` or `torchvision`

EasyOCR depends on PyTorch. Install a wheel that matches your backend before or
alongside EasyOCR.

### `ImportError` for image or geometry libraries

If the package imports fail around image or geometry dependencies, re-check the
base runtime install and the selected detector path. Common problem packages
include `opencv-python-headless`, `Pillow`, `Shapely`, and `pyclipper`. DBNet
paths also need the geometry stack used by the DBNet package.

## Model cache and download failures

### Missing weight files

If a `Reader` construction fails because a `.pth` file is missing, either allow
model downloads or pre-populate the cache directory and retry.

### Corrupt cached models

If checksum verification fails, delete the affected file from the model cache
and let EasyOCR re-download it.

### `download_enabled=False`

With downloads disabled, a missing model file becomes a hard error. That is
intentional and useful for offline reproducibility checks.

## Backend and runtime quirks

### GPU fallback

`gpu=True` does not guarantee CUDA. EasyOCR falls back to MPS or CPU when the
requested accelerator is not available.

### Quantization off-switch bug

The current source stores `Reader.quantize` as a one-item tuple. As a result,
`quantize=False` is not a reliable off switch for downstream checks that only
inspect truthiness. Verify the actual behavior if you need a strict non-
quantized CPU path.

### Legacy `readtextlang`

`readtextlang` expects a local `characters/` directory and is brittle outside
that legacy layout. Prefer `readtext` or `readtext_batched` for ordinary use.

### CLI boolean and list flags

The current CLI parser uses brittle `argparse` types for several flags:

- `--gpu`, `--download_enabled`, `--detector`, `--recognizer`, `--verbose`,
  `--quantize`, and `--paragraph` all parse through `type=bool`, so any
  non-empty string becomes truthy.
- `--rotation_info` uses `type=list`, which does not parse a list literal the
  way users usually expect.

Use the Python API for reliable falsey or list-valued options.

## Language compatibility errors

If `Reader` raises a compatibility error for a language combination, reduce the
`lang_list` to one of the supported family combinations and keep English as the
shared companion language when the documentation requires it.

## When to escalate to a sub-skill

- DBNet compile or detector issues -> `sub-skills/dbnet/references/troubleshooting.md`
- Custom recognition bundle layout issues -> `sub-skills/custom-models/references/troubleshooting.md`
- OCR workflow or CLI misuse -> `sub-skills/inference/references/troubleshooting.md`
