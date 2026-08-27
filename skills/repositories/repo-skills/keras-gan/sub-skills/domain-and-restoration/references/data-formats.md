# Data Formats and Runtime Layouts

This reference documents file-system and tensor contracts for Keras-GAN's CCGAN, ContextEncoder, PixelDA, and SRGAN workflows. Paths are shown relative to the directory from which a standalone adapted script is run.

## Common tensor conventions

- Image data is normally normalized to `[-1, 1]` before training.
- Sample routines convert generated arrays back to display range with `0.5 * x + 0.5` or equivalent.
- The original scripts assume channels-last Keras tensors.
- Several scripts use relative directories (`datasets/`, `images/`, `saved_model/`) and do not create all of them before writing.

## Output directories

| Workflow | Required/expected output directories | Files written by source behavior |
|---|---|---|
| CCGAN | `images/`, `saved_model/` | `images/{epoch}.png`; `saved_model/ccgan_generator.json`; `saved_model/ccgan_generator_weights.hdf5`; `saved_model/ccgan_discriminator.json`; `saved_model/ccgan_discriminator_weights.hdf5` |
| ContextEncoder | `images/`; `saved_model/` only if `save_model()` is called manually | `images/{epoch}.png`; optional `saved_model/generator*` and `saved_model/discriminator*` |
| PixelDA | `datasets/`, `images/` | `datasets/mnist_x.npy`, `datasets/mnist_y.npy`, `datasets/mnistm_x.npy`, `datasets/mnistm_y.npy`; `images/{epoch}.png` |
| SRGAN | `datasets/img_align_celeba/`, `images/img_align_celeba/` | `images/img_align_celeba/{epoch}.png`; `images/img_align_celeba/{epoch}_lowres{i}.png` |

Use `scripts/check_restoration_layout.py --check-output-dirs --output-root <run-dir>` to check output directories without creating them.

## CCGAN data contract

Training calls Keras MNIST:

```python
(X_train, y_train), (_, _) = mnist.load_data()
```

The training loop then:

1. Resizes each 28x28 MNIST digit to `(32, 32)` with `scipy.misc.imresize`.
2. Normalizes images as `(x.astype(np.float32) - 127.5) / 127.5`.
3. Expands the channel axis to produce `(num_examples, 32, 32, 1)`.
4. Reshapes labels to `(num_examples, 1)`.
5. Creates random 10x10 zero masks per batch with `mask_randomly`.

Mask format:

- Input: `imgs` shape `(batch, 32, 32, 1)`.
- Coordinates: sampled separately for each image, with `y1 in [0, 22)`, `x1 in [0, 22)`, then `y2 = y1 + 10`, `x2 = x1 + 10`.
- Output: `masked_imgs` with the selected patch set to `0`.

The discriminator target validity arrays use shape `(batch_size, 4, 4, 1)`. Class labels are one-hot encoded with 11 classes: digits `0..9` and fake class `10`.

## ContextEncoder data contract

Training calls Keras CIFAR-10:

```python
(X_train, y_train), (_, _) = cifar10.load_data()
```

The training loop then:

1. Keeps CIFAR-10 cats (`label == 3`) and dogs (`label == 5`).
2. Stacks them into one training array.
3. Normalizes images to `[-1, 1]` with `X_train / 127.5 - 1.`.
4. Creates random 8x8 zero masks and extracts the missing patch.

Mask and missing-patch format:

- Input: `imgs` shape `(batch, 32, 32, 3)`.
- `masked_imgs`: same shape as input with one 8x8 patch set to zero.
- `missing_parts`: shape `(batch, 8, 8, 3)`, copied from the original image before zeroing.
- Coordinates tuple: `(y1, y2, x1, x2)`, where each element is an array of length `batch`.

The generator predicts only `missing_parts`, not the full image. The sample routine composites the predicted patch back into a copy of the original image for visualization.

## PixelDA dataset/cache contract

PixelDA uses a hard-coded `datasets/` directory with both source and cached artifacts.

### Required cached arrays for offline construction/training

A fully cached offline PixelDA setup should contain:

