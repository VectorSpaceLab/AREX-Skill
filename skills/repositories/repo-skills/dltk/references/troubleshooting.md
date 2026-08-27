# DLTK cross-cutting troubleshooting

## Import and version failures

**Symptoms:** `tf.Session`, `tf.layers`, `tf.contrib`, or `tf.estimator` is
missing; `dltk.io.abstract_reader` fails at import; an application fails before
printing `--help`.

**Action:** run `python scripts/check_environment.py` and inspect only version
and symbol results. Use one coherent TensorFlow 1.x environment, with DLTK
0.2.1 and compatible NumPy/protobuf. TensorFlow 2.x is outside this graph.
Do not patch individual imports or claim a port without a separately reviewed
migration.

## Modern NumPy incompatibilities

Some legacy code uses removed aliases such as `np.int` or `np.float`, and the
crop/pad helper passes a list of slices where modern NumPy expects a tuple. Use
the bounded synthetic helpers in the relevant sub-skill to isolate the intended
behavior, then either use a compatible legacy dependency set or make an
explicit, tested compatibility adaptation. Preserve array rank, dtype, and
label semantics; do not hide an error with broad casts.

## Data and configuration failures

Missing NIfTI files, CSV rows, modality names, registration, or permissions are
caller data prerequisites. Validate the dataset root, row schema, expected
modality files, spatial alignment, and interpolation policy before calling a
Reader. Do not launch a downloader, archive extraction, credential workflow,
or cleanup command from an agent check. Replace example-specific paths with
caller-owned paths and stop with a precise missing-input report.

## TensorFlow graph and contract failures

A Reader must emit records matching its nested `dtypes` and
`example_shapes`; a network expects a static rank-5 channels-last feature
contract; and Estimator TRAIN/EVAL/PREDICT branches have different label and
export requirements. Check the earliest boundary first. Preserve output keys
such as `logits`, `y_prob`, `y_`, and `x_` when passing between routes. See the
nearest sub-skill troubleshooting reference for shape-specific recovery.

## Checkpoint, export, and restart hazards

An existing model directory normally means resume when graph and parameter
contracts match. Compare the checkpoint, global step, output shapes, and
serving receiver before reusing it. Reject historical `--restart` behavior
that recursively deletes a model directory. Use a new directory or an
explicitly approved reversible archive/rename. Export only after a bounded
prediction check and inspect the actual SavedModel signature before deployment.

## Verification boundaries

A passing synthetic smoke proves only the exercised local contract. It does
not prove NIfTI readability, data completeness, convergence, medical accuracy,
physical registration, or modern GPU compatibility. Keep optional CUDA and
external-data limitations visible in the handoff.
