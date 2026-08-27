# Troubleshooting

Use this as the quick failure map for setup, data layout, and loader smoke issues.

## Missing labels, instances, or images

**Symptom**: `check_cityscapes_layout.py` says a folder is missing, empty, or has a sample-count mismatch.

**Likely cause**: the `dataroot` is wrong or the phase folder names do not match what `AlignedDataset` expects.

**Fix**:

- for label-based data, use `<phase>_label`, `<phase>_inst`, and `<phase>_img`
- for label-free translation, use `<phase>_A` and `<phase>_B`
- keep the bundled Cityscapes sample flat and remove stray non-image files
- rerun the pure layout checker before trying the smoke loader again

## Malformed dataroot or phase folder names

**Symptom**: the loader raises an assertion or `make_dataset` says a directory is not valid.

**Likely cause**: the root path points at the wrong checkout level or the phase name does not match the folder prefix.

**Fix**:

- point `dataroot` at the dataset root, not at a leaf folder
- keep `phase` aligned with the folder prefix you actually created
- remember that `AlignedDataset` uses `phase + '_label'`, `phase + '_inst'`, and `phase + '_img'` for the Cityscapes-style path

## Legacy resize-and-crop failure

**Symptom**: `AttributeError: module 'torchvision.transforms' has no attribute 'Scale'`.

**Likely cause**: `data/base_dataset.py` still uses the deprecated `resize_and_crop` branch and the installed torchvision is modern.

**Fix**:

- prefer `scale_width`, `scale_width_and_crop`, `crop`, or `none`
- if you must keep `resize_and_crop`, patch the transform branch to `torchvision.transforms.Resize`
- rerun the smoke helper with `--probe-legacy-resize` if you want a visible compatibility check

## CPU-versus-CUDA confusion

**Symptom**: a data-only inspection tries to select a GPU or the user assumes CUDA is required for the smoke checks.

**Likely cause**: the default `gpu_ids=0` from `BaseOptions` was left unchanged.

**Fix**:

- pass `--gpu_ids -1` for setup-and-data smoke checks
- keep the layout checker pure stdlib; it does not need CUDA at all
- remember that the repo's training and inference workflows do need CUDA, but the data smoke does not

## Missing repo import path or `.pth` exposure

**Symptom**: imports from `options`, `data`, `models`, or `util` fail even though the checkout exists.

**Likely cause**: the temporary inspection environment does not expose the checkout on `sys.path` or via a `.pth` file.

**Fix**:

- run `check_data_smoke.py` with `--repo-root <repo-root>` so it can add the checkout to `sys.path`
- if you are working manually, add the checkout root to `PYTHONPATH`
- if the private inspection env is supposed to expose the checkout and does not, refresh the environment handoff before continuing

## `TestOptions` parser error about `continue_train`

**Symptom**: `TestOptions().parse()` fails with an `AttributeError` for `continue_train`.

**Likely cause**: the default save path in `BaseOptions.parse()` assumes the train-only flag exists.

**Fix**:

- call `TestOptions().parse(save=False)` in smoke utilities and scripts
- keep `save=True` only for `TrainOptions` when you actually want the experiment options written to disk

## Dataset length is unexpectedly zero

**Symptom**: the loader appears empty even though the folders contain images.

**Likely cause**: `AlignedDataset.__len__` floors the length to a multiple of `batchSize`.

**Fix**:

- keep `batchSize=1` for tiny smoke fixtures
- if you need a larger batch later, ensure the fixture size is still large enough to survive the floor operation

## Optional feature-cache folder is missing

**Symptom**: a later feature workflow asks for `<phase>_feat`.

**Likely cause**: `load_features` is enabled, but the feature cache was not generated.

**Fix**:

- consult the instance-features sub-skill for the feature-cache layout and generation flow
- do not add feature-generation logic here
