# Forced Alignment

Use this reference when the task involves NeMo Forced Aligner (NFA), word/token/segment timestamps, CTM files, ASS subtitle files, or start/end-of-utterance timing. It distills evidence from `tools/nemo_forced_aligner/README.md`, `tools/nemo_forced_aligner/align.py`, `tools/nemo_forced_aligner/align_eou.py`, `tools/nemo_forced_aligner/utils/*.py`, and `tools/nemo_forced_aligner/tests/**`.

## What NFA Does

NeMo Forced Aligner uses CTC ASR models to align speech audio with text. It can:

- align audio to provided reference text;
- transcribe audio first and align to predicted text with `align_using_pred_text=True`;
- emit CTM files at token, word, and segment levels;
- emit ASS subtitle files at token and word levels;
- write an output manifest containing paths to generated files;
- produce start/end-of-utterance timing variants through the EOU aligner.

NFA is ASR-based. General ASR model selection and decoding details belong in `../asr/SKILL.md`; this reference focuses on alignment-specific inputs, outputs, and failure modes.

## Minimal Alignment Inputs

Reference-text alignment manifest:

```json
{"audio_filepath":"audio/utt001.wav","text":"this is the transcript to align"}
```

Predicted-text alignment manifest:

```json
{"audio_filepath":"audio/utt001.wav"}
```

Config/CLI shape:

```bash
python align.py \
  pretrained_name=stt_en_fastconformer_hybrid_large_pc \
  manifest_filepath=align_manifest.json \
  output_dir=align_output
```

Use `model_path=/path/to/model.nemo` instead of `pretrained_name=...` for local checkpoint runs. Do not set both.

Before running:

```bash
python scripts/check_speaker_manifest.py align_manifest.json --task forced-alignment
```

If using predicted text:

```bash
python scripts/check_speaker_manifest.py align_manifest.json --task forced-alignment --align-using-pred-text
```

## Important Config Fields

- `pretrained_name`: CTC ASR pretrained model name. It may download model assets.
- `model_path`: local `.nemo` CTC ASR checkpoint. Overrides `pretrained_name` in intent, but the source aligner rejects having both set.
- `manifest_filepath`: JSONL manifest with `audio_filepath` and, unless `align_using_pred_text=True`, `text`.
- `output_dir`: destination for CTM, ASS, and output manifest files.
- `align_using_pred_text`: transcribe audio first, then align using generated text. Use when reference text is unavailable.
- `batch_size`: number of utterances per ASR/alignment batch. Reduce for memory pressure.
- `use_local_attention`: changes Conformer attention to local attention in compatible models for long audio.
- `additional_segment_grouping_separator`: string/list of separators used to split text into smaller segments. Common defaults include `.`, `?`, `!`, and `...`.
- `audio_filepath_parts_in_utt_id`: number of trailing audio path components used to build output utterance IDs.
- `save_output_file_formats`: usually includes `ctm` and/or `ass`.
- `ctm_file_config.remove_blank_tokens`: remove `<blank>` tokens from token-level CTM outputs.
- `ctm_file_config.minimum_timestamp_duration`: enforce a minimum token/word/segment timestamp duration; must be non-negative.
- `ass_file_config.vertical_alignment`: `top`, `center`, or `bottom`.
- `ass_file_config.resegment_text_to_fill_space`: resegment text to fit subtitle display constraints.

## Output Files

NFA writes a manifest named from the input manifest stem with output file path fields. It can also create these subdirectories under `output_dir`:

- `ctm/tokens/`: token-level CTM files;
- `ctm/words/`: word-level CTM files;
- `ctm/segments/`: segment-level CTM files;
- `ass/tokens/`: token-level ASS subtitle files;
- `ass/words/`: word-level ASS subtitle files.

CTM line shape:

```text
<source> <channel> <start-time> <duration> <token> <confidence> <token-type> <speaker>
```

ASS files are human-readable subtitles. Use CTM, not ASS, for downstream word-timestamp evaluation.

## Missing Text Decision Tree

When a forced-alignment manifest lacks `text`:

1. If the user has reference transcripts, add `text` to every manifest line and keep `align_using_pred_text=False`.
2. If no reliable reference exists, set `align_using_pred_text=True` and use a CTC ASR model suitable for the language/domain.
3. If some lines have text and some do not, split the manifest into reference-text and predicted-text batches. The aligner expects the mode to be consistent.
4. Do not add empty `text` only to satisfy validation. Empty text can produce empty or unusable CTM/ASS outputs.
5. Do not pre-fill `pred_text` in the input when using `align_using_pred_text=True`; the source aligner rejects that ambiguity.

