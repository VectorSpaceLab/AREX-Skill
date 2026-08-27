# Data Formats

This reference covers shared NeMo Speech data schemas distilled from `docs/source/dataloaders.rst`, `docs/source/common/data.rst`, `tools/speech_data_explorer/README.md`, `nemo/collections/common/data/lhotse/nemo_adapters.py`, Lhotse tests under `tests/collections/common/test_lhotse_*`, tokenizer scripts, and customization dataset preparation code/tests.

## NeMo JSONL Manifests

NeMo speech utilities commonly use JSON Lines: one JSON object per utterance or sample.

Core ASR-style fields:

| Field | Required for most audio-text tasks | Notes |
| --- | --- | --- |
| `audio_filepath` | Yes | Local path, datastore URI, filename inside a tar archive, or path relative to the manifest location depending on the workflow. |
| `duration` | Yes for training, Lhotse, SDE, and filtering | Seconds as a positive number. Missing or zero duration breaks duration weighting and bucketing. |
| `text` | Usually yes | Reference transcript; use `text_field` override if a workflow uses another key such as `normalized_text`. |
| `offset` | Optional | Segment start in seconds for sliced audio. NeMo's Lhotse adapter turns it into a partial cut. |
| `lang` | Optional | Language tag; override with `lang_field` when another key holds language. |
| `sampling_rate` or `sample_rate` | Optional but useful | Avoids audio header probing for some metadata-only operations. |
| `_skipme` | Optional | Truthy values make Lhotse skip the entry; useful for filtered tarred subsets without retarring. |
| `pred_text` or `pred_text_*` | Optional | ASR prediction fields for Speech Data Explorer or evaluator-style analysis. |
| `shard_id` | Required for NeMo tarred manifests | Integer shard identifier matching the tar shard that contains `audio_filepath`. |

Validation checklist before long jobs:

1. Confirm the file is JSONL, not a single JSON array unless the consuming tool explicitly accepts JSON.
2. Confirm every line parses and required keys are present for the workflow.
3. Confirm `duration` is numeric and within expected bounds.
4. Confirm `audio_filepath` semantics match the workflow: local paths for non-tarred data, tar member names for tarred data, remote URIs only for tools that support them.
5. Confirm transcript key naming is consistent; mixed `text`, `normalized_text`, `pred_text`, and `answer` fields require explicit `text_field` or tool-specific overrides.
6. Confirm duplicate `audio_filepath` values are intentional when using offsets; otherwise duplicates often indicate accidental repeated data.
7. Confirm tarred manifests include `shard_id` and that sharded manifest patterns align with tar patterns.
8. For weighted blends, confirm every leaf dataset has a positive `weight` or is processed through a weight estimation step.

Bundled safe check:

```bash
python scripts/validate_manifest.py train.jsonl \
  --required audio_filepath duration text \
  --min-duration 0.1 --max-duration 30 --summary
```

Use `--text-keys text normalized_text pred_text` to summarize mixed transcript conventions, and `--check-files` only for local non-tarred manifests where file existence checks are cheap and meaningful.

## Lhotse CutSet and NeMo Adapter Semantics

NeMo can read regular NeMo manifests, tarred NeMo manifests, Lhotse CutSet manifests, and Lhotse Shar directories through Lhotse dataloading.

Important NeMo adapter behavior:

- `manifest_filepath` reads NeMo JSONL manifests when `cuts_path` and `shar_path` are absent.
- `cuts_path` reads a Lhotse CutSet manifest such as `cuts.jsonl.gz`.
- `shar_path` reads Lhotse Shar data; it may be a string, weighted list, or mapping of Shar fields with a `cuts` key.
- `text_field` defaults to `text`; `lang_field` defaults to `lang`.
- `metadata_only=true` allows metadata iteration without opening audio for non-tarred NeMo manifests, but it does not prove the audio is loadable.
- `force_finite=true` forces a finite CutSet; avoid it for normal multi-GPU training unless the model workflow explicitly requires finite iteration.
- `_skipme` truthy entries are skipped by NeMo Lhotse adapters.
- `offset` creates partial cuts; duplicate audio paths are valid when offsets differ.

Lhotse tests verify standard NeMo manifests, multichannel manifests, offset manifests, tarred manifests, tarred subsets, `_skipme`, sharded manifest patterns, CutSet/Shar inputs, and temperature reweighting. Treat those behaviors as stable contracts when planning data.

## `input_cfg` Dataset Blends

Use `input_cfg` when a run combines multiple datasets, tasks, languages, modalities, or tarred sources.

Flat weighted blend:

```yaml
input_cfg:
  - type: nemo_tarred
    manifest_filepath: data/asr_en/manifest__OP_0..127_CL_.json
    tarred_audio_filepath: data/asr_en/audio__OP_0..127_CL_.tar
    weight: 0.6
    tags:
      task: asr
      source_lang: en
  - type: nemo_tarred
    manifest_filepath: data/asr_pl/manifest__OP_0..63_CL_.json
    tarred_audio_filepath: data/asr_pl/audio__OP_0..63_CL_.tar
    weight: 0.4
    tags:
      task: asr
      source_lang: pl
```

Nested group blend:

