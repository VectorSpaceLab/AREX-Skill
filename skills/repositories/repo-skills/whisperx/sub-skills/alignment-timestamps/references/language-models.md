# Language and alignment model reference

## Purpose

Read this before choosing a WhisperX alignment language, relying on an automatic default alignment model, configuring offline/cache-only alignment, or selecting a custom Hugging Face wav2vec2 model.

WhisperX can transcribe many languages, but forced alignment requires a language-specific CTC/wav2vec2 alignment model whose tokenizer can represent the transcript well enough for CTC alignment.

## Verified model-selection facts

- Installed package version inspected: `whisperx` 3.8.7rc1.
- Public language table contains 100 language codes for ASR/CLI language selection.
- Default torchaudio alignment models: 5 languages.
- Default Hugging Face alignment models: 36 languages.
- Languages without whitespace word splitting: `ja`, `zh`.
- Punkt sentence tokenizer map: 19 language codes, with English fallback for languages not in the map.

## Default torchaudio alignment models

These names are torchaudio pipeline identifiers. They are selected automatically when `model_name=None` and `language_code` matches the left column.

| Language code | Default torchaudio pipeline |
| --- | --- |
| `en` | `WAV2VEC2_ASR_BASE_960H` |
| `fr` | `VOXPOPULI_ASR_BASE_10K_FR` |
| `de` | `VOXPOPULI_ASR_BASE_10K_DE` |
| `es` | `VOXPOPULI_ASR_BASE_10K_ES` |
| `it` | `VOXPOPULI_ASR_BASE_10K_IT` |

Notes:

- You may pass another torchaudio pipeline name with `--align_model` or `model_name=...` if the installed torchaudio exposes it.
- `model_cache_only` is not the same guarantee for torchaudio pipelines as it is for Hugging Face models; torchaudio decides whether weights are already present under its cache/model directory.
- README guidance notes that a larger alignment model is not always more helpful than selecting the right language-specific model and transcription quality.

## Default Hugging Face alignment models

These Hugging Face model ids are selected automatically when `model_name=None` and `language_code` matches the left column.

| Language code | Default Hugging Face model id |
| --- | --- |
| `ar` | `jonatasgrosman/wav2vec2-large-xlsr-53-arabic` |
| `ca` | `softcatala/wav2vec2-large-xlsr-catala` |
| `cs` | `comodoro/wav2vec2-xls-r-300m-cs-250` |
| `da` | `saattrupdan/wav2vec2-xls-r-300m-ftspeech` |
| `el` | `jonatasgrosman/wav2vec2-large-xlsr-53-greek` |
| `eu` | `stefan-it/wav2vec2-large-xlsr-53-basque` |
| `fa` | `jonatasgrosman/wav2vec2-large-xlsr-53-persian` |
| `fi` | `jonatasgrosman/wav2vec2-large-xlsr-53-finnish` |
| `gl` | `ifrz/wav2vec2-large-xlsr-galician` |
| `he` | `imvladikon/wav2vec2-xls-r-300m-hebrew` |
| `hi` | `theainerd/Wav2Vec2-large-xlsr-hindi` |
| `hr` | `classla/wav2vec2-xls-r-parlaspeech-hr` |
| `hu` | `jonatasgrosman/wav2vec2-large-xlsr-53-hungarian` |
| `id` | `cahya/wav2vec2-large-xlsr-indonesian` |
| `ja` | `jonatasgrosman/wav2vec2-large-xlsr-53-japanese` |
| `ka` | `xsway/wav2vec2-large-xlsr-georgian` |
| `ko` | `kresnik/wav2vec2-large-xlsr-korean` |
| `lv` | `jimregan/wav2vec2-large-xlsr-latvian-cv` |
| `ml` | `gvs/wav2vec2-large-xlsr-malayalam` |
| `nl` | `jonatasgrosman/wav2vec2-large-xlsr-53-dutch` |
| `nn` | `NbAiLab/nb-wav2vec2-1b-nynorsk` |
| `no` | `NbAiLab/nb-wav2vec2-1b-bokmaal-v2` |
| `pl` | `jonatasgrosman/wav2vec2-large-xlsr-53-polish` |
| `pt` | `jonatasgrosman/wav2vec2-large-xlsr-53-portuguese` |
| `ro` | `gigant/romanian-wav2vec2` |
| `ru` | `jonatasgrosman/wav2vec2-large-xlsr-53-russian` |
| `sk` | `comodoro/wav2vec2-xls-r-300m-sk-cv8` |
| `sl` | `anton-l/wav2vec2-large-xlsr-53-slovenian` |
| `sv` | `KBLab/wav2vec2-large-voxrex-swedish` |
| `te` | `anuragshas/wav2vec2-large-xlsr-53-telugu` |
| `tl` | `Khalsuu/filipino-wav2vec2-l-xls-r-300m-official` |
| `tr` | `mpoyraz/wav2vec2-xls-r-300m-cv7-turkish` |
| `uk` | `Yehor/wav2vec2-xls-r-300m-uk-with-small-lm` |
| `ur` | `kingabzpro/wav2vec2-large-xls-r-300m-Urdu` |
| `vi` | `nguyenvulebinh/wav2vec2-base-vi-vlsp2020` |
| `zh` | `jonatasgrosman/wav2vec2-large-xlsr-53-chinese-zh-cn` |

