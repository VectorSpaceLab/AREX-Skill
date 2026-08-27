---
name: data-pipelines
description: "Implement and validate DLTK TensorFlow 1.x medical-image readers,
  preprocessing, augmentation, patch extraction, and NIfTI/CSV input contracts."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# DLTK data pipelines

Use this route when a task must turn medical-image files or synthetic arrays into
DLTK `Reader`/Estimator inputs. It covers `dltk.io.preprocessing`,
`dltk.io.augmentation`, `dltk.io.abstract_reader`, SimpleITK/NIfTI layouts,
CSV-driven file references, serving placeholders, and safe resampling choices.
It does **not** cover network architecture, optimizer/Estimator orchestration,
or exported-model prediction/stitching; route those to
[model-building](../model-building/SKILL.md),
[training-and-estimators](../training-and-estimators/SKILL.md), or the
inference route.

## Compatibility gate

The public package baseline is DLTK 0.2.1 (provenance: commit
`f94d3bb509eb0741164149acbef0788769a869e4`). Its reader uses TensorFlow 1.x
graph/session APIs (`tf.Session`, `tf.data.Dataset.from_generator`,
`tf.train.SessionRunHook`, and `tf.estimator`). For source-compatible
execution, provision Python 3.7 with TensorFlow 1.15 and dependency versions
that expose those APIs. Do not imply that the code is TensorFlow 2.x
compatible: NumPy-only preprocessing/augmentation checks can run without
TensorFlow, while `abstract_reader` requires the TF1 hook API. SimpleITK,
NIfTI data, and any dataset permissions are separate prerequisites.

## Operating sequence

1. **Freeze the sample contract.** Define the row layout in `file_references`,
   the `mode`, `params`, spatial patch `example_size`, channel count, label
   shape/dtype, and whether a full volume or patches are emitted. A custom
   reader has the exact signature `read_fn(file_references, mode,
   params=None)` and yields dictionaries, normally with `features` and (outside
   PREDICT) `labels`.
2. **Read and orient data explicitly.** Read NIfTI with SimpleITK, convert with
   `sitk.GetArrayFromImage`, and add/stack channels last so a 3-D volume is
   `[z, y, x, channels]` for the TensorFlow examples. Keep the original
   `sitk.Image` metadata outside TensorFlow if output reslicing is needed.
3. **Normalize before training augmentation.** Choose whitening, `[0, 1]`, or
   `[-1, 1]` based on the model contract. Copy an array before using the
   in-place Gaussian offset/noise helpers. Use the safe crop/pad logic in the
   reference rather than assuming the legacy list-indexing implementation works
   with modern NumPy 2.x.
4. **Augment only where valid.** Apply random flips to every synchronized image
   and label with the same decision; apply intensity noise/offset only to image
   channels. Elastic deformation in the legacy helper is not a label interpolation
   contract. In a training reader, ensure `params` has defaults before indexing
   `params['extract_examples']`.
5. **Extract patches with a label policy.** For ordinary patches use
   `extract_random_example_array`; for segmentation use
   `extract_class_balanced_example_array` with image shape `[spatial..., C]` and
   label shape `[spatial...]`. Verify every requested class exists and expect
   fewer than `n_examples` when class availability/weights cannot supply all
   requested patches.
6. **Bind the nested TensorFlow contract.** Construct `dtypes` and
   `example_shapes` with the same dictionary/list structure as each yielded
   example. Shapes describe one unbatched element; `Reader.get_inputs` adds the
   batch dimension. Extra keys are recursively removed by the legacy cleaner,
   while missing keys or dict/list mismatches fail. Do not put arbitrary
   SimpleITK objects in a TensorFlow dtype tree.
7. **Treat PREDICT as a separate branch.** Yield exactly one prediction record
   containing only feature keys declared for prediction, then `return`. Several
   source application readers yield their prediction record and continue into
   label/patch code; copying that pattern can duplicate examples or dereference
   absent labels/params. Test PREDICT independently from TRAIN/EVAL.
8. **Validate on synthetic data first.** Run
   `scripts/preprocessing_smoke.py` and
   `scripts/validate_reader_contract.py` from any working directory. Then use a
   small, permissioned fixture and a bounded TF1 session/Estimator check. Do not
   download, delete, extract untrusted archives, or start full training from
   this route.

## Handoffs

- Pass feature rank/channel and label shape facts to
  [model-building](../model-building/SKILL.md).
- Pass `Reader.get_inputs`, hook, mode, batch, and serving contracts to
  [training-and-estimators](../training-and-estimators/SKILL.md).
- Keep metadata-preserving output and sliding-window stitching in the sibling
  inference/deployment route.

For exact signatures and mutation/shape caveats, read
[references/api-reference.md](references/api-reference.md). For complete reader
and serving wiring, read [references/reader-workflows.md](references/reader-workflows.md).
For CSV, SimpleITK, IXI/MRBrainS conventions, and resampling boundaries, read
[references/data-formats-and-resampling.md](references/data-formats-and-resampling.md).
Use [references/troubleshooting.md](references/troubleshooting.md) when a
contract or compatibility check fails.