```yaml
input_cfg:
  - type: group
    weight: 0.7
    tags:
      task: asr
    input_cfg:
      - type: nemo_tarred
        manifest_filepath: data/asr_clean/manifest__OP_0..31_CL_.json
        tarred_audio_filepath: data/asr_clean/audio__OP_0..31_CL_.tar
        weight: 0.8
      - type: nemo_tarred
        manifest_filepath: data/asr_noisy/manifest__OP_0..31_CL_.json
        tarred_audio_filepath: data/asr_noisy/audio__OP_0..31_CL_.tar
        weight: 0.2
  - type: group
    weight: 0.3
    tags:
      task: ast
    input_cfg:
      - type: nemo
        manifest_filepath: data/ast_manifest.jsonl
        weight: 1.0
        tags:
          source_lang: en
          target_lang: de
```

Rules for blends:

- Use positive weights only; zero or negative weights fail temperature reweighting.
- Group weights multiply with child weights.
- `tags` are attached to sampled examples and are useful for prompt formatting, task routing, language-aware tokenizers, and analysis.
- `reweight_temperature=1.0` preserves ratios; lower values oversample smaller datasets; `0.0` equalizes same-level sources.
- If `reweight_temperature` is a list, its length must match the `input_cfg` nesting depth. A scalar broadcasts to all levels.
- Do not mix tarred and non-tarred sources in a single sampler unless the model/datamodule explicitly supports the resulting sampler flavor.

## Multimodal and Text Inputs

NeMo's Lhotse dataloading can also read text-only and mixed text/audio sources.

Common parser types:

| Type | Shape | Use |
| --- | --- | --- |
| `txt` | Raw text files with one example per line | Language-modeling or text-only batches. |
| `txt_pair` | Aligned source/target text files | Translation-style tasks. |
| `multimodal_conversation` | JSONL conversations with text and audio turns | Speech LLM conversation tasks. |
| `nemo` | NeMo JSONL audio manifest | Non-tarred speech data. |
| `nemo_tarred` | NeMo manifest plus tar files | Large sharded speech data. |
| `lhotse` | Lhotse CutSet manifest | Lhotse-native audio data. |
| `lhotse_shar` | Lhotse Shar directory or fields | Modular tarred Lhotse data. |

Text and multimodal sampling knobs:

- `use_multimodal_sampling: true` switches length measurement from audio duration to token counts.
- `prompt_format` applies a NeMo prompt formatter before sampling length estimation.
- `measure_total_length: true` is typical for decoder-only total context+answer length; use `false` for encoder-decoder workflows that track source and target separately.
- `min_tokens` and `max_tokens` filter token counts.
- `min_tpt` and `max_tpt` filter target-token-per-source-token ratio for text.
- `token_equivalent_duration` maps audio duration to token-like units in multimodal conversations.
- Shard text files for multi-GPU training to avoid worker/rank duplication.

## Tokenizer Preparation Inputs

The ASR tokenizer script accepts either:

- `--manifest` with comma-separated JSONL manifests containing `text`, or
- `--data_file` with one text example per line.

Planning checklist:

1. Normalize transcript field names before building the corpus.
2. Decide whether lowercasing is desired; the tokenizer script lowercases by default unless `--no_lower_case` is used.
3. Choose `--tokenizer spe` for SentencePiece or `--tokenizer wpe` for HuggingFace wordpiece.
4. Set `--vocab_size` based on language and model needs.
5. For SentencePiece, choose `--spe_type`, `--spe_character_coverage`, special symbol options, digit splitting, byte fallback, and sampling for large corpora.
6. Keep tokenizer output directories separate from raw data and model checkpoints.

## ASR Evaluator Inputs

ASR evaluator workflows use a Hydra YAML config with engine and analyst sections. Manifest data should include `audio_filepath`, `duration`, and `text`; additional metadata fields can be analyzed by class or interval when configured. Noise augmentation references require separate noise manifests.

Use ASR evaluator for robust evaluation planning and detailed error analysis, not as a cheap manifest validator. It performs inference and may need GPU/model dependencies.

## Speech Data Explorer Inputs

Speech Data Explorer requires `audio_filepath`, `duration`, and `text` unless run with its force mode. It can display extra fields, compute error analysis from `pred_text`, compare two prediction fields or two manifests, and read tarred data when a tar base path and optional DALI indexes are supplied.

Treat it as an interactive Dash app: validate manifests first, choose a safe port, and avoid using it in headless automation unless the environment supports web services.

## Customization Dataset JSONL

The customization dataset preparation utility targets JSONL rows with exactly two fields:

```jsonl
{"prompt": "Question: ... Answer:", "completion": "...\n"}
```

It can convert JSONL/JSON/CSV/TSV/XLSX columns with `--prompt_template` and `--completion_template`, optionally drop duplicate prompt+completion rows, and split train/validation. Tests show it warns about empty completions, imbalanced completions, missing prompt/completion suffixes, duplicate rows, low sample counts, long samples, and invalid template braces.

Template rules:

- Fields use single braces such as `{context}` and `{answer}`.
- `{{field}}`, missing braces, or nested braces are invalid.
- Add explicit suffixes such as newlines or `Answer:` when the training recipe expects them.
- For classification-like datasets, inspect completion imbalance before training.
