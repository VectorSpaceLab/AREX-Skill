# Troubleshooting

## Purpose

Read this for install/import, CUDA, dependency, and cross-workflow issues before
opening a workflow-specific troubleshooting page.

## Install and dependency issues

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: models`, `dataio`, or `utils` | The repository package is not installed and no checkout was added to `PYTHONPATH`. | Install the distribution or pass `--repo-root /path/to/checkout` to bundled helpers. |
| `ModuleNotFoundError: torchsample` | The repo depends on legacy `torchsample==0.1.3`; the old dependency link may not be honored by modern pip. | Install `git+https://github.com/ozan-oktay/torchsample.git@master`, then verify `import torchsample`. |
| `ImportError: cannot import name 'Iterable' from 'collections'` | Legacy torchsample on Python versions where ABCs moved to `collections.abc`. | Patch the environment copy of torchsample or use a Python version compatible with both torchsample and the chosen PyTorch wheel. |
| `RuntimeError: Numpy is not available` or NumPy ABI warning from PyTorch | PyTorch 1.x with NumPy 2.x, or mismatched scientific wheels. | Use a coherent stack, usually PyTorch 1.x with `numpy<2` and matching SciPy/scikit-image/scikit-learn wheels. |
| `No module named SimpleITK`, `cv2`, `sklearn`, `visdom`, or `dominate` | Optional-looking packages are used by validation, metrics, visualizer, and HTML helpers. | Install the missing package in the same environment; use `opencv-python-headless` on servers. |

## CUDA issues

The unmodified repository is CUDA-first. `BaseModel` selects CUDA tensor types
when `gpu_ids` is non-empty, classifier/segmentation wrappers call `.cuda()`,
and several utility paths allocate CUDA tensors directly.

Use:

```bash
python scripts/check_env.py --repo-root /path/to/Attention-Gated-Networks --mode cuda
```

If CUDA is not available, either switch to a GPU environment or explicitly patch
the source modules for CPU-only use. Do not treat a CPU import check as
verification of this repository's default training, validation, or visualization
workflows.

## Visdom and output directory behavior

Training and testing instantiate `utils.visualiser.Visualiser`. When
`visualisation.display_id > 0`, it imports Visdom and tries to connect to a
Visdom server. If the task does not need live plots, pass `--disable-visdom` to
bundled runners or edit the config to use `display_id: 0`.

Model wrappers create checkpoint directories below
`model.checkpoints_dir/model.experiment_name`. Ensure that path is writable and
has enough disk space before a long training run.

## Config portability

Every shipped config uses old absolute dataset paths. Treat them as examples of
field structure only:

1. copy the config;
2. replace `data_path.<arch_type>` with a current, accessible path;
3. confirm `model.output_nc`, data labels, split names, and patch sizes;
4. choose a writable checkpoint directory and provide any external checkpoint;
5. pass `--repo-root` for a relative `--config` (config-relative data paths are
   resolved from the config parent, not the process cwd);
6. run `scripts/check_env.py --repo-root REPO --config CONFIG --mode imports`.

The checker and bundled runners fail fast on missing paths and historical
private `/vol/...` paths. They do not create fake datasets or weights. Override
the config before attempting training or evaluation.

## Workflow-specific pages

- For ultrasound HDF5, samplers, Sononet, `AggregatedClassifier`, and attention
  overlays, read `sub-skills/classification/references/troubleshooting.md`.
- For 3D NIfTI folders, CT deep supervision, feature maps, SimpleITK, and shape
  or metric failures, read `sub-skills/segmentation/references/troubleshooting.md`.

## Legacy source caveats

- The source training filename `train_classifaction.py` is misspelled. The
  generated skill uses `sub-skills/classification/scripts/run_classifier.py`
  instead.
- Some source code still uses deprecated PyTorch `Variable(..., volatile=True)`,
  old init function names, `F.upsample`, and legacy NumPy aliases. These usually
  emit warnings but may become errors in modern environments.
- The CRF post-processing script contains private path assumptions and is not
  bundled as a safe runnable helper.
