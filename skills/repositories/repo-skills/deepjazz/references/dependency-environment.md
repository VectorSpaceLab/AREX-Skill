# Dependency and Environment Guidance

## Purpose

Read this before running or adapting deepjazz. The project is a legacy Keras/Theano script collection and needs an older runtime for faithful execution.

## Faithful legacy stack

The verified inspection stack used these public package families:

- Python 2.7
- NumPy 1.16.x
- SciPy 1.2.x
- Theano 0.9.x
- Keras 1.2.x with Theano backend
- music21 3.1.x

A generic setup shape is:

```bash
# Use an isolated environment from your preferred manager; do not install into a modern base environment.
python -m pip install "Theano==0.9.0" "Keras==1.2.2" "music21==3.1.0"
export KERAS_BACKEND=theano
python scripts/check_deepjazz_environment.py --expect-theano
```

If your manager supports Python version selection, create the environment with Python 2.7 and install NumPy/SciPy from binary packages first.

## Modern Python warning

The original source uses Python 2-era APIs and old Keras names:

- `xrange`
- `itertools.izip_longest`
- Keras `nb_epoch`
- `keras.layers.core` and `keras.layers.recurrent` import paths
- NumPy `np.bool`

For a modern port, fix these before debugging model behavior. The LSTM generation sub-skill has a dedicated modernization reference.

## CPU and optional GPU

The public project documentation describes both CPU execution and a Theano GPU mode. Treat CPU as the baseline for this skill. The GPU path is optional legacy acceleration and requires a compatible NVIDIA CUDA/Theano stack with Theano flags equivalent to `mode=FAST_RUN`, `device=gpu`, and `floatX=float32`.

Do not claim GPU verification from a CPU import. If a user explicitly needs legacy CUDA execution, verify it separately on compatible hardware and with a compatible Theano/CUDA runtime before launching any playback-capable generator entrypoint.

## Safe checks

Run checks that do not train, play audio, or write MIDI before attempting full generation:

```bash
python scripts/check_deepjazz_environment.py --expect-theano
python sub-skills/grammar-and-qa/scripts/grammar_roundtrip_smoke.py --seed 7
python sub-skills/midi-preprocessing/scripts/inspect_midi_structure.py --midi-file <input.mid>
python sub-skills/lstm-generation/scripts/legacy_generation_check.py --check-imports --show-settings --expect-theano
```

Use these checks to separate environment, data, grammar, and generation problems.
