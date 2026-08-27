# Model Zoo and Registry Reference

## Purpose

Read this before listing, querying, downloading, or naming released Coqui TTS, vocoder, or voice-conversion models from Python. Use [scripts/inspect_tts_models.py](../scripts/inspect_tts_models.py) for safe registry inspection without downloads.

## Registry shape and counts

Coqui TTS 0.22.0 ships a bundled model registry with this nested grammar:

```text
<model_type>/<language>/<dataset>/<model>
```

Allowed top-level `model_type` values:

- `tts_models`
- `vocoder_models`
- `voice_conversion_models`

Verified registry size for this version:

| Type | Count | Example |
| --- | ---: | --- |
| `tts_models` | 70 | `tts_models/en/ljspeech/tacotron2-DDC` |
| `vocoder_models` | 17 | `vocoder_models/en/ljspeech/hifigan_v2` |
| `voice_conversion_models` | 1 | `voice_conversion_models/multilingual/vctk/freevc24` |
| Total | 88 | all of the above |

Model names are case-sensitive and slash-separated. Do not drop the model type prefix when using Python `TTS(model_name=...)` or `ModelManager` queries.

## Safe registry queries

Read-only queries do not download weights:

```bash
python scripts/inspect_tts_models.py --count
python scripts/inspect_tts_models.py --type tts_models --contains xtts --format table
python scripts/inspect_tts_models.py --query tts_models/en/ljspeech/tacotron2-DDC --format json
```

Equivalent Python:

```python
from TTS.api import TTS

manager = TTS().list_models()      # returns ModelManager, not a plain list
all_names = manager.list_models()
tts_names = manager.list_tts_models()
vocoder_names = manager.list_vocoder_models()
vc_names = manager.list_vc_models()
manager.model_info_by_full_name("tts_models/en/ljspeech/tacotron2-DDC")
```

`model_info_by_full_name` prints metadata. If structured output is needed, use the bundled inspector script instead of scraping printed text.

## Default vocoder handling

Each registry item may define `default_vocoder`.

- When `TTS.download_model_by_name` or `TTS.load_tts_model_by_name` loads a normal TTS checkpoint with a `default_vocoder`, it also downloads/loads that vocoder unless a caller supplies a different vocoder path/name through another interface.
- `tts_models/en/ljspeech/tacotron2-DDC` reports default vocoder `vocoder_models/en/ljspeech/hifigan_v2`.
- End-to-end or multi-file models such as VITS, XTTS, Bark, and Tortoise often have `default_vocoder: null`; they may include waveform generation internally or load from a model directory.
- Not every vocoder is compatible with every TTS model. Match sample rate, mel features, and normalization before overriding a default vocoder; route deep vocoder checks to [../vocoder-and-audio-tools/SKILL.md](../../vocoder-and-audio-tools/SKILL.md).

## License, TOS, network, and cache decisions

Registry records may include `license`, `contact`, `tos_required`, URLs, model hashes, and a default vocoder.

Operating policy for future agents:

1. Listing/filtering/querying the registry is safe.
2. Loading/downloading a released model is not automatically safe: it can use network, write model-cache files, validate hashes, redownload stale cache entries, and prompt for terms-of-service acceptance.
3. Do not answer interactive TOS prompts or set `COQUI_TOS_AGREED=1` unless the user explicitly accepts the model terms for the requested use.
4. If the task is only planning, prefer `python scripts/synthesize_text.py --dry-run ...` or the registry inspector.
5. If the task must synthesize with a released model, require an explicit user acknowledgement such as `--allow-download` in the bundled helper or equivalent conversation approval.

## Model-family naming cautions

| Family | Name pattern | Cautions |
| --- | --- | --- |
| Normal released TTS | `tts_models/<language>/<dataset>/<model>` | May have a default vocoder. Multi-speaker/multilingual models require `speaker`, `speaker_wav`, and/or `language` after load. |
| Vocoder | `vocoder_models/<language>/<dataset>/<model>` | Use for explicit pairing only after compatibility checks. Do not use a vocoder name where `TTS(model_name=...)` expects a TTS model. |
| Voice conversion | `voice_conversion_models/multilingual/vctk/freevc24` | Source/target conversion details belong in [../voice-conversion/SKILL.md](../../voice-conversion/SKILL.md). |
| XTTS | Registry full name `tts_models/multilingual/multi-dataset/xtts_v2`; shorthand forms such as `xtts` and versioned `xtts_v2.0.2` are accepted by model-manager loading logic | CPML/TOS gated; multi-file model directory; no default external vocoder; requires `language` and either `speaker_wav` or a supported built-in `speaker`. Docs and registry may differ on exact language count, so inspect `tts.languages` after load. |
| YourTTS | `tts_models/multilingual/multi-dataset/your_tts` | Multilingual voice cloning with `speaker_wav` and `language`; no default external vocoder in registry. |
| Fairseq MMS VITS | Dynamic `tts_models/<iso3_language_code>/fairseq/vits`, such as `tts_models/eng/fairseq/vits` or `tts_models/deu/fairseq/vits` | Not all Fairseq language names appear in the static registry list. Loading constructs a dynamic Fairseq download path and returns a model directory. Verify the language code before download. |
| Bark | `tts_models/multilingual/multi-dataset/bark` | Multi-file model, large download/runtime, no default external vocoder; can be slow on CPU. |
| Tortoise | `tts_models/en/multi-dataset/tortoise-v2` | Multi-file model, large download/runtime, no default external vocoder; `voice_dir` may matter for voice assets. |
| VITS/YourTTS-style end-to-end models | Commonly `.../vits` or `.../your_tts` | Often do not need an external vocoder because the architecture includes waveform generation. |

## Query examples and expected facts

For `tts_models/en/ljspeech/tacotron2-DDC`, registry metadata reports:

- type: `tts_models`
- language: `en`
- dataset: `ljspeech`
- model: `tacotron2-DDC`
- description: Tacotron2 with Double Decoder Consistency
- default vocoder: `vocoder_models/en/ljspeech/hifigan_v2`

For XTTS v2, registry metadata reports a CPML license, TOS requirement, no default vocoder, and a multi-file download. Treat it as a model-directory load and require explicit user approval for download/TOS.

## When a model name is not found

1. Check the slash count and prefix: `tts_models/...`, `vocoder_models/...`, or `voice_conversion_models/...`.
2. Run `python scripts/inspect_tts_models.py --contains <substring>`.
3. For Fairseq, verify the dynamic grammar `tts_models/<iso3_language_code>/fairseq/vits`; the static registry does not enumerate every Fairseq language.
4. For XTTS shorthand, prefer the full registry name for reproducibility unless the user explicitly asks for `xtts` latest or a versioned alias.
5. If the request is actually a CLI/server task, route to [../server-and-cli/SKILL.md](../../server-and-cli/SKILL.md).
