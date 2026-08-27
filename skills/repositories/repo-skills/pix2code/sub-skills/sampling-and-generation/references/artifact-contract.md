# pix2code Trained Artifact Contract

## Purpose

Read this before sampling from a trained pix2code model directory.

## Required files

A valid artifact directory must contain all of these files with the same basename prefix:

```text
pix2code.json
pix2code.h5
meta_dataset.npy
words.vocab
```

## What each file means

| File | Role |
| --- | --- |
| `pix2code.json` | Keras model architecture serialized by the legacy training code. |
| `pix2code.h5` | Trained model weights. |
| `meta_dataset.npy` | NumPy array containing input shape, output size, and dataset size metadata. |
| `words.vocab` | Vocabulary serialization used to convert between tokens and one-hot vectors. |

## Sampling prerequisites

- The artifact directory must be passed separately from the input screenshot path.
- The screenshot must be a PNG image readable by OpenCV.
- The legacy sampler expects a valid tokenizer vocabulary and model metadata before it can run.

## Safe validation command

```bash
python sub-skills/sampling-and-generation/scripts/check_pix2code_artifacts.py --artifacts /path/to/bin
```

The helper fails fast when one or more required files are missing and can optionally try a lightweight model load when the legacy ML stack is installed.
