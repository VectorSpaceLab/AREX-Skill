# Inference and Evaluation API Reference

This reference captures the source APIs that matter for inference/evaluation workflows. Use it to reason about script behavior, postprocess return values, and checkpoint compatibility.

## LaneNet model entry points

| Object | Signature | Notes |
| --- | --- | --- |
| `lanenet_model.lanenet.LaneNet.__init__` | `(self, phase, cfg)` | Use `phase='test'` for inference. The front-end is selected by `cfg.MODEL.FRONT_END`, default `bisenetv2`. |
| `LaneNet.inference` | `(self, input_tensor, name, reuse=False)` | Returns `(binary_seg_prediction, instance_seg_prediction)`. In scripts, `name='LaneNet'`. |

Expected inference placeholder:

```python
input_tensor = tf.placeholder(dtype=tf.float32, shape=[1, 256, 512, 3], name='input_tensor')
```

Expected input preprocessing:

```python
image = cv2.resize(image, (512, 256), interpolation=cv2.INTER_LINEAR)
image = image / 127.5 - 1.0
```

Model outputs:

| Output | Shape expectation | Meaning |
| --- | --- | --- |
| `binary_seg_ret` | `[1, 256, 512]` after session run | Lane/non-lane class prediction from softmax argmax; values are class ids and are often visualized as 0/255. |
| `instance_seg_ret` | `[1, 256, 512, cfg.MODEL.EMBEDDING_FEATS_DIMS]` | Per-pixel embedding used for lane-instance DBSCAN clustering; default embedding dimension is `4`. |

## Checkpoint restore APIs

Single-image inference originally restores exponential-moving-average variables:

```python
with tf.variable_scope(name_or_scope='moving_avg'):
    variable_averages = tf.train.ExponentialMovingAverage(cfg.SOLVER.MOVING_AVE_DECAY)
    variables_to_restore = variable_averages.variables_to_restore()
saver = tf.train.Saver(variables_to_restore)
```

Batch evaluation originally restores raw graph variables:

```python
saver = tf.train.Saver()
```

Both restore modes can be valid depending on how the checkpoint was saved. A checkpoint created by the repo trainers can include both raw variables and moving-average shadow variables because moving averages are applied during training and the saver captures global variables. If one restore mode fails with `NotFoundError` or missing variables, try the other mode and confirm the checkpoint was trained with the same front-end and embedding dimension.

## LaneNetPostProcessor

Verified constructor:

```python
LaneNetPostProcessor(cfg, ipm_remap_file_path='./data/tusimple_ipm_remap.yml')
```

The constructor asserts that the remap file exists, then loads `remap_ipm_x` and `remap_ipm_y` matrices with OpenCV `FileStorage`. Even when lane fit is later disabled, the current constructor still requires a readable remap file.

Verified postprocess signature:

```python
LaneNetPostProcessor.postprocess(
    binary_seg_result,
    instance_seg_result=None,
    min_area_threshold=100,
    source_image=None,
    with_lane_fit=True,
    data_source='tusimple',
)
```

### Inputs

| Parameter | Required | Meaning |
| --- | --- | --- |
| `binary_seg_result` | yes | Single-image binary prediction, normally `binary_seg_image[0]` from the TensorFlow session. It is converted to `uint8` by multiplying by 255. |
| `instance_seg_result` | yes for useful clustering | Single-image embedding prediction, normally `instance_seg_image[0]`. Required by DBSCAN clustering. |
| `min_area_threshold` | optional | Removes connected components with area at or below the threshold. Default source signature is `100`; config default has the same value. |
| `source_image` | yes for overlays/lane fit | Original unnormalized image at source resolution, in OpenCV BGR order. |
| `with_lane_fit` | optional | If `True`, fit TuSimple-style second-order lane curves and draw lane points; if `False`, directly resize/overlay the clustered mask. |
| `data_source` | optional | Lane fitting only supports `'tusimple'`; any other value raises `ValueError`. |

### Internal stages

