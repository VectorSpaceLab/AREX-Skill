# Cross-cutting troubleshooting

## TensorFlow import or missing `tf.contrib`

**Symptom:** `ModuleNotFoundError`, missing `tensorflow.contrib`, or errors from
`tensorflow.contrib.rnn`/`seq2seq`.

**Cause:** TensorFlow 2.x or a Python/platform combination without a usable
TensorFlow 1.x wheel. Install a supported TensorFlow 1.x environment or treat
the repository as requiring a port; do not patch one import and call it
compatible.

## `librosa`/SciPy/NumPy import failure

**Symptom:** missing `numpy.testing.nosetester`, old `numba` JIT errors, or
`llvmlite` ABI messages.

**Recovery:** inspect all four versions together. The verified legacy baseline
uses NumPy 1.16.6 with SciPy 0.19.0 and llvmlite 0.31.0 with the old numba
selected by the resolver. Use an isolated environment and record any change;
do not mutate a user-owned environment casually.

## Missing dataset files

**Symptom:** `FileNotFoundError` for `metadata.csv`, `wavs/`, Blizzard `lab/`,
or `train.txt`.

**Recovery:** check the exact dataset layout in the data-preparation route,
run the bundled metadata validator, and only then run preprocessing. A missing
file is not fixed by changing `--num_workers`.

## Spectrogram shape mismatch

**Symptom:** errors such as `Incompatible shapes: [32,1340,80] vs [32,1000,80]`.

**Cause:** an utterance is longer than `max_iters * outputs_per_step *
frame_shift_ms`, or training/eval hparams differ.

**Recovery:** calculate the allowed duration, increase `max_iters` deliberately,
or filter/segment long utterances. Keep `outputs_per_step`, sample rate, and
spectrogram dimensions synchronized.

## Checkpoint or synthesis failure

**Symptom:** `saver.restore` cannot find a checkpoint, output WAVs are empty, or
synthesis fails immediately.

**Recovery:** pass the checkpoint prefix, not an arbitrary directory; confirm
that checkpoint sidecar files exist; use the same hparams used for training;
check the text cleaner and maximum decoder iterations. Test command construction
with the bundled synthesis builder before starting a server.

## Full-run boundaries

Dataset downloads, full preprocessing, model training, checkpoint evaluation,
and a long-running HTTP server are not small smoke tests. Require explicit data,
checkpoint, disk, memory, and runtime decisions before launching them. The
bundled scripts in this skill validate inputs and build commands without those
side effects.
