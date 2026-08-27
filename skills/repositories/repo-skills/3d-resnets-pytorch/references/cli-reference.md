# CLI reference

This repository is driven by a small set of bundled helpers and sub-skill scripts.
Use these wrappers instead of pointing future agents at the source checkout.

## Root helpers

| Script | Purpose | Typical use |
| --- | --- | --- |
| `scripts/check_imports.py` | Imports the core source modules from a checkout and applies the temporary legacy `Scale` alias when needed | Quick environment and compatibility check |
| `scripts/check_main_help.py` | Prints the full `main.py` help output through the same compatibility shim | Discover the training / inference CLI flags |
| `scripts/run_main.py` | Forwards arguments into the repository CLI after preparing the checkout | Train, resume, fine-tune, validate, or run inference |

## Root helper examples

```bash
python scripts/check_imports.py --repo-root .
python scripts/check_main_help.py --repo-root .
python scripts/run_main.py --repo-root . --dataset kinetics --model resnet --model_depth 50 --n_classes 700
```

## Training and inference helpers

| Script | Purpose |
| --- | --- |
| `sub-skills/training-and-inference/scripts/evaluate_results.py` | Score averaged per-video recognition JSONs against a ground-truth JSON |
| `sub-skills/training-and-inference/scripts/strip_dataparallel.py` | Remove `module.` prefixes from checkpoint state dicts |

## Data-preparation helpers

| Script | Purpose |
| --- | --- |
| `sub-skills/data-preparation/scripts/extract_video_frames.py` | Extract RGB JPEG frame trees |
| `sub-skills/data-preparation/scripts/extract_video_hdf5.py` | Convert raw videos to RGB HDF5 |
| `sub-skills/data-preparation/scripts/build_annotation_json.py` | Build dataset JSONs and add ActivityNet fps fields |

## Argument conventions that matter

- Use `--repo-root` when the current working directory is not the repo checkout you want to inspect.
- Use `--no-scale-shim` only when you know the checkout already has a compatible torchvision release.
- For training and inference, pass the same CLI flags documented in the training-and-inference sub-skill.
- For data preparation, choose the dataset mode first and then add `--video-type`, `--path-map`, `--include-video-paths`, `--strict`, or `--pretty` as needed.
