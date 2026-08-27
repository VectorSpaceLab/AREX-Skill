# Workflows for Restoration and Domain Adaptation

These workflows are designed for future agents working from the generated skill tree. They avoid network access, full training, destructive writes, and accidental dependency-heavy constructors unless explicitly authorized.

## Workflow 1: classify the request

1. If the request says inpainting, context, masked MNIST, or semi-supervised context-conditional generation, select `CCGAN`.
2. If the request says context encoder, missing patch, cats/dogs, or CIFAR-10 inpainting, select `ContextEncoder`.
3. If the request says MNIST to MNIST-M, pixel-level domain adaptation, domain A/B with a classifier, or MNIST-M cache, select `PixelDA`.
4. If the request says super-resolution, 4x upscaling, low-resolution to high-resolution, CelebA, or VGG19 perceptual loss, select `SRGAN`.
5. If the request says CycleGAN, DiscoGAN, Pix2Pix, paired facades, apple2orange, or edges2shoes, use the sibling image-translation sub-skill. If it says vanilla GAN/DCGAN/WGAN-style MNIST generation, use the sibling mnist-generators sub-skill.

## Workflow 2: safe dataset/layout validation

Use the bundled checker before importing Keras or running model code.

```bash
# Show options.
python sub-skills/domain-and-restoration/scripts/check_restoration_layout.py --help

# SRGAN CelebA-style image directory under ./datasets/img_align_celeba.
python sub-skills/domain-and-restoration/scripts/check_restoration_layout.py \
  --workflow srgan \
  --data-root ./datasets \
  --dataset-name img_align_celeba \
  --min-images 8

# PixelDA cache/source artifacts under ./datasets.
python sub-skills/domain-and-restoration/scripts/check_restoration_layout.py \
  --workflow pixelda \
  --data-root ./datasets \
  --json

# Check expected output directories for a script run from its workflow directory.
python sub-skills/domain-and-restoration/scripts/check_restoration_layout.py \
  --workflow context-encoder \
  --check-output-dirs \
  --output-root .
```

Interpretation:

- Exit code `0`: required layout for that validation mode is present.
- Exit code `1`: one or more required files/directories are absent, empty, or unsupported. Read the printed messages and the JSON `errors` field if `--json` was used.
- Exit code `2`: invalid checker arguments.

The checker does not validate model quality, labels, or image semantic correctness. It validates only the file-system preconditions that can be checked safely.

## Workflow 3: adapt CCGAN for context-conditional MNIST inpainting

1. Confirm that the user accepts Keras MNIST cache/download behavior or already has the Keras dataset cache available. Training calls `mnist.load_data()`.
2. Use a legacy Keras/TensorFlow 1.x runtime with keras-contrib; modern Keras 3 / TensorFlow 2 APIs are not compatible without porting.
3. Create run-local output directories before a short run:

```bash
mkdir -p images saved_model
```

4. Instantiate only after dependencies are confirmed:

```python
from ccgan import CCGAN
model = CCGAN()
```

5. For a shape/masking unit check without training, call `mask_randomly` on synthetic data:

```python
import numpy as np
imgs = np.ones((4, 32, 32, 1), dtype='float32')
masked = model.mask_randomly(imgs)
assert masked.shape == imgs.shape
assert (masked == 0).any()
```

6. For a bounded training probe, use a tiny epoch count and large `sample_interval` so the script does not run the historical default:

```python
model.train(epochs=1, batch_size=4, sample_interval=1)
```

7. Expected outputs on sample intervals: `images/0.png`; `saved_model/ccgan_generator.json`, `saved_model/ccgan_generator_weights.hdf5`, `saved_model/ccgan_discriminator.json`, and `saved_model/ccgan_discriminator_weights.hdf5` when `save_model()` is called by the training loop.

Adaptation notes:

- Keep grayscale image tensors `(batch, 32, 32, 1)` normalized to `[-1, 1]`.
- If changing the mask size, update both `mask_height` and `mask_width`; discriminator validity shape may need review if image size changes.
- `ccgan.py` uses `scipy.misc.imresize`, so a modern SciPy environment requires replacing it with Pillow or `skimage.transform.resize` during a port.

## Workflow 4: adapt ContextEncoder for CIFAR-10 inpainting

1. Confirm Keras CIFAR-10 cache/download behavior. Training calls `cifar10.load_data()`.
2. Use a legacy Keras/TensorFlow 1.x runtime. The constructor builds the generator, discriminator, and combined model but does not download data.
3. Create `images/` if `sample_images` can run:

```bash
mkdir -p images saved_model
```

4. Constructor and mask sanity check:

```python
from context_encoder import ContextEncoder
import numpy as np
model = ContextEncoder()
imgs = np.ones((4, 32, 32, 3), dtype='float32')
masked, missing, coords = model.mask_randomly(imgs)
assert masked.shape == imgs.shape
assert missing.shape == (4, 8, 8, 3)
assert len(coords) == 4
```

5. For a bounded run, do not use the script's default 30,000 epochs. Use:

```python
model.train(epochs=1, batch_size=4, sample_interval=1)
```

