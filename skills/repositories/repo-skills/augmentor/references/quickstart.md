# Augmentor Quickstart

## Purpose

Use this reference for the shortest complete Augmentor workflow and to decide which sub-skill owns the next details. Augmentor is a pure-Python/Pillow/NumPy image augmentation package organized around stochastic pipelines.

## Install and import

```bash
pip install Augmentor
python - <<'PY'
import Augmentor
print(Augmentor.__version__)
print(Augmentor.__all__)
PY
```

For older Augmentor 0.2.x environments, prefer compatible dependency pins when behavior is sensitive to Pillow or NumPy API changes:

```bash
pip install 'Augmentor==0.2.12' 'Pillow<10' 'numpy<2' tqdm
```

## Minimal directory-backed augmentation

Create a pipeline pointing at a directory of images, add operations, then sample outputs:

```python
import Augmentor

p = Augmentor.Pipeline("train_images", output_directory="output")
p.rotate(probability=0.7, max_left_rotation=10, max_right_rotation=10)
p.flip_left_right(probability=0.5)
p.resize(probability=1.0, width=224, height=224)
p.set_save_format("PNG")
p.sample(100, multi_threaded=False)
```

Outputs are written below the source directory's output folder. If the source directory has immediate subfolders, Augmentor treats those subfolders as classes and writes class-specific output folders.

Read `../sub-skills/pipeline-augmentation/SKILL.md` for scanning, output, `sample()` versus `process()`, class folders, seeds, and multithreading.

## Pick operations

Every operation has a `probability` argument controlling whether it is applied to each image. Common operations include:

- `rotate`, `rotate90`, `rotate180`, `rotate270`, `rotate_random_90`
- `flip_left_right`, `flip_top_bottom`, `flip_random`
- `crop_by_size`, `crop_centre`, `crop_random`, `zoom`, `zoom_random`, `resize`, `scale`
- `skew`, `skew_tilt`, `skew_corner`, `shear`, `random_distortion`, `gaussian_distortion`
- `greyscale`, `black_and_white`, `invert`, `histogram_equalisation`, `random_brightness`, `random_color`, `random_contrast`, `random_erasing`

Read `../sub-skills/operation-reference/SKILL.md` for parameter ranges, operation selection, custom operations, and validation errors.

## Ground truth and masks

For on-disk masks with matching filenames:

```python
p = Augmentor.Pipeline("images")
p.ground_truth("masks")
p.rotate(probability=1, max_left_rotation=5, max_right_rotation=5)
p.sample(20)
```

For in-memory originals plus one or more masks, use `Augmentor.DataPipeline` with each training example as a list such as `[image_array, mask_array]`.

Read `../sub-skills/masks-and-arrays/SKILL.md` for filename/class matching, dimension checks, grouped arrays, labels, and mask-specific troubleshooting.

## Generators and framework boundaries

Augmentor can return batches instead of writing files:

```python
p = Augmentor.Pipeline("train_images")
g = p.keras_generator(batch_size=32, scaled=True, image_data_format="channels_last")
images, labels = next(g)
```

Despite the method names, Augmentor's direct generator helpers do not import Keras. They return NumPy arrays that downstream code can feed to Keras/TensorFlow-style training loops. `torch_transform()` returns a PIL-transform callable that can be composed with torchvision when torchvision is installed separately.

Read `../sub-skills/generators-and-frameworks/SKILL.md` for generator shapes, scaling, `channels_last` versus `channels_first`, `torch_transform()`, and DataFramePipeline caveats.

## Safe bundled checks

Run the root smoke helper after installing Augmentor:

```bash
python scripts/augmentor_env_smoke.py --samples 2 --size 24
```

This creates temporary images, runs a tiny disk pipeline, verifies outputs with Pillow, and deletes the temporary fixture by default.
