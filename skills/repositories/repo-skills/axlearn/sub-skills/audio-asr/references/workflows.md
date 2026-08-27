# audio-asr workflows

## Purpose

Read this when you need to inspect or explain AXLearn's speech feature extraction, ASR model stack, or LibriSpeech trainer catalogs.

## Verified API facts

The installed package exposes these important signatures:

- `axlearn.audio.frontend.LogMelFrontend.default_config()`
- `axlearn.audio.encoder_asr.ASREncoder.default_config()`
- `axlearn.audio.encoder_asr.SpeechFeatureLayer.default_config()`
- `axlearn.audio.encoder_asr.SpeechContextNetwork.default_config()`
- `axlearn.audio.model_asr.ASRModel.default_config()`
- `axlearn.audio.input_asr.speech_input(max_len, input_key='speech', normalize_by_scale=None, truncate=False)`
- `axlearn.audio.input_asr.text_input(max_len, vocab, input_key='text', truncate, min_len=1, eos_id=None)`
- `axlearn.audio.input_asr.make_autoregressive_inputs(vocab, bos_id)`
- `axlearn.audio.input_asr.pad_example_fn(element_spec)`
- `axlearn.audio.evaler_asr.compute_word_errors(hypothesis, reference)`
- `axlearn.audio.evaler_asr.normalize_text()`
- `axlearn.audio.evaler_asr.WordErrorRateMetricCalculator.default_config()`
- `axlearn.audio.streaming.streaming_base.compute_encoder_segment_pad(layer_cfgs)`
- `axlearn.audio.streaming.streaming_base.compute_decoder_segment_pad(layer_cfgs)`
- `axlearn.audio.streaming.streaming_base.next_segment_pos(current_len, *, segment_pad=0, stride=1)`
- `axlearn.audio.frontend_utils.sharded_fft(n, partition_spec)`

## Workflow patterns

### 1) LibriSpeech trainer setup

The LibriSpeech trainer uses a fake-data branch when `DATA_DIR=FAKE` and TFDS/SentencePiece paths when a real dataset is available.

The main builder pieces are:

- `feature_config(dim, jax_backend=None)` for speech features.
- `asr_input(...)` for combining speech and text processing.
- `evaler_config_dict(...)` for WER evalers.
- `named_trainer_configs()` for the catalog names.

### 2) Fake-data smoke check

The smallest safe probe is the `conformer-test-ctc` config with `DATA_DIR=FAKE`. This keeps the workflow CPU-safe and avoids LibriSpeech downloads.

### 3) Streaming helpers

`StreamingBase` and the `compute_*_segment_pad` helpers are useful when the task is about online/streaming decoding behavior or segment boundaries.

### 4) ASR evaluation

`WordErrorRateMetricCalculator` is the main reusable evaluation surface. It normalizes text, decodes model outputs, and computes WER from Levenshtein-style opcodes.

## Typical command patterns

### Fake-data LibriSpeech probe

```bash
DATA_DIR=FAKE python -m axlearn.common.launch_trainer_main \
  --module=axlearn.experiments.audio.conformer.librispeech_trainer \
  --config=conformer-test-ctc \
  --trainer_dir=/tmp/axlearn-librispeech-test \
  --data_dir=FAKE \
  --jax_backend=cpu
```

### Inspect the catalog names

```bash
python scripts/inspect_audio_configs.py --module axlearn.experiments.audio.conformer.librispeech_trainer --data-dir FAKE
```

## When to read more

- For failure modes and tokenizer-path issues, see `references/troubleshooting.md`.
- For the shared trainer runtime, use `../training-core/`.
