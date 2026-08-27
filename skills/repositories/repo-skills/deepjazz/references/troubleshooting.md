# deepjazz Cross-Cutting Troubleshooting

## Missing dependency or wrong backend

**Symptoms**: `ImportError` for `music21`, `keras`, or `theano`; Keras selects TensorFlow; Theano import warnings become fatal.

**Recovery**:

1. Use a Python 2.7-compatible environment for faithful legacy runs.
2. Install legacy Keras/Theano/music21 versions.
3. Set `KERAS_BACKEND=theano` before importing Keras.
4. Run `scripts/check_deepjazz_environment.py --expect-theano`.

## Python 3 source incompatibility

**Symptoms**: `xrange` is undefined, `izip_longest` cannot import, Keras does not accept `nb_epoch`, or NumPy rejects `np.bool`.

**Recovery**:

- For faithful reproduction, switch to a Python 2.7 legacy environment.
- For modernization, apply the porting notes in `sub-skills/lstm-generation/references/modernization-notes.md` and re-run grammar/data smoke checks before training.

## Data error appears during training

**Symptoms**: model sequence arrays are empty, preprocessing assertions fail, or grammar unparse fails after a new MIDI file is used.

**Recovery**:

1. Do not debug the LSTM first.
2. Run `sub-skills/midi-preprocessing/scripts/inspect_midi_structure.py` on the MIDI file.
3. Read `sub-skills/midi-preprocessing/references/data-assumptions.md` and adapt part/window selection.
4. Run grammar smoke checks before full generation.

## Headless or server-side playback failure

**Symptoms**: generation reaches the end but realtime MIDI playback fails, blocks, or errors because no audio/MIDI output device exists.

**Recovery**:

- Treat playback as optional side effect, not proof of generation quality.
- Adapt the generation entrypoint to skip the realtime `StreamPlayer(...).play()` call and write MIDI directly.
- Keep MIDI output validation separate from audio playback.

## Full generator is slow or nondeterministic

**Symptoms**: one epoch still takes too long, outputs vary, or generated pitch choices differ between runs.

**Recovery**:

- Reduce epochs only for smoke tests; quality depends on training and data.
- Set random seeds in adapted code when deterministic tests are needed.
- Validate structural outputs instead of exact melodies.
- Use the bundled no-training scripts for quick environment/data/grammar checks.

## Optional CUDA path fails

**Symptoms**: Theano cannot use GPU, CUDA flags are ignored, or GPU errors appear on modern drivers/hardware.

**Recovery**:

- Use CPU unless the task explicitly requires legacy Theano CUDA.
- Verify Theano GPU support with a tiny device operation before training.
- Do not install random modern CUDA packages and assume compatibility with old Theano.
- If CUDA is required, treat unavailable compatibility as a backend block rather than a normal skip.
