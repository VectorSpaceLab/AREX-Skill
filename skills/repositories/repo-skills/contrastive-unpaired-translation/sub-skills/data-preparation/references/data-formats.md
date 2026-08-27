# Data formats

This page documents the directory and file shapes that the dataset loaders and bundled helpers expect.

## Unaligned CUT/CycleGAN format

```text
root/
  trainA/
  trainB/
  testA/
  testB/
```

### Notes
- Used by `data.unaligned_dataset.UnalignedDataset`.
- `trainA` and `trainB` do not need matching filenames.
- `testA`/`testB` are optional only in the sense that test-time loading can fall back to `valA`/`valB` when `testA`/`testB` are absent.

## SinCUT single-image format

```text
root/
  trainA/
    one_image_A.jpg
  trainB/
    one_image_B.jpg
```

### Notes
- Used by `data.singleimage_dataset.SingleImageDataset`.
- The loader asserts exactly one image in each domain.
- The one-image dataset is still repeated many times by random crops and patches.

## Parallel A/B split-tree format

```text
root_A/
  train/
    0001.jpg
  test/
    0001.jpg
root_B/
  train/
    0001.jpg
  test/
    0001.jpg
```

### Notes
- Used by `scripts/combine_A_and_B.py` when creating pix2pix-style side-by-side composites from two separate roots.
- Matching split names and A/B filenames are required.
- The helper writes composites with A on the left and B on the right.

## Aligned export input format

```text
root/
  trainA/
    0001.jpg
  trainB/
    0001.jpg
  testA/
    0001.jpg
  testB/
    0001.jpg
```

### Notes
- Used by `scripts/make_dataset_aligned.py`.
- The A and B folders for each split must have equal counts and matching image sizes.
- The helper writes side-by-side composites into `root/train/` and `root/test/`.

## Cityscapes prepared format

After running the bundled Cityscapes helper, the output directory contains both paired composites and CUT-style splits.

```text
output/
  train/
    0000.jpg
  trainA/
    0000_A.jpg
  trainB/
    0000_B.jpg
  test/
    0000.jpg
  testA/
    0000_A.jpg
  testB/
    0000_B.jpg
```

### Notes
- The `train/` and `test/` directories are the paired pix2pix-style composites.
- The `trainA`/`trainB` and `testA`/`testB` trees are for CUT/CycleGAN-style loading.

## Cat-face crop format

```text
input_dir/
  image1.jpg
  image2.png
output_dir/
  image1_cat0.jpg
  image1_cat1.jpg
```

### Notes
- The helper processes top-level images from the input directory.
- Multiple detected faces can produce multiple output files per source image.
- The crop helper depends on OpenCV and a cat-face cascade file.

## Implementation details worth remembering

- `data.image_folder.make_dataset` accepts image files inside the target directory tree and its subdirectories.
- `UnalignedDataset` uses random pairings between domain A and B during training unless `serial_batches` is enabled.
- `SingleImageDataset` precomputes repeated crop/patch indices so the same minibatch sees consistent random scaling.
