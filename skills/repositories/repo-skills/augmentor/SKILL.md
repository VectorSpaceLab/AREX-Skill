---
name: augmentor
description: "Use Augmentor for Pillow-based image augmentation pipelines,
  operation selection, mask-safe augmentation, array/generator workflows, and
  package-specific troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Augmentor Repo Skill

Use this skill when a task names **Augmentor** or asks for Augmentor-style image augmentation: stochastic `Pipeline` construction, Pillow/NumPy operations, class-folder scanning, generated image output, ground-truth/mask pairing, in-memory `DataPipeline` arrays, Keras-style batches, or torchvision transform callables.

Augmentor is a CPU/Pillow/NumPy package. It does not require CUDA, ROCm, MPS, Keras/TensorFlow, or torch/torchvision for core package workflows.

## First checks

1. Install the package in the task environment:

   ```bash
   pip install Augmentor
   ```

   For Augmentor 0.2.x compatibility-sensitive work, prefer:

   ```bash
   pip install 'Augmentor==0.2.12' 'Pillow<10' 'numpy<2' tqdm
   ```

2. Verify the import:

   ```bash
   python -c "import Augmentor; print(Augmentor.__version__)"
   ```

3. For a safe end-to-end check, run the bundled smoke helper:

   ```bash
   python scripts/augmentor_env_smoke.py --samples 2 --size 24
   ```

4. If the task uses masks, framework generators, or optional pandas/torch/Keras integrations, route to the matching sub-skill before giving final code.

## Route by task

| User task or signal | Read next |
| --- | --- |
| Create a `Pipeline` from a folder, scan class subfolders, write augmented files, choose `sample()` vs `process()`, control output directories, seeds, or multithreading. | `sub-skills/pipeline-augmentation/SKILL.md` |
| Choose operations, fix probability/range errors, understand rotate/crop/zoom/skew/distortion/color operations, or write custom `Operation` subclasses. | `sub-skills/operation-reference/SKILL.md` |
| Apply identical transforms to images and masks, use `ground_truth()`, verify matched filenames/classes/dimensions, or build grouped in-memory original+mask arrays. | `sub-skills/masks-and-arrays/SKILL.md` |
| Use `keras_generator`, `keras_generator_from_array`, `keras_preprocess_func`, `torch_transform`, or `DataFramePipeline`; debug batch shapes or optional framework dependencies. | `sub-skills/generators-and-frameworks/SKILL.md` |
| Diagnose install/import, Pillow/PIL, save-format, dependency, stochastic reproducibility, or optional dependency issues that span several workflows. | `references/troubleshooting.md` |
| Check whether this skill matches a local Augmentor checkout or package version. | `references/repo-provenance.md` |

## Minimal examples

### Disk-backed augmentation

```python
import Augmentor

p = Augmentor.Pipeline("train_images", output_directory="output")
p.rotate(probability=0.7, max_left_rotation=10, max_right_rotation=10)
p.flip_left_right(probability=0.5)
p.resize(probability=1.0, width=224, height=224)
p.set_save_format("PNG")
p.sample(100, multi_threaded=False)
```

Outputs are written under the source directory's output folder. If the source directory has immediate subdirectories, Augmentor treats those subdirectories as class labels. Read `pipeline-augmentation` before changing layouts or counting class outputs.

### Mask-safe augmentation

```python
import Augmentor

p = Augmentor.Pipeline("images")
p.ground_truth("masks")
p.rotate(probability=1.0, max_left_rotation=5, max_right_rotation=5)
p.sample(20)
```

Use `masks-and-arrays` to validate matched names, class subfolders, equal dimensions, and multiple masks per image.

### Generator batches

```python
import Augmentor

p = Augmentor.Pipeline("train_images")
g = p.keras_generator(batch_size=32, scaled=True, image_data_format="channels_last")
images, labels = next(g)
```

The direct Augmentor generator APIs return NumPy arrays and do not import Keras/TensorFlow. Read `generators-and-frameworks` before promising external framework behavior.

## Compatibility caveats

- Augmentor 0.2.x predates newer Pillow and NumPy APIs. For legacy behavior, `Pillow<10` and `numpy<2` are safer than latest-only installs.
- `DataFramePipeline` is optional and legacy. This checkout's `scan_dataframe()` path failed with pandas 1.5.3 and 3.0.5 because it calls `Categorical.get_values()`. Prefer ordinary `Pipeline` or `DataPipeline` unless maintaining or patching Augmentor.
- `torch_transform()` returns a PIL-image callable; torchvision is optional and only needed for `torchvision.transforms.Compose` or `ToTensor()`.
- Do not assert exact output filenames in tests or examples. Augmentor uses UUID filenames; assert counts, dimensions, formats, labels, and readable images.

## Bundled references and scripts

- `references/quickstart.md` gives a compact route map and common snippets.
- `references/troubleshooting.md` covers cross-cutting install/import, dependency, save-format, optional dependency, and reproducibility issues.
- `references/repo-provenance.md` records the source version and evidence baseline for refresh decisions.
- `references/repo-routing-metadata.json` provides managed repo-skills-router metadata for import tooling.
- `scripts/augmentor_env_smoke.py` runs a safe generated-fixture smoke check for the active Python environment.

## Boundaries

Use this skill for **using Augmentor as a package**. For maintainer tasks that modify Augmentor source code, packaging, CI, or docs, combine this usage skill with a Python repository maintenance workflow and run focused source tests after editing.
