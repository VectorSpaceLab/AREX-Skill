# Inference troubleshooting

## Missing phonemizer or espeak backend

**Symptoms**

- `ImportError: No module named phonemizer`
- `phonemizer.backend.EspeakBackend` fails to construct
- `espeak` or `espeak-ng` is missing from `PATH`

**What it means**

The notebooks require Python `phonemizer` and a system espeak backend for the
English phoneme conversion step.

**What to check**

- Python package `phonemizer` is installed.
- A binary named `espeak-ng` or `espeak` is available.
- NLTK tokenization data is present for `word_tokenize`.

**What to do**

- Install the Python dependency if it is missing.
- Provide an `espeak-ng` or `espeak` binary.
- Re-run the safe asset checker with `--check-phonemizer`.

The checker reports the Python package, the detected binary, and whether the
backend can be instantiated without downloading anything.

## Missing checkpoints or reference audio

**Symptoms**

- `Models/LJSpeech/config.yml` or `Models/LJSpeech/epoch_2nd_00100.pth` is
  missing.
- `Models/LibriTTS/config.yml` or `Models/LibriTTS/epochs_2nd_00020.pth` is
  missing.
- `Demo/reference_audio/` is missing or empty.

**What it means**

The pretrained demos are not self-contained; the public Hugging Face assets must
be downloaded and unpacked locally.

**What to do**

- Download the matching Hugging Face model tree.
- For LibriTTS, download `reference_audio.zip` and extract it so the wav files
  are available under `Demo/reference_audio/`.
- Re-run `scripts/check_inference_assets.py`.

## NLTK tokenization data missing

**Symptoms**

- `LookupError` from `word_tokenize`
- NLTK complains about missing `punkt`

**What it means**

The notebooks call `word_tokenize` after phonemization. If the tokenizer data is
absent, text preprocessing fails before inference starts.

**What to do**

- Provide NLTK `punkt` data in the runtime.
- If you are preparing a notebook environment, follow the notebook behavior and
  download the tokenizer data before synthesis.

## CPU vs CUDA performance

**CPU behavior**

- Works for inference, but is slower.
- Useful when you want to avoid older-GPU numerical artifacts.

**CUDA behavior**

- Faster when a compatible GPU is available.
- Default notebook device selection is `cuda` when available, otherwise `cpu`.

**What to do when it is slow**

- Keep `diffusion_steps` at `5` for the default notebook balance.
- Shorten the text or break long passages into smaller chunks.
- Use long-form smoothing only where you need it.

## Older GPU high-pitched noise

**Symptom**

- Synthesized audio has a high-pitched background tone.

**What it means**

The README attributes this to numerical float differences on older GPUs.

**What to do**

- Prefer a newer CUDA GPU.
- Fall back to CPU inference if you need a clean result and can tolerate slower
  synthesis.

## Unsupported characters silently disappear

**Symptom**

- Some characters never appear in the synthesized output.

**What it means**

`TextCleaner` is a fixed symbol inventory. Unsupported symbols are dropped while
processing the text string.

**What to do**

- Normalize the input text to the notebook's supported ASCII/IPA symbol set.
- Inspect the `text_utils.py` symbol inventory if a character looks suspicious.

## Voice permission and license cautions

**Requirement**

- The README requires you to inform listeners that samples are synthesized unless
  you have explicit permission and license to clone the voice.

**What to do**

- Use only voices allowed by permission or license.
- If you share outputs, disclose that they are synthesized when required.

## Dependency variant caveat

The README mentions a GPL-licensed fork and an MIT-licensed PyPI package as
external alternatives. They are not the core workflow in this repository.
Use them only if you deliberately want those alternate packaging trade-offs.
