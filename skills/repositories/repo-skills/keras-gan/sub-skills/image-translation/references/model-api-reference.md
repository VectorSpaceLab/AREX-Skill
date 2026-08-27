# Model API Reference: Keras-GAN Image Translation

This reference distills the standalone Keras-GAN scripts for CycleGAN, DiscoGAN,
and Pix2Pix. It is intended for adapting or inspecting the workflows without
reopening the original repository.

## Runtime stance

Keras-GAN is stale educational code. Use a pinned legacy stack when executing the
model scripts or constructor smoke tests: Python 3.7-era, TensorFlow 1.15.x, Keras
2.2.x, `keras-contrib` with `InstanceNormalization`, NumPy 1.18.x, SciPy 1.2.x,
Matplotlib, Pillow, and scikit-image. Newer SciPy removed `scipy.misc.imread` and
`scipy.misc.imresize`; see [troubleshooting.md](troubleshooting.md).

Do not treat the repository as a package. The scripts were written to be run from
their own workflow directories where a sibling `data_loader.py` is importable as
`from data_loader import DataLoader` and relative paths like `./datasets/...`
resolve.

## Shared conventions

| Workflow | Class | Default dataset | Resolution | Channels | Generator filters | Discriminator filters | PatchGAN label shape |
|---|---:|---:|---:|---:|---:|---:|---|
| CycleGAN | `CycleGAN` | `apple2orange` | `128x128` | 3 | `gf=32` | `df=64` | `(8, 8, 1)` |
| DiscoGAN | `DiscoGAN` | `edges2shoes` | `128x128` | 3 | `gf=64` | `df=64` | `(8, 8, 1)` |
| Pix2Pix | `Pix2Pix` | `facades` | `256x256` | 3 | `gf=64` | `df=64` | `(16, 16, 1)` |

PatchGAN shape is computed in every class as:

```python
patch = int(self.img_rows / 2**4)
self.disc_patch = (patch, patch, 1)
```

If you change `img_rows`/`img_cols`, regenerate the model and the label tensors
with the updated `disc_patch`. The scripts assume square image resolutions.

## CycleGAN

### Class and constructor

`CycleGAN()` sets:

- `img_rows = img_cols = 128`, `channels = 3`, `img_shape = (128, 128, 3)`.
- `dataset_name = 'apple2orange'`.
- `data_loader = DataLoader(dataset_name='apple2orange', img_res=(128, 128))`.
- Two discriminators: `d_A`, `d_B`.
- Two U-Net generators: `g_AB` for A-to-B and `g_BA` for B-to-A.
- Loss weights: `lambda_cycle = 10.0`, `lambda_id = 1.0`.
- Optimizer: `Adam(0.0002, 0.5)`.

### Architecture distinctions

- `build_generator()` returns a compact U-Net with 4 downsampling blocks and 4
  upsampling stages. It uses `InstanceNormalization` after downsampling and
  upsampling convolutions, skip connections via `Concatenate`, and final
  `tanh` output.
- `build_discriminator()` is a PatchGAN discriminator with four stride-2
  convolution blocks followed by a `Conv2D(1, kernel_size=4, strides=1,
  padding='same')` validity map.
- The combined model consumes `[img_A, img_B]` and outputs
  `[valid_A, valid_B, reconstr_A, reconstr_B, img_A_id, img_B_id]` with losses
  `['mse', 'mse', 'mae', 'mae', 'mae', 'mae']` and weights
  `[1, 1, lambda_cycle, lambda_cycle, lambda_id, lambda_id]`.

### Training and sampling APIs

```python
CycleGAN.train(epochs, batch_size=1, sample_interval=50)
CycleGAN.sample_images(epoch, batch_i)
```

Training pulls unpaired mini-batches from `data_loader.load_batch(batch_size)`.
For each batch it predicts `fake_B = g_AB(imgs_A)` and `fake_A = g_BA(imgs_B)`,
updates both discriminators, then updates both generators through the combined
cycle/identity graph.

`sample_images()` creates `images/<dataset_name>/` and writes
`<epoch>_<batch_i>.png`. The sample grid is 2 rows x 3 columns:
`Original`, `Translated`, `Reconstructed` for A then B.

## DiscoGAN

### Class and constructor

`DiscoGAN()` sets:

- `img_rows = img_cols = 128`, `channels = 3`, `img_shape = (128, 128, 3)`.
- `dataset_name = 'edges2shoes'`.
- `data_loader = DataLoader(dataset_name='edges2shoes', img_res=(128, 128))`.
- Two discriminators: `d_A`, `d_B`.
- Two U-Net generators: `g_AB`, `g_BA`.
- Optimizer: `Adam(0.0002, 0.5)`.

