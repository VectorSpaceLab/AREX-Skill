# Alignment troubleshooting

## Purpose

Use this when WhisperX alignment fails, word timestamps are missing, language/model selection is unclear, or a downstream output workflow reports missing word or character timing.

## Quick triage

1. Confirm the task is same-language transcription, not translation. CLI translation disables alignment.
2. Confirm ASR produced non-empty `segments` with plausible `start`, `end`, and `text` fields.
3. Confirm the selected `language_code` has a default alignment model or an explicit custom `align_model`/`model_name`.
4. Run the safe bundled checker to verify the installed aligner still handles wildcard numeric/comma timestamps synthetically:
   ```bash
   python scripts/check_alignment_contract.py
   ```
5. Inspect `aligned["word_segments"]` for the specific words needed downstream; segment-level timestamps alone are not enough.

## Failure surfaces

| Symptom or error fragment | Likely cause | Recovery steps |
| --- | --- | --- |
| `No default alignment model for language: <code>` or `No default align-model for language` | The language is valid for ASR but missing from WhisperX default torchaudio/Hugging Face alignment maps. | Pass a custom wav2vec2 CTC model with `--align_model` or `model_name=...`; verify the tokenizer covers the language/script; test on representative audio. If no suitable model exists, skip alignment and route file rendering to segment-level outputs. |
| `The chosen align_model ... could not be found in huggingface ... or torchaudio` | Model name is misspelled, unavailable to the current install, gated/private, or not cached when cache-only mode is requested. | Check whether the name is a torchaudio pipeline identifier or a Hugging Face model id. For Hugging Face cache-only runs, pre-populate both processor/tokenizer and model weights before setting cache-only. For gated/private models, obtain proper access outside the skill helper. |
| Network/cache failure while loading a Hugging Face alignment model | `model_cache_only=True` with missing local files, offline runtime, blocked network, or model access restrictions. | Retry with cache-only disabled only if downloads are allowed. Otherwise use a pre-populated model cache or choose a model already available in the runtime. Do not bake local cache paths into reusable code. |
| Torchaudio model unexpectedly tries to fetch weights | Torchaudio pipeline loading uses its own cache/model directory behavior; WhisperX's cache-only flag does not provide the same local-only guarantee in that branch. | Use a known cached torchaudio pipeline, set a controlled model directory if appropriate, or choose a Hugging Face model with `local_files_only` behavior when strict offline operation is required. |
| `Failed to download NLTK 'punkt_tab' data` or missing `tokenizers/punkt_tab/<language>.pickle` | Sentence splitting requires NLTK `punkt_tab`; automatic download failed or network is unavailable. | Install `punkt_tab` before alignment in the runtime environment, for example with `python -m nltk.downloader punkt_tab` when downloads are allowed. For offline systems, provision NLTK data through the environment image/cache and ensure NLTK can discover it. |
| Words with digits, commas, currency, or symbols lack `start`/`end` | The wildcard CTC path did not produce a usable path, interpolation was set to `ignore`, or the real model emissions did not support those characters well. | Run `scripts/check_alignment_contract.py` to separate package-contract failure from real-model quality. Try `interpolate_method="nearest"` or `"linear"` if interpolated timestamps are acceptable. Consider ASR numeral suppression or spelling numbers in ASR prompts only when that belongs to the ASR workflow. |
| `word_segments` is empty | ASR produced no speech segments, each segment had no usable characters, segment starts were beyond audio duration, or CTC backtracking failed. | First verify ASR/VAD/audio in the ASR sub-skill. For Python alignment, pass a list of segments with non-empty text. Check that audio length covers every segment's `end`. |
| Warning that original start time is longer than audio duration | A segment `start` time is greater than or equal to the loaded audio duration. | Validate audio sample rate/duration and segment timestamps before alignment. Do not trim or resample audio after ASR unless segment times are updated consistently. |
| Segment text exists but aligned segment has empty `words` | No characters in the text were usable for the model dictionary, or alignment fell back after failure. | Check language/model mismatch, unsupported script, and whether text is mostly whitespace/symbols. Use a custom model with a suitable tokenizer or treat the segment as unaligned. |
| `return_char_alignments=True` but `chars` is missing/empty or lacks timing on some entries | Char alignments are only produced when alignment succeeds and the caller requested them. Missing character timing can be omitted from individual char dictionaries. | Request JSON-style results with `return_char_alignments=True`; assert only the characters/timing fields required by the downstream task; do not expect subtitle writers to preserve char-level timing. |
| Japanese or Chinese result has one-character word units | WhisperX marks `ja` and `zh` as languages without spaces, so alignment grouping increments by character rather than splitting on spaces. | Treat `word_segments` as character-level units unless an upstream tokenizer creates explicit word-like boundaries. For output formatting, avoid inserting spaces for these languages. |
| Word-highlighting or line-width options fail with `--no_align` | Word-based subtitle options require alignment. | Remove `--no_align` or disable word highlighting / word-based line options. Detailed output rendering belongs to `outputs-subtitles`. |
| Alignment skipped during CLI translation | CLI sets `no_align=True` when `--task translate` is used. | Use same-language `--task transcribe` when word timestamps are required. Translation output cannot be directly forced-aligned to source-language audio. |

## Custom Hugging Face model selection checklist

Use this when the difficult case is a language without a default align model:

1. Identify a wav2vec2 CTC model trained or fine-tuned for the target language.
2. Pass it explicitly:
   ```python
   model_a, metadata = whisperx.load_align_model(
       language_code="xx",
       device=device,
       model_name="organization/model-id",
       model_cache_only=False,
   )
   ```
3. Confirm `metadata["type"] == "huggingface"` and inspect whether important transcript characters appear in `metadata["dictionary"]`.
4. For cache-only operation, prove the model and processor load once before setting `model_cache_only=True`.
5. Align a short representative transcript and assert required `word_segments` timestamps before scaling up.

## Numeric comma timestamp recovery

For German-style decimal text such as `4,9`:

```bash
python scripts/check_alignment_contract.py --language de --text "halt mit 4,9 nicht ins parlament" --required-word "4,9"
```

If the synthetic checker passes but real audio still lacks a timestamp for `4,9`, investigate model quality, ASR text accuracy, audio/segment boundaries, and interpolation settings rather than assuming the package cannot represent comma decimals.

## When to stop

Stop and report a real limitation instead of inventing timestamps when:

- No suitable alignment model exists for the language/script and custom model selection is outside the allowed budget.
- Required model weights are not available and downloads or credentials are not permitted.
- Segment timestamps do not correspond to the audio being aligned.
- The task requires verified acoustic timestamp quality but only the synthetic contract checker has been run.
