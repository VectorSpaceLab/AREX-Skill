# Troubleshooting: Domain Adaptation and Restoration

Use this guide to diagnose Keras-GAN CCGAN, ContextEncoder, PixelDA, and SRGAN issues without reopening the original checkout.

## First triage

1. Identify the workflow and whether the error happened during layout validation, import/construction, data loading, training, or saving samples.
2. Run the safe checker when the issue involves local files:

```bash
python sub-skills/domain-and-restoration/scripts/check_restoration_layout.py --workflow pixelda --data-root ./datasets --json
python sub-skills/domain-and-restoration/scripts/check_restoration_layout.py --workflow srgan --data-root ./datasets --dataset-name img_align_celeba
python sub-skills/domain-and-restoration/scripts/check_restoration_layout.py --workflow ccgan --check-output-dirs --output-root .
```

3. If the error happened before model construction, avoid running the upstream script again until data/cache and output directories are known.
4. If the error happened inside Keras/TensorFlow, confirm that the runtime is legacy-compatible. These scripts target standalone Keras 2.x with TensorFlow 1.x behavior and keras-contrib.

## Legacy runtime and imports

### Symptom: `ModuleNotFoundError: No module named 'keras_contrib'`

Affected workflows: CCGAN and PixelDA use `InstanceNormalization` from keras-contrib. SRGAN imports it even though the visible SRGAN architecture does not depend on it directly.

Fixes:

- Use a legacy runtime with `keras-contrib` installed.
- For a modern port, replace `InstanceNormalization` with an equivalent layer implementation and update imports consistently.
- Do not treat a modern TensorFlow/Keras import failure as proof that the model design is invalid; it is a dependency-staleness issue.

### Symptom: TensorFlow 2.x / Keras 3 import errors, graph-mode errors, or optimizer signature mismatches

Likely causes:

- The scripts use standalone `keras`, not `tensorflow.keras`.
- They rely on TensorFlow 1.x graph/session behavior.
- Optimizers are created as `Adam(0.0002, 0.5)`.

Fixes:

- Prefer the verified legacy stack for faithful execution.
- If porting, update imports, optimizer arguments, normalization layers, and any backend/session calls together. Do not change only one import line.

## SciPy image API failures

### Symptom: `AttributeError: module 'scipy.misc' has no attribute 'imresize'`

Affected workflows: CCGAN uses `scipy.misc.imresize`; SRGAN's data loader uses `scipy.misc.imresize`.

Fixes:

- Use legacy SciPy where `scipy.misc.imresize` is available, or
- Port resizing to Pillow or `skimage.transform.resize`. Preserve output sizes and dtype/range handling.

### Symptom: `AttributeError: module 'scipy.misc' has no attribute 'imread'`

Affected workflow: SRGAN data loader.

Fixes:

- Use legacy SciPy where `scipy.misc.imread` exists, or
- Replace reading with Pillow, e.g. open as RGB, then convert to a NumPy array. Preserve the source behavior of RGB channels and later normalization to `[-1, 1]`.

## Output directory errors

### Symptom: `FileNotFoundError` or `OSError` while saving `images/...png` or `saved_model/...hdf5`

Cause: source scripts often assume output directories already exist.

Fix:

```bash
mkdir -p images saved_model
mkdir -p images/img_align_celeba  # SRGAN sample output
```

Then rerun only a bounded smoke command, not the full default training loop.

Use the checker to diagnose without creating directories:

```bash
python sub-skills/domain-and-restoration/scripts/check_restoration_layout.py --workflow srgan --check-output-dirs --output-root .
```

## CCGAN-specific issues

### Symptom: shape mismatch around discriminator validity targets

Expected target shape is `(batch_size, 4, 4, 1)` for the default 32x32 CCGAN. If you change image size, discriminator stride depth, or patch head, recompute this target shape.

### Symptom: mask has no visible effect

`mask_randomly` sets masked pixels to numerical `0`. If your images are normalized to `[-1, 1]`, zero represents mid-gray, not black. This matches source behavior. If a port uses a different normalization, keep the mask value explicit.

### Symptom: MNIST download attempted unexpectedly

`train()` calls Keras `mnist.load_data()`. Do not call `train()` in a no-network environment unless the Keras MNIST cache is already present or the user permits downloads.

## ContextEncoder-specific issues

### Symptom: generator output shape differs from input image shape

