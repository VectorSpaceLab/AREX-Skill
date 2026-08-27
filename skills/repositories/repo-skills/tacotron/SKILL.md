---
name: tacotron
description: "Guides the legacy TensorFlow 1.x Tacotron repository for text
  normalization, speech-data preprocessing, Tacotron graph inspection, training,
  checkpoint synthesis, evaluation, and the Falcon demo server."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Tacotron

Use this skill for the original `keithito/tacotron`-style implementation of
Tacotron speech synthesis in TensorFlow 1.x. It is a repository workflow skill,
not a modern TensorFlow 2 or Tacotron 2 guide. Keep the original model's
checkpoint, hyperparameters, text cleaners, and spectrogram conventions
consistent across preprocessing, training, and synthesis.

## First route

- **Text cleaning, number expansion, symbols, ARPAbet, or CMUDict:** read
  [`text-normalization`](sub-skills/text-normalization/SKILL.md).
- **LJ Speech/Blizzard layout, preprocessing, or custom data conversion:** read
  [`data-preparation`](sub-skills/data-preparation/SKILL.md).
- **Graph shapes, CBHG/prenet/attention internals, or audio dimensions:** read
  [`model-architecture`](sub-skills/model-architecture/SKILL.md).
- **Training commands, hparams, checkpoints, TensorBoard, or loss recovery:**
  read [`training`](sub-skills/training/SKILL.md).
- **Checkpoint WAV synthesis, batch evaluation, or HTTP serving:** read
  [`synthesis-serving`](sub-skills/synthesis-serving/SKILL.md).

For a request spanning routes, use data-preparation → training →
synthesis-serving, and use text-normalization whenever the cleaner or symbol
contract changes.

## Runtime contract

The repository is not packaged with `setup.py`, `setup.cfg`, or `pyproject.toml`.
Use an isolated legacy Python environment and run repository entry points from a
Tacotron checkout. The documented requirements omit TensorFlow; install a
TensorFlow 1.x build compatible with the platform. TensorFlow 1.15.5 with
Python 3.6 was verified for inspection, together with the pinned audio/text
dependencies, but newer Python/TensorFlow combinations are not automatically
compatible with `tf.contrib`.

Use explicit roots in command examples; replace these two assignments only when
the checkout is stored elsewhere:

```bash
SKILL_ROOT=/path/to/tacotron-skill
CHECKOUT_ROOT=/path/to/tacotron-checkout
```

Bundled command builders run from `SKILL_ROOT` and print a command prefixed by
`cd "$CHECKOUT_ROOT"`. Native preprocessing, training, evaluation, and serving
must therefore run with the checkout as their cwd; a skill directory is not a
source checkout. The skill's audio path uses the repository's `librosa`/SciPy
helpers and built-in Griffin-Lim reconstruction. It does not bundle or require
a neural vocoder, but real WAV input is required for preprocessing and a real
checkpoint is required for synthesis.

```bash
cd "$CHECKOUT_ROOT"
python -m pip install -r requirements.txt
# Select a platform-compatible TensorFlow 1.x package; do not use TensorFlow 2.x.
python -c "import tensorflow as tf; print(tf.__version__); print(hasattr(tf, 'contrib'))"
```

The repository's requirements pin old versions. If modern package resolution
breaks `scipy`, `librosa`, or `numba`, follow the compatibility notes in
[`references/installation.md`](references/installation.md) rather than
blindly upgrading all dependencies.

## Verification boundary

The bundled text, metadata, fixture, environment, shape, and command helpers
are offline or dry-run checks. They do not prove real audio decoding,
spectrogram quality, checkpoint compatibility, generated WAV quality, GPU
performance, full preprocessing, training convergence, or server security.
Full training and checkpoint synthesis need external data/checkpoints and can
be expensive. Use the bundled builders and validators before starting them.

## Shared invariants

- The default sample rate is 20 kHz; audio uses 80 mel channels, 1025 linear
  frequency bins, 50 ms windows, and 12.5 ms frame shifts.
- `outputs_per_step=5` and `max_iters=200` affect both training and synthesis;
  use the same relevant hparams at both times.
- Preprocessing writes time-major `.npy` spectrogram arrays and `train.txt`
  rows with two filenames, frame count, and text. Validate this before training.
- Text conversion appends the `~` EOS symbol. Cleaner names and ARPAbet syntax
  must be available in both training and inference environments.
- Full training and checkpoint synthesis need real datasets/checkpoints and can
  be expensive. Use the bundled builders and validators before starting them.

Read [`references/troubleshooting.md`](references/troubleshooting.md) for
cross-cutting TensorFlow-version, dependency, path, checkpoint, and audio
failure handling. Read [`references/repo-provenance.md`](references/repo-provenance.md)
before deciding whether this skill is stale for a changed checkout.
