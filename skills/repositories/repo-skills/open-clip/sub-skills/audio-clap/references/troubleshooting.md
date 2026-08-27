# Audio CLAP Troubleshooting

## Optional Dependencies Missing

Symptoms:

- `AUDIO_AVAILABLE` is `False`.
- `require_audio()` raises about `torchaudio`, `torchlibrosa`, or `openai-whisper`.
- Audio transform or HTSAT/Whisper model construction fails at import time.

Actions:

- Install audio extras required by the chosen path: `torchaudio`, `torchlibrosa`, and `openai-whisper` for audio model support.
- Install `datasets[audio]` only when using Hugging Face audio zero-shot datasets.
- Re-run `scripts/audio_config_report.py` to confirm imports and config fields.

## HF Dataset Download or Cache Fails

Symptoms:

- `build_hf_audio_zero_shot_dataset()` raises while importing `datasets` or calling `load_dataset`.
- Dataset access needs network, authentication, or local cache configuration.

Actions:

- Dry-run the intended flags with `scripts/clap_zero_shot_args.py`; it does not download data.
- Verify the dataset id and split separately with Hugging Face tooling.
- Use a local/cache-aware environment for real evaluation.
- Keep `--audio-zeroshot-workers 0` while diagnosing dataset decode issues.

## Wrong Target or Class Keys

Symptoms:

- Class names are numeric strings instead of readable labels.
- Targets map to the wrong class names.
- `KeyError` for target/class columns.

Actions:

- Inspect the dataset schema and set `--audio-zeroshot-target-key` and `--audio-zeroshot-class-key` explicitly.
- For ESC-50-like datasets, common keys are `target` and `category`.
- For UrbanSound8K-like datasets, common keys are `classID` and `class`.
- If the HF target feature has `ClassLabel.names`, a separate class key may be unnecessary.

## Template Missing Placeholder

Symptoms:

- Audio zero-shot evaluation raises `Audio zero-shot template missing '{}' placeholder`.

Actions:

- Every `--audio-zeroshot-template` value must include `{}`.
- Use examples such as `This is a sound of {}.` or `A recording of {}.`.

## Worker Multiprocessing Deadlocks

Symptoms:

- Audio data loading hangs with `--workers > 0`.
- The hang appears after torchaudio/mel processing starts.

Actions:

- Prefer `--audio-multiprocessing-context forkserver` for training/eval audio loaders.
- Prefer `--audio-zeroshot-workers 0` while debugging HF datasets.
- If using zero-shot workers, try `--audio-zeroshot-multiprocessing-context forkserver` or `spawn`.
- Avoid importing heavy audio libraries before forking worker processes.

## Transform Sample Rate or Clip Length Mismatch

Symptoms:

- Unexpected waveform length, poor evaluation results, or excessive truncation/padding.
- Whisper configs behave differently from HTSAT defaults.

Actions:

- Inspect effective fields with `scripts/audio_config_report.py --model <name>`.
- Check `sample_rate`, `clip_samples`, `window_size`, `hop_size`, and `mel_bins`.
- Remember that fixed CLAP resamples to `audio_cfg.sample_rate` and pads/truncates to `clip_samples`.
- Eval forces deterministic truncation unless fusion is enabled; training may use random truncation.

## WebDataset Audio vs Image Dataset Confusion

Symptoms:

- Samples are filtered out or the loader cannot find `audio` fields.
- The data loader emits image keys or tuple batches instead of audio dicts.

Actions:

- Use `--dataset-type webdataset-audio` for real CLAP/NaFlexClap audio training.
- Ensure shards contain one caption member (`txt`, `json`, or `cls`) and one audio member (`wav`, `flac`, `mp3`, or `ogg`).
- Set `--audio-ext` to match the stored audio extension.
- Downstream training code should read `batch["audio"]` and `batch["text"]`.

## CLAP vs NaFlexClap Transform Mismatch

Symptoms:

- A NaFlexClap model receives `{"waveform", "longer"}` and fails in the audio tower.
- A fixed CLAP model receives `{"patches", "patch_coord", "patch_valid"}` and fails.
- `synthetic-audio` raises for a NaFlex audio model.

Actions:

- If `model.audio.cfg.model_type.lower() == "naflexvit"`, use `AudioNaFlexTransformFactory` and NaFlex collation.
- Otherwise use `audio_transform_v2` and `_audio_collate`/`_collate_audio_zero_shot`.
- Use `webdataset-audio`, not `synthetic-audio`, for NaFlexClap.
- Keep GenLAP-specific packed-prefix and generative loss details in the NaFlex/generative route.

## HF CLAP Conversion Mismatches

Symptoms:

- `load_state_dict(converted, strict=False)` reports many unexpected keys.
- Projection shapes differ.
- Both HF directional logit scales are expected but only one OpenCLIP scale exists.

Actions:

- Confirm the HF checkpoint is a Transformers `ClapModel` state dict.
- Convert with `convert_hf_clap_state_dict()` or `load_hf_clap_state_dict()`.
- Instantiate a matching OpenCLIP CLAP config, typically an HTSAT + Roberta CLAP config for HF CLAP.
- Inspect missing and unexpected keys before deciding whether strict loading is safe.
- Expect `logit_scale_a` to map to OpenCLIP's single `logit_scale`; do not try to load a separate text-direction scale.

## Audio Layer Decay Unsupported

Symptoms:

- Optimizer creation raises that audio layer-wise LR decay is unsupported for HTSAT or Whisper.

Actions:

- `--audio-layer-decay` requires `model.audio.layer_groups()` support and is intended for NaFlex spectrogram-ViT audio towers.
- Leave `--audio-layer-decay` unset for from-scratch HTSAT/Whisper CLAP unless you have implemented compatible layer groups.
