# Cross-cutting troubleshooting

## The original scripts fail under Python 3

Symptoms include `No module named cPickle`, `No module named cStringIO`,
`reload`/`setdefaultencoding` errors, or byte/string failures while reading
custom charset files.

Likely cause: zi2zi was written for Python 2.7. Use a legacy environment for
the original scripts. Use the bundled helper scripts in this skill for safe
Python 3 planning and inspection only; they do not run the full TensorFlow
model.

## TensorFlow imports but training or inference fails

Common causes:

- TensorFlow 2 was installed instead of TensorFlow 1.x.
- A TensorFlow 1.x CPU build was installed but the user expects CUDA training.
- The GPU runtime is too new or too old for the selected TensorFlow 1.x wheel.
- GPUs are visible but already full, causing context-retain or OOM failures.
- `tf.contrib` or `tf.app.run` is unavailable because the code is being run
  against incompatible TensorFlow APIs.

Recovery:

1. Check `python -c "import tensorflow as tf; print(tf.__version__)"`.
2. Confirm `1.x` before running original zi2zi scripts.
3. For CUDA tasks, separately verify GPU visibility and free memory.
4. If device initialization is flaky on a modern GPU, use a legacy container or
   hide CUDA for CPU-only parser/graph checks.

## `scipy.misc` image functions are missing

Symptoms include `AttributeError: module 'scipy.misc' has no attribute 'imread'`
or similar errors for `imresize`/`imsave`.

Likely cause: modern SciPy removed these helpers. Use an older SciPy compatible
with Python 2.7 and TensorFlow 1-era zi2zi, or perform a maintenance port that
replaces image I/O with Pillow/imageio equivalents.

## Checkpoints cannot be restored

Symptoms include `fail to restore model`, TensorFlow `NotFoundError`, missing
`checkpoint` state file, or variable shape/name mismatch.

Check:

- `--model_dir` points at the concrete directory that contains TensorFlow
  checkpoint state and shard files, not just the top-level experiment folder.
- `--batch_size`, `--embedding_num`, `--embedding_dim`, and `--inst_norm` match
  the model that produced the checkpoint.
- Generator-only exports contain `embedding` and `g_` variables, not the full
  discriminator state.

## Training creates no useful samples or crashes on data

Check that `experiment/data/train.obj` and `experiment/data/val.obj` exist,
contain at least one record, and were packaged from JPGs named with integer
label prefixes. Empty sample directories often trace back to empty packaging,
over-aggressive glyph filtering, wrong font paths, or a charset with characters
unsupported by the target font.

## Output directories and relative paths are confusing

The original scripts often create or read paths relative to the process working
directory. Before running a command, decide explicitly where outputs should go:

- rendered JPG sample directory;
- experiment data directory;
- experiment checkpoint/log/sample directories;
- inference image or frame directory;
- exported generator directory.

Prefer absolute or clearly project-relative paths in commands you hand to the
user, and create output directories before long runs.
