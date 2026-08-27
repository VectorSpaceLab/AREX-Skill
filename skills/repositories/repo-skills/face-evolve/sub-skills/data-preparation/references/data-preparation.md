# face.evoLVe data preparation

This reference covers the dataset facts a future agent needs before using
face.evoLVe training, validation, or balancing workflows. It is intentionally
self-contained: use the bundled scripts in `../scripts/` for local checks rather
than relying on original repository scripts.

## Identity-folder layout

face.evoLVe expects one immediate directory per identity/class and image files
inside that directory.

```text
<data-root>/
  identity_0001/
    image_0001.jpg
    image_0002.jpg
  identity_0002/
    image_0001.png
```

Framework-specific notes:

- **PyTorch** training uses `torchvision.datasets.ImageFolder`. In the original
  training flow the configured training parent contains an `imgs/` child, so the
  ImageFolder root is effectively `<DATA_ROOT>/imgs`. If the user gives a root
  that already contains identity folders, validate that root directly.
- **PaddlePaddle** `NormalDataset` and the balancing dataset use the supplied
  data root directly; immediate child folders become integer classes and the
  loader reads every listed image with OpenCV-style image loading.
- Keep validation `bcolz` pairs separate from training ImageFolder roots; the
  validation layout is described below.

## Class-folder rules

- Use one folder per face identity; the folder name is the class name.
- Put image files directly under the identity folder; do not add another nested
  train/val/image level inside each identity.
- Keep only image files in class folders. The bundled checker accepts common
  image extensions such as `.jpg`, `.jpeg`, `.png`, `.bmp`, `.webp`, `.gif`,
  `.tif`, and `.tiff`.
- Remove hidden entries such as `.DS_Store` and `.ipynb_checkpoints`; they can
  make class counts wrong and can break PaddlePaddle loaders that try to open
  every listed file.
- Preserve class names and roots across a run. The PaddlePaddle source assigns
  integer labels from directory listing order, so changing or inserting folders
  after checkpoint creation can change labels.

## Low-shot balancing

A low-shot identity is a class whose valid image count is below the chosen
`min_num` threshold. The public README describes removing low-shot classes as a
balancing option, while the training utilities also support weighted sampling.
Choose the less destructive option that matches the user's goal:

- If the user wants to keep all identities but reduce imbalance during training,
  route to the training sub-skill and use weighted sampling.
- If the user wants to physically prune tiny classes, use the safe bundled
  workflow below.

Safe pruning sequence:

1. Run `scripts/check_image_folder.py --root <train-root> --min-num <N>` and
   review hidden files, empty classes, and classes below threshold.
2. Run `scripts/remove_lowshot_safe.py --root <train-root> --min-num <N>` without
   `--apply`; this is a dry-run and reports what would be removed.
3. Prefer `--copy-to <new-root> --apply` so the source dataset remains intact.
4. Re-run the checker on the pruned root and compare class counts before
   training.

The safe helper removes classes with **fewer than** `min_num` valid images. It
counts image files, not hidden files or unrelated metadata files.

## RandAugment and augmentation notes

face.evoLVe includes a RandAugment-style helper as concept evidence rather than
as a mandatory data-prep CLI. The policy samples a number of operations and
magnitudes from transformations such as autocontrast, equalize, rotate,
solarize, color, posterize, contrast, brightness, sharpness, shearX/shearY, and
translateX/translateY.

Use augmentation only after folder validation. For PyTorch training, the normal
pipeline resizes from 112-based scale to 128, applies random crop, horizontal
flip, converts to tensor, and normalizes with mean/std around 0.5. PaddlePaddle
normalization uses 127.5-style mean/std values in its config. If adding
RandAugment, test a tiny sample visually first because rotation/translation and
color magnitudes can harm aligned face crops if they are too strong.

## Validation bcolz pair layout

Validation data are not ImageFolder class roots. The validation utilities expect
benchmark pairs as a `bcolz` carray directory plus a NumPy boolean pair list:

```text
<validation-root>/
  lfw/                 # bcolz carray directory
  lfw_list.npy         # issame flags for lfw pairs
  cfp_ff/
  cfp_ff_list.npy
  cfp_fp/
  cfp_fp_list.npy
  agedb_30/
  agedb_30_list.npy
  calfw/
  calfw_list.npy
  cplfw/
  cplfw_list.npy
  vgg2_fp/
  vgg2_fp_list.npy
```

The standard face.evoLVe validation set names are `lfw`, `cfp_ff`, `cfp_fp`,
`agedb_30`, `calfw`, `cplfw`, and `vgg2_fp`. Each `<name>_list.npy` must match
its carray pair order. Missing one pair blocks only that benchmark; it does not
prove the training ImageFolder root is wrong.

`bcolz` itself is an environment dependency and can be sensitive to Python/numpy
compatibility. If import fails, fix the runtime environment before reorganizing
data.

## Before and after checks

Before training or pruning:

- Confirm the root you pass to a training loader contains immediate identity
  folders.
- Record total class count, valid image count, classes below threshold, hidden
  entries, and non-image files.
- Confirm validation artifacts live in a separate validation root with carray
  folders and `_list.npy` files.

After pruning or copying:

- Confirm only expected low-shot classes were removed.
- Confirm no hidden entries remain in the pruned root.
- Confirm retained classes still meet the requested `min_num` threshold.
- Hand off to `pytorch-training` or `paddle-workflows` only after the data root
  passes the intended checks.
