# Inference Workflows

## Purpose

Use these recipes to plan or run Python inference with Coqui TTS without reopening repository docs or examples. Loading released models can download large files and prompt for TOS; use the helper script's `--dry-run` and `--allow-download` gates when acting noninteractively.

## Bundled helper provenance

The two scripts in this sub-skill are safe wrappers around the installed Coqui `tts` model-listing and synthesis behavior, implemented through public installed-package APIs instead of source-checkout imports. They intentionally omit persistent server flags, full CLI catalogs, training commands, audio preprocessing, and FreeVC source/target conversion because those surfaces are owned by sibling sub-skills. Model-zoo download sweeps, optional released-model synthesis tests, and XTTS streaming tests are reference-only for this sub-skill unless the user explicitly approves network/cache/TOS and runtime budget.

## 1. Discover a model without downloading

```bash
python scripts/inspect_tts_models.py --count
python scripts/inspect_tts_models.py --type tts_models --contains vits --format names
python scripts/inspect_tts_models.py --query tts_models/en/ljspeech/tacotron2-DDC --format table
```

Use this before selecting a model for synthesis, before checking a default vocoder, or when diagnosing a misspelled model name.

## 2. Single-speaker released model inference

Use this when the selected model does not require speaker or language inputs.

```python
import torch
from TTS.api import TTS

device = "cuda" if torch.cuda.is_available() else "cpu"
tts = TTS(model_name="tts_models/de/thorsten/tacotron2-DDC", progress_bar=False).to(device)
tts.tts_to_file(
    text="Ich bin eine Testnachricht.",
    file_path="output.wav",
    split_sentences=True,
)
```

Validation:

- Confirm the output file exists and is non-empty.
- If the chosen model is actually multi-speaker or multilingual, `TTS` raises a `ValueError`; switch to the relevant workflow below.
- If the task is only to prepare a command safely, use:

```bash
python scripts/synthesize_text.py \
  --model-name tts_models/de/thorsten/tacotron2-DDC \
  --text "Ich bin eine Testnachricht." \
  --out-path output.wav \
  --dry-run
```

To actually load a released model through the helper, add `--allow-download` after user approval.

## 3. Multi-speaker released model inference

Use this after loading a model where `tts.is_multi_speaker` is true.

```python
import torch
from TTS.api import TTS

device = "cuda" if torch.cuda.is_available() else "cpu"
tts = TTS(model_name="tts_models/en/vctk/vits", progress_bar=False).to(device)

if tts.is_multi_speaker:
    print(tts.speakers)
    speaker = tts.speakers[0]
else:
    speaker = None

tts.tts_to_file(
    text="This is a multi-speaker synthesis check.",
    speaker=speaker,
    file_path="speaker-output.wav",
)
```

Rules:

- Pass `speaker=<name>` when selecting a speaker known to the model.
- Pass `speaker_wav=<path-or-list>` only for models that support reference-audio voice cloning.
- Do not pass `speaker` to a single-speaker model.

## 4. Multilingual voice cloning with XTTS or YourTTS

Use this when a user asks for cross-language voice cloning, multilingual output, XTTS, or YourTTS.

```python
import torch
from TTS.api import TTS

device = "cuda" if torch.cuda.is_available() else "cpu"
tts = TTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2", progress_bar=False).to(device)
print("languages:", tts.languages)
print("built-in speakers:", tts.speakers)

tts.tts_to_file(
    text="It took me quite a long time to develop a voice.",
    speaker_wav=["reference-speaker.wav"],
    language="en",
    file_path="xtts-output.wav",
    split_sentences=True,
)
```

Rules:

- Provide `language`; multilingual models reject missing language.
- Provide either a supported `speaker` or `speaker_wav`; multi-speaker models reject requests with neither.
- `speaker_wav` may be a single path or a list of paths for XTTS-style cloning.
- `split_sentences=True` is safer for long text and VRAM. `False` can preserve context but may hit context-length or memory limits.
- XTTS v2 is TOS-gated and may be large; require explicit download/TOS approval before loading.

## 5. Custom checkpoint with optional external vocoder

Use this when a user already has model/config files and does not want a registry download.

High-level `TTS.api.TTS` path:

```python
from TTS.api import TTS

tts = TTS(
    model_path="checkpoint.pth",
    config_path="config.json",
    vocoder_path="vocoder.pth",
    vocoder_config_path="vocoder_config.json",
    progress_bar=False,
).to("cpu")

tts.tts_to_file(
    text="Custom checkpoint inference.",
    file_path="custom-output.wav",
    split_sentences=True,
)
```

