# Dataset Preparation Recipes

## Purpose

The original MUNIT demo shell scripts combine dataset download, archive extraction, image splitting/cropping, and full training launch. Treat them as evidence for how public datasets are shaped, not as safe runtime helpers.

## Why The Source Demo Scripts Are Reference-Only

The three demo scripts are intentionally not bundled as executable helpers because they:

- remove or recreate dataset directories;
- download archives from external URLs;
- require system tools such as `axel`, `unzip`, `tar`, and ImageMagick `convert`;
- crop images in place into new domain folders;
- immediately start a long CUDA training job.

Use this reference to recreate the same intent with explicit user approval and separate steps.

## Edges-to-Shoes or Edges-to-Handbags

The pix2pix edges datasets store paired images side-by-side. The demo workflow is:

1. Obtain the dataset archive from the pix2pix dataset source.
2. Extract it under a dataset root.
3. Split each image into left/right halves using ImageMagick-style cropping.
4. Rename the halves into MUNIT domain folders:
   - left half -> `trainA` / `testA` (edge sketches in the repo demos);
   - right half -> `trainB` / `testB` (photo domain in the repo demos).
5. Point `data_root` to the resulting folder-mode root.
6. Validate with `scripts/inspect_munit_dataset.py` before running training.

A safe folder result looks like:

```text
edges2shoes/
  trainA/00000.jpg
  trainB/00000.jpg
  testA/00000.jpg
  testB/00000.jpg
```

## Summer-to-Winter Yosemite

The Yosemite demo expects a CycleGAN-style unpaired dataset that already uses domain split folders. After downloading and extracting the archive, point `data_root` to the nested folder that contains `trainA`, `trainB`, `testA`, and `testB`.

## List Files

For small curated subsets, list mode can avoid copying image files. Create one list file per split/domain, with entries relative to the paired folder:

```text
./00002.jpg
./00006.jpg
```

Then set `data_folder_train_a` to the folder containing those images, not to the dataset parent unless the list entries include the split folder prefix.

## Validation Before Training

Run both checks before launching a long job:

```bash
python scripts/validate_munit_config.py --config /path/to/config.yaml --repo-root /path/to/user/munit-checkout
python scripts/inspect_munit_dataset.py --config /path/to/config.yaml --repo-root /path/to/user/munit-checkout
```

If the intended config uses a large full dataset, also create a tiny config or tiny copied subset for parser/data-loader troubleshooting. Do not run the training loop until runtime and CUDA checks pass in `../environment-and-setup/`.
