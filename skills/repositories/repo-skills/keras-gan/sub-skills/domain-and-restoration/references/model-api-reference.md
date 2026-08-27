# Model/API Reference: CCGAN, ContextEncoder, PixelDA, SRGAN

This reference summarizes the Keras-GAN restoration/domain-adaptation scripts owned by this sub-skill. The source repository is a stale collection of standalone scripts, so treat these APIs as script-level classes rather than importable package APIs.

## Quick comparison

| Workflow | Class | Source evidence | Main purpose | Default data | Input/output shapes | High-risk side effects |
|---|---|---|---|---|---|---|
| CC-GAN | `CCGAN` | `ccgan/ccgan.py`, README CC-GAN section | Context-conditional MNIST inpainting plus semi-supervised discriminator labels | Keras MNIST, resized to 32x32 | generator maps `(32, 32, 1)` masked image to `(32, 32, 1)` restored image | Keras MNIST cache/download; writes `images/*.png` and `saved_model/*` |
| Context Encoder | `ContextEncoder` | `context_encoder/context_encoder.py`, README Context Encoder section | Learn to fill missing image patches in CIFAR-10 cat/dog images | Keras CIFAR-10, classes 3 and 5 | generator maps `(32, 32, 3)` masked image to missing patch `(8, 8, 3)` | Keras CIFAR-10 cache/download; writes `images/*.png` and optional saved models |
| PixelDA | `PixelDA` | `pixelda/pixelda.py`, `pixelda/data_loader.py`, `pixelda/test.py`, README PixelDA section | Translate MNIST-like images into MNIST-M style while training a classifier | `datasets/mnist_*.npy`, `datasets/mnistm_*.npy`, or source MNIST/MNIST-M artifacts | generator maps `(32, 32, 3)` domain A to `(32, 32, 3)` domain B-style image; classifier predicts 10 classes | DataLoader may download MNIST and MNIST-M and write cache arrays |
| SRGAN | `SRGAN` | `srgan/srgan.py`, `srgan/data_loader.py`, README SRGAN section | 4x super-resolution from low-resolution to high-resolution images | `datasets/img_align_celeba/*` images | low-resolution `(64, 64, 3)` to high-resolution `(256, 256, 3)` | `SRGAN()` builds `VGG19(weights="imagenet")`, which may fetch weights; writes `images/img_align_celeba/*` |

## CCGAN

### Construction and attributes

`CCGAN()` sets:

- `img_rows = 32`, `img_cols = 32`, `channels = 1`, `img_shape = (32, 32, 1)`.
- `mask_height = 10`, `mask_width = 10`.
- `num_classes = 10`; discriminator label head uses `num_classes + 1` to include a fake class.
- `gf = 32`, `df = 32`.
- `optimizer = Adam(0.0002, 0.5)`.
- `discriminator`: Keras `Model(img, [validity, label])`, compiled with losses `['mse', 'categorical_crossentropy']`, equal `0.5` weights, and accuracy metric.
- `generator`: U-Net style encoder/decoder returning a full 32x32 image.
- `combined`: `Model(masked_img, valid)`, compiled with MSE to fool the discriminator validity output.

The discriminator uses `keras_contrib.layers.normalization.instancenormalization.InstanceNormalization`, so keras-contrib is required for construction.

### Methods

- `build_generator() -> Model`: U-Net downsampling/upsampling generator with skip connections and tanh output.
- `build_discriminator() -> Model`: Conv/InstanceNorm discriminator with a PatchGAN-like validity output and a class-label head.
- `mask_randomly(imgs) -> masked_imgs`: for each image, picks one random 10x10 rectangle and sets it to zero. Input must have shape `(batch, 32, 32, 1)`.
- `train(epochs, batch_size=128, sample_interval=50)`: loads Keras MNIST, resizes to 32x32 using `scipy.misc.imresize`, normalizes to `[-1, 1]`, then alternates discriminator and generator batches.
- `sample_images(epoch, imgs)`: saves a 3-row plot of original, masked, and generated images to `images/{epoch}.png`.
- `save_model()`: writes `saved_model/ccgan_generator.json`, `saved_model/ccgan_generator_weights.hdf5`, `saved_model/ccgan_discriminator.json`, and `saved_model/ccgan_discriminator_weights.hdf5`.

### Training signature and labels

```python
ccgan = CCGAN()
ccgan.train(epochs, batch_size=128, sample_interval=50)
```

