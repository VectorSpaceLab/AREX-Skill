# Workflows

This sub-skill follows a short, safe sequence: verify the local Python stack, validate the bundled Cityscapes-style folders, parse the CLI options that affect data loading, and smoke one real sample from the bundled fixture.

## 1) Establish the baseline

The README only requires a working Python install, PyTorch, and `dominate` for the project as a whole. For setup-and-data work, the smoke path is CPU-safe and only needs the data stack plus the repo modules.

Verified inspection baseline:

- `torch 2.13.0+cu130`
- `torchvision 0.28.0+cu130`
- `dominate 2.9.1`
- `scikit-learn 1.9.0`
- CUDA available on NVIDIA A100 hardware

Notes:

- `dominate` is a documented repo prerequisite even though the data smoke does not need HTML generation.
- `scikit-learn` is present in the verified environment for later feature workflows, but it is not required for this sub-skill.
- The data smoke should run with `--gpu_ids -1` so a CPU-only inspection environment still works.

## 2) Validate the bundled Cityscapes layout

Run the pure-stdlib checker first:

```bash
python scripts/check_cityscapes_layout.py --repo-root <repo-root>
```

What it checks:

- `datasets/cityscapes/` exists
- `train_label`, `train_inst`, and `train_img` exist and match in sample count
- `test_label` and `test_inst` exist and match in sample count
- `test_img` is optional unless a caller explicitly enables encoded-image inference
- file IDs line up after removing the Cityscapes suffixes

Why this comes first:

- it produces a clearer error than a traceback from `make_dataset`
- it can diagnose malformed `dataroot` and phase-folder naming before any repo import work

Recovery path:

- fix the folder names to the expected `<phase>_label`, `<phase>_inst`, and `<phase>_img` pattern
- keep the Cityscapes sample flat unless you have a strong reason to nest files
- remove stray non-image files or mismatched duplicates

## 3) Parse options and smoke one sample

Run the option and data smoke after the layout check:

```bash
python scripts/check_data_smoke.py --repo-root <repo-root>
```

What it checks:

- `TrainOptions` parses with a CPU-safe `gpu_ids=-1` override
- `TestOptions` parses with `save=False`
- the train sample loads from the bundled Cityscapes fixture
- the test sample loads from the bundled Cityscapes fixture even though `test_img` is absent
- `tensor2label` and `tensor2im` still work on the loaded train sample
- the loader returns the expected keys and image channel counts

Why `save=False` matters:

- `BaseOptions.parse()` writes `opt.txt` and creates the experiment directory unless saving is disabled
- `TestOptions` does not define `continue_train`, so the smoke path must not rely on the default save behavior

Recovery path:

- if parsing tries to select a GPU on a CPU-only machine, pass `--gpu_ids -1`
- if the smoke path creates unwanted directories, point `--checkpoints_dir` and `--results_dir` at a scratch location
- if `batchSize` is not 1, the dataset length helper can truncate tiny fixtures to zero

## 4) Probe the legacy resize-and-crop path only when needed

The repository still contains the legacy `resize_and_crop` branch that calls `torchvision.transforms.Scale` in `data/base_dataset.py`. Modern torchvision releases no longer provide `Scale`.

Optional compatibility probe:

```bash
python scripts/check_data_smoke.py --repo-root <repo-root> --probe-legacy-resize
```

Interpretation:

- if the probe warns about `transforms.Scale`, use `scale_width`, `scale_width_and_crop`, `crop`, or `none` instead
- if you must keep `resize_and_crop`, patch the loader to use `transforms.Resize` or pin a compatible torchvision version

## 5) Hand off to the next workflow

Once the layout and smoke checks pass, training can rely on this sub-skill for data validation, and inference can rely on it for `dataroot` and label/instance naming rules.
