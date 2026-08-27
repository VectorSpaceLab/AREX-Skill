# Data/audio pipeline troubleshooting

## Audio shape surprises

- `audio_io.load(..., channels_first=True, always_2d=True)` returns `(channels, frames)` for files.
- Model batch inputs usually need `(batch, time)` or `(batch, time, channels)`.
- For a mono loaded file with shape `(1, frames)`, use `wave.squeeze(0).unsqueeze(0)` only if the target model expects `(batch, time)`.
- Print shapes at every boundary: file load, feature extraction, collate, `Brain.compute_forward`.

## Unsupported audio format

- Prefer WAV or FLAC for debugging.
- Use `audio_io.info(path)` to check format/subtype/channels before loading.
- Upgrade `soundfile` or install system `libsndfile` if common formats fail.
- Convert AAC/M4A or unusual codecs outside SpeechBrain before loading.

## Dynamic item does not run

- Confirm the dynamic function's `@provides` key appears in `set_output_keys` or a downstream requested dependency.
- Confirm every `@takes` key exists in the static manifest or is provided by another dynamic item.
- Use `DataPipeline.compute_specific(["key"], example)` to debug one key.
- Multi-output generator functions must yield in the same order as `@provides`.

## Dataset replacement path errors

- Keep manifests portable with placeholders such as `{data_root}`.
- Pass replacements through `DynamicItemDataset.from_json(..., replacements={...})`.
- Avoid hard-coding machine-specific absolute paths in manifests or generated examples.

## Encoder/tokenizer failures

- Fit encoders on the same label/text field consumed later.
- Insert CTC blank or BOS/EOS before training when the recipe expects those symbols.
- Check expected vocabulary size with `expect_len` only after understanding recipe hparams.
- SentencePiece training writes model files; use a temp or output directory and avoid overwriting production tokenizers during smoke tests.

## Augmentation failures

- Confirm noise/RIR CSV files and referenced audio paths exist.
- Confirm sample rate fields match the clean/noise/reverb files.
- Disable one augmentation at a time to isolate failure.
- Generate one tiny batch and inspect output shape/range before full recipe training.

## Feature normalization issues

- Pass correct relative lengths to normalization modules.
- Ensure padded frames are masked when expected.
- Distinguish global, sentence, batch, and speaker normalization modes.
- Reset or checkpoint normalization stats intentionally when resuming experiments.
