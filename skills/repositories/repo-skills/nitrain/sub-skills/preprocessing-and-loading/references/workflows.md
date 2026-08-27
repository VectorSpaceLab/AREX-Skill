# Workflows

## Purpose

Read this for the common preprocessing and batching recipes that users ask
for directly.

## 1. Aligned preprocessing for inputs and outputs

Use tuple keys when both sides must stay geometrically aligned.

```python
import nitrain as nt
from nitrain import readers, transforms as tx

base_dir = nt.fetch_data("example-01")

dataset = nt.Dataset(
    inputs=readers.ImageReader("*/img3d.nii.gz"),
    outputs=readers.ImageReader("*/img3d_seg.nii.gz"),
    transforms={
        ("inputs", "outputs"): tx.Resample((40, 40, 40)),
    },
    base_dir=base_dir,
)
```

If you need a label transform too, apply it after the aligned geometric step:

```python
transforms={
    ("inputs", "outputs"): tx.Resample((40, 40, 40)),
    "outputs": tx.LabelsToChannels(),
}
```

## 2. Random augmentation

Random transforms wrap a deterministic transform and only apply with the
configured probability.

```python
transforms={
    "inputs": [
        tx.RandomRotate(-15, 15, p=0.5),
        tx.RandomFlip(axis=0),
        tx.RandomZoom(0.9, 1.1, p=0.5),
    ]
}
```

Good practice:
- keep paired geometry transforms on tuple keys;
- keep random appearance transforms on a single key when they only affect one
  side;
- use `p=1` while debugging and lower it only after the data path is correct.

## 3. Slice, patch, and block sampling

Choose the sampler by output geometry:

- `SliceSampler` for 3D volumes that should become batches of 2D slices;
- `PatchSampler` for 2D patch extraction;
- `BlockSampler` for 3D subvolumes;
- `SlicePatchSampler` when you need patches from slices.

```python
from nitrain.samplers import SliceSampler

loader = nt.Loader(
    dataset,
    images_per_batch=1,
    sampler=SliceSampler(batch_size=12, axis=-1),
)

xb, yb = next(iter(loader))
```

## 4. Loader to Keras

Use `Loader.to_keras()` when the next step is TensorFlow or Keras training.

```python
keras_loader = loader.to_keras()
```

The loader infers a `tf.data`-style signature from a tiny batch when you do not
provide one manually.

## 5. Multi-input workflows

The dataset and loader both support aligned nested inputs.

```python
dataset = nt.Dataset(
    inputs={
        "image": readers.ImageReader("*/img3d.nii.gz"),
        "aux": readers.ImageReader("*/img3d_100.nii.gz"),
    },
    outputs=readers.ImageReader("*/img3d_seg.nii.gz"),
    base_dir=base_dir,
)
```

When the loader sees nested inputs, it keeps the structure aligned through the
sampler and into the final numpy batch.

## 6. Shape and channel decisions

- `channels_first=True` adds a channel axis in the loader.
- `channels_first=None` leaves images as they are.
- `AddChannel()` is useful when the dataset itself needs an explicit channel
  axis before the loader.
- `LabelsToChannels()` turns a segmentation mask into one channel per label.

## 7. Use the smoke checker

When you are debugging a packaging or import problem, run:

```bash
python scripts/check_install.py --mode preprocess
```

That confirms the transforms, sampler, loader, and Keras bridge are wired up
correctly before you move on to model construction.