The script's `__main__` uses `epochs=20000`, `batch_size=32`, `sample_interval=200`; treat that as expensive, not as a smoke-test default. For each batch, `valid` and `fake` have shape `(batch_size, 4, 4, 1)` because the discriminator downsamples 32x32 images four times. Real labels are one-hot MNIST digits over 11 classes; fake labels are the extra fake class at index 10.

## ContextEncoder

### Construction and attributes

`ContextEncoder()` sets:

- `img_rows = 32`, `img_cols = 32`, `channels = 3`, `img_shape = (32, 32, 3)`.
- `mask_height = 8`, `mask_width = 8`, `missing_shape = (8, 8, 3)`.
- `num_classes = 2` is present but not used as a classifier head; training selects CIFAR-10 cats and dogs.
- `optimizer = Adam(0.0002, 0.5)`.
- `discriminator`: Keras `Model(img_missing_patch, validity)` compiled with binary cross-entropy.
- `generator`: encoder/decoder mapping a full masked image to only the missing 8x8 patch.
- `combined`: `Model(masked_img, [gen_missing, valid])`, compiled with losses `['mse', 'binary_crossentropy']` and weights `[0.999, 0.001]`.

### Methods

- `build_generator() -> Model`: convolutional encoder to a bottleneck, then upsampling decoder to an `(8, 8, 3)` tanh patch.
- `build_discriminator() -> Model`: discriminator for `(8, 8, 3)` real or generated missing patches.
- `mask_randomly(imgs) -> (masked_imgs, missing_parts, (y1, y2, x1, x2))`: picks a random 8x8 rectangle for each image, stores the original patch in `missing_parts`, zeroes that region in `masked_imgs`, and returns the coordinates.
- `train(epochs, batch_size=128, sample_interval=50)`: loads Keras CIFAR-10, keeps cats (`label == 3`) and dogs (`label == 5`), normalizes to `[-1, 1]`, then alternates discriminator and generator training.
- `sample_images(epoch, imgs)`: saves original, masked, and filled images to `images/{epoch}.png`.
- `save_model()`: defines `saved_model/generator*` and `saved_model/discriminator*` outputs, but the main training loop does not call it by default.

### Training signature

```python
context_encoder = ContextEncoder()
context_encoder.train(epochs, batch_size=128, sample_interval=50)
```

The script's `__main__` uses `epochs=30000`, `batch_size=64`, `sample_interval=50`; this is not safe as a default verification command.

## PixelDA

### Construction and attributes

`PixelDA()` sets:

- `img_rows = 32`, `img_cols = 32`, `channels = 3`, `img_shape = (32, 32, 3)`.
- `num_classes = 10`.
- `data_loader = DataLoader(img_res=(32, 32))`; constructing `PixelDA` constructs the data loader and may prepare/download/cache datasets.
- `lambda_adv = 10`, `lambda_clf = 1`.
- `disc_patch = (2, 2, 1)` because `32 / 2**4 == 2`.
- `residual_blocks = 6`, `df = 64`, `cf = 64`.
- `discriminator`: PatchGAN discriminator compiled with MSE and accuracy.
- `generator`: residual generator that keeps the input spatial size and outputs a tanh RGB image.
- `clf`: classifier with InstanceNormalization blocks and a 10-way softmax.
- `combined`: `Model(img_A, [valid, class_pred])`, compiled with MSE plus categorical cross-entropy and metrics.

### DataLoader contract

`pixelda.data_loader.DataLoader(img_res=(128, 128))` is hard-wired for MNIST and MNIST-M. With PixelDA it is called as `img_res=(32, 32)`.

- `setup_mnist(img_res)`: if `datasets/mnist_x.npy` does not exist, loads Keras MNIST, normalizes, resizes, expands grayscale to 3 channels, and writes `datasets/mnist_x.npy` and `datasets/mnist_y.npy`. Otherwise loads those arrays.
- `setup_mnistm(img_res)`: if `datasets/mnistm_x.npy` does not exist, expects or downloads/decompresses `datasets/keras_mnistm.pkl`, loads `data[b'train']`, normalizes/resizes it, copies labels from MNIST, and writes `datasets/mnistm_x.npy` and `datasets/mnistm_y.npy`.
- `load_data(domain, batch_size=1)`: `domain='A'` returns MNIST arrays; any other value returns MNIST-M arrays. It samples with replacement using `np.random.choice`.

