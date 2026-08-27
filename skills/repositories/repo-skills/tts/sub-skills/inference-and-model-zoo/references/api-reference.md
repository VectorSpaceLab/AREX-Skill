# Python API Reference

## Purpose

Read this when choosing between `TTS.api.TTS`, `TTS.utils.manage.ModelManager`, and `TTS.utils.synthesizer.Synthesizer` for inference-time work. The facts here were verified against Coqui TTS 0.22.0 package/source inspection and installed API signatures.

## Version and import constraints

- Distribution/import: install distribution `TTS`, import package `TTS`.
- Verified package version: `0.22.0`.
- Supported Python range from package metadata: `>=3.9,<3.12`.
- CUDA smoke was optional; CPU is sufficient for registry inspection and argument planning.

## `TTS.api.TTS` facade

Use `TTS.api.TTS` for most future-agent inference tasks: released model loading, simple custom checkpoint loading, `tts` waveform generation, and `tts_to_file` output.

### Constructor

```python
TTS(
    model_name: str = "",
    model_path: str = None,
    config_path: str = None,
    vocoder_path: str = None,
    vocoder_config_path: str = None,
    progress_bar: bool = True,
    gpu=False,
)
```

Notes:

- `model_name` may be a released TTS model name, a voice-conversion model name, a dynamic Fairseq name, or an XTTS shorthand accepted by `ModelManager`; loading may download model files.
- `model_path` + `config_path` load a custom checkpoint. Optional `vocoder_path` + `vocoder_config_path` load an external vocoder.
- `gpu` remains in the signature but emits a deprecation warning. Prefer `tts = TTS(...).to("cuda")` or `.to("cpu")` after construction.
- `progress_bar=False` is useful for noninteractive agents and logs.

### Discovery and load methods

| Method | Signature | Use | Download behavior |
| --- | --- | --- | --- |
| `list_models` | `TTS.list_models(self)` | Returns a `ModelManager` configured for the bundled registry. Call `.list_models()`, `.list_tts_models()`, `.list_vocoder_models()`, or `.list_vc_models()` on it. | No downloads. |
| `models` property | `tts.models` | Returns only released TTS model names through `ModelManager.list_tts_models()`. | No downloads. |
| `download_model_by_name` | `TTS.download_model_by_name(self, model_name: str)` | Downloads a released model and its default vocoder when applicable; returns `(model_path, config_path, vocoder_path, vocoder_config_path, model_dir)`. | Downloads and may prompt for TOS. |
| `load_tts_model_by_name` | `TTS.load_tts_model_by_name(self, model_name: str, gpu: bool = False)` | Downloads/loads a released TTS model into `self.synthesizer`. | Downloads and may prompt for TOS. |
| `load_tts_model_by_path` | `TTS.load_tts_model_by_path(self, model_path: str, config_path: str, vocoder_path: str = None, vocoder_config: str = None, gpu: bool = False)` | Loads a custom TTS checkpoint and optional vocoder paths into `self.synthesizer`. | No registry download; file paths must already exist. |

`download_model_by_name` return shape:

- Normal TTS checkpoint with default vocoder: `model_path`, `config_path`, `vocoder_path`, and `vocoder_config_path` are populated; `model_dir` is `None`.
- Normal TTS checkpoint with no default vocoder: `model_path` and `config_path` are populated; vocoder paths and `model_dir` are `None`.
- Fairseq and multi-file models such as XTTS, Bark, and Tortoise: `model_dir` is populated and checkpoint/config path returns may be `None`, because the model implementation loads from a directory.

### Synthesis methods

```python
TTS.tts(
    self,
    text: str,
    speaker: str = None,
    language: str = None,
    speaker_wav: str = None,
    emotion: str = None,
    speed: float = None,
    split_sentences: bool = True,
    **kwargs,
)

TTS.tts_to_file(
    self,
    text: str,
    speaker: str = None,
    language: str = None,
    speaker_wav: str = None,
    emotion: str = None,
    speed: float = 1.0,
    pipe_out=None,
    file_path: str = "output.wav",
    split_sentences: bool = True,
    **kwargs,
)
```

Key arguments:

- `text`: required text input for TTS synthesis.
- `speaker`: speaker name for multi-speaker models. Inspect `tts.is_multi_speaker` and `tts.speakers` after loading.
- `speaker_wav`: reference wav path, or for models that support it a list of reference wav paths, for voice cloning.
- `language`: language code/name for multilingual models. Inspect `tts.is_multi_lingual` and `tts.languages` after loading.
- `split_sentences`: defaults to `True`; synthesis splits text into sentences and concatenates generated audio. Set `False` only when context coherence is more important than memory/context-length safety.
- `tts` returns waveform samples; `tts_to_file` saves audio and returns the output file path.

