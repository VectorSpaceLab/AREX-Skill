# Ordered StarDist 2D workflows

Use the smallest workflow that satisfies the request. Record the input/output
contract before loading a model so that an accepted function call cannot hide
an axes, channel, or normalization error.

## 0. Run contract

Record:

```text
input: source/store, shape, dtype, axes, channel meaning
model: pretrained key or local basedir/name; expected config
normalization: pre-normalized or Normalizer class/statistics
operation: data check / predict / instances / big / train / thresholds
parameters: sparse, probability/NMS thresholds, scale, n_tiles, blocks
outputs: labels/details/maps, output store and dtype
resources: CPU/RAM, optional network/OpenCL/CUDA
acceptance: shape/dtype/count and fixture/visual checks
```

Runtime files must not require a source checkout. External model directories and
output stores are user-selected inputs and belong in the run record.

## 1. Validate 2D data

**Input:** image, optional labels, intended axes, expected channels.

1. Require rank 2 `YX` or rank 3 `YXC`; require exactly matching explicit axes.
   A rank-4 `ZYXC` or time stack is not a 2D input. Select a documented plane
   or route to [3d-workflows](../../3d-workflows/SKILL.md).
2. For labels require rank 2 `YX`, integer dtype, background `0`, and positive
   distinct ids for instances. The image and mask must share `(Y,X)`.
3. For multichannel input verify `shape[-1] == model.config.n_channel_in`.
   For one channel, choose consistently between rank-2 `YX` and rank-3
   `YXC`-with-one-channel.
4. Check finite values and intensity distribution. Apply one documented
   normalization policy before inference or provide a normalizer.
5. For training, validate every `X[i],Y[i]` pair and ensure all images are at
   least the selected patch size.

**Output:** a validated 2D image contract and paired training arrays, or an
explicit failure before model execution.

## 2. Prepare training data (no side-effect script)

Training data may be lists of different-sized images or arrays with a common
shape. Normalize train and validation data identically, for example:

```python
from csbdeep.utils import normalize
X = [normalize(x, 1, 99.8, axis=(0,1)) for x in X]
```

For RGB, record whether channels use independent `(0,1)` or joint `(0,1,2)`
statistics. Repair label holes or other annotation problems only in an explicit
reviewed preprocessing step. Keep labels integer and preserve instance ids.

Choose `n_rays`, `grid`, `n_channel_in`, and optional `n_classes` from the data
contract. Start with `n_rays=32` and `grid=(1,1)` or `(2,2)` only when the
field-of-view/memory tradeoff is understood. Keep `use_gpu=False` for the
required CPU route; `use_gpu=True` is optional OpenCL/gputools data generation,
not CUDA TensorFlow.

Before training, check U-Net/grid divisibility. Without shape completion,
`train_patch_size` must be divisible by the model's spatial divisor
`unet_pool ** unet_n_depth * grid`. With shape completion, the same applies to
`train_patch_size - 2*train_completion_crop`, and the completion crop must be
grid-divisible. The model itself raises a `ValueError` when these checks fail.

## 3. Bounded training handoff

Training is side-effectful and deliberately has no bundled training script.
Use a bounded smoke request, then obtain approval before production scale:

```python
from stardist.models import Config2D, StarDist2D

conf = Config2D(
    n_channel_in=1, n_rays=32, grid=(1,1), n_classes=None,
    train_patch_size=(128,128), train_batch_size=1,
    train_epochs=2, train_steps_per_epoch=1, use_gpu=False,
)
model = StarDist2D(conf, name="model-name", basedir="model-root")
history = model.train(
    X_train, Y_train, validation_data=(X_val,Y_val),
    epochs=2, steps_per_epoch=1, workers=1,
)
```

For multiclass use `classes=C_train` and
`validation_data=(X_val,Y_val,C_val)`. Preserve the printed config, history,
checkpoints, normalization, and axes. A smoke run must prove only that the
data generator, compile, checkpoint, reload, and one prediction work; it does
not prove segmentation quality.

Acceptance checks: generated arrays are finite and shape-compatible; history
contains loss entries; `StarDist2D(None,name=...,basedir=...)` reloads; one
prediction has the expected output shape/dtype. Keep training artifacts
outside the runtime skill tree.

## 4. Pretrained/local inference

1. For pretrained weights, call `StarDist2D.from_pretrained(name)`. Registered
   2D names in this baseline are `2D_versatile_fluo`, `2D_versatile_he`,
   `2D_paper_dsb2018`, and `2D_demo`. The call may need network/cache access;
   report that optional block rather than substituting an untrained model.
2. For local weights, call
   `StarDist2D(None, name=model_name, basedir=model_root)` and verify persisted
   config/weight files. Inspect `model.config.axes`, `n_channel_in`, `n_rays`,
   `grid`, and `n_classes`.
3. Compare model modality and channel count. The fluorescent versatile model
   is a single-channel fluorescence-like model; the H&E versatile model is
   RGB brightfield-like. A load is not a domain validation.
4. Normalize exactly once. For small images, use a documented percentile call
   or pass a `csbdeep.data.Normalizer` for lazy/block operation.
5. Run a small known crop first:

   ```python
   axes = "YX" if x.ndim == 2 else "YXC"
   labels, details = model.predict_instances(
       x, axes=axes, sparse=True, show_tile_progress=False,
   )
   ```

6. Assert `labels.shape == x.shape[:2]` (unless labels were deliberately
   disabled), integer labels, finite details, and equal object counts across
   `prob`, `points`, and `coord`. Save the exact run parameters.

## 5. Dense/sparse and threshold workflow

Compare memory modes with fixed model/input/threshold/tile parameters:

```python
ld, dd = model.predict_instances(x, axes=axes, sparse=False,
                                 n_tiles=tiles, show_tile_progress=False)
ls, ds = model.predict_instances(x, axes=axes, sparse=True,
                                 n_tiles=tiles, show_tile_progress=False)
```

Native tests expect labels and numeric detail arrays to agree up to floating
point/order effects. `return_predict=True` intentionally forces dense mode and
returns dense network outputs; do not use it for a RAM-constrained run.

For held-out normalized validation images and integer masks:

```python
thresholds = model.optimize_thresholds(
    X_val, Y_val, nms_threshs=[.3,.5], iou_threshs=[.3,.5],
    optimize_kwargs={"tol": 1e-1}, save_to_json=True,
)
```

This updates in-memory thresholds and optionally writes `thresholds.json`.
Record the validation split, candidate grids, and selected values. If the local
model is read-only, use `save_to_json=False` and pass explicit thresholds.

## 6. Safe result handoff

Report model source/config, image shape/dtype/axes/channels, normalization and
statistics, exact threshold/scale/tile/sparse settings, label shape/dtype/max
id, detail keys/counts, optional network/backend requirements, fixture/visual
checks, warnings, and unresolved modality/scale assumptions. Keep generic
matching/evaluation with [evaluation-geometry](../../evaluation-geometry/SKILL.md).
