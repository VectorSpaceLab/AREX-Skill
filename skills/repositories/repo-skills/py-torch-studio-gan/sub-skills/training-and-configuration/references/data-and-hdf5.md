# Data layout and HDF5 reference

StudioGAN training uses either torchvision CIFAR datasets or an ImageFolder-style directory. HDF5 is an optional train-split cache for faster I/O. Validate custom folders before launching training.

## Dataset modes

| `DATA.name` family | Loader behavior | Required `-data` value |
| --- | --- | --- |
| `CIFAR10` | Uses torchvision CIFAR10 with `download=True`. | A writable cache/root directory. |
| `CIFAR100` | Uses torchvision CIFAR100 with `download=True`. | A writable cache/root directory. |
| Other dataset names | Uses ImageFolder under `train/` or `valid/`. | Directory containing split subdirectories. |

CIFAR10/100 do not use `valid`; compatibility permits `-ref train` or `-ref test` only.

## Custom ImageFolder layout

Expected layout:

```text
/path/to/data/
  train/
    class_a/
      image001.jpg
      image002.png
    class_b/
      image003.jpg
  valid/
    class_a/
      image101.jpg
    class_b/
      image102.jpg
```

Rules:

- `train/<class>/...` is required for training and train-reference metrics.
- `valid/<class>/...` is required when using `-ref valid` or evaluation workflows that request the validation split.
- Class directory names define integer class indices through ImageFolder sorting. Keep class names stable across train and valid.
- For conditional configs, `DATA.num_classes` should match the number of training class directories.
- If the dataset is effectively unconditional, use one class directory and set `DATA.num_classes: 1`, or start from an unconditional config with `W/O` conditioning.
- Use image extensions that PIL/ImageFolder can open, such as `.jpg`, `.jpeg`, `.png`, `.bmp`, `.webp`, or `.tif`.

Run the bundled checker:

```bash
python sub-skills/training-and-configuration/scripts/check_studiogan_dataset.py \
  --data-dir /path/to/data --require-valid --min-classes 2 --min-images-per-class 1
```

## Preprocessing path

For non-HDF5 loading, StudioGAN builds a transform stack roughly as follows:

1. If the dataset is not in the no-processing set (`CIFAR10`, `CIFAR100`, `Tiny_ImageNet`), center-crop the long edge.
2. If `resize_size` is set and `--pre_resizer` is not `wo_resize`, resize to `DATA.img_size` using the selected resizer.
3. Apply random horizontal flip when `PRE.apply_rflip` is true.
4. Convert to tensor and normalize channels with mean/std `0.5`.

For CIFAR10/100/Tiny ImageNet, preprocessing is reduced: no long-edge crop and no pre-resize; `pre_resizer` is effectively forced to `wo_resize`.

Allowed pre-resizers:

- `wo_resize`
- `nearest`
- `bilinear`
- `bicubic`
- `lanczos`

## HDF5 workflow

`-hdf5` asks StudioGAN to prepare or reuse a train-split HDF5 file under `-data`:

```bash
CUDA_VISIBLE_DEVICES=0 python src/main.py -t -hdf5 \
  -cfg /path/to/config.yaml -data /path/to/data -save /path/to/save
```

The HDF5 filename follows one of these patterns:

```text
DATA.name_DATA.img_size_PRE_RESIZER_train.hdf5
DATA.name_DATA.img_size_train.hdf5
```

The cache stores:

- `imgs`: uint8 images with shape `[N, img_size, img_size, 3]`.
- `labels`: int64 labels with shape `[N]`.

During HDF5 creation, images are loaded through the normal dataset path without random flip and without normalization, then converted to HDF5 chunks. This can be slow and large; it is still safer than repeatedly reprocessing very large ImageFolder trees during training.

## In-memory loading

`-l` loads the HDF5 arrays into host memory:

```bash
CUDA_VISIBLE_DEVICES=0 python src/main.py -t -hdf5 -l \
  -cfg /path/to/config.yaml -data /path/to/data -save /path/to/save
```

Compatibility rules:

- `-l` requires `-hdf5`.
- In-memory HDF5 is useful for small/medium datasets with enough RAM.
- Do not use `-l` on a high-resolution dataset unless memory capacity has been estimated.
- iFID with HDF5 requires `-l`; otherwise StudioGAN rejects the combination.

## Reference dataset selection

`-ref` controls which split is used for evaluation metrics during or after training:

| `-ref` value | Data source | Notes |
| --- | --- | --- |
| `train` | CIFAR train or ImageFolder `train/` | Most training command templates use this. |
| `valid` | ImageFolder `valid/` | Not available for CIFAR10/100. |
| `test` | CIFAR test | CIFAR10/100 only. |

If a custom dataset has no validation split, use `-ref train` or create a proper `valid/<class>` split. Do not point `-data` directly at a folder of images without `train/<class>`; ImageFolder expects class subdirectories.

## Adapting a CIFAR config to custom images

When adapting a CIFAR config, update at least:

| YAML field | Why |
| --- | --- |
| `DATA.name` | Any name other than `CIFAR10`/`CIFAR100` switches to ImageFolder loading. |
| `DATA.img_size` | Must match the intended training resolution and backbone constraints. |
| `DATA.num_classes` | Must match class directories for conditional training. |
| `MODEL.g_cond_mtd` / `MODEL.d_cond_mtd` | Use conditional methods only if labels/classes are meaningful. |
| `OPTIMIZATION.batch_size` | Must fit memory and divide GPU world size. |
| `--pre_resizer` | For non-CIFAR data, choose `lanczos`, `bicubic`, or another allowed resizer if images are not already the target size. |

Recommended safe sequence:

1. Copy an existing YAML outside the generated skill tree.
2. Edit dataset identity, class count, and image size.
3. Run `check_studiogan_dataset.py` on the folder.
4. Run `validate_studiogan_config.py` with the planned `--gpus`, `--metrics`, and HDF5 flags.
5. Build the training command with `build_studiogan_train_command.py`.

## Dataset checker output

The bundled checker reports per-split class and image counts. Treat these as hard blockers before training:

- Missing `train/` split.
- No class directories under `train/`.
- Any class with fewer than the requested minimum image count.
- Missing or empty `valid/` when `--require-valid` is set.
- Train/valid class-name mismatch when a valid split is required.

## Common data mistakes

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `Couldn't find any class folder` or no classes reported | `-data` points to images directly, not to a directory containing `train/<class>`. | Create `train/class_name/` folders and retry. |
| CIFAR config tries to download data unexpectedly | `DATA.name` still `CIFAR10` or `CIFAR100`. | Change `DATA.name` for custom ImageFolder data. |
| Metrics fail for `-ref valid` | No `valid/<class>` split. | Use `-ref train` or create validation split. |
| Classifier/conditional losses behave oddly | `DATA.num_classes` does not match folder classes. | Update YAML and validate. |
| HDF5 creation consumes too much storage or time | High-resolution ImageFolder with `-hdf5`. | Start without HDF5, or prepare storage/RAM explicitly. |
| `load_data_in_memory` assertion | `-l` used without `-hdf5`. | Add `-hdf5` or remove `-l`. |
