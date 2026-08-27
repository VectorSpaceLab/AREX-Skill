# EasyOCR Configuration

This reference summarizes the runtime knobs that matter most when using or
troubleshooting EasyOCR.

## Cache and environment variables

EasyOCR resolves its module data directory in this order:

1. `EASYOCR_MODULE_PATH`
2. `MODULE_PATH`
3. `~/.EasyOCR/`

Within that directory it expects:

- `model/` for downloaded detector and recognizer weights.
- `user_network/` for custom recognition bundle files.

The constructor arguments `model_storage_directory` and
`user_network_directory` override those defaults for a specific `Reader`
instance.

## Backend selection

- `gpu=True` tries CUDA first, then MPS, then CPU.
- `gpu=False` forces CPU.
- A string value is treated as the explicit device name.
- `quantize=True` is the default intent for CPU speedups, but see the
  troubleshooting note about the current tuple assignment bug before relying on
  it as a strict off switch.
- `cudnn_benchmark=True` only matters on CUDA paths.

## Detector selection

`Reader` routes through these detector choices in this checkout:

- `craft` — default detector.
- `dbnet18` — alternative DBNet detector.

The lower-level DBNet package also contains `resnet50` support internally, but
`Reader` does not expose `dbnet50` as a public `detect_network` choice here.

## Language and model selection

EasyOCR groups built-in languages into a few families and selects a default
recognizer family from `lang_list`:

- English-only -> `english_g2`
- Latin-family combos -> `latin_g2`
- Thai -> `thai_g1`
- Traditional Chinese -> `zh_tra_g1`
- Simplified Chinese -> `zh_sim_g2`
- Japanese -> `japanese_g2`
- Korean -> `korean_g2`
- Tamil -> `tamil_g1`
- Telugu -> `telugu_g2`
- Kannada -> `kannada_g2`
- Bengali-family -> `bengali_g1`
- Arabic-family -> `arabic_g1`
- Cyrillic-family -> `cyrillic_g2`
- Devanagari-family -> `devanagari_g1`

The built-in language compatibility rules are strict. Some families only allow a
small English-compatible combination, and unsupported codes raise a `ValueError`.

## Supported bundle shape

Custom recognition bundles must keep the same stem across:

- `<stem>.pth`
- `<stem>.yaml`
- `<stem>.py`

`Reader` looks for the Python/YAML files in `user_network_directory` and the
weight file in `model_storage_directory`.

## Useful runtime checks

- `python scripts/inspect_runtime.py` for a fast import/backend smoke.
- `python -m easyocr.cli --help` for the CLI option surface.

## Related references

- `references/api-reference.md` for method signatures.
- `sub-skills/custom-models/references/workflows.md` for bundle loading.
- `sub-skills/dbnet/references/workflows.md` for DBNet-specific setup.
