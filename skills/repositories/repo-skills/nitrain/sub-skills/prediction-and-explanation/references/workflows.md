# Workflows

## Purpose

Read this for the canonical Nitrain prediction pattern and the current state of
`OcclusionExplainer`.

## 1. Slice-based prediction

Use `Predictor` when the model expects batched slices but the source data is a
full 3D volume.

```python
import nitrain as nt
from nitrain import readers, transforms as tx
from nitrain.samplers import SliceSampler

base_dir = nt.fetch_data("example-01")

dataset = nt.Dataset(
    inputs=readers.ImageReader("*/img3d.nii.gz"),
    outputs=readers.ImageReader("*/img3d_100.nii.gz"),
    transforms={("inputs", "outputs"): tx.Resample((40, 40, 40))},
    base_dir=base_dir,
)

arch_fn = nt.fetch_architecture("unet", dim=2)
model = arch_fn(
    (40, 40, 1),
    number_of_outputs=1,
    number_of_layers=2,
    number_of_filters_at_base_layer=8,
    mode="regression",
)

predictor = nt.Predictor(model, task="regression", sampler=SliceSampler(axis=-1))
y_pred = predictor.predict(dataset.select(1))
```

## 2. Output-shape rules

`Predictor.predict()` behaves differently by task:

- regression: multidimensional predictions may be returned as ANTs images;
- segmentation and classification: predictions are rounded to `uint8`;
- slice sampling: the sampled axis is rolled back into place when the sampler is
  a `SliceSampler`.

Keep these rules in mind when you compare the prediction output against the
source label image.

## 3. Expansion-axis decisions

`expand_dims` controls the extra dimension inserted before the model call.

- `expand_dims=-1` is the usual image-channel path;
- `expand_dims=0` or another integer changes where the channel axis is inserted;
- `expand_dims=None` disables the extra expansion entirely.

Choose the same convention that the model was trained with.

## 4. Current explainer surface

```python
explainer = nt.OcclusionExplainer(model)
result = explainer.fit(dataset)
```

Important: in this snapshot, `fit()` is a placeholder and returns `1`. It does
not yet perform a real occlusion analysis. Use it as a surface inspection aid,
not as a functioning saliency implementation.

## 5. When prediction goes wrong

- If the output shape is off, confirm the sampler axis and model input shape.
- If the output type is wrong, confirm the task string.
- If the prediction is not image-shaped, verify that the model actually returns
  a multidimensional tensor.

## 6. Smoke helper

Use the bundled helper to confirm the path after install:

```bash
python scripts/check_install.py --mode predictor
```