1. Convert `binary_seg_result` to an 8-bit image with values near `0` or `255`.
2. Apply morphological close with an elliptical kernel of size `5`.
3. Run connected-component analysis and zero small components at or below `min_area_threshold`.
4. Gather embedding vectors where the cleaned binary mask equals `255`.
5. Standardize the embedding vectors and cluster with DBSCAN using `cfg.POSTPROCESS.DBSCAN_EPS` and `cfg.POSTPROCESS.DBSCAN_MIN_SAMPLES`.
6. Build a color mask for non-noise DBSCAN clusters.
7. If `with_lane_fit=False`, resize the mask to source-image resolution and alpha-blend it over the source image.
8. If `with_lane_fit=True`, remap lane masks to IPM space, fit second-order lane curves, sample TuSimple y positions, and draw colored lane points on the source image.

### Return keys

| Key | Value when clustering succeeds | Value when clustering fails |
| --- | --- | --- |
| `mask_image` | RGB/BGR-style color cluster mask at network resolution `(256, 512, 3)`. | `None` |
| `fit_params` | List of second-order polynomial parameter arrays when lane fit is enabled; `None` when lane fit is disabled. | `None` |
| `source_image` | Source image with fitted lane points or direct cluster-mask overlay. | `None` |

Treat `mask_image is None` as a postprocess/cluster failure, not necessarily as a TensorFlow inference failure. Inspect the binary output before retraining or replacing checkpoints.

## DBSCAN cluster details

The clusterer extracts lane embedding features from pixels where the cleaned binary segmentation equals `255`, then runs:

```python
DBSCAN(eps=cfg.POSTPROCESS.DBSCAN_EPS, min_samples=cfg.POSTPROCESS.DBSCAN_MIN_SAMPLES)
```

Default values are:

| Config key | Default | Effect |
| --- | --- | --- |
| `POSTPROCESS.DBSCAN_EPS` | `0.35` | Neighborhood radius in standardized embedding space. Increasing it can merge or recover sparse custom-data clusters. |
| `POSTPROCESS.DBSCAN_MIN_SAMPLES` | `1000` | Minimum samples for a core point. Reducing it can help custom images with fewer lane pixels. |
| `POSTPROCESS.MIN_AREA_THRESHOLD` | `100` | Minimum connected-component area kept before clustering. |

Repo evidence for custom data suggests a starting adjustment of `DBSCAN_EPS=0.5` and `DBSCAN_MIN_SAMPLES=250` when default values produce a black mask. Validate on binary and mask images before applying broadly.

## Evaluation helper functions

The metric-helper module is reference-only for this sub-skill; it is not bundled as a standalone script. These helpers operate on TensorFlow tensors, not NumPy arrays:

| Function | Signature | Meaning / caveat |
| --- | --- | --- |
| `calculate_model_precision` | `(input_tensor, label_tensor)` | Applies softmax and argmax to binary segmentation logits, then divides true lane predictions by the number of lane-label pixels. Despite the name, this behaves more like lane-pixel recall against ground truth positives. |
| `calculate_model_fp` | `(input_tensor, label_tensor)` | Computes false-positive fraction among predicted lane pixels. Watch for divide-by-zero if there are no predicted lane pixels. |
| `calculate_model_fn` | `(input_tensor, label_tensor)` | Computes false-negative fraction among ground-truth lane pixels. Watch for divide-by-zero if there are no lane-label pixels. |
| `get_image_summary` | `(img)` | Normalizes a tensor to a 0-255 range for TensorBoard-style image summary visualization. Watch for constant tensors causing zero denominator. |

These helpers are not used by the batch image-saving evaluator. If a user asks for benchmark metrics against labels, first confirm label tensors and evaluation graph wiring; otherwise the shipped batch workflow only saves postprocessed overlays and logs timing.

## Output-file semantics in bundled wrappers

| Output | Producer | Meaning |
| --- | --- | --- |
| `source_image.png` | single-image wrapper | Original image as read by OpenCV. |
| `binary_image.png` | single-image wrapper | Binary class prediction scaled to 0/255. |
| `instance_embedding.png` | single-image wrapper | Visual encoding of the first embedding channels after min-max scaling. |
| `mask_image.png` | postprocessor | Cluster mask before source-resolution lane-fit drawing. |
| `source_overlay.png` | postprocessor | Source image with direct mask overlay or fitted TuSimple lane points. |
| Batch `.jpg` outputs | batch wrapper | Source-resolution `source_image` returned by postprocess for each image, saved under the post-`clips` relative path. |