### Methods

- `build_generator() -> Model`: 6 residual blocks, tanh RGB output.
- `build_discriminator() -> Model`: InstanceNorm PatchGAN domain discriminator.
- `build_classifier() -> Model`: InstanceNorm image classifier producing 10 class probabilities.
- `train(epochs, batch_size=128, sample_interval=50)`: alternates domain discriminator updates, generator/classifier updates from domain A labels, and classifier evaluation on domain B.
- `sample_images(epoch)`: saves a 2x5 grid of original MNIST images and translated MNIST-M-style images to `images/{epoch}.png`.

### Training signature and README result

```python
gan = PixelDA()
gan.train(epochs, batch_size=128, sample_interval=50)
```

The script's `__main__` uses `epochs=30000`, `batch_size=32`, `sample_interval=500`. The README reports MNIST-M classification accuracy of 55% for a naive method and 95% for PixelDA, but that is a historical educational claim, not a verification target for this generated skill.

`pixelda/test.py` is a visualization helper: it constructs the same `DataLoader`, samples 25 images from domain A and 25 from domain B, and writes `0.png` and `1.png` in the current directory.

## SRGAN

### Construction and attributes

`SRGAN()` sets:

- `channels = 3`.
- `lr_height = 64`, `lr_width = 64`, `lr_shape = (64, 64, 3)`.
- `hr_height = 256`, `hr_width = 256`, `hr_shape = (256, 256, 3)`.
- `n_residual_blocks = 16`, `gf = 64`, `df = 64`.
- `vgg = build_vgg()`, which calls `VGG19(weights="imagenet")` and replaces outputs with layer 9 features.
- `dataset_name = 'img_align_celeba'` and `data_loader = DataLoader(dataset_name='img_align_celeba', img_res=(256, 256))`.
- `disc_patch = (16, 16, 1)` because `256 / 2**4 == 16`.
- `discriminator`: high-resolution PatchGAN-like discriminator compiled with MSE and accuracy.
- `generator`: residual 4x upsampling generator from 64x64 to 256x256.
- `combined`: `Model([img_lr, img_hr], [validity, fake_features])` compiled with `['binary_crossentropy', 'mse']` and weights `[1e-3, 1]`.

### VGG19 risk

Do not instantiate `SRGAN()` as a dry-run check unless the user accepts that Keras may try to download VGG19 ImageNet weights or the cache is known to exist. To inspect SRGAN source behavior safely, read references or validate the image layout with `scripts/check_restoration_layout.py --workflow srgan`.

### Methods

- `build_vgg() -> Model`: builds a pretrained VGG19 feature extractor and uses layer 9 output.
- `build_generator() -> Model`: 9x9 first convolution, 16 residual blocks, post-residual skip, two 2x upsampling blocks, and tanh output.
- `build_discriminator() -> Model`: convolutional high-resolution discriminator ending in dense validity output.
- `train(epochs, batch_size=1, sample_interval=50)`: repeatedly loads high/low-resolution image batches, trains discriminator, extracts VGG features, trains generator, and writes samples.
- `sample_images(epoch)`: writes `images/img_align_celeba/{epoch}.png` plus low-resolution comparison files named `{epoch}_lowres{i}.png`.

### DataLoader contract

`srgan.data_loader.DataLoader(dataset_name, img_res=(128, 128))` uses `glob('./datasets/{dataset_name}/*')` and samples file paths randomly. It reads images with `scipy.misc.imread(path, mode='RGB')`, resizes high-resolution images to `img_res`, resizes low-resolution images to one quarter of each dimension, optionally flips during training, and normalizes both arrays to `[-1, 1]`.

The default SRGAN instance uses `dataset_name='img_align_celeba'` and `img_res=(256, 256)`, so each batch returns:

- `imgs_hr`: `(batch_size, 256, 256, 3)`
- `imgs_lr`: `(batch_size, 64, 64, 3)`

## Common constructor smoke-test guidance

- `CCGAN()` and `ContextEncoder()` constructors are reasonable legacy-environment smoke candidates when keras-contrib and Keras/TensorFlow 1.x are present. They build Keras graphs but do not download datasets until `train()` is called.
- `PixelDA()` is not a pure constructor smoke test because its `DataLoader` immediately prepares MNIST/MNIST-M caches and may download data.
- `SRGAN()` is not a safe constructor smoke test because `build_vgg()` may fetch VGG19 ImageNet weights.
