# Deployment workflows

These recipes describe a self-contained DLTK 0.2.1 deployment pattern without depending on a particular dataset, checkout, or model archive.

## 1. Inspect the export before running a volume

The application deploy scripts look for numeric SavedModel export directories beneath `model_path` and pass the selected directory to `tensorflow.contrib.predictor.from_saved_model`. Use numeric parsing, not plain lexical sorting, because `10` must be newer than `9`:

```python
candidates = [
    os.path.join(model_path, name)
    for name in os.listdir(model_path)
    if name.isdigit() and os.path.isdir(os.path.join(model_path, name))
]
if not candidates:
    raise RuntimeError("no numeric SavedModel export directory under model_path")
export_dir = max(candidates, key=lambda path: int(os.path.basename(path)))
```

DLTK's age and sex workflows sort numeric-looking names before taking the last item; the segmentation workflow takes the last unsorted numeric item. The numeric-key selection above is the safer equivalent. It does not validate the export itself. Load it in the known TF1 environment, then inspect the public SavedModel signature and static shapes before touching patient data. Never select a directory merely because it is alphabetically last.

## 2. Full-volume segmentation

The DLTK segmentation workflow assumes its reader has returned a multi-channel array in `output['features']['x']`, a label array in `output['labels']['y']`, an identifier, and a SimpleITK image carrying geometry. The reader-specific CSV and NIfTI layout belong to [data-pipelines](../../data-pipelines/SKILL.md); this route only consumes the resulting arrays.

A bounded deployment sequence is:

1. Read/preprocess one volume according to the training reader, preserving channel-last layout.
2. Add one batch dimension: `img = np.expand_dims(x, axis=0)`. Check that `[batch, spatial..., channels]` matches the predictor feed tensor.
3. Fetch the graph probability tensor (`y_prob`) and use its final dimension for `num_classes`. For a smaller model output patch, pass its exact static output shape to the plan helper first.
4. Call `sliding_window_segmentation_inference` with the predictor session, the fetched op, the predictor feed tensor, and a bounded window `batch_size` (the example uses 32). Use an explicit `striding` only after checking coverage; otherwise preserve DLTK's defaults described in [api-reference.md](api-reference.md).
5. Convert the assembled `[1, spatial..., classes]` probabilities with `np.argmax(assembled, axis=-1)`. Do not argmax every patch before overlap averaging unless that discrete-vote behavior is an intentional departure from the source pattern.
6. If labels are available, calculate per-class Dice and absolute volume difference. Report class IDs, background policy, absent-class/NaN policy, and whether AVD is voxel-count relative difference or geometry-aware volume difference.
7. Export `pred[0].astype(np.int32)` through SimpleITK. `sitk.GetImageFromArray` creates a new image; call `new_image.CopyInformation(source_sitk_image)` before `sitk.WriteImage`. Check equal array dimensions first. This preserves origin, spacing, and direction; it does not repair a preprocessing/resampling mismatch.

A deployment wrapper may write under `model_path` using a subject-derived filename. Prefer a separate, pre-created output directory and reject path traversal or accidental overwrite in production wrappers.

## 3. Regression and classification by random-crop averaging

The IXI age and sex examples do not slide across the complete volume. They call DLTK's `extract_random_example_array` with model-compatible spatial shape `[64, 96, 96]` and `n_examples=4`, then run the predictor on the crop batch.

- The image must be large enough for the requested crop and use the same channels-last convention as training. The helper samples each spatial origin with `np.random`, so four crops are stochastic; the age README explicitly says deployment results can vary.
- Regression fetches `logits`, averages the returned crop predictions with `np.mean(y_)`, and computes an absolute error against the label. Confirm the expected scalar shape before formatting it as an age.
- Classification fetches `y_prob`, averages with `np.mean(y_, axis=0)`, and then takes `np.argmax` over classes. Averaging class probabilities before argmax is different from majority voting crop labels.
- If repeatability matters, seed NumPy at the caller and record the seed, crop shape, and crop count. A seed controls the crop selection, not nondeterminism inside a GPU graph.
- If the full input is smaller than the model crop or incompatible with model downsampling, pad/crop using the training pipeline's documented convention rather than silently changing the random sampler.

## 4. SavedModel calls: public signature before private fields

First inspect the SavedModel signature and make one ordinary public predictor call
with the exact input key. This catches wrong export selection, key mismatches, and
shape errors without guessing internal names. The public call returns values and
is sufficient when full-volume assembly is not required; see the inspection-first
sequence in [api-reference.md](api-reference.md).

The DLTK sliding helper has a narrower low-level contract: it needs graph tensor
keys and a session. After the public call succeeds and the output shape is
confirmed, a TF1-only full-volume path may use the predictor's private fields:

```python
# Replace these keys only with names confirmed by the public signature probe.
feed_tensor = my_predictor._feed_tensors[input_key]
prob_tensor = my_predictor._fetch_tensors[output_key]
assembled = sliding_window_segmentation_inference(
    session=my_predictor.session,
    ops_list=[prob_tensor],
    sample_dict={feed_tensor: img},
    batch_size=1,
)[0]
```

`_feed_tensors`, `_fetch_tensors`, and `session` are private and may differ across
TensorFlow builds. If inspection or the public call fails, stop and inspect the
export rather than guessing names. Do not promise that this works with TF2's
`tf.saved_model.load`; `tf.contrib.predictor` is a removed TF1 API. If only a
public serving callable is available, route export/signature adaptation through
[training-and-estimators](../../training-and-estimators/SKILL.md) and do not
pretend it has the same tensor contract.

## 5. Batching and overlap decisions

A batch is assembled from windows, not subjects. `batch_size=1` is the simplest diagnostic. Increase it only after a one-window session call works and the model accepts a dynamic patch batch. For smaller output patches, the helper pads the input around the volume and maps each output patch onto the unpadded volume. Test the exact combination of output shape, overlap stride, and batch size with `sliding_window_smoke.py` or a synthetic graph before deploying.

Remember that overlap is averaged, including boundary regions. If a model emits logits, averaging logits and then softmaxing is not identical to averaging probabilities; follow the output key's semantics. For a probability output, the DLTK deployment pattern averages probabilities.
