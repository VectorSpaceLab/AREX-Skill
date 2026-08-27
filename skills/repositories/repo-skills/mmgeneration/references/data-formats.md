# Data Formats

## Purpose

Read this when a config, dataset, or translation workflow fails because the file layout or pipeline keys are wrong.

## Dataset layouts

### Unconditional image data

`UnconditionalImageDataset(imgs_root, pipeline, test_mode=False)` scans image files recursively under `imgs_root`.
A minimal layout is a directory of real images with no paired structure.

### Paired translation data

`PairedImageDataset(dataroot, pipeline, test_mode=False, testdir='test')` expects paired images concatenated along the width dimension.
The docs and tests use:

```text
./data/dataset_name/
├── test
└── train
```

Each image contains the two domains side by side.

### Unpaired translation data

`UnpairedImageDataset(dataroot, pipeline, test_mode=False, domain_a=None, domain_b=None)` expects separate domain folders:

```text
./data/dataset_name/
├── testA
├── testB
├── trainA
└── trainB
```

### Grow-scale data for progressive GANs

`GrowScaleImgDataset(imgs_roots, pipeline, len_per_stage=1000000, gpu_samples_per_scale=None, gpu_samples_base=32, test_mode=False)` expects a mapping from scale names to resized image directories.
This is the dataset family used for dynamic resolution training.

### SinGAN data

`SinGANDataset(img_path, min_size, max_size, scale_factor_init, num_samples=-1)` starts from one image and builds the scale pyramid needed by SinGAN-style workflows.

### Quick test data

`QuickTestImageDataset(*args, size=None, **kwargs)` synthesizes a fixed-size toy dataset and is useful for smoke tests or shape checks.

## Pipeline keys and common sample dictionaries

### Unconditional data

Typical keys:

- `real_img`
- `real_img_path`

### Paired translation data

Typical keys:

- `img_a`
- `img_b`
- `img_a_path`
- `img_b_path`

### Unpaired translation data

Typical keys:

- `img_a`
- `img_b`
- `img_a_path`
- `img_b_path`

### Sampling helpers

`sample_img2img_model` injects temporary keys named like:

- `pair_path`
- `img_<source_domain>_path`
- `img_<target_domain>_path`

so the test pipeline can read a single image and produce a translated sample.

## Common pipeline primitives

Verified pipeline classes exported by `mmgen.datasets.pipelines` include:

- `LoadImageFromFile`
- `Compose`
- `ImageToTensor`
- `Collect`
- `ToTensor`
- `Flip`
- `Resize`
- `RandomImgNoise`
- `RandomCropLongEdge`
- `CenterCropLongEdge`
- `Normalize`
- `NumpyPad`
- `Crop`
- `FixedCrop`

## Practical checks

- A paired-image dataset should yield two tensors per sample.
- An unpaired-image dataset should return two domain images, not a single concatenated image.
- `QuickTestImageDataset(size=(256, 256))` is a safe way to validate image-shaped outputs without using real data.
