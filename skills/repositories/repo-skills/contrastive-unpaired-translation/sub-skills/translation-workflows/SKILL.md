---
name: translation-workflows
description: "Routes CUT, FastCUT, and SinCUT training, testing, checkpoint
  loading, and result inspection workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# translation-workflows

Use this sub-skill when the task is about the repository's main image-to-image translation flows: training CUT or FastCUT, testing a trained model, loading checkpoints, or running the single-image SinCUT variant.

## Read this when

- The user wants to train CUT or FastCUT on an unaligned dataset.
- The user wants to test a checkpoint and inspect HTML or visdom outputs.
- The user wants the single-image SinCUT path with one image per domain.
- The user asks which `--model`, `--CUT_mode`, or option family to use.
- The user needs to understand checkpoint and results directory conventions.
- The user wants a quick runtime/import smoke check for the repo package.

## What this sub-skill covers

- `train.py` and `test.py` as the public entry points.
- `options/base_options.py`, `options/train_options.py`, and `options/test_options.py`.
- `models/cut_model.py`, `models/sincut_model.py`, `models/networks.py`, and `models/base_model.py`.
- `data/base_dataset.py`, `data/unaligned_dataset.py`, and `data/singleimage_dataset.py` as they affect these workflows.
- `util/visualizer.py` and `util/html.py` for logging and output artifacts.
- Pretrained checkpoint loading through `--checkpoints_dir`, `--name`, `--epoch`, and `--pretrained_name`.

## What this sub-skill does not cover

- Dataset conversion, Cityscapes preprocessing, and image pairing. Read `../data-preparation/` for those tasks.
- Launcher presets and tmux behavior. Read `../experiment-launchers/` for those tasks.
- Legacy CycleGAN as a first-class route. It is mentioned only in troubleshooting.

## Use the bundled helper

Run `scripts/check_runtime.py` when you want a safe import and backend smoke check from a repo root:

```bash
python scripts/check_runtime.py --repo-root . --check-cuda
```

That helper is the quickest way to confirm the installed runtime can import the repo modules that these workflows use.

## Core workflow map

- **CUT/FastCUT training**: choose `--model cut` and set `--CUT_mode CUT` or `--CUT_mode FastCUT`.
- **CUT/FastCUT testing**: use `test.py` with the trained name, checkpoint epoch, and results directory.
- **SinCUT training**: choose `--model sincut` and use a dataset with one image in `trainA` and one image in `trainB`.
- **SinCUT testing**: use the same `--model sincut` checkpoint and the single-image dataset layout.
- **Pretrained inference**: use `--name`, `--epoch`, `--phase`, and `--results_dir` to point at the saved checkpoint and output tree.

## Read next

- `references/cli-reference.md` for the verified flag families and their interactions.
- `references/workflows.md` for end-to-end command sequences and output conventions.
- `references/troubleshooting.md` for missing-dependency, checkpoint, output-path, and legacy-model failures.

## Common routing choices

- If the task is about `train.py` or `test.py` options, stay here.
- If the task is about data folders or conversion scripts, route to `../data-preparation/`.
- If the task is about `python -m experiments` presets, route to `../experiment-launchers/`.

## Quick reminders

- `--gpu_ids -1` is the CPU path.
- `--direction AtoB` is the default; `BtoA` is available when the dataset or experiment needs it.
- `--preprocess`, `--load_size`, and `--crop_size` control input resizing and cropping.
- `--results_dir` is only for testing; training writes checkpoints and web outputs under `--checkpoints_dir`.
- The upstream `--model test` example is stale in this checkout because there is no `models/test_model.py`.