6. Expected sample output: `images/0.png`, containing original, masked, and filled-in rows.

Adaptation notes:

- The default training data is a subset of CIFAR-10 labels 3 and 5. If replacing the dataset, provide RGB 32x32 images normalized to `[-1, 1]`.
- The generator returns only the missing patch, not a full image. The sample routine composites that patch back into a copy of the input image.
- If changing `mask_height` or `mask_width`, update `missing_shape` and rebuild the discriminator.

## Workflow 5: inspect or prepare PixelDA data safely

PixelDA is the most network/cache-sensitive workflow in this sub-skill because `DataLoader.__init__` immediately calls both dataset setup methods.

1. Before `PixelDA()` or `DataLoader()`, inspect the dataset directory:

```bash
python sub-skills/domain-and-restoration/scripts/check_restoration_layout.py --workflow pixelda --data-root ./datasets
```

2. Interpret the cache state:
   - If `mnist_x.npy`, `mnist_y.npy`, `mnistm_x.npy`, and `mnistm_y.npy` are all present, `DataLoader` can load cached arrays without rebuilding either domain.
   - If only `keras_mnistm.pkl` is present, `DataLoader` can rebuild MNIST-M arrays but may still need Keras MNIST for labels and MNIST arrays.
   - If MNIST-M source/cache files are absent, `DataLoader` may try a network download from its hard-coded MNIST-M URL.
3. If network is not allowed, do not call `PixelDA()` with incomplete caches. Ask the user to provide complete cached arrays or the decompressed `keras_mnistm.pkl` plus an allowed way to populate MNIST arrays.
4. Create output directory before sampling/training:

```bash
mkdir -p images datasets
```

5. For a bounded PixelDA run in a prepared legacy runtime:

```python
from pixelda import PixelDA
model = PixelDA()
# This is already after cache validation; construction may load arrays.
model.train(epochs=1, batch_size=4, sample_interval=1)
```

6. Expected sample output: `images/0.png`, a 2x5 grid where the first row is MNIST domain A and the second row is translated domain B-style images.

Adaptation notes:

- Domain A is grayscale MNIST expanded to three channels. Domain B is MNIST-M RGB.
- Both domains are resized to `(32, 32)` and normalized to `[-1, 1]`.
- `DataLoader.load_data(domain='A')` uses MNIST; any non-`A` domain uses MNIST-M.
- The classifier is trained on domain A labels while seeing translated images; domain B labels are copied from MNIST labels by position in the prepared cache.

## Workflow 6: validate SRGAN without triggering VGG19 downloads

SRGAN uses VGG19 perceptual features and `VGG19(weights="imagenet")` is called inside `SRGAN.__init__`. A dry-run that simply constructs `SRGAN()` can trigger a weight download.

Safe path:

1. Validate the image directory first:

```bash
python sub-skills/domain-and-restoration/scripts/check_restoration_layout.py \
  --workflow srgan \
  --data-root ./datasets \
  --dataset-name img_align_celeba \
  --min-images 8
```

2. Confirm that the user has either:
   - an existing Keras VGG19 ImageNet weights cache, or
   - explicit permission for Keras to download those weights, or
   - a port/adaptation plan that replaces `build_vgg()` with a local/random-weight feature extractor for testing only.
3. Create output directory:

```bash
mkdir -p images/img_align_celeba
```

4. If VGG19 risk is accepted and the legacy runtime is available, a bounded run is:

```python
from srgan import SRGAN
model = SRGAN()
model.train(epochs=1, batch_size=1, sample_interval=1)
```

5. Expected sample outputs: `images/img_align_celeba/0.png` and low-resolution comparison files such as `images/img_align_celeba/0_lowres0.png`.

Adaptation notes:

- Default HR image size is `(256, 256, 3)` and LR size is `(64, 64, 3)`.
- The data loader samples from all files under `datasets/img_align_celeba/*`; it does not split train/test even though `is_testing` changes random flipping.
- `scipy.misc.imread` and `scipy.misc.imresize` are removed in newer SciPy versions; use a legacy SciPy runtime or port the loader to Pillow/skimage.
- The discriminator expects `disc_patch = (16, 16, 1)` for 256x256 HR images.

## Workflow 7: source-porting checklist

When adapting these scripts to a modern project, keep the old behavior explicit:

1. Replace legacy imports deliberately:
   - `keras`/`keras_contrib` may need `tensorflow.keras` or custom normalization layers.
   - `scipy.misc.imread/imresize` should be replaced with Pillow or skimage.
2. Preserve normalization contracts: most tensors are expected in `[-1, 1]` and sample images are rescaled back with `0.5 * x + 0.5`.
3. Preserve relative output paths or parameterize them. The source scripts write to relative `images/`, `saved_model/`, and `datasets/` paths.
4. Reduce default epochs from 20,000-30,000 to a test-controlled parameter.
5. Keep network operations behind explicit flags. PixelDA and SRGAN have hidden network paths via MNIST/MNIST-M and VGG19.
6. Validate layout with the bundled checker before importing Keras-heavy modules.
