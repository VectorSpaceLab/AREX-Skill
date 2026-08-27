# Mask Workflows

Augmentor has two mask-safe patterns:

- `Pipeline.ground_truth(ground_truth_directory)` for disk-backed original images plus one ground-truth image per original image.
- `DataPipeline(images, labels=None)` for in-memory original images plus one or more masks per sample.

This page focuses on disk-backed ground truth. See [data-formats.md](data-formats.md) for grouped arrays.

## Directory-backed ground truth

```python
import Augmentor

p = Augmentor.Pipeline("images")
p.ground_truth("masks")
p.rotate(probability=1, max_left_rotation=5, max_right_rotation=5)
p.zoom_random(probability=0.5, percentage_area=0.8)
p.sample(50)
```

`ground_truth()` attaches a mask/ground-truth path to each image already scanned by the pipeline. During `_execute`, Augmentor opens the original and its ground truth together, applies the same selected operation instances to the whole image list, and saves each transformed image.

## Matching rules

| Dataset layout | Required match |
| --- | --- |
| Single flat class/input folder | Ground-truth file has the same filename as the original image. |
| Class-subfolder dataset | Ground-truth root repeats the class subfolder and filename, for example `images/cat/im0.png` pairs with `masks/cat/im0.png`. |
| Dimension safety | Original and ground-truth images should have equal width and height before sampling. Augmentor checks this in the class-subfolder matching path; verify it yourself for flat layouts before relying on a long run. |

Recommended preflight:

```python
p = Augmentor.Pipeline("images")
p.ground_truth("masks")
matched = [(src, gt) for src, gt in p.get_ground_truth_paths() if gt is not None]
assert matched, "no ground-truth images matched"
assert len(matched) == len(p.augmentor_images), "some originals have no mask"
```

`get_ground_truth_paths()` returns a list of `(image_path, ground_truth_path)` pairs for every scanned original image and prints the same pairs for manual inspection. An unmatched image appears with `ground_truth_path` as `None`.

## Output behavior

- `Pipeline.sample(n)` writes augmented files to the pipeline output directory; with one ground-truth companion, expect roughly two output files per generated sample.
- The same randomly selected operations are applied to every member of a ground-truth group.
- Ground-truth processing is enabled only when `ground_truth()` finds at least one match.
- Use the pipeline output/layout guidance from the disk pipeline sub-skill for output directory and save-format details.

## Operation choice for masks

Prefer geometric operations that should affect originals and masks identically:

- rotate variants
- flips
- crop/zoom/scale when the resulting dimensions are acceptable
- shear/skew/distortion only when the mask interpretation remains valid

Be careful with color/intensity operations on segmentation masks. Augmentor can apply them to every image in the group, but changing mask pixel values can corrupt class IDs. For masks with categorical values, use geometric-only pipelines unless you intentionally want the mask image colors transformed.

## When to use `DataPipeline` instead

Use `DataPipeline` instead of directory ground truth when:

- each original has more than one mask;
- images/masks already exist as NumPy arrays;
- you need arrays returned to the caller instead of files on disk;
- you need to preserve labels alongside grouped arrays.

See [data-formats.md](data-formats.md) and the bundled [array smoke helper](../scripts/augmentor_mask_array_smoke.py).