This directly supports the hard case: a forced-alignment manifest with missing `text` and ambiguous CTM/ASS paths. Validate with `--task forced-alignment`; then decide whether to add reference text or use predicted text. Pick an explicit `output_dir` and check whether the downstream consumer needs `ctm/words`, `ctm/tokens`, `ctm/segments`, `ass/words`, or `ass/tokens`.

## Utterance ID and Path Collisions

Output files are named from an utterance ID derived from trailing audio path components. If two audio files share the same basename, set `audio_filepath_parts_in_utt_id` high enough to disambiguate them.

Example:

- `meetings/a/session.wav` with `audio_filepath_parts_in_utt_id=1` -> `session`;
- `calls/b/session.wav` with `audio_filepath_parts_in_utt_id=1` -> also `session`, collision risk;
- set `audio_filepath_parts_in_utt_id=2` to produce `a_session` and `b_session`-style IDs.

Use `check_speaker_manifest.py --require-unique-audio-basename` when outputs are keyed by basename and collisions would be unsafe.

## Segment Separators

`additional_segment_grouping_separator` controls text grouping. Good separators reduce very long segment alignment and improve subtitle readability. Empty string and plain space are invalid. Starting with NeMo 2.5-era behavior in the source comments, separators are preserved in segment text after splitting, so downstream text comparisons should expect punctuation to remain.

Guidance:

- Use punctuation separators for normal transcripts.
- Use domain-specific separators for transcripts with tags or custom delimiters.
- Disable or simplify separators for text where punctuation is noisy or absent.
- If ASS lines are too dense, use shorter text segments or enable ASS resegmentation.

## EOU Alignment

`align_eou.py` follows the same broad alignment pattern but additionally writes start/end-of-utterance timing to a manifest. Use it when the task asks for utterance boundary timing, `sou_time`, `eou_time`, or conversation turn boundary preparation.

Rules:

- Inputs still require `audio_filepath` and text unless predicted-text alignment is selected.
- Provide `output_manifest_filepath` when the downstream workflow expects a specific manifest path; otherwise the source behavior places output next to the input manifest.
- Treat EOU output fields as utterance-level metadata, not diarization speaker labels.

## Integration with Speaker Workflows

- Forced-alignment CTM can be used as reference CTM for ASR+diarization WER/cpWER only when speaker fields are meaningful and match RTTM speaker IDs. NFA itself does not infer diarization speakers.
- If you need speaker-attributed words, combine ASR/forced-alignment word timestamps with diarization labels in an ASR+diarization workflow.
- If the user has reference transcripts and diarization RTTM, keep these as separate manifest fields: `text` for alignment, `rttm_filepath` for diarization scoring, and `ctm_filepath` for word-level transcript scoring.

## Safe Checks Before Running NFA

Run:

```bash
python scripts/check_speaker_manifest.py align_manifest.json \
  --task forced-alignment \
  --require-existing-files \
  --allowed-audio-ext .wav .flac .ogg .mp3
```

Also check:

- exactly one of `model_path` or `pretrained_name` is planned;
- `output_dir` is explicit and not a protected/source directory;
- no duplicate utterance IDs will overwrite CTM/ASS outputs;
- `save_output_file_formats` includes only what the downstream task needs;
- GPU memory is sufficient for the ASR model and batch size;
- local checkpoint language/vocabulary matches transcript language.

## Failure Patterns

- `NFA requires all lines to contain a text entry`: either add `text` everywhere or set `align_using_pred_text=True`.
- `Both cfg.model_path and cfg.pretrained_name cannot be None`: set one model source.
- `One of cfg.model_path and cfg.pretrained_name must be None`: remove one model source.
- Empty CTM/ASS files: text is empty, audio is silent, wrong language/model, or segmentation produced no alignable tokens.
- Missing output files: `save_output_file_formats` excluded that format or output utterance IDs collided.
- Invalid ASS config: `vertical_alignment` is not `top`, `center`, or `bottom`, or RGB lists are malformed.
- Poor timestamps: transcript differs from audio, wrong CTC model/language, audio sample rate/channel issues, batch too large causing truncation/OOM, or very long unsegmented text.