```text
datasets/
  mnist_x.npy
  mnist_y.npy
  mnistm_x.npy
  mnistm_y.npy
```

Expected array intent:

| File | Domain | Expected content |
|---|---|---|
| `mnist_x.npy` | A | MNIST images resized to `(32, 32)`, expanded/repeated to RGB, normalized to `[-1, 1]` |
| `mnist_y.npy` | A | MNIST digit labels |
| `mnistm_x.npy` | B | MNIST-M RGB images resized to `(32, 32)` and normalized to `[-1, 1]` |
| `mnistm_y.npy` | B | labels copied from the MNIST labels used by the loader |

The bundled checker verifies file presence and can optionally inspect `.npy` shape headers with NumPy disabled by default. It does not prove label alignment or image quality.

### Source artifacts and download behavior

If `datasets/mnistm_x.npy` is missing, the source loader tries to obtain `datasets/keras_mnistm.pkl` as follows:

1. It sets a hard-coded URL for `keras_mnistm.pkl.gz`.
2. If `datasets/keras_mnistm.pkl` is absent, it downloads `datasets/keras_mnistm.pkl.gz`, decompresses it to `datasets/keras_mnistm.pkl`, and deletes the `.gz`.
3. It reads the pickle with `pickle.load(f, encoding='bytes')` and extracts `data[b'train']`.
4. It normalizes/resizes MNIST-M and writes `mnistm_x.npy`, `mnistm_y.npy`.

If `datasets/mnist_x.npy` is missing, the source loader calls Keras MNIST and writes `mnist_x.npy`, `mnist_y.npy`.

Offline policy:

- Complete `.npy` cache: safe to construct the loader without network, assuming files are readable.
- `keras_mnistm.pkl` present but arrays absent: can rebuild MNIST-M arrays, but still verify MNIST cache or permit Keras MNIST access.
- Only `keras_mnistm.pkl.gz` present: the source code does not use it directly unless it first downloads to that same path; decompress it manually or provide `.pkl`/`.npy` files before offline construction.
- No MNIST-M source/cache: do not instantiate `DataLoader` if network is disallowed.

### PixelDA tensors

- Domain A images: `(batch, 32, 32, 3)`.
- Domain B images: `(batch, 32, 32, 3)`.
- Labels: integer digit labels; domain A labels are one-hot encoded inside `train` for the classifier loss.
- Discriminator validity target: `(batch_size, 2, 2, 1)`.

## SRGAN dataset contract

The source script expects the user to download CelebA aligned images externally and place the folder under `datasets/`:

```text
datasets/
  img_align_celeba/
    000001.jpg
    000002.jpg
    ...
```

The loader uses:

```python
path = glob('./datasets/%s/*' % dataset_name)
batch_images = np.random.choice(path, size=batch_size)
```

Implications:

- The directory must contain image files directly under `datasets/img_align_celeba/`; nested directories are not handled by the source loader.
- The source loader samples with replacement. A one-image directory can technically load a batch, but it is not meaningful for training; use a higher minimum for real runs.
- The `is_testing` flag only disables random horizontal flips. It does not change the file glob.

Default SRGAN transformations:

1. Read each image as RGB.
2. Resize HR image to `(256, 256)` because `img_res=(hr_height, hr_width)`.
3. Resize LR image to `(64, 64)` because low dimensions are one quarter of HR.
4. Randomly flip HR and LR together during training with probability 0.5.
5. Normalize HR and LR arrays to `[-1, 1]`.

Expected batch shapes:

| Array | Shape |
|---|---|
| `imgs_hr` | `(batch_size, 256, 256, 3)` |
| `imgs_lr` | `(batch_size, 64, 64, 3)` |
| discriminator validity/fake targets | `(batch_size, 16, 16, 1)` |

## File extensions recognized by the bundled checker

For SRGAN image-layout checks, the checker treats these extensions as images: `.jpg`, `.jpeg`, `.png`, `.bmp`, `.gif`, `.webp`, `.tif`, and `.tiff`. The original source uses SciPy image reading and may not support every extension equally in a given legacy environment; for safest compatibility, prefer `.jpg` or `.png` RGB images.
