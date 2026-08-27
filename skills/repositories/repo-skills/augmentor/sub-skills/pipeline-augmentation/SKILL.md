---
name: pipeline-augmentation
description: "Directory-backed Augmentor Pipeline workflows for folder scanning,
  class-aware disk augmentation, output control, sampling, status, seeding, and
  threading."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Pipeline Augmentation

Use this sub-skill when the task is a directory-backed `Augmentor.Pipeline` workflow: scan image folders, interpret class subfolders, add pipeline-level operations, write augmented samples to disk, process every image once, set output save formats, inspect status, set seeds, or decide whether to disable multithreading.

## Fast routing

- For the operation catalog, probability/range validation, or custom `Operation` subclasses, route to `operation-reference`.
- For ground-truth masks, paired mask directories, or in-memory grouped image/mask arrays, route to `masks-and-arrays`.
- For Keras-style generators, PyTorch/torchvision transforms, DataFrame input, or framework integration, route to `generators-and-frameworks`.
- For disk pipeline layout, sampling, output folders, class subfolders, reproducibility, and per-class strategy, stay here and use the bundled references.

## Core API facts

- Constructor: `Augmentor.Pipeline(source_directory=None, output_directory="output", save_format=None)`.
- Disk execution: `sample(n, multi_threaded=True)` writes `n` sampled augmented images; `process()` processes every image once and internally uses `sample(0, multi_threaded=True)`.
- Output/save controls: `set_save_format(save_format)` accepts formats understood by Pillow; pass `"auto"` to return to per-input extension behavior.
- Inspection/control: `status()` prints operation/image/class/dimension/format status; `set_seed(seed)` seeds Python `random` and NumPy random state.
- Directory switching: `add_further_directory(new_source_directory, new_output_directory="output")` reruns the same population path for another source directory; inspect `status()` after calling before assuming what images are active.
- `ImageUtilities.scan()` ignores the configured output directory and treats immediate source subdirectories as class labels.

## Minimal disk pattern

```python
import Augmentor

p = Augmentor.Pipeline("train_images", output_directory="output")
p.rotate(probability=0.7, max_left_rotation=10, max_right_rotation=10)
p.flip_left_right(probability=0.5)
p.resize(probability=1.0, width=224, height=224)
p.set_save_format("PNG")

p.set_seed(123)
p.sample(500, multi_threaded=False)  # deterministic transform order is easiest single-threaded
```

Use `p.process()` when each source image should be processed once, usually with every required operation set to `probability=1`. If exact single-threaded execution matters, prefer `p.sample(0, multi_threaded=False)`.

## Bundled references and helper

- [Workflows](references/workflows.md): end-to-end disk recipes, `sample()` versus `process()`, `add_further_directory()`, and per-class augmentation strategy.
- [Data layouts](references/data-layouts.md): class-subfolder scanning, output directory placement, file extensions, and class labels.
- [Troubleshooting](references/troubleshooting.md): empty inputs, output surprises, save-format errors, missing operations, and reproducibility.
- [Disk smoke script](scripts/augmentor_pipeline_disk_smoke.py): generates temporary PIL images, builds a class-aware disk pipeline, samples tiny PNG outputs, and asserts files were written.