This is expected. `ContextEncoder` generator outputs only the missing patch `(8, 8, 3)`, while the sample routine composites that patch into the full `(32, 32, 3)` image.

### Symptom: training set smaller than expected

The source training loop filters CIFAR-10 to cats and dogs only (`labels == 3` or `labels == 5`). This is intentional for the educational example.

### Symptom: CIFAR-10 download attempted unexpectedly

`train()` calls Keras `cifar10.load_data()`. Do not call training in a no-network environment unless the dataset cache is available or network is allowed.

## PixelDA-specific issues

### Symptom: constructor starts downloading MNIST-M

Cause: `PixelDA()` constructs `DataLoader`, and `DataLoader.__init__` immediately calls `setup_mnist` and `setup_mnistm`. If `datasets/mnistm_x.npy` is absent and `datasets/keras_mnistm.pkl` is absent, the loader downloads from a hard-coded MNIST-M URL.

Fixes:

- Before construction, run:

```bash
python sub-skills/domain-and-restoration/scripts/check_restoration_layout.py --workflow pixelda --data-root ./datasets --json
```

- Provide complete cached arrays (`mnist_x.npy`, `mnist_y.npy`, `mnistm_x.npy`, `mnistm_y.npy`) for offline use.
- Or provide `keras_mnistm.pkl` and allow/cache Keras MNIST so arrays can be rebuilt.
- Do not instantiate `DataLoader` when network is disallowed and the required cache/source files are incomplete.

### Symptom: only `keras_mnistm.pkl.gz` is present but the loader still fails

The source code downloads a `.gz` file only when the decompressed `.pkl` is absent, then decompresses it. It does not simply read an already-present `.gz` as the source. Decompress the file to `datasets/keras_mnistm.pkl` or prepare `.npy` arrays before offline construction.

### Symptom: label or domain mismatch

Expected domains:

- `domain='A'`: MNIST arrays and labels.
- any other domain value: MNIST-M arrays and labels.

MNIST-M labels are copied from MNIST labels during cache construction. If you rebuild caches externally, keep image order and labels aligned.

### Symptom: `skimage` resize differences or warnings

`pixelda/data_loader.py` uses `skimage.transform.resize` imported as `imresize`. Modern scikit-image may return floats with anti-aliasing behavior. Preserve normalization and shape `(32, 32, 3)` when porting or precomputing arrays.

## SRGAN-specific issues

### Symptom: `SRGAN()` tries to download VGG19 ImageNet weights

Cause: `SRGAN.__init__` calls `build_vgg()`, which calls `VGG19(weights="imagenet")`.

Fixes:

- For layout-only validation, do not instantiate `SRGAN()`. Use:

```bash
python sub-skills/domain-and-restoration/scripts/check_restoration_layout.py --workflow srgan --data-root ./datasets --dataset-name img_align_celeba
```

- If a constructor smoke test is required, ensure weights are already cached or ask for explicit download permission.
- For a code-port smoke test, temporarily replace `build_vgg()` with a local/random-weight feature extractor only if the user accepts that this no longer matches perceptual-loss training.

### Symptom: `ValueError: 'a' cannot be empty unless no samples are taken`

Cause: `srgan.data_loader.DataLoader.load_data` globs `./datasets/{dataset_name}/*` and passes the result to `np.random.choice`. The dataset directory is missing or empty.

Fix:

```bash
python sub-skills/domain-and-restoration/scripts/check_restoration_layout.py --workflow srgan --data-root ./datasets --dataset-name img_align_celeba --min-images 1
```

Place image files directly inside `datasets/img_align_celeba/`, not only in nested directories.

### Symptom: generated low-resolution or high-resolution shapes are unexpected

Default shapes are HR `(256, 256, 3)` and LR `(64, 64, 3)`. If changing `lr_height`, `lr_width`, or `img_res`, update the generator input, data loader, discriminator patch shape, and VGG input consistently.

### Symptom: very slow or memory-heavy training

SRGAN uses 256x256 images, a 16-block generator, VGG19 features, and adversarial training. Use batch size 1 for smoke tests and avoid default 30,000 epochs.

## Full-training warnings

The source `__main__` blocks use long educational defaults:

- CCGAN: 20,000 epochs.
- ContextEncoder: 30,000 epochs.
- PixelDA: 30,000 epochs.
- SRGAN: 30,000 epochs.

Never use those defaults as routine verification. Use one-epoch smoke runs only after data/cache, output directories, and network/weight risks are explicit.
