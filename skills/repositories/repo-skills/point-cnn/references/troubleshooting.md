# PointCNN troubleshooting

## Installation and imports

- **`ModuleNotFoundError` for `tensorflow`, `h5py`, `plyfile`, or
  `transforms3d`:** install the legacy dependency set in an isolated Python
  environment, then rerun `scripts/check_environment.py`. Do not repair a
  valuable user environment in place.
- **`tf.contrib` or `tf.layers` is missing:** the runtime is too new or is not
  the TensorFlow 1.x compatibility stack. Use a tested legacy TensorFlow build;
  do not patch the model to eager APIs as an incidental troubleshooting step.
- **Import succeeds but graph execution hangs or fails during GPU setup:**
  separate framework/device validation from custom-op validation, select one
  visible GPU, check competing workloads and CUDA shared libraries, and record
  the bounded timeout. A device listing alone is not a pass.

## Data and configuration

- **HDF5 keys/ranks/counts do not align:** route to
  `data-preparation`, run its read-only validators, and regenerate the data in a
  new destination. Classification and segmentation schemas are different; do
  not mix their file lists.
- **`data_dim`, normals/RGB, or class counts mismatch:** use the setting matrix
  and ensure the model, setting, checkpoint, feature width, and label map are a
  matched tuple. Do not silently discard feature channels.
- **Relative file-list entries cannot be found:** resolve each entry relative
  to the list that contains it, including nested segmentation lists. Avoid
  changing the process working directory as a hidden fix.
- **`K * D` exceeds the point count or `P` is invalid:** inspect the actual
  layer input and setting tuple. Reduce dilation/neighborhood or increase the
  available point count intentionally; never hide a top-k shape error with
  padding that changes semantics.

## Custom operators and backends

- **`tf_sampling_so.so` is missing or cannot load:** check the sampling source,
  TensorFlow include/library paths, CUDA toolkit/compiler, C++ ABI, driver, and
  shared-library search path with the core/FPS diagnostic. Build only after the
  prerequisites are visible and keep the output outside valuable artifacts.
- **Undefined TensorFlow C++ symbols or ABI errors:** rebuild against the exact
  TensorFlow framework headers/library and compatible C++ ABI. A library that
  loads at graph-build time but fails in `Session.run` is not verified.
- **FPS times out, crashes, or returns no result:** stop the workflow. Confirm
  a small GPU framework smoke independently, use a bounded custom-op smoke,
  inspect GPU contention, and report `BLOCKED_REQUIRED_BACKEND` if execution
  still cannot be proven. CPU execution is not an equivalent substitute.

## CLI, checkpoints, and artifacts

- **Dynamic `-m`/`-x` import fails:** run the command from an application
  checkout or explicitly set its module search path; verify the model module
  and setting basename as a pair. The generated skill's helper scripts do not
  replace the application trainer.
- **Checkpoint restore fails:** compare model class count, `data_dim`, feature
  flags, X-Conv/X-DeConv tuples, variable names, and preprocessing with the run
  that produced the checkpoint. Use a new output directory for a fresh graph.
- **Predictions have length/index/category errors:** stop before merge; validate
  `data_num`, `indices_split_to_full`, category offsets, confidence arrays, and
  label conventions with the evaluation route. Never pad or truncate a
  prediction to make a metric run.
- **A metric looks plausible despite missing files:** treat coverage, untouched
  indices, class-0/default labels, and missing branches as failures until the
  artifact inventory is complete. PLY output is visualization, not a score.

## Expensive or unsafe operations

Dataset downloads, archive extraction, full conversion, Semantic3D's very large
acquisition, full training, and benchmark evaluation require explicit scope and
resource approval. They are not default verification steps. Historical launch
scripts may encode backgrounding and unquoted relative paths; use their
settings as evidence but construct a foreground command with explicit paths.
