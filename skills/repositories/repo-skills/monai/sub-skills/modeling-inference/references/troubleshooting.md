# Modeling Troubleshooting

Use this matrix when MONAI modeling, loss, metric, postprocessing, visualization, or sliding-window inference fails. The fixes assume installed package APIs only and do not require source checkout paths.

## Shape And Channel Mismatch

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `Expected ... channels` or first convolution mismatch | Input tensor channel count does not match network `in_channels`. | Inspect tensor shape before forward; use channel-first `(B, C, spatial...)`; fix preprocessing in `data-transforms` or set `in_channels` correctly. |
| Loss complains about target dimensions | Label layout does not match `to_onehot_y` and output channels. | For multi-class logits `(B, C, spatial...)`, use labels `(B, 1, spatial...)` with `to_onehot_y=True`; for one-hot labels, use `(B, C, spatial...)` and `to_onehot_y=False`. |
| Metric output has unexpected class count | `include_background` or one-hot conversion changed channel count. | Decide whether channel 0 is background; set `include_background` consistently for loss and metric reporting. |
| Sliding-window output spatial shape differs unexpectedly | Predictor changes spatial size or ROI is not compatible with model stride/downsampling. | Test a single ROI through the model; use network-compatible ROI sizes; avoid models that crop/pad internally unless downstream stitching handles it. |
| `spatial_dims` mismatch | Model is 2D but input is 3D, or vice versa. | Match `spatial_dims` to input rank minus batch/channel axes; use `spatial_dims=3` for `(B, C, H, W, D)`. |

## Activation And One-Hot Misuse

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Training loss is flat or too smooth | Activation was applied before a loss that also applies `sigmoid=True` or `softmax=True`. | Pass raw logits to MONAI losses when the loss activation flag is enabled. |
| Multi-class Dice loss is wrong or errors | Used `sigmoid=True` for mutually exclusive classes or forgot `to_onehot_y=True`. | Use `DiceCELoss(to_onehot_y=True, softmax=True)` for class-index labels and multi-class logits. |
| Binary segmentation loss expects two channels | Treated binary single-channel logits as two-class softmax. | Either keep one output channel with `sigmoid=True`, or intentionally use two output channels with `softmax=True` and class-index labels. |
| Postprocessing produces all foreground/background | Threshold used on raw logits or argmax used after sigmoid multi-label output. | For binary/multi-label: sigmoid then threshold. For mutually exclusive multi-class: softmax then argmax then optional one-hot. |
| `to_onehot` creates wrong axis | Label tensor has no singleton channel or wrong class dimension. | Standardize labels to `(B, 1, spatial...)` before one-hot conversion; confirm `num_classes`. |

## Metric Reset, Aggregation, And Decollation

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Validation metric improves or worsens across epochs unexpectedly | Metric object was not reset after aggregation. | Call `metric.reset()` after every independent `aggregate()` result. |
| Metric differs from loss even on same batch | Metrics got raw logits while loss internally activated logits. | Apply validation postprocessing before metrics. |
| Empty-label cases return `NaN` or are skipped | `ignore_empty=True` and some classes are absent in ground truth. | Decide whether empty classes should be ignored; inspect `get_not_nans=True` output if needed. |
| Batched dictionary metric fails after transforms | Prediction and label keys have inconsistent shapes after postprocessing. | Decollate or inspect each item; ensure both prediction and label are one-hot or both are compatible for the metric. |
| Foreground scores shifted by one class | Background channel was included in one metric and excluded in another. | Align `include_background` across metrics and reports; document whether reported Dice excludes background. |

## Sliding-Window ROI, Device, And OOM

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| CUDA out-of-memory during inference | ROI too large, `sw_batch_size` too high, model too large, or output stitched on GPU. | First lower `sw_batch_size`; then lower `roi_size`; consider `device="cpu"` for stitched output and keep `sw_device` on accelerator if available. |
| CPU out-of-memory during inference | Output stitching, input volume, or `device="cpu"` accumulation exceeds host memory. | Reduce volume/ROI, stream cases one at a time, avoid caching too many outputs, and write results incrementally in downstream code. |
| Window seams or block artifacts | Too little overlap or constant blending for a model with edge effects. | Increase `overlap` and use `mode="gaussian"`; test on a known smooth input. |
| `roi_size` error or wrong number of dimensions | ROI included batch/channel axes or wrong spatial rank. | Pass spatial dimensions only, e.g. `(96, 96, 96)` for 3D. |
| Device mismatch inside predictor | Input window and model parameters are on different devices. | Move the model to the same device as the windows or set `sw_device` intentionally; avoid creating new tensors on an implicit default device inside `forward`. |
| Predictor returns tuple/dict but downstream expects tensor | `sliding_window_inference` preserves structure of predictor outputs. | Select the desired output key/index or wrap the predictor to return a single tensor. |

## Visualization Issues

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| CAM or occlusion method cannot find a layer | Target layer name/module is not compatible with the selected visualization helper. | Inspect model modules and select a convolutional or feature layer that produces spatial features. |
| Visualization map has wrong orientation or shape | Channel-first tensor was treated as channel-last, or metadata-aware inversion was skipped. | Keep tensors channel-first; route metadata/inverse orientation problems to `data-transforms`. |
| TensorBoard or image logging import fails | Optional visualization/logging package is missing. | Install only the optional dependency needed for that workflow, or skip visualization in minimal validation. |

## Export And Optional Dependency Failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| ONNX export import error | `onnx` or related optional packages are not installed. | Install the optional export stack in the target environment, or limit the task to forward-path validation. |
| TensorRT export fails | TensorRT, compatible NVIDIA GPU/driver, or supported compute capability is unavailable. | Treat TensorRT as hardware-specific; use Bundle export guidance in `bundle-config` only after confirming backend support. |
| Exported model output does not match eager output | Dynamic control flow, nondeterminism, unsupported ops, or device numerical differences. | Use `eval()`, fixed example tensors, CPU comparison first, tolerance-based checks, and wrapper modules for unsupported return structures. |
| Export tool rejects metadata/dict outputs | Model returns non-tensor structures. | Wrap the model so `forward` returns only the tensor(s) intended for export. |

## CPU/CUDA Limitations

- The bundled smoke script is CPU-only by design; passing it does not prove GPU, TensorRT, ONNX, or visualization optional dependencies.
- CUDA availability can change valid device strings and memory behavior; always check `torch.cuda.is_available()` before selecting CUDA paths.
- CPU and CUDA numerical results can differ slightly, especially after export or mixed precision; use tolerances instead of exact equality for floating-point validation.
- Some MONAI tests and recipes intentionally compare export outputs on CPU to avoid CUDA-specific export differences.

## Fast Debug Checklist

1. Print input, logits, and label shapes.
2. Confirm channel-first layout and `spatial_dims`.
3. Confirm `out_channels` equals intended output channels/classes.
4. Confirm exactly one activation path for loss and one explicit postprocessing path for metrics.
5. Confirm metrics receive postprocessed predictions and are reset after aggregation.
6. For sliding-window failures, test one ROI through the model before stitching the full volume.
7. Treat ONNX, TensorRT, TensorBoard, and advanced visualization imports as optional until proven installed.
