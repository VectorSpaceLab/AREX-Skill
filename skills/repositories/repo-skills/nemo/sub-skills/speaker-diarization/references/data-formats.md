# Speaker Data Formats

Use this reference for NeMo speaker recognition, diarization, VAD, ASR+diarization, and forced-alignment manifests and outputs. It distills repository evidence from speaker docs, speaker example configs, `scripts/speaker_tasks/pathfiles_to_diarize_manifest.py`, `scripts/speaker_tasks/filelist_to_manifest.py`, `nemo/collections/asr/parts/utils/manifest_utils.py`, `nemo/collections/asr/parts/utils/speaker_utils.py`, diarization metric tests, and forced-aligner tests.

## JSONL Manifest Rules

NeMo speaker workflows use line-delimited JSON. Each non-empty line must be a JSON object. Paths may be absolute or relative to the process working directory, but generated public skill instructions should show placeholders and never hard-code local checkout paths.

Common fields:

| Field | Required For | Meaning |
| --- | --- | --- |
| `audio_filepath` | all speaker workflows | Path to audio file. It is mandatory for diarization, recognition, VAD, and forced alignment. |
| `offset` | diarization/recognition/VAD segments | Segment start in seconds. Use `0` for whole-file examples. |
| `duration` | diarization/recognition/VAD segments | Segment duration in seconds; `null` means the whole file or unknown duration for many inference paths. |
| `text` | forced alignment unless `align_using_pred_text=True`; ASR+diarization reference text optional | Transcript/reference text. Use `"-"` for diarization manifests that do not need transcript text. |
| `label` | speaker recognition/classification | Speaker/class label for training or enrollment; commonly `"infer"` for inference. |
| `speaker` | some generated/transcript data | Speaker ID for word/segment objects, not the main recognition training label field. |
| `rttm_filepath` | diarization evaluation, oracle VAD | Path to reference RTTM file. |
| `uem_filepath` | diarization scoring region restriction | Path to UEM file for scored regions. |
| `ctm_filepath` | ASR+diarization WER/cpWER | Path to reference CTM file with speaker IDs. |
| `num_speakers` | oracle speaker count | Speaker count for `diarizer.clustering.parameters.oracle_num_speakers=True` or Sortformer/eval metadata. |
| `uniq_id` | long recordings or repeated audio paths | Explicit unique ID when multiple manifest lines share the same audio file. |

Validation command:

```bash
python scripts/check_speaker_manifest.py manifest.json --task diarization-eval --require-rttm --check-rttm-speakers
```

## Diarization Inference Manifest

Minimal pure inference line:

```json
{"audio_filepath":"audio/session01.wav","offset":0,"duration":null,"label":"infer","text":"-"}
```

Evaluation/oracle line:

```json
{"audio_filepath":"audio/session01.wav","offset":0,"duration":null,"label":"infer","text":"-","num_speakers":2,"rttm_filepath":"rttm/session01.rttm","uem_filepath":"uem/session01.uem"}
```

Rules:

- `audio_filepath` is mandatory. Most speaker docs/examples include `offset`, `duration`, `label`, and `text` as standard fields even when some are optional at runtime.
- Set `rttm_filepath` when evaluating DER or using `diarizer.oracle_vad=True`.
- Set `num_speakers` only when known; turn on `diarizer.clustering.parameters.oracle_num_speakers=True` to use it in clustering.
- If you provide RTTM/UEM/CTM path lists to a manifest-generation helper, keep basenames unique and aligned across audio/RTTM/text/CTM/UEM files.
- When `duration` is known, scoring utilities can clamp evaluation to `[offset, offset + duration]` so predictions past the segment end do not pollute scoring.

## Sortformer Training Manifest

Sortformer training and validation use audio plus RTTM labels:

```json
{"audio_filepath":"audio/session01.wav","offset":390.83,"duration":90.0,"text":"-","num_speakers":2,"rttm_filepath":"rttm/session01.rttm","uniq_id":"session01#000#390.83#90.0"}
```

Rules:

- Use one JSON line per training/eval segment.
- `rttm_filepath` must point to ground-truth speaker timestamps.
- `offset` and `duration` define the audio window. The dataloader reads only that segment and windows RTTM labels to the same range.
- Reuse the same long audio and RTTM file across many windows when needed, but add a unique `uniq_id` for every window.
- `num_speakers` is optional in some paths because the dataloader can infer speaker count from RTTM labels within the segment, but including it makes validation and debugging clearer.
- Training data should cover all speaker counts needed at inference time. A model trained only on 1-2 speakers should not be expected to generalize to 4-speaker sessions.

## Speaker Recognition Manifest

Training/enrollment line:

```json
{"audio_filepath":"audio/spk01_utt01.wav","offset":0,"duration":3.6,"label":"speaker_01"}
```

Inference/test line:

```json
{"audio_filepath":"audio/unknown_utt01.wav","offset":0,"duration":null,"label":"infer"}
```

Rules:

- `label` is the class/speaker ID for training and enrollment.
- `labels: null` in recognition configs lets NeMo infer labels from the manifest.
- Enrollment and test manifests for speaker identification should have the same sample rate expected by the model, commonly 16 kHz in example configs.
- When running `batch_inference()`, outputs preserve manifest order: embeddings, logits, ground-truth labels, and trained labels.
- For verification trial files, make sure embedding keys match the naming convention used by the embedding extraction workflow. The source extraction script derives keys from the last path components, so mismatched manifests/trials are a common failure source.

