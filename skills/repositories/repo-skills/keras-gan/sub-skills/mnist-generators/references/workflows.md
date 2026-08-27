# MNIST-Generator Workflows

Use these workflows to inspect and adapt Keras-GAN's standalone MNIST-style scripts safely. They avoid network downloads, full default training, destructive writes, and unnecessary Keras imports unless explicitly requested.

## 1. Static inventory, no Keras import

Run this first when you need to identify classes, train signatures, default train calls, imports, and hard-coded output paths.

```bash
# Run from this generated skill's root directory.
python sub-skills/mnist-generators/scripts/model_inventory.py \
  --repo-root /path/to/a/Keras-GAN-checkout

python sub-skills/mnist-generators/scripts/model_inventory.py \
  --repo-root /path/to/a/Keras-GAN-checkout --json > keras_gan_mnist_inventory.json
```

Expected observations:

- The command prints one record for each covered standalone script: `gan`, `dcgan`, `cgan`, `acgan`, `sgan`, `infogan`, `lsgan`, `bgan`, `bigan`, `aae`, `cogan`, `dualgan`, `wgan`, and `wgan_gp`.
- It reports imports and AST-derived facts without importing TensorFlow, Keras, Matplotlib, SciPy, or datasets.
- Missing scripts are reported explicitly instead of causing a training or import attempt.

## 2. Import and constructor smoke checks

Use `dry_run_model.py` when the user asks whether a local checkout and runtime can load a representative model. The default is import-only; it does not construct a model and never calls `train(...)`.

```bash
# Run from this generated skill's root directory.
python sub-skills/mnist-generators/scripts/dry_run_model.py \
  --repo-root /path/to/a/Keras-GAN-checkout --model gan

python sub-skills/mnist-generators/scripts/dry_run_model.py \
  --repo-root /path/to/a/Keras-GAN-checkout --model dcgan --construct

python sub-skills/mnist-generators/scripts/dry_run_model.py \
  --repo-root /path/to/a/Keras-GAN-checkout --model wgan-gp
```

Supported `--model` values are `gan`, `dcgan`, `cgan`, `acgan`, `wgan`, and `wgan-gp`. These are representative native candidates for import/constructor smoke. For a broader static catalog, use `model_inventory.py` instead.

Expected observations:

| Mode | Expected success signal | Common non-fatal diagnostic |
|---|---|---|
| Import-only | `IMPORT OK` plus module path and class name. | `ImportError` explaining that legacy Keras/TensorFlow dependencies are missing or too new. |
| Constructor | `CONSTRUCT OK` plus selected attributes such as `latent_dim` and `img_shape`. | WGAN-GP may fail on modern Keras because `_Merge` was removed or because graph-mode gradient APIs changed. |

## 3. Compare GAN, DCGAN, and WGAN-GP safely

When asked to compare these models without expensive training:

1. Use the API table in [model-api-reference.md](model-api-reference.md):
   - `GAN`: MLP baseline, binary cross-entropy, `Adam(0.0002, 0.5)`, default `30000` epochs.
   - `DCGAN`: convolutional generator/discriminator, binary cross-entropy, `Adam(0.0002, 0.5)`, default `4000` epochs.
   - `WGANGP`: convolutional generator/critic, Wasserstein loss plus gradient penalty, `RMSprop(lr=0.00005)`, default `30000` epochs and batch-size-sensitive `RandomWeightedAverage`.
2. Run `dry_run_model.py` import-only for all three.
3. If the runtime is legacy-compatible, construct `gan` and `dcgan`; construct `wgan-gp` only when `_Merge` imports successfully and batch size 32 is acceptable.
4. Do not compare by launching their `__main__` defaults. If a training sanity check is necessary, run a one-epoch wrapper in a temporary working directory with synthetic or cached MNIST-shaped arrays.

## 4. Safe one-epoch smoke-run pattern

Only use a training smoke when import and constructor checks pass and the user accepts short compute plus local PNG/model writes. Run from a temporary directory so the scripts' hard-coded `images/` and `saved_model/` paths do not modify the source checkout.

```bash
mkdir -p keras-gan-smoke/images keras-gan-smoke/saved_model
cd keras-gan-smoke
python run_one_epoch_gan.py
```

A wrapper should:

- Import the chosen source file by path.
- Monkey-patch that module's `mnist.load_data` to return tiny cached or synthetic arrays shaped like MNIST: `X.shape == (N, 28, 28)`, labels shaped `(N,)` or `(N, 1)` for conditional scripts.
- Instantiate the class.
- Call `train(epochs=1, batch_size=<small>, sample_interval=1)` only after creating output directories.
- For `WGANGP`, keep `batch_size=32` unless `RandomWeightedAverage` is patched to use the dynamic batch size.
- For `ACGAN`, create `saved_model/` or monkey-patch `save_model` to a no-op because its training loop calls `save_model()` at epoch 0.

Minimal wrapper sketch for vanilla GAN:

```python
import importlib.util
import os
import numpy as np

repo_root = "/path/to/a/Keras-GAN-checkout"
script_path = os.path.join(repo_root, "gan", "gan.py")
spec = importlib.util.spec_from_file_location("keras_gan_vanilla", script_path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

x = np.random.randint(0, 255, size=(64, 28, 28), dtype="uint8")
y = np.random.randint(0, 10, size=(64,), dtype="uint8")
module.mnist.load_data = lambda: ((x, y), (x[:8], y[:8]))

os.makedirs("images", exist_ok=True)
model = module.GAN()
model.train(epochs=1, batch_size=8, sample_interval=1)
```

Expected output for a successful one-epoch smoke is one progress line and a PNG under `images/`. Treat image quality as meaningless for one epoch; the check only proves the loop, tensor shapes, and output handling.

## 5. Adapting to custom array data

Prefer adapting a copy of a script in a separate work directory. Keep the original source checkout unchanged.

Checklist:

1. Replace `mnist.load_data()` with a local array loader that returns `X_train` in `uint8` `[0,255]` or float arrays that you explicitly normalize to `[-1,1]`.
2. Update `img_rows`, `img_cols`, `channels`, and `img_shape` together. For RGB data use `channels=3` and ensure generator final `Conv2D(self.channels, ...)` or final dense reshape matches.
3. Update label handling for conditional models:
   - `CGAN` and `ACGAN` expect integer digit labels and `num_classes=10` by default.
   - `SGAN` creates an extra fake class at index `num_classes`.
   - `INFOGAN` expects one-hot categorical codes with width `num_classes` concatenated with Gaussian noise.
4. Keep output paths configurable in your copy. At minimum, replace hard-coded `images/...` and `saved_model/...` strings with paths under a run directory.
5. Reduce training defaults for smoke: `epochs=1`, small `batch_size`, `sample_interval=1`. Restore large runs only after shape and dependency checks pass.

## 6. Output handling

The scripts assume these directories already exist relative to the process working directory:

- `images/` for PNG samples in all covered scripts.
- `saved_model/` for `ACGAN.save_model`, `SGAN.save_model`, `INFOGAN.save_model`, and `AdversarialAutoencoder.save_model` when called.

Recommended safe run layout:

```text
keras-gan-run/
  images/
  saved_model/
  run_wrapper.py
```

After a run, preserve only artifacts the user asked for. Generated PNG grids are qualitative samples, not benchmark metrics. Full default runs may produce many PNGs and HDF5 files.
