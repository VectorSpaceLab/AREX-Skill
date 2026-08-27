---
name: dltk
description: "Route DLTK 0.2.1 medical-imaging workflows across legacy
  TensorFlow 1.x data, models, Estimators, and deployment utilities."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# DLTK

Use this skill when a task names DLTK or asks for its medical-image readers,
preprocessing, 3-D TensorFlow networks, Estimator applications, SavedModel
prediction, or sliding-window segmentation utilities. This is a compatibility-
first operating graph for the public DLTK 0.2.1 surface, not a maintainer or
full-training guide.

## First gate: preserve the legacy runtime

DLTK uses TensorFlow 1.x graph APIs including `tf.Session`, `tf.layers`,
`tf.contrib`, `tf.train`, and `tf.estimator`. A known compatible reference is
Python 3.7 with TensorFlow 1.15 and legacy-compatible NumPy/SciPy/protobuf
versions. Do not claim TensorFlow 2.x compatibility or repair one missing
symbol with `tensorflow.compat.v1` and call that equivalent. From the directory containing this file, run the bundled read-only diagnostic
before importing application code:

```bash
python scripts/check_environment.py
```

If the diagnostic reports a missing TensorFlow 1.x symbol, stop and resolve the
caller-managed runtime first. CUDA support is historical and version-sensitive;
CPU execution is the verified functional baseline for the selected APIs. Do
not infer modern CUDA or accelerator compatibility from a CPU import.

## Public installation starting point

For a fresh caller-managed environment, install the public distribution and
then verify a coherent TensorFlow 1.x stack rather than accepting an arbitrary
modern resolver result:

```bash
python -m pip install dltk==0.2.1
python scripts/check_environment.py
```

The package's historical requirement declarations are inconsistent, so choose
compatible TensorFlow 1.x, NumPy, and protobuf versions deliberately. Add
SimpleITK for NIfTI workflows and pandas for CSV-driven applications only when
those routes are needed. Do not mutate an existing environment without
approval.

## Route by task

- **Readers, NIfTI/CSV layouts, normalization, augmentation, patches, serving
  placeholders:** read [data-pipelines](sub-skills/data-pipelines/SKILL.md).
- **3-D networks, residual units, activations, losses, metrics, or output
  dictionaries:** read [model-building](sub-skills/model-building/SKILL.md).
- **`model_fn`, `Reader`-to-Estimator composition, train/eval/resume, exports,
  application flags, or the monitored-session GAN:** read
  [training-and-estimators](sub-skills/training-and-estimators/SKILL.md).
- **SavedModel prediction, crop averaging, sliding windows, segmentation
  metrics, or metadata-preserving NIfTI output:** read
  [inference-and-deployment](sub-skills/inference-and-deployment/SKILL.md).

For a request spanning routes, freeze the data shape and output-key contract
first, then compose the Reader and model function, and only then export or
stitch predictions. Keep each route's references available while crossing the
handoff rather than duplicating their API details.

## Safe operating sequence

1. Confirm the DLTK/TensorFlow 1.x API gate and package version.
2. Replace private dataset paths with caller-owned, validated roots and use
   synthetic arrays or a permissioned tiny fixture first.
3. Make the nested Reader `dtypes`/`example_shapes` contract agree with every
   yielded record; separate PREDICT from TRAIN/EVAL and return after a
   feature-only prediction yield.
4. Use rank-5, channels-last feature tensors and preserve network output keys.
5. Bound checks to `--help`, graph construction, one or a few Estimator steps,
   temporary model directories, and deterministic synthetic volumes.
6. Before deployment, inspect the SavedModel signature, window/output geometry,
   coverage, label semantics, and SimpleITK metadata. Write output only to an
   explicitly selected caller directory.

Do not download IXI/MRBrainS data, use credentials, run full historical
training, invoke destructive restart cleanup, or load external models as a
routine skill check. The source applications are data-bound demonstrations and
some are unsafe to copy verbatim. See the cross-cutting
[troubleshooting guide](references/troubleshooting.md) and
[compatibility reference](references/compatibility-and-installation.md) when a
runtime, dependency, data, or workflow gate fails.

## Package facts and staleness

The generated graph targets DLTK commit `f94d3bb509eb0741164149acbef0788769a869e4`,
version `0.2.1`. Read [repo-provenance.md](references/repo-provenance.md)
before relying on it for a different package version or changed public API.
The structured routing metadata is in
[repo-routing-metadata.json](references/repo-routing-metadata.json).