## Forced Alignment Manifest

Reference-text alignment line:

```json
{"audio_filepath":"audio/session01.wav","text":"hello world this is the reference transcript"}
```

Predicted-text alignment line:

```json
{"audio_filepath":"audio/session01.wav"}
```

Rules:

- `audio_filepath` is always mandatory.
- If `align_using_pred_text=False`, every manifest line must contain `text`.
- If `align_using_pred_text=True`, `text` is not required because the ASR model generates `pred_text`; do not pre-populate `pred_text` in the input manifest for that mode.
- `model_path` and `pretrained_name` are mutually exclusive in the aligner config; one must be set.
- `output_dir` must be set, and the aligner writes a new manifest with output file path fields.
- `additional_segment_grouping_separator` controls segment splitting. Empty string or plain space are invalid separators in the source aligner.
- `audio_filepath_parts_in_utt_id` chooses how many trailing path components are used to form output utterance IDs. Choose a value that avoids collisions when two files share a basename.

## RTTM Format

RTTM line shape:

```text
SPEAKER <recording-id> 1 <start> <duration> <NA> <NA> <speaker-id> <NA> <NA>
```

Example:

```text
SPEAKER session01 1 0.120 1.430 <NA> <NA> speaker_0 <NA> <NA>
SPEAKER session01 1 1.100 0.800 <NA> <NA> speaker_1 <NA> <NA>
```

Rules:

- Start and duration are seconds and must be non-negative; duration must be positive for meaningful scoring.
- Overlap is represented by multiple speaker lines whose time intervals intersect.
- Speaker IDs should be stable within a file. Common NeMo examples use `speaker_0`, `speaker_1`, etc.
- The RTTM recording ID should align with the unique ID derived from `audio_filepath` or explicitly supplied `uniq_id`; basename mismatches can cause missing labels or missing scores.
- Use `rttm_filepath` in the manifest for DER evaluation and `oracle_vad=True` workflows.

## UEM Format

UEM restricts scoring regions. Typical line shape:

```text
<recording-id> 1 <start> <end>
```

Rules:

- Use UEM when only a subset of a recording should be scored.
- If no UEM is provided but manifest `offset` and `duration` are present, NeMo scoring utilities can create a scoring region from the manifest segment window.
- Keep UEM recording IDs aligned with RTTM and manifest IDs.

## CTM Format

CTM line shape used by NeMo utilities:

```text
<source> <channel> <start-time> <duration> <token> <confidence> <token-type> <speaker>
```

Example:

```text
session01 1 0.12 0.43 hello NA lex speaker_0
session01 1 0.60 0.28 world NA lex speaker_1
```

Rules:

- `token-type` for words is usually `lex`.
- `confidence` may be `NA` when no confidence is computed.
- `speaker` should exactly match speaker IDs in RTTM for ASR+diarization evaluation.
- `ctm_filepath` in the manifest enables reference transcript comparison for WER/cpWER workflows.
- CTM can be produced by forced alignment at token, word, and segment levels; downstream scoring usually expects word-level CTM.

## ASS Output Concepts

ASS files are subtitle-style outputs generated by forced alignment. The aligner can produce word-level and token-level ASS files with configurable text colors, font size, vertical alignment, and optional text resegmentation to fit screen space.

Rules:

- Use ASS for human-readable timing review, not for DER/cpWER scoring.
- `ass_file_config.vertical_alignment` must be `top`, `center`, or `bottom`.
- RGB color configs must contain exactly three integers.
- Empty or extremely dense text can make ASS generation difficult; consider predicted-text alignment or segment separators when reference text is missing or poorly segmented.

## Output Path Sanity

Common output file fields and directories:

- diarization: predicted RTTMs often live under an output `pred_rttms/` directory keyed by unique ID;
- ASR+diarization: transcript, CSV, CTM, Audacity, and Gecko-style outputs may be generated under the configured output root;
- forced alignment: outputs include `ctm/tokens/`, `ctm/words/`, `ctm/segments/`, `ass/tokens/`, `ass/words/`, plus a manifest with saved output file path fields.

Use `check_speaker_manifest.py` to catch ambiguous extension/path issues before running heavy workflows:

```bash
python scripts/check_speaker_manifest.py align_manifest.json \
  --task forced-alignment \
  --require-existing-files \
  --allowed-audio-ext .wav .flac .ogg .mp3
```

## Common Data Mistakes

- Missing `text` in forced alignment while `align_using_pred_text=False`.
- Providing both `model_path` and `pretrained_name` in forced alignment.
- `rttm_filepath` paths present but basenames do not match `audio_filepath` basenames.
- RTTM speaker IDs differ from CTM speaker IDs, making cpWER/speaker-attributed scoring misleading.
- `duration` is negative, zero for a non-empty segment, or a string that cannot parse as a number.
- `offset` is negative or missing when segment windows are expected.
- `num_speakers` does not match speakers actually present in RTTM.
- Multiscale diarization lists have mismatched lengths for `window_length_in_sec`, `shift_length_in_sec`, and `multiscale_weights`.
- `label` is omitted in speaker recognition training/enrollment manifests.
- Multiple long-audio windows share the same audio path without a unique `uniq_id`, causing collisions in outputs or metrics.
