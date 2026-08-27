# Keras-GAN Cross-Cutting Troubleshooting

Use this root troubleshooting reference for failures that affect multiple Keras-GAN script families. Workflow-specific details live in each sub-skill's `references/troubleshooting.md`.

## Quick symptom map

| Symptom | Likely cause | Next step |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'keras'` | No standalone legacy Keras runtime. | Read [compatibility-and-install.md](compatibility-and-install.md); use a scratch legacy environment. |
| TensorFlow/Keras import works but model code fails on optimizer args or graph APIs | Modern Keras/TensorFlow mismatch. | Use legacy Keras 2.2/TensorFlow 1.x or port the script deliberately. |
| `ModuleNotFoundError: No module named 'keras_contrib'` | CycleGAN, DiscoGAN, CCGAN, PixelDA, and SRGAN imports may require keras-contrib. | Install the historical keras-contrib in a scratch environment or replace `InstanceNormalization` in a modern port. |
| `Descriptors cannot be created directly` while importing TensorFlow 1.x | Protobuf is too new for TensorFlow 1.x. | Pin protobuf below 3.21 in the legacy environment. |
| `AttributeError: scipy.misc has no attribute imread/imresize` | SciPy is too new. | Use SciPy 1.2.x or port image I/O/resizing to Pillow/skimage with matching normalization. |
| `ModuleNotFoundError: No module named 'data_loader'` | Standalone scripts expect a sibling `data_loader.py` on the Python path. | Run from the workflow directory or temporarily add that directory to `sys.path`. |
| `ValueError: 'a' cannot be empty unless no samples are taken` | A loader glob matched no dataset files. | Use the relevant bundled dataset checker and verify working directory plus split names. |
| `FileNotFoundError` or `OSError` writing PNG/HDF5 outputs | Relative `images/` or `saved_model/` directory is missing or points to the wrong run directory. | Create output directories in a scratch run directory before a bounded run. |
| Training appears stuck or writes many files | The original `__main__` defaults use thousands of epochs. | Stop and replace with a one-epoch wrapper or static/constructor checks. |

## Environment diagnosis

From this generated skill root:

```bash
python scripts/check_legacy_runtime.py
python scripts/check_legacy_runtime.py --json
```

The checker is safe: it imports dependency packages and builds a tiny Keras graph, but it does not import source scripts, download datasets, train, or write model outputs.

## Data and network risks

The repository has several hidden or direct network paths:

- Keras MNIST and CIFAR-10 loaders can download dataset caches during `train()`.
- PixelDA can download MNIST-M from a hard-coded URL if cache/source files are incomplete.
- SRGAN construction can request VGG19 ImageNet weights.
- CycleGAN/DiscoGAN/Pix2Pix download shell scripts fetch external archives.

Ask before allowing network access unless the user's environment policy already permits it. When network is not allowed, validate local files first and avoid constructors that trigger downloads.

## Output and mutation risks

The scripts are educational and often hard-code relative outputs:

- Most sample methods write `images/...png`.
- ACGAN, SGAN, InfoGAN, CCGAN, and optional save methods write `saved_model/...json` or `.hdf5`.
- PixelDA writes cache arrays under `datasets/` during loader construction.

For any training or sampling smoke, run in a caller-approved scratch directory and create expected directories explicitly. Do not let generated verification mutate the source checkout by accident.

## Choosing a recovery path

- If the task is usage, diagnosis, or adaptation in the original legacy style, prefer a scratch legacy environment and the bundled safe helpers.
- If the task is adding modern features, port the script family systematically and add tests for imports, shapes, data loaders, and one-step training.
- If the task is model-quality reproduction, do not rely on the generated skill alone. Full training requires datasets, compute, seeds, and acceptance metrics beyond this operating graph.
