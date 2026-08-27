# MNIST-Generator Troubleshooting

This page lists failure signals specific to the standalone MNIST-style Keras-GAN scripts and safe recovery actions.

## Legacy Keras/TensorFlow import failures

Symptoms:

- `ModuleNotFoundError: No module named 'keras'`
- `ImportError: cannot import name 'merge' from 'keras.layers'`
- TensorFlow descriptor/protobuf errors during import.
- Eager-mode or graph-gradient errors when constructing Wasserstein models.
- Constructors work in old examples but fail after installing latest `keras` or `tensorflow`.

Recovery:

1. Use a legacy stack: Python 3.7-era, TensorFlow 1.15.x, Keras 2.2.x, NumPy 1.18.x, SciPy 1.2.x, `h5py<3`, and `protobuf<3.21`.
2. Do not repair by installing latest standalone Keras. These scripts use Keras 2.2-era module paths such as `keras.layers.advanced_activations`, `keras.layers.convolutional`, and `keras.layers.merge`.
3. For static investigation, avoid the runtime entirely and run `scripts/model_inventory.py`.
4. For runtime diagnosis, run `scripts/dry_run_model.py` import-only first; add `--construct` only after imports succeed.

## WGAN-GP `_Merge` failure

Symptoms:

- `ImportError: cannot import name '_Merge' from 'keras.layers.merge'`
- `ModuleNotFoundError: No module named 'keras.layers.merge'`
- Constructor errors involving `RandomWeightedAverage`, `K.gradients`, or graph tensors.

Cause:

- `wgan_gp/wgan_gp.py` subclasses the private legacy class `keras.layers.merge._Merge`. Modern Keras removed or moved this private API.
- `RandomWeightedAverage._merge_function` uses `alpha = K.random_uniform((32, 1, 1, 1))`, so the script assumes batch size 32 unless patched.

Recovery options:

1. If the goal is to inspect the original implementation, use the legacy runtime and keep WGAN-GP batch size 32 for smoke checks.
2. If the goal is a modern port, replace `_Merge` with a supported custom `Layer` or `Lambda` that samples `alpha` with dynamic batch size, for example `K.shape(inputs[0])[0]`.
3. If the goal is a quick Wasserstein baseline, use `wgan/wgan.py` instead; it uses clipping rather than gradient penalty and avoids `_Merge`.
4. Do not treat `_Merge` import failure as evidence that the repository source is missing; it is a dependency-version mismatch.

## `keras_contrib` confusion

The covered MNIST-generator scripts do not import `keras_contrib`, but the broader Keras-GAN repository requirements include it for other sub-skills. If a shared environment setup fails with `No matching distribution found for keras-contrib`, install it from the documented Git URL rather than PyPI. If a workflow is only inspecting the models covered here, `keras_contrib` is not required by these source files.

## Missing `images/` or `saved_model/`

Symptoms:

- `FileNotFoundError: [Errno 2] No such file or directory: 'images/mnist_0.png'`
- HDF5 or JSON save failures under `saved_model/`.

Recovery:

```bash
mkdir -p images saved_model
```

Run from a temporary output directory, not from the source checkout, when doing smoke training. The scripts hard-code relative output paths and do not create directories themselves.

Model-specific notes:

- `ACGAN.train(...)` calls `save_model()` whenever `epoch % sample_interval == 0`, including epoch 0, so `saved_model/` is needed even for a one-epoch smoke unless `save_model` is monkey-patched.
- `AdversarialAutoencoder.save_model()` is stale: it calls `save(self.generator, "aae_generator")` even though the class defines `self.decoder`, not `self.generator`. Patch to `save(self.decoder, "aae_decoder")` or avoid calling it.

## MNIST or CIFAR download/cache failures

Symptoms:

- A first training call hangs or fails while `keras.datasets.mnist.load_data()` tries to download data.
- Network, SSL, or proxy errors from Keras dataset utilities.
- User adapts to CIFAR-10 and hits shape/channel errors.

Recovery:

1. For smoke tests, monkey-patch `mnist.load_data` in the imported module to return tiny synthetic or cached arrays. See [workflows.md](workflows.md).
2. For offline real runs, pre-populate the Keras datasets cache or replace `mnist.load_data()` with a local file loader.
3. For CIFAR-style adaptation, update both data and architecture:
   - Use `keras.datasets.cifar10.load_data()` or a local CIFAR-shaped loader.
   - Set `img_rows=32`, `img_cols=32`, `channels=3`, and `img_shape=(32, 32, 3)`.
   - Ensure final generator output channels and discriminator input shapes match RGB.
   - Keep labels as integers for CGAN/ACGAN or one-hot vectors where the script explicitly uses `to_categorical`.

## Long training or apparent hangs

Symptoms:

- No useful sample quality for many minutes on CPU.
- A direct script run appears to hang after model summaries.
- Disk fills with many `images/*.png` or `saved_model/*.hdf5` artifacts.

Cause:

- README examples run `python3 script.py`, but the `__main__` defaults are large: 4,000 to 50,000 epochs depending on the model.
- Each epoch may perform multiple critic/discriminator updates (`WGAN.n_critic=5`, `WGANGP.n_critic=5`, `DUALGAN` local `n_critic=4`).

Recovery:

1. Start with static inventory and import-only dry run.
2. If training is necessary, use a one-epoch wrapper with synthetic/cached data and a temporary output directory.
3. Increase epochs only after tensor shapes, output directories, and dependencies are verified.
4. Set `MPLBACKEND=Agg` in headless environments before training or sampling.

## SciPy rotation and deprecated APIs

`COGAN` and `DUALGAN` call SciPy rotation to create a synthetic rotated-MNIST domain. Use SciPy 1.2-era behavior for faithful reproduction. In modern SciPy ports, prefer `scipy.ndimage.rotate` and verify that output shapes remain compatible with the script's reshape/flatten logic.

## Multi-output loss and label-shape errors

Symptoms:

- `ValueError` about target arrays, sparse categorical labels, or class weights.
- `train_on_batch` returns more loss entries than the print format expects.

Recovery:

- `CGAN` labels are integer arrays shaped `(batch, 1)`.
- `ACGAN` discriminator targets are `[validity, integer_label]` and use sparse categorical cross-entropy.
- `SGAN` discriminator targets are `[validity, one_hot_label_plus_fake]`; fake labels use class index `num_classes`.
- `INFOGAN` generator input concatenates Gaussian noise width 62 with one-hot categorical labels width 10, producing `latent_dim=72`.
- Preserve the original loss list order when porting multi-output models.