### Architecture distinctions

- `build_generator()` is a deeper U-Net than CycleGAN: 7 downsampling blocks and
  7 upsampling stages, with `InstanceNormalization` and skip connections.
- The combined model consumes `[img_A, img_B]` and outputs
  `[valid_A, valid_B, fake_B, fake_A, reconstr_A, reconstr_B]`.
- Its objectives combine adversarial losses, direct cross-domain translation MAE
  (`fake_B` vs `imgs_B`, `fake_A` vs `imgs_A`), and reconstruction MAE.
  Unlike CycleGAN, it does not include identity mapping outputs or explicit loss
  weights in the compiled model.

### Training and sampling APIs

```python
DiscoGAN.train(epochs, batch_size=128, sample_interval=50)
DiscoGAN.sample_images(epoch, batch_i)
```

The script's `__main__` path overrides the large default and calls
`train(epochs=20, batch_size=1, sample_interval=200)`. Prefer small batch sizes
for smoke work because the implementation is memory-heavy.

`sample_images()` creates `images/<dataset_name>/` and writes
`<epoch>_<batch_i>.png`. The sample grid is 2 rows x 3 columns:
`Original`, `Translated`, `Reconstructed` for A then B.

## Pix2Pix

### Class and constructor

`Pix2Pix()` sets:

- `img_rows = img_cols = 256`, `channels = 3`, `img_shape = (256, 256, 3)`.
- `dataset_name = 'facades'`.
- `data_loader = DataLoader(dataset_name='facades', img_res=(256, 256))`.
- One conditional discriminator: `discriminator`.
- One U-Net generator: `generator`.
- Optimizer: `Adam(0.0002, 0.5)`.

### Architecture distinctions

- The generator maps conditioning image B to generated image A:
  `fake_A = generator(img_B)`.
- The discriminator receives pairs `[img_A, img_B]`. Internally it concatenates
  image and condition along channels before PatchGAN convolution blocks.
- The combined model consumes `[img_A, img_B]` and outputs `[valid, fake_A]`
  with losses `['mse', 'mae']` and loss weights `[1, 100]`.
- The U-Net uses `BatchNormalization(momentum=0.8)`, not
  `InstanceNormalization`.

### Training and sampling APIs

```python
Pix2Pix.train(epochs, batch_size=1, sample_interval=50)
Pix2Pix.sample_images(epoch, batch_i)
```

Training reads paired side-by-side images, splits each image into left half A and
right half B, trains the discriminator on real `[imgs_A, imgs_B]` and fake
`[fake_A, imgs_B]`, then trains the generator through the combined model.

`sample_images()` creates `images/<dataset_name>/` and writes
`<epoch>_<batch_i>.png`. It loads three test pairs and saves a 3 x 3 grid with
rows titled `Condition`, `Generated`, `Original`.

## DataLoader API summary

| Workflow | Constructor | `load_data` | `load_batch` | Notes |
|---|---|---|---|---|
| CycleGAN | `DataLoader(dataset_name, img_res=(128,128))` | `load_data(domain, batch_size=1, is_testing=False)` | `load_batch(batch_size=1, is_testing=False)` | Separate `trainA/trainB/testA/testB`; `load_batch(is_testing=True)` looks for `valA/valB`. |
| DiscoGAN | `DataLoader(dataset_name, img_res=(128,128))` | `load_data(batch_size=1, is_testing=False)` | `load_batch(batch_size=1, is_testing=False)` | Source code expects side-by-side `train/val` images even though the workflow is often described as two-domain translation; see data formats. |
| Pix2Pix | `DataLoader(dataset_name, img_res=(128,128))` in loader, called with `(256,256)` by class | `load_data(batch_size=1, is_testing=False)` | `load_batch(batch_size=1, is_testing=False)` | Side-by-side paired `train/test/val` images split into left A and right B. |

Important batch behavior:

- `load_batch()` sets `self.n_batches = int(num_files / batch_size)` and then
  loops over `range(self.n_batches - 1)`. A dataset with exactly one batch worth
  of files may yield zero batches. Use more than `batch_size` files for actual
  training smoke tests.
- Image arrays are normalized with `np.array(imgs) / 127.5 - 1.0`; samples are
  rescaled back with `0.5 * gen_imgs + 0.5` for plotting.
- Training augmentations randomly horizontal-flip images. CycleGAN flips A and B
  independently only in `load_data`; in `load_batch` it flips both images when
  the random condition is met. Paired loaders flip both halves together.
