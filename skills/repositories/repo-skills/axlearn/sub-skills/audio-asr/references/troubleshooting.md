# audio-asr troubleshooting

## Purpose

Read this when ASR or speech-feature workflows fail to import, find tokenizer data, or switch between fake and real inputs.

## Common failures

### `DATA_DIR` is missing or not `FAKE` for a fake-data smoke test

**Likely cause:** The LibriSpeech or speech-feature helper followed the real-data path.

**Recovery:** Set `DATA_DIR=FAKE` before running the probe or use the bundled helper for the fake-data branch.

### Tokenizer or SentencePiece file not found

**Likely cause:** The ASR helpers expect sentencepiece or tokenizer files under the configured data directory.

**Recovery:**

- Set `DATA_DIR=FAKE` to use packaged repository data where supported.
- Or point `DATA_DIR` to a directory containing `tokenizers/sentencepiece/`.

### `WordErrorRateMetricCalculator` or decode path fails

**Likely cause:** The decode model method or tokenizer path is inconsistent with the selected ASR config.

**Recovery:** Check the named trainer config first, then inspect the decoder's expected `beam_search_decode` arguments.

### Streaming segment padding does not match the expected output

**Likely cause:** The layer stride or segment boundary assumptions changed.

**Recovery:** Use the `compute_encoder_segment_pad` / `compute_decoder_segment_pad` helpers to reason about the needed gap before recomputing the streaming route.

## Recovery order

1. Confirm fake vs real data path.
2. Confirm the tokenizer or vocabulary file path.
3. Confirm the decoder method / WER setup.
4. Only then debug feature-extraction or streaming math.