Argument validation performed by `TTS`:

- Multi-speaker model with neither `speaker` nor `speaker_wav` raises `ValueError`.
- Multilingual model without `language` raises `ValueError`.
- Passing `speaker` to a non-multi-speaker model raises `ValueError` unless the model uses a `voice_dir` path.
- Passing `language` to a non-multilingual model raises `ValueError`.
- `emotion` and `speed` together are rejected for discontinued Coqui Studio-only behavior.

### Mixed TTS plus voice conversion entry points

```python
TTS.tts_with_vc(
    self,
    text: str,
    language: str = None,
    speaker_wav: str = None,
    speaker: str = None,
    split_sentences: bool = True,
)

TTS.tts_with_vc_to_file(
    self,
    text: str,
    language: str = None,
    speaker_wav: str = None,
    file_path: str = "output.wav",
    speaker: str = None,
    split_sentences: bool = True,
)
```

These methods synthesize temporary TTS output, then use the default FreeVC model if a voice converter is not already loaded. They are useful when a single-speaker TTS model must imitate a target speaker reference, but source/target wav semantics and FreeVC failures are owned by [../voice-conversion/SKILL.md](../../voice-conversion/SKILL.md).

## `TTS.utils.manage.ModelManager`

Use `ModelManager` for registry-only listing/querying, or for explicit model downloads after user approval.

```python
ModelManager(models_file=None, output_prefix=None, progress_bar=False, verbose=True)
```

Important methods:

| Method | Behavior |
| --- | --- |
| `list_models()` | Returns all registry names across `tts_models`, `vocoder_models`, and `voice_conversion_models`; prints names when `verbose=True`. |
| `list_tts_models()` | Returns only TTS model names. |
| `list_vocoder_models()` | Returns only vocoder model names. |
| `list_vc_models()` | Returns only voice-conversion model names. |
| `model_info_by_full_name(model_query_name)` | Prints model type, language, dataset, model name, description, and default vocoder when available. It is a print-style query, not a structured return. |
| `download_model(model_name)` | Downloads model files into the user model cache, handles TOS checks, extracts archives, validates cached hashes when present, and returns `(model_path_or_dir, config_path, model_item)`. |

Registry counts verified for TTS 0.22.0: 88 total entries: 70 `tts_models`, 17 `vocoder_models`, and 1 `voice_conversion_models` entry.

## `TTS.utils.synthesizer.Synthesizer`

Use `Synthesizer` directly when `TTS.api.TTS` is too high-level, especially for custom checkpoints that need explicit speaker/language files, encoder files, voice-conversion checkpoints, or a downloaded multi-file `model_dir`.

```python
Synthesizer(
    tts_checkpoint: str = "",
    tts_config_path: str = "",
    tts_speakers_file: str = "",
    tts_languages_file: str = "",
    vocoder_checkpoint: str = "",
    vocoder_config: str = "",
    encoder_checkpoint: str = "",
    encoder_config: str = "",
    vc_checkpoint: str = "",
    vc_config: str = "",
    model_dir: str = "",
    voice_dir: str = None,
    use_cuda: bool = False,
)
```

Synthesis and output:

```python
Synthesizer.tts(
    self,
    text: str = "",
    speaker_name: str = "",
    language_name: str = "",
    speaker_wav=None,
    style_wav=None,
    style_text=None,
    reference_wav=None,
    reference_speaker_name=None,
    split_sentences: bool = True,
    **kwargs,
)
Synthesizer.save_wav(self, wav, path: str, pipe_out=None)
Synthesizer.split_into_sentences(self, text)
```

`Synthesizer.split_into_sentences` uses an English `pysbd` segmenter. Native unit evidence covers abbreviations, initials, URLs, list numbering, and punctuation such as `Hey!!`.

Direct `Synthesizer` loading checklist:

1. Confirm checkpoint/config files exist before constructing the object.
2. If `use_cuda=True`, verify `torch.cuda.is_available()` first; the constructor asserts when CUDA is unavailable.
3. If the TTS config uses phonemes, ensure a phonemizer is configured and installed.
4. When pairing a custom TTS checkpoint with an external vocoder, verify compatible sample rate, mel dimensions, and normalization. Detailed vocoder mismatch recovery belongs in [../vocoder-and-audio-tools/SKILL.md](../../vocoder-and-audio-tools/SKILL.md).
5. For custom multi-speaker or multilingual models, provide `tts_speakers_file` and/or `tts_languages_file` when they are not embedded in the checkpoint/config.