Direct `Synthesizer` path when speaker/language/encoder files are needed:

```python
from TTS.utils.synthesizer import Synthesizer

synthesizer = Synthesizer(
    tts_checkpoint="checkpoint.pth",
    tts_config_path="config.json",
    tts_speakers_file="speakers.json",
    tts_languages_file="language_ids.json",
    vocoder_checkpoint="vocoder.pth",
    vocoder_config="vocoder_config.json",
    use_cuda=False,
)

wav = synthesizer.tts(
    text="Custom multi-speaker inference.",
    speaker_name="speaker-id-or-name",
    language_name="en",
    split_sentences=True,
)
synthesizer.save_wav(wav, "custom-output.wav")
```

Checklist before running:

- Verify every checkpoint/config path exists.
- Ensure the TTS config matches the checkpoint architecture.
- If a vocoder is provided, check audio sample rate, number of mel bins, hop length, and normalization compatibility; route detailed vocoder diagnosis to [../vocoder-and-audio-tools/SKILL.md](../../vocoder-and-audio-tools/SKILL.md).
- If the config uses phonemes, ensure the phonemizer is defined and installed.

The bundled helper can safely plan this without downloads:

```bash
python scripts/synthesize_text.py \
  --model-path checkpoint.pth \
  --config-path config.json \
  --vocoder-path vocoder.pth \
  --vocoder-config-path vocoder_config.json \
  --text "Custom checkpoint inference." \
  --out-path custom-output.wav \
  --dry-run
```

## 6. Fairseq MMS VITS model names

Use Fairseq names for the large MMS language set:

```python
from TTS.api import TTS

api = TTS(model_name="tts_models/eng/fairseq/vits", progress_bar=False).to("cpu")
api.tts_to_file("This is a test.", file_path="fairseq-output.wav")
```

Cautions:

- Name grammar is `tts_models/<iso3_language_code>/fairseq/vits`.
- Fairseq language names are dynamically handled by the model manager and may not all appear in `list_models()`.
- Loading downloads a model directory; require explicit user approval and enough disk/network budget.
- For TTS plus voice conversion with Fairseq output, route FreeVC/source-target semantics to [../voice-conversion/SKILL.md](../../voice-conversion/SKILL.md).

## 7. XTTS streaming at high level

The high-level `TTS.api.TTS.tts_to_file` workflow does not expose streaming chunks. XTTS streaming uses the lower-level XTTS model API after model files are available:

1. Confirm the user approved XTTS download/TOS and has enough GPU/CPU budget.
2. Load an `XttsConfig` from the downloaded XTTS model directory.
3. Initialize `Xtts`, load its checkpoint, and move it to the selected device.
4. Compute `gpt_cond_latent` and `speaker_embedding` from one or more reference wav files.
5. Call `model.inference_stream(text, language, gpt_cond_latent, speaker_embedding, ...)` and concatenate returned chunks before saving.

Only plan this at a high level in this sub-skill. If the task becomes fine-tuning or GPT encoder training, route to [../training-config-data/SKILL.md](../../training-config-data/SKILL.md).

## 8. TTS with voice conversion fallback

`TTS.tts_with_vc` and `TTS.tts_with_vc_to_file` synthesize speech first, then convert it toward a `speaker_wav` target using FreeVC when no converter is loaded:

```python
from TTS.api import TTS

tts = TTS("tts_models/de/thorsten/tacotron2-DDC", progress_bar=False).to("cpu")
tts.tts_with_vc_to_file(
    text="Wie sage ich auf Italienisch, dass ich dich liebe?",
    speaker_wav="target-speaker.wav",
    file_path="tts-vc-output.wav",
)
```

Use this sub-skill for the `TTS` method signatures and model-loading implications. For missing source/target/reference wavs, FreeVC cache/download failures, or conversion role confusion, use [../voice-conversion/SKILL.md](../../voice-conversion/SKILL.md).

## 9. Decide whether to run synthesis now

Before running any released-model synthesis, answer these questions:

- Did the user approve network/model-cache writes and possible license/TOS prompts?
- Is the model likely large or slow on CPU (XTTS, Bark, Tortoise, Fairseq)?
- Are required speaker/language/reference wav arguments known?
- Is the output path safe to write?
- Is this a planning task where `--dry-run` or registry inspection is enough?

If any answer is unclear, stop and ask before using `--allow-download` or loading the model.
