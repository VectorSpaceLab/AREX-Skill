# Troubleshooting Image Translation Workflows

Use this when CycleGAN, DiscoGAN, or Pix2Pix tasks fail in Keras-GAN.

## Quick diagnosis table

| Symptom | Likely cause | What to do |
|---|---|---|
| `ModuleNotFoundError: No module named 'keras_contrib'` | CycleGAN/DiscoGAN import `InstanceNormalization` from `keras_contrib`. | Use a legacy environment with `keras-contrib`; do not replace it silently because layer behavior affects checkpoints. |
| `AttributeError: module 'scipy.misc' has no attribute 'imread'` or `imresize` | Newer SciPy removed image helpers used by all three loaders. | Use SciPy 1.2.x in the legacy environment, or adapt loaders to Pillow/skimage and document the change. |
| `ModuleNotFoundError: No module named 'data_loader'` | Scripts expect to run from their own directory with local `data_loader.py`. | Run from the workflow directory, set `PYTHONPATH` to include the copied workflow directory, or convert to package-relative imports in an adaptation. |
| No batches, no progress, or `n_batches` is 0/1 | Too few files for `int(num_files / batch_size)` plus `range(n_batches - 1)`. | Add more files or reduce `batch_size`. For smoke training, use at least `2 * batch_size` files in every required training split. |
| `ValueError: 'a' cannot be empty unless no samples are taken` | Loader glob matched no files. | Validate with `check_dataset_layout.py`; confirm split names and working directory. |
| PatchGAN label shape mismatch in `train_on_batch` | `img_rows` changed but `disc_patch` or discriminator output changed inconsistently. | Recompute `patch = int(img_rows / 2**4)` after resolution changes and recreate `valid`/`fake` labels. |
| Pix2Pix runs but output direction is wrong | Stock model conditions on B and generates A from side-by-side images split left=A, right=B. | Swap halves in the dataset, change the training targets, or rename variables in a documented adaptation. |
| Pix2Pix with `trainA/trainB` folders fails | Stock loader expects side-by-side images in `train`, `test`, and `val`, not separate domains. | Convert pairs into one side-by-side file per sample or write a custom loader. |
| DiscoGAN layout confusion | README describes cross-domain translation, but stock loader reads side-by-side `train/val` images. | Use the stock paired layout for this repo code; use CycleGAN or a deliberate loader adaptation for unpaired folders. |
| `images/<dataset>/...png` not produced | Sampling split is missing, Matplotlib backend failed, or process wrote relative to a different working directory. | Validate the sample split, use a non-interactive Matplotlib backend if needed, and check the current working directory. |

## Dataset layout failures

Run the bundled validator first:

```bash
python sub-skills/image-translation/scripts/check_dataset_layout.py \
  --dataset-root datasets/facades \
  --workflow pix2pix \
  --min-files 1 \
  --check-images
```

The validator exits nonzero for missing directories, too few image files, and
Pix2Pix/DiscoGAN side-by-side images that Pillow can prove are malformed. It
prints warnings for questionable but not necessarily fatal image properties such
as odd widths.

Common fixes:

- CycleGAN: create `trainA`, `trainB`, `testA`, and `testB`; do not use `train/`
  for the stock CycleGAN loader.
- DiscoGAN as shipped: create paired side-by-side `train` and `val`; do not rely
  on `trainA/trainB` unless you rewrite the loader.
- Pix2Pix: create paired side-by-side `train`, `test`, and `val`; separate A/B
  folders are not read.

## Legacy dependency failures

The source code predates modern TensorFlow/Keras packaging. A compatible
verified runtime family for these scripts included Python 3.7-era, TensorFlow
1.15.x, Keras 2.2.x, `keras-contrib` 2.0.x, NumPy 1.18.x, SciPy 1.2.x,
Matplotlib, Pillow, and scikit-image. Treat this as a legacy pinned stack rather
than a current installation recommendation.

Do not upgrade one package at a time in a user environment. If a modern project
needs these models, prefer a scratch legacy environment or port the code to a
maintained framework with explicit tests.

## Training-loop pitfalls

- Full training is slow and should not be used as a generated-skill verification
  gate.
- All three scripts create adversarial label tensors as `np.ones((batch_size,) +
  disc_patch)` and `np.zeros((batch_size,) + disc_patch)`. If the final batch is
  smaller than `batch_size`, the scripts do not adjust labels; use fixed-size
  batches from the existing loaders or adapt carefully.
- The loaders sample with `np.random.choice(..., replace=False)` for CycleGAN
  batch paths. If a split has fewer usable files than requested, it fails.
- Random horizontal flips alter reproducibility unless you seed NumPy and the
  backend.

## Output and path pitfalls

The scripts write sample PNGs to relative directories:

- CycleGAN: `images/apple2orange/<epoch>_<batch_i>.png` by default.
- DiscoGAN: `images/edges2shoes/<epoch>_<batch_i>.png` by default.
- Pix2Pix: `images/facades/<epoch>_<batch_i>.png` by default.

They also include `saved_model/` directories in the repository layout, but the
shown training scripts do not save checkpoints by default. If you add checkpoint
saving, make the output path explicit and keep it outside generated skill
runtime files.

## When to adapt instead of run unchanged

Adapt the scripts when:

- The caller needs configurable dataset names, paths, or output directories.
- The caller has a modern TensorFlow/Keras environment.
- Pix2Pix data is not side-by-side or the desired direction is A-to-B rather
  than B-to-A.
- DiscoGAN should use truly unpaired A/B folders instead of the stock paired
  side-by-side loader.
- The task needs deterministic CI-style tests. Replace stochastic training with
  dataset validation, constructor smoke checks, and controlled one-step tests on
  tiny synthetic data.