## Languages without spaces

`ja` and `zh` are handled specially:

- The aligner does not split on spaces for these languages.
- Each character is effectively grouped as its own word-like unit during alignment.
- Subtitle writers also join words without inserting spaces for these languages.
- Do not expect English-style word segmentation from the alignment result unless an upstream tokenizer has already inserted suitable boundaries and the output workflow preserves them.

## Punkt sentence splitting

Alignment splits each ASR segment into sentence spans before producing aligned subsegments. The language-specific Punkt map is:

| Code | Punkt model |
| --- | --- |
| `cs` | `czech` |
| `da` | `danish` |
| `de` | `german` |
| `el` | `greek` |
| `en` | `english` |
| `es` | `spanish` |
| `et` | `estonian` |
| `fi` | `finnish` |
| `fr` | `french` |
| `it` | `italian` |
| `ml` | `malayalam` |
| `nl` | `dutch` |
| `no` | `norwegian` |
| `pl` | `polish` |
| `pt` | `portuguese` |
| `ru` | `russian` |
| `sl` | `slovene` |
| `sv` | `swedish` |
| `tr` | `turkish` |

If a code is not listed, WhisperX falls back to English Punkt for sentence splitting. Missing `punkt_tab` data can trigger an attempted download; see troubleshooting for offline-safe handling.

## Choosing a language and model

### Automatic path

Use this when the detected or user-specified language is in the default tables:

```python
model_a, metadata = whisperx.load_align_model(
    language_code=result["language"],
    device=device,
)
```

CLI equivalent:

```bash
whisperx audio.wav --language de --model large-v2
```

For non-English ASR, docs recommend a large Whisper ASR model when quality matters because forced alignment can only align the transcript it receives.

### Custom Hugging Face wav2vec2 model path

Use this when there is no default model, a default model performs poorly, or a task requires a specific domain/language model:

```python
model_a, metadata = whisperx.load_align_model(
    language_code="xx",
    device=device,
    model_name="organization/wav2vec2-ctc-model-id",
    model_cache_only=False,
)
```

CLI equivalent:

```bash
whisperx audio.wav --language xx --align_model organization/wav2vec2-ctc-model-id
```

Checklist for custom models:

1. Prefer a wav2vec2-style CTC ASR model fine-tuned for the target language.
2. Confirm its tokenizer vocabulary includes the relevant script or can tolerate unknown digits/symbols via wildcard alignment.
3. Test on representative audio and manually inspect word timestamps before using it as ground truth.
4. For offline work, pre-populate the model cache and set cache-only behavior only after proving both processor and model weights are present.
5. Keep the `language_code` aligned with the transcript language so sentence splitting and no-space behavior match the text.

## Language mismatch hazards

- English-only ASR model names ending in `.en` force English language handling in the CLI path.
- `task="translate"` disables alignment in the CLI path because translated text does not match the original spoken language.
- When automatic language detection changes between files, the CLI orchestration can reload a new alignment model for the new result language.
- A language may be valid for transcription but still lack a default alignment model. In that case, pass a custom `--align_model`/`model_name` or skip alignment for that language.
