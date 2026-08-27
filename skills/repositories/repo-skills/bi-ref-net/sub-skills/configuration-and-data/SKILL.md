---
name: configuration-and-data
description: "Route BiRefNet configuration, task selection, and dataset layout checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# configuration-and-data

Use this sub-skill when you need to inspect or adapt `Config`, choose task/testset/backbone/loss settings, or prepare a BiRefNet-style dataset tree before training or evaluation.

## Handles
- `Config()` defaults and mutable knobs
- Built-in task names: `DIS5K`, `COD`, `HRSOD`, `General`, `General-2K`, `Matting`
- Data layout under `<data-root>/<task>/<dataset>/{im,gt}`
- `MyData(...)` pairing, augmentation, dynamic-size collation, and `background_color_synthesis`
- Auxiliary classification filename assumptions
- Safe dataset-tree validation for image/label pairing

## Use the bundled scripts
- `scripts/birefnet_config_summary.py` — print distilled config defaults, task profiles, backbone choices, and optional checkout-inspected schedule notes.
- `scripts/birefnet_dataset_check.py` — validate a BiRefNet dataset tree, pair `im`/`gt` files, and report missing or duplicate basenames.

## Read next
- `references/configuration.md` for task profiles, default values, path knobs, precision/compile, losses, and schedule extraction.
- `references/data-formats.md` for the exact dataset tree, image/label pairing rules, dynamic-size collation, and auxiliary classification filenames.
- `references/troubleshooting.md` when data folders are missing, counts differ, Config behaves differently outside a checkout, or dynamic-size training is unstable.

## Recommended operating flow

1. Identify the task family (`DIS5K`, `COD`, `HRSOD`, `General`, `General-2K`, or `Matting`) and decide whether the user is changing data, model shape, or only paths.
2. Run `scripts/birefnet_config_summary.py` to confirm the distilled defaults; add `--repo-root` only when the user has a current checkout and wants live schedule inspection.
3. Validate each dataset with `scripts/birefnet_dataset_check.py --data-root <root> --task <task> --dataset <name>` before recommending training or evaluation.
4. If the user changes `config.bb`, `size`, `dynamic_size`, `lambdas_pix_last`, `mixed_precision`, or `compile`, route to the sibling workflow that depends on that field before finalizing a command.
5. Keep config edits explicit and reversible; BiRefNet stores many active choices directly in `config.py`, so hidden edits can affect model loading, training, and evaluation together.

## Done criteria

- The data tree has matching `im` and `gt` basenames for every selected dataset.
- The selected task/testset/training-set names match the user's directory names.
- Any dynamic-size, `load_all`, auxiliary classification, or background synthesis assumptions are recorded before training begins.
- Architecture-sensitive config changes have been checked with `model-architecture`.

## Route out
- Model internals and patch helpers -> `../model-architecture/SKILL.md`
- Full training and evaluation commands -> `../training-and-evaluation/SKILL.md`
- Image/video outputs and refinement -> `../inference-and-postprocessing/SKILL.md`
