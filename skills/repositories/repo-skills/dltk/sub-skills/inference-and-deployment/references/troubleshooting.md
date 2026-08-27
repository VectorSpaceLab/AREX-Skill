# Inference and deployment troubleshooting

## Shape or coverage errors before running the model

- **Invalid rank or zero/negative dimension:** `SlidingWindow` and the assembly helper do little validation. Confirm spatial `input >= output`, `window >= output`, all three shapes have the same positive rank, and every stride is a positive integer. Run `sliding_window_plan.py` to fail with a useful message before session execution.
- **Output patch larger than input patch:** DLTK computes `out_diff = window_shape - output_shape` and passes it to `np.pad`. A negative difference is not a supported upsampling contract and usually fails in padding. Use the model-building route to establish the graph's real output shape.
- **Zero division or NaN in assembly:** the helper divides every accumulator by its counter without checking zero. A malformed window, stride, or output mapping can leave uncovered voxels. Inspect the plan's padded shape and tile counts, start with `batch_size=1`, and test with a constant synthetic op. Do not hide the warning with `nan_to_num`.
- **Gaps from an overly large stride:** stride is a movement step, not overlap. A step larger than the output tile can leave uncovered or poorly sampled regions. Choose a step no larger than the output tile unless gaps are intentional and externally validated.
- **Boundary mismatch:** the final window is shifted back so it ends at the image boundary. Do not replace DLTK's iterator with a simple `range` loop without checking edge coverage and pairing with the output-volume iterator.

## Smaller output, overlap, and batching

For a model with input patch `W` and output patch `O < W`, DLTK pads each spatial input array by `W - O` (split floor-half left and remainder right), feeds `W`, and writes the returned `O` into the original-volume coordinates. The default step is `O`, while an explicit smaller step creates overlap. With `batch_size > 1`, the helper concatenates window slices, runs one session call, splits each op result by the number of windows, and then applies the paired output slices. Validate all three together; a graph with a fixed batch dimension may only work at `batch_size=1`.

The bundled smoke covers this difficult combination with a constant output and checks finite, all-one assembly. It uses a local slice-friendly test adapter because the DLTK helper passes a list of `slice` objects to NumPy arrays; modern NumPy versions can reject that indexing expression even though the TensorFlow 1.x test intent is clear. The adapter is confined to the smoke and does not alter the production library.

## Predictor and export failures

- **`tensorflow.contrib` missing:** you are not in the documented TensorFlow 1.x environment. Do not substitute a TF2 API and claim equivalence. Re-enter the verified Python 3.7/TensorFlow 1.15 environment or route a deliberate export adaptation through training/export ownership.
- **Missing `x`, `y_prob`, or `logits`:** inspect the loaded SavedModel signature and make a public predictor call with its exact string input key first. Only if full-volume assembly is required should you map those confirmed keys to private predictor fields. Application names are not universal. Verify input rank, channel count, and output key before calling the helper.
- **Private field failure (`_feed_tensors`, `_fetch_tensors`, `session`):** these are implementation details used only by the low-level DLTK assembly path, not a stable predictor API. Stop and inspect the public signature and export rather than guessing tensor names; use the public predictor callable when it meets the task.
- **No model selected:** check that the model directory contains numeric export subdirectories and select by `int(basename)`. If none exist, do not fall back to an arbitrary checkpoint or lexical path.
- **Static batch incompatibility:** a predictor/op with batch dimension `1` may reject concatenated windows. Use `batch_size=1` for diagnosis; increase only when the graph shape and feed contract allow it.

## Output conversion and metric warnings

- **Argmax axis error:** segmentation probabilities/logits are channels-last `[batch, spatial..., classes]`; use the final axis and remove only the synthetic batch for export. Never argmax over a spatial axis.
- **Dice is NaN:** DLTK's per-class Dice has no empty-class special case. Report the NaN, use an explicitly documented `nanmean` policy if appropriate, and state whether class 0/background was excluded. Do not silently turn absent-class scores into one or zero.
- **Unexpected AVD:** `abs_vol_difference` uses voxel counts and a `1e-6` label-count epsilon. It is not spacing-aware physical volume. The source also uses the deprecated `np.float` alias, which can fail on modern NumPy; preserve the known environment or provide a reviewed compatibility change outside this route.
- **Crossentropy instability:** for logits, keep the source's max-subtracted softmax behavior. For probabilities, ensure values are probabilities and retain the `1e-8` log offset.

## SimpleITK/NIfTI output

- **Geometry lost:** `GetImageFromArray` does not inherit metadata. Call `CopyInformation(source_sitk_image)` before `WriteImage`; this copies origin, spacing, and direction.
- **`CopyInformation` rejects the result:** compare array dimensions/size and ensure the prediction was not transposed, cropped, or resampled without the corresponding source image. Fix the geometry contract; do not suppress the exception.
- **Wrong orientation or channels:** verify the reader's array convention and whether a singleton batch/channel axis was removed. The DLTK segmentation deployment pattern writes `pred[0].astype(np.int32)` as a scalar label image.

## Stochastic crop results

The DLTK IXI workflows call `extract_random_example_array` for four random crops. Different runs can produce different outputs, and a fixed NumPy seed does not guarantee deterministic GPU execution. Record crop count/shape and seed policy. Average regression predictions as the DLTK workflow does, and average classification probabilities before argmax; do not compare these numbers to a deterministic full-volume segmentation run as if they used the same estimator.
