# Augmentor Troubleshooting

## Purpose

Use this cross-cutting troubleshooting reference for install/import, dependency compatibility, save-format, optional dependency, and stale-skill questions. Workflow-specific failures live in the nearest sub-skill troubleshooting reference.

## Install and import failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'Augmentor'` | Package is not installed in the active Python environment. | Run `pip install Augmentor` in the environment that will execute the task. Verify with `python -c "import Augmentor; print(Augmentor.__version__)"`. |
| `ImportError` or odd Pillow behavior after installing both PIL and Pillow | Pillow is the maintained fork and Augmentor depends on Pillow; legacy PIL conflicts with Pillow. | Uninstall `PIL` if present, reinstall Pillow, then rerun the import check. |
| New Pillow errors around resampling filters such as `ANTIALIAS` | Augmentor 0.2.x uses legacy Pillow constants/strings. Pillow 10+ removed some legacy aliases. | Prefer `Pillow<10` for Augmentor 0.2.x, or use filters that exist in the installed Pillow version and smoke-test `resize()`. |
| NumPy compatibility warnings or failures in legacy code paths | Augmentor 0.2.x predates NumPy 2.x. | Prefer `numpy<2` when reproducing Augmentor 0.2.x behavior or when native tests cover older NumPy aliases. |
| `pip check` reports dependency conflicts | Mixed package manager installs or incompatible pins. | Use a fresh virtual environment, install Augmentor and exact optional dependencies needed for the task, then rerun `python scripts/augmentor_env_smoke.py`. |

## Save-format and Pillow errors

### JPEG alpha/channel failures

Augmentor ultimately calls Pillow to save images. If an augmented image has an alpha channel or an incompatible mode, forcing JPEG can fail.

Recovery:

1. Prefer `p.set_save_format("PNG")` for masks, alpha images, and smoke tests.
2. If JPEG output is required, convert images to RGB before saving or before creating fixtures.
3. Run a tiny `p.sample(2, multi_threaded=False)` before a large run.

### Format validation timing

`set_save_format("SOMETHING")` stores the requested value, but the final error may appear only when `sample()` writes output. Use known Pillow formats (`PNG`, `JPEG`, `BMP`, `GIF`) and prove the target format with the root smoke helper or a tiny pipeline.

## Optional dependency boundaries

Augmentor core requires Pillow, NumPy, and tqdm. Several APIs mention other ecosystems but do not make them core dependencies:

- `keras_generator()` and `keras_generator_from_array()` return NumPy batches directly. They do not import Keras/TensorFlow; downstream training code may require those frameworks.
- `keras_preprocess_func()` returns a callable for Keras-style image preprocessing, but the function itself does not import Keras.
- `torch_transform()` returns a callable that transforms a PIL image. `torchvision.transforms.Compose` and `ToTensor()` require torchvision/torch installed separately.
- `DataFramePipeline` requires pandas and is a legacy API with a verified pandas compatibility issue in this checkout: `ImageUtilities.scan_dataframe()` calls `Categorical.get_values()`, which failed with pandas 1.5.3 and pandas 3.0.5. Prefer ordinary `Pipeline` or `DataPipeline`, or patch `scan_dataframe` in a maintenance task before relying on DataFramePipeline.

## Stochastic and reproducibility surprises

- Every pipeline operation has a probability; even `sample(n)` can return different transformations for the same source image.
- Use `p.set_seed(seed)` immediately before a smoke run.
- For deterministic debugging, call `p.sample(..., multi_threaded=False)`.
- Do not assert UUID output filenames; assert counts, dimensions, formats, labels, and that outputs open with Pillow.

## Where to troubleshoot next

- Disk scanning, output folders, empty inputs, and multithreading: `../sub-skills/pipeline-augmentation/references/troubleshooting.md`.
- Operation parameter ranges and custom operation errors: `../sub-skills/operation-reference/references/troubleshooting.md`.
- Mask/ground-truth filename, class, dimension, and DataPipeline input issues: `../sub-skills/masks-and-arrays/references/troubleshooting.md`.
- Generator shapes, optional frameworks, and DataFramePipeline failures: `../sub-skills/generators-and-frameworks/references/troubleshooting.md`.
