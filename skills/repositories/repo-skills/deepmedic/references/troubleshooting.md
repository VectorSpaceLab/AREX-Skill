# DeepMedic Cross-Cutting Troubleshooting

Read this reference when a failure spans installation, the CLI, TensorFlow,
configuration paths, or checkpoint handoff. Then read the nearest sub-skill
troubleshooting file for workflow-specific recovery.

## Install and import

**Symptom:** `import tensorflow` fails with `Descriptors cannot be created
directly` or a generated `*_pb2.py` error.

**Cause:** Older TensorFlow 2.6-era generated protobuf code is being loaded with
a newer protobuf runtime. Pin protobuf to a compatible 3.20.x release, or use a
fully matched newer TensorFlow/Python stack. Verify with `python -m pip check`
and a fresh `import tensorflow as tf`; do not hide the error with an arbitrary
environment variable in production.

**Symptom:** TensorFlow imports but reports NumPy ABI or binary incompatibility.

**Cause:** The package metadata allows newer NumPy than the TensorFlow build
supports. Use a coherent version set rather than upgrading only NumPy. The
verified baseline used NumPy 1.19.5 with TensorFlow 2.6.2 and the older SciPy,
pandas, and NiBabel releases listed in the root skill.

**Symptom:** `deepMedicRun` is missing or imports from the wrong checkout.

**Recovery:** Install the distribution into the environment used for the
command, run `python -m pip show deepmedic` for private diagnostics, then run
`deepMedicRun -h`. Do not copy a source checkout path into a reusable workflow.
A legacy `setup.py` editable-install deprecation warning is not itself a runtime
failure.

## CUDA and device selection

**Symptom:** `-dev cuda0` falls back to CPU, TensorFlow reports
`Could not load dynamic library 'libcudart.so'`, `libcublas.so`, or
`libcudnn.so`, or no GPU appears in `tf.config.list_physical_devices('GPU')`.

**Recovery:** Check the installed TensorFlow build's CUDA/cuDNN versions, the
host driver, and runtime library visibility. The driver-reported CUDA version is
not the same as an installed toolkit. Use the package's documented compatible
runtime or a matching TensorFlow build; inspect `PATH`/`LD_LIBRARY_PATH` only
for the current environment. Re-run a tiny device allocation before launching
DeepMedic. A visible GPU alone does not prove that the framework can execute.

**Symptom:** the process uses too much GPU memory or is killed during graph
construction.

**Recovery:** select one device with `-dev cudaN`, reduce feature maps, segment
dimensions, batch sizes, and loaded sample counts, and disable full-volume
validation or feature-map saving during the smoke run. Do not treat a smaller
CPU run as proof of a large GPU configuration.

## CLI and configuration

**Symptom:** `deepMedicRun` says `-model` is required, or rejects both `-train`
and `-test`.

**Recovery:** use exactly one session mode and supply the architecture config:
`deepMedicRun -model MODEL.cfg -train TRAIN.cfg` or
`deepMedicRun -model MODEL.cfg -test TEST.cfg`. `-resetopt` is valid only for
training. Run `deepMedicRun -h` to confirm the installed entry point.

**Symptom:** a config cannot find a list, NIFTI, or output path.

**Cause:** Config paths and file-list paths are resolved relative to different
anchors. A path written inside a config is resolved relative to that config;
paths inside a list file are resolved relative to the list file. Make this
explicit by using absolute paths for a first smoke test or carefully preserving
the relative layout. Do not change the working directory midway through a
session.

**Symptom:** a config raises a syntax error or unexpectedly imports code.

**Cause:** `.cfg` files are Python source, not a declarative key/value format.
Use literal assignments, trusted files, and the bundled model-config inspector
for architecture fields. Never use the package loader as a sandbox for an
untrusted config.

## Data and labels

**Symptom:** mismatched case counts, array shapes, voxel sizes, or affine
errors appear during loading.

**Recovery:** run the bundled NIFTI manifest validator for every channel list
and optional label/ROI list. Fix the subject table, registration/resampling,
or manifest ordering before changing CNN parameters. Every subject's modalities,
label, and ROI must share a grid; use one voxel size across the database.

**Symptom:** `GT labels include value ... greater than what CNN expects`, or
metrics are nonsensical.

**Recovery:** inspect unique labels, reserve `0` for background, remap sparse
values such as `0,10,20` to contiguous ids, and set
`numberOfOutputClasses` to include all classes. Do not silently clip labels.

**Symptom:** normalization creates NaNs, constant values, or unexpectedly poor
results.

**Recovery:** check ROI occupancy and intensity variance, choose exactly one
z-score mode (all channels or a per-channel boolean list), and avoid applying
runtime normalization twice to already normalized images. A missing ROI makes
statistics use the whole volume.

## Checkpoints and outputs

**Symptom:** restore fails with missing variables, shape mismatch, or file-not-
found errors.

**Recovery:** pass the shared checkpoint prefix ending in `.model.ckpt`, confirm
both `.index` and `.data-*` shards exist, and use the exact architecture that
created it. A directory may be used when it contains a TensorFlow latest
checkpoint. If this is fine-tuning, use `-resetopt` only after confirming that
network weights should be retained while optimizer state is reset.

**Symptom:** the process exits but expected predictions, probabilities, logs,
or TensorBoard files are absent.

**Recovery:** inspect `folderForOutput`, `sessionName`, and configured save
flags. Use the relevant read-only output checker, then inspect the session log
for caught exceptions. Do not infer success from exit status alone; validate
NIFTI shape/affine, finite values, class ranges, and case-name coverage.
