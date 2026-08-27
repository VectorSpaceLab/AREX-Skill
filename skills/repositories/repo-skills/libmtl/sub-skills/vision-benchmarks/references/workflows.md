# Vision Benchmark Workflows

This reference covers the two image benchmark families shipped with LibMTL.

## NYUv2

Use the NYUv2 benchmark runner with the shared trainer flags shown below.

Typical command pattern:

```bash
python main.py --weighting EW --arch HPS --dataset_path /path/to/nyuv2 --gpu_id 0 --scheduler step --mode train --save_path /tmp/libmtl-nyu
```

Important flags:

- `--aug` toggles the NYUv2 augmentation pipeline.
- `--train_bs` and `--test_bs` control the two dataloaders.
- `--dataset_path` must point at the preprocessed NYUv2 root.

NYUv2 task structure:

- `segmentation`
- `depth`
- `normal`

The example uses `process_preds(...)` to resize decoder outputs back to the
benchmark image size.

## Cityscapes

Use the Cityscapes benchmark runner with the shared trainer flags shown below.

Typical command pattern:

```bash
python main.py --weighting EW --arch HPS --dataset_path /path/to/cityscapes2 --gpu_id 0 --scheduler step --mode train --save_path /tmp/libmtl-city
```

Important flags:

- `--train_mode` controls whether the loader uses the training split or the
  combined train/val variant documented in the repo.
- `--train_bs` and `--test_bs` control the image batch sizes.
- `--dataset_path` must point at the preprocessed Cityscapes root.

Cityscapes task structure:

- `segmentation`
- `depth`

## Shared model wiring

- DeepLabV3+ examples use `resnet_dilated('resnet50')` plus `DeepLabHead`.
- SegNet+MTAN uses `SegNet_MTAN_encoder` plus `SegNet_MTAN_decoder`.
- `multi_input` must remain `False` for both datasets.

## Shared workflow checks

1. Verify the expected `train/` and `val/` subdirectories exist.
2. Verify the `image/`, `label/`, `depth/`, and `normal/` leaf folders for
   NYUv2, or the corresponding two-task subset for Cityscapes.
3. Confirm that the example is run from the example directory so the local
   imports resolve.
4. Confirm that the backbone weights can be downloaded or are already cached.
