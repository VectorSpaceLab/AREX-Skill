# Directory-Backed Pipeline Workflows

These recipes use only public `Augmentor` APIs and generated/local image files. They do not require notebooks, external datasets, network access, GPUs, or ML frameworks.

## 1. Build and sample a disk pipeline

Use this when a directory already contains images, or class subfolders containing images.

```python
import Augmentor

p = Augmentor.Pipeline("data/train", output_directory="output")
p.rotate(probability=0.7, max_left_rotation=10, max_right_rotation=10)
p.zoom(probability=0.3, min_factor=1.1, max_factor=1.5)
p.flip_left_right(probability=0.5)
p.set_save_format("PNG")

p.status()          # prints operation count, image count, labels, dimensions, formats
p.sample(1000)      # writes 1000 stochastic outputs under the pipeline output directory
```

Notes:

- Each operation has a `probability`; the operation is considered independently as each image passes through the pipeline.
- `sample(n)` chooses `n` source images with replacement. It does not mean “augment each source image `n` times”.
- The default `multi_threaded=True` is useful for many disk writes, but can be slower for tiny images and is harder to reason about for exact reproducibility.

## 2. Deterministic tiny or debug sampling

Use single-threaded sampling and seed before sampling. Do not compare generated filenames because Augmentor includes a UUID in output names.

```python
import Augmentor

p = Augmentor.Pipeline("data/train")
p.rotate90(probability=1)
p.resize(probability=1, width=64, height=64)
p.set_save_format("PNG")

p.set_seed(7)
p.sample(4, multi_threaded=False)
```

For reproducible checks, compare output count, dimensions, file readability, and broad pixel properties rather than filename strings.

## 3. Process every image exactly once

`process()` is a convenience for applying the current pipeline to every image once. It is often appropriate for resizing or normalizing a dataset.

```python
import Augmentor

p = Augmentor.Pipeline("raw_images", output_directory="resized")
p.resize(probability=1, width=256, height=256)
p.set_save_format("PNG")
p.process()
```

Important details:

- `process()` internally calls `sample(0, multi_threaded=True)`.
- Set transformation probabilities to `1` when you need every source image transformed the same way.
- If exact single-threaded order matters, use `p.sample(0, multi_threaded=False)` instead of `process()`.

## 4. Use class subfolders safely

When the source has immediate subdirectories, those subdirectories become class labels. A single pipeline applies the same operations to all classes.

```text
data/train/
├── cat/
│   ├── c1.jpg
│   └── c2.jpg
└── dog/
    ├── d1.jpg
    └── d2.jpg
```

```python
import Augmentor

p = Augmentor.Pipeline("data/train", output_directory="output")
p.flip_left_right(probability=0.5)
p.rotate(probability=0.4, max_left_rotation=8, max_right_rotation=8)
p.sample(200)
```

For multiple class folders, outputs are written below the configured output directory by class label, for example `data/train/output/cat/` and `data/train/output/dog/`.

## 5. Per-class augmentation strategy

Use one pipeline per class when different classes need different augmentation probabilities or sample counts. Point each pipeline at the class directory so that the class folder name becomes the label for that pipeline.

```python
from pathlib import Path
import Augmentor

train_root = Path("data/train")
plan = {
    "minority": {"samples": 800, "ops": "strong"},
    "majority": {"samples": 200, "ops": "light"},
}

for class_name, cfg in plan.items():
    source = train_root / class_name
    p = Augmentor.Pipeline(str(source), output_directory=f"../augmented/{class_name}")

    if cfg["ops"] == "strong":
        p.rotate(probability=0.8, max_left_rotation=12, max_right_rotation=12)
        p.flip_left_right(probability=0.5)
        p.zoom(probability=0.4, min_factor=1.05, max_factor=1.3)
    else:
        p.flip_left_right(probability=0.2)
        p.rotate(probability=0.2, max_left_rotation=5, max_right_rotation=5)

    p.set_save_format("PNG")
    p.sample(cfg["samples"], multi_threaded=False)
```

This pattern avoids applying a global operation list to every class. Because Augmentor joins relative `output_directory` values to the source directory, check the resolved output path printed during pipeline initialization before launching a large run.

## 6. Repoint a pipeline with `add_further_directory()`

`add_further_directory(new_source_directory, new_output_directory="output")` runs the same directory population path for another directory.

```python
import Augmentor

p = Augmentor.Pipeline("data/train_a")
p.flip_left_right(probability=0.5)
p.sample(100)

p.add_further_directory("data/train_b", new_output_directory="output")
p.status()  # confirm which images/classes are active after repopulation
p.sample(100)
```

Because this version repopulates the pipeline image list, use `status()` after calling it. If the goal is separate outputs per dataset, two explicit `Pipeline(...)` objects are easier to audit.

## 7. Output format choices

- Use `p.set_save_format("PNG")` for alpha-channel PNGs or when JPEG compatibility is uncertain.
- Use `p.set_save_format("auto")` to save using each input image extension/format again.
- Invalid or incompatible formats may not fail until saving, because the final write is delegated to Pillow.
