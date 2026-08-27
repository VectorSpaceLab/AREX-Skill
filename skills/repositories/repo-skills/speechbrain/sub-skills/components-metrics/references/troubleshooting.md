# Components and metrics troubleshooting

## Tensor shape mismatch

- Print tensor shapes before feature extraction, model blocks, decoders, loss, and metrics.
- Confirm batch is first and time is second.
- Confirm `wav_lens`/sequence lengths correspond to the time dimension used by that module.
- Check whether a module expects raw waveforms, features, logits, token ids, or decoded strings.

## Decoder errors

- Verify tokenizer/label encoder indices and blank/BOS/EOS IDs.
- Confirm logits are log-probabilities or probabilities as required by the decoder/loss.
- For beam search/rescoring, verify language-model vocabulary matches the acoustic model tokenizer.
- Reduce beam size to isolate shape/configuration errors from search complexity.

## Metric errors

- `ErrorRateStats` needs decoded predictions and reference sequences, not arbitrary logits.
- `BinaryMetricStats` expects aligned score/label tensors.
- Classification category labels must match the label encoder used in training.
- Missing hypothesis keys in WER scoring depend on mode: `strict`, `present`, or `all`.

## Checkpoint recovery errors

- Compare `recoverables` keys with checkpoint file names/metadata.
- Confirm the model architecture matches the checkpoint source.
- Treat partial loads as a deliberate limitation; do not silently enable them for production evaluation.
- In DDP, ensure only intended ranks write checkpoints or use node-aware save helpers.

## Pretrainer errors

- Confirm `paths` keys match `loadables` keys.
- For remote sources, separate `collect_files` failures from `load_collected` failures.
- Use `LocalStrategy.COPY` if symlinks are restricted.
- Use `FetchConfig(allow_network=False)` for offline local artifacts.

## Streaming errors

- Distinguish sample counts from feature-frame counts.
- Validate chunk splitting on a synthetic ramp signal before real audio.
- Match `DynChunkTrainConfig` to the model's training hparams.
- Compare chunked output with non-streaming output for tiny inputs when the model supports both.
