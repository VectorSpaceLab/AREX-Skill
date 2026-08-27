# Pretrained inference troubleshooting

## `from_hparams` cannot find files

- Confirm the `source` is a valid local directory, URL, or Hugging Face model id.
- Confirm `hparams_file` matches the model artifact name; most models use `hyperparams.yaml`.
- Set a stable `savedir` and check whether symlink/copy permissions are available.
- Use `download_only=True` to separate fetch/cache failures from model construction failures.

## Network or cache errors

- For offline work, pass `FetchConfig(allow_network=False)` and use a local source.
- For reproducibility, pin `FetchConfig(revision="...")`.
- For private models, configure Hugging Face credentials outside the skill and pass the appropriate token setting.
- If symlinks fail, use `LocalStrategy.COPY` instead of the default symlink strategy.

## HyperPyYAML/custom-code trust boundary

- HyperPyYAML constructs Python objects and may execute arbitrary constructors.
- `foreign_class` fetches and imports Python code from the model source.
- Do not load untrusted model repositories or custom Python files in automated workflows.
- Prefer pinned revisions and local reviewed copies for production/research reproducibility.

## Audio shape, sample rate, or channel errors

- Use `model.load_audio(path)` for file inputs that need model-specific audio normalization.
- Use `speechbrain.dataio.audio_io.info(path)` to inspect sample rate and channel count.
- Batch methods usually expect `(batch, time)` for mono waveform batches plus `wav_lens` in `[0, 1]`.
- If a method documents `[batch, time, channels]`, preserve the channel dimension.

## Device or precision errors

- Use `run_opts={"device": "cpu"}` for deterministic CPU diagnosis.
- Use CUDA only after a separate `torch.cuda.is_available()` and allocation check.
- Mixed precision and `torch.compile`/JIT settings can fail for some modules; disable them first when diagnosing functional failures.

## Method/class mismatch

- `EncoderDecoderASR.transcribe_file` returns one transcription string.
- `EncoderDecoderASR.transcribe_batch` returns `(predicted_words, predicted_tokens)`.
- `EncoderClassifier.classify_file` returns probability/score/index/label values.
- `SpeakerRecognition.verify_files` compares two audio files, not one.
- `SepformerSeparation.separate_file` separates one mixture file.
- `GraphemeToPhoneme.g2p` accepts text, not audio.

When in doubt, run `scripts/pretrained_interface_smoke.py --json` to verify class availability and signatures before downloading any model.
