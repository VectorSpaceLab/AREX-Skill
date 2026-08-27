---
name: data-preparation
description: "Guides Tacotron LJ Speech and Blizzard data layouts, spectrogram
  preprocessing, train.txt metadata contracts, and custom dataset
  preprocessors."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Data preparation

Use this route for dataset layout checks, `preprocess.py` command construction,
custom preprocessor design, spectrogram metadata validation, and failures before
training. Read [`references/data-formats.md`](references/data-formats.md) before
creating data.

## Workflow

1. Put the selected dataset in a stable base directory. LJ Speech requires
   `LJSpeech-1.1/metadata.csv` and `LJSpeech-1.1/wavs/*.wav`; Blizzard expects
   the documented book directories, `sentence_index.txt`, `lab/`, and `wav/`.
2. Build the preprocessing command with the bundled helper, choosing an
   explicit dataset and output directory. Review the printed command before
   intentionally executing the repository's matching entry point.
3. Confirm that the output contains time-major linear and mel `.npy` arrays and
   `train.txt` rows. Use the bundled validator before training.
4. For a new corpus, implement the four-field tuple contract and register a
   dataset branch only after a tiny fixture validates its paths, dtypes, frame
   counts, and text.
## Command roots and external audio boundary

Run bundled dry-runs from the skill root and execute the repository preprocessor
only from the checkout root:

```bash
SKILL_ROOT=/path/to/tacotron-skill
CHECKOUT_ROOT=/path/to/tacotron-checkout
cd "$SKILL_ROOT" && python sub-skills/data-preparation/scripts/build_preprocess_command.py --checkout-root "$CHECKOUT_ROOT" --base-dir /data/tacotron --dataset ljspeech --output training
cd "$SKILL_ROOT" && python sub-skills/data-preparation/scripts/validate_training_metadata.py --data-dir /data/tacotron/training
```

Preprocessing itself needs downloaded LJ Speech or Blizzard audio, readable WAV
decoding through the pinned `librosa`/SciPy stack, writable storage, and enough
disk. The fixture creates only local layout/array metadata plus a placeholder
PCM WAV; it does not run preprocessing, validate spectrograms, or train.

The bundled [`scripts/build_preprocess_command.py`](scripts/build_preprocess_command.py)
builds the documented CLI without reading a dataset. The bundled
[`scripts/create_tiny_ljspeech_fixture.py`](scripts/create_tiny_ljspeech_fixture.py)
creates a no-network layout fixture. [`scripts/validate_training_metadata.py`](scripts/validate_training_metadata.py)
checks rows and arrays without starting TensorFlow training. Read
[`references/workflows.md`](references/workflows.md) for preprocessing and
custom-corpus recipes and [`references/troubleshooting.md`](references/troubleshooting.md)
for path, audio, and shape failures.
