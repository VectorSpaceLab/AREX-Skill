# Audio Troubleshooting

Use this reference to diagnose NeMo Speech audio-to-audio install/import, hardware/backend, manifest/config, processing, evaluation, Lhotse, augmentation, multi-channel, and model-family failures. Evidence was distilled from audio docs, examples, configs, source, and tests.

## Install and Import Failures

Symptoms:

- `ModuleNotFoundError: No module named 'nemo'`
- `ImportError` for `lightning`, `torch`, `lhotse`, `soundfile`, `librosa`, `torchmetrics`, `pesq`, `pystoi`, SQUIM dependencies, CUDA libraries, or compiled packages
- Basic imports work but Lhotse, metrics, or processing fails

Actions:

1. Verify the active environment is the one where NeMo Speech is installed.
2. Check Python/PyTorch compatibility. Current NeMo Speech docs target Python 3.12+ and PyTorch 2.7+ for normal use, while package metadata allows Python `>=3.10`.
3. Install optional dependencies only for the selected workflow: Lhotse for CutSet/Shar/online augmentation, SoundFile/libsndfile for audio I/O, metric packages for PESQ/STOI/SQUIM, CUDA/compiled packages only when needed.
4. If only using the bundled manifest checker, do not install NeMo; `scripts/check_audio_manifest.py` uses only the Python standard library.
5. If source checkout and installed package differ, prefer the user's intended runtime and avoid mixing source-tree scripts from one version with a different installed package.

## CUDA, GPU, Precision, and Backend Problems

Symptoms:

- CUDA is unavailable despite `cuda=0` or `trainer.accelerator=gpu`.
- Processing unexpectedly runs on CPU or is very slow.
- AMP/float16/bfloat16 errors.
- Training OOMs or validation OOMs during generative metric calculation.
- Optional compiled backend errors.

Actions:

- Confirm PyTorch sees the intended CUDA device before running NeMo.
- For processing on CPU, set `cuda=-1`, reduce `batch_size`, disable `amp`, and expect slower throughput.
- For GPU processing, set `cuda=<device_index>` and use `amp=true` only when stable for the model.
- Lower `batch_size` first for OOMs. For generative validation, also lower or set `max_utts_evaluation_metrics`.
- For long sampler-based inference, reduce sampler steps or sample count through explicit sampler overrides only after confirming the model has those sampler fields.
- For training, use a CUDA-capable GPU setup; CPU training is generally impractical for real audio models.
- Keep optional compiled/CUDA packages aligned with the installed PyTorch/CUDA stack.

## Manifest and Data Problems

Symptoms:

- JSON decode errors or blank-line failures.
- `KeyError` for `audio_filepath`, `input_filepath`, `noisy_filepath`, `target_filepath`, `clean_filepath`, `speech_filepath`, or `processed_audio_filepath`.
- Samples silently disappear after duration filtering.
- Relative paths fail to resolve.
- Target audio is missing for training/evaluation.
- Channel selectors fail or produce wrong shapes.

Actions:

1. Run the bundled checker:

```bash
python scripts/check_audio_manifest.py data.jsonl \
  --input-key noisy_filepath \
  --target-key clean_filepath \
  --require-target \
  --check-files \
  --min-duration 0.1
```

2. Ensure every non-empty line is one JSON object and remove blank lines.
3. Ensure `duration` is numeric and positive; adjust `min_duration`, `max_duration`, or `audio_duration` so filters do not remove all samples.
4. Match config keys to manifest keys for train, validation, test, processing, and evaluation.
5. Resolve relative paths relative to the manifest location when preparing manifests.
6. For list-valued audio paths, verify every element is a string and every file has compatible sample rate/channel semantics for the intended composition.
7. For training/evaluation, require target audio; for processing-only inference, omit `--require-target` and set `target_key=null` only in contexts that support it.

## Hydra and CLI Misuse

Symptoms:

- Hydra says a key is not in struct.
- Overrides appear ignored.
- Shell expands lists or special characters unexpectedly.
- Processing complains both model options are missing.
- Evaluation rejects `audio_dir`.

Actions:

- Use `+`/`++` for new Hydra keys such as `+init_from_nemo_model`, `+init_from_pretrained_model`, `+input_cuts`, `+output_cuts`, or `++sampler.num_steps`.
- Quote list overrides: `'input_channel_selector=[0,1]'`.
- Use YAML values `null`, `true`, and `false`.
- For processing, set `model_path` or `pretrained_name`, and set `audio_dir` or `dataset_manifest`.
- For evaluation, set `dataset_manifest` and do not set `audio_dir`.
- Override both train and validation/test dataset keys when switching manifest schemas.
- Read the logged resolved config before a long run.

## Model Loading Failures

Symptoms:

- `.nemo` restore fails due to missing class path or config mismatch.
- `from_pretrained()` fails because network/cache access is unavailable.
- Fine-tuning fails with missing or unexpected keys.
- Sampler override raises that the model has no sampler or field.

Actions:

- Use `restore_from()` for local checkpoints and verify the file exists.
- Use `from_pretrained()` only after confirming downloads or cache reads are allowed.
- For unknown `.nemo` files, recover the target class from `return_config=True` and import the concrete class before restoring.
- Keep architecture YAML compatible with the checkpoint when fine-tuning; encoder/decoder/estimator shape changes require intentional partial loading or reinitialization.
- Only override `sampler.*` fields after checking the loaded model has `sampler` and that the field exists.
- If a checkpoint was produced by a different NeMo version, compare config structure and model class names before forcing load.

## Processing Failures

Symptoms:

- `Both cfg.model_path and cfg.pretrained_name cannot be None!`
- `Both cfg.audio_dir and cfg.dataset_manifest cannot be None!`
- Empty manifest error.
- Output directory already exists.
- Input files are missing or output paths are ambiguous.
- Model output length differs from input length.

Actions:

- Provide exactly one model source and at least one data source.
- Validate the manifest and check file existence before processing.
- Set explicit `output_dir` and `output_filename`; avoid relying on defaults when paths are safety-critical.
- Leave `overwrite_output=false` unless the user confirms replacement is safe.
- Use `max_utts` for smoke tests before a full run.
- Lower `batch_size` and `num_workers` if data loading or GPU memory fails.
- For multi-channel files, set `input_channel_selector` if the model expects fewer channels.
- If output length or padding matters, remember `AudioToAudioModel.process()` crops output to the input length before writing.

## Evaluation Failures

Symptoms:

- Evaluation rejects `audio_dir`.
- `Processed key ... not found` or `Target key ... not found`.
- Processed or target files are missing.
- Length mismatch between processed and target signals.
- `return_values_per_example` fails with `batch_size > 1`.
- PESQ/STOI/SQUIM import or runtime errors.

Actions:

- Use a manifest input for evaluation and override `target_key` to the manifest's actual target field.
- If scoring an existing processed manifest, set `only_score_manifest=true` and `processed_key` correctly.
- If running processing then evaluation, ensure `output_filename` is the manifest that evaluation should score.
- Set `target_dataset_dir` when target relative paths should resolve against a directory different from the processed manifest's directory.
- Use `processed_channel_selector` and `target_channel_selector` to align channel counts.
- Set `batch_size=1` when `return_values_per_example=true`.
- Start with `sdr`/`sisdr`/`estoi`; add PESQ/SQUIM only after optional metric dependencies are installed and sample rate is appropriate.
- Investigate length mismatches by checking sample rate, resampling, trimming, padding, and channel selection.

## Training and Fine-Tuning Failures

Symptoms:

- Model type is wrong or defaults unexpectedly to mask-based.
- Loss receives wrong shapes.
- NaN/Inf gradients.
- Validation is too slow.
- Fine-tuning from a checkpoint fails to load weights.
- Post-fit test crashes after distributed training.

Actions:

- Set `model.type` explicitly unless using mask-based defaults intentionally.
- Confirm model outputs and targets both use `(B, C, T)` after dataset collation.
- Use `input_channel_selector` and `target_channel_selector` to align channel counts.
- For NaN/Inf gradients, lower learning rate, check normalization, inspect data clipping, and consider `skip_nan_grad=true` only as a last-resort guard.
- For generative models, lower `max_utts_evaluation_metrics` or reduce sampler cost during validation.
- When fine-tuning, use architecture-compatible configs and add `+init_from_nemo_model` or `+init_from_pretrained_model` explicitly.
- If post-fit test is not needed, remove or null `model.test_ds` to avoid single-device test setup surprises.

## Model-Family-Specific Problems

Masking and beamforming:

- Symptom: channel mismatch between multi-channel input and target. Action: use flex-channel configs for variable input channels, keep `input_channel_selector=null` when all microphone channels are needed, and set `target_channel_selector` intentionally.
- Symptom: target selected from the wrong channel. Action: verify target file channel layout and selector values with a tiny manifest.

Predictive:

- Symptom: output amplitude is wrong. Action: check `normalize_input` and `normalization_signal`; avoid double-normalizing in dataset and model unless intended.
- Symptom: streaming predictive config gives poor results in offline mode. Action: verify whether `normalize_input=false` and streaming architecture choices match the checkpoint.

Score-based generative:

- Symptom: sampler config raises `SDE should be defined in the model config`. Action: move SDE definition to `model.sde`, not `model.sampler.sde`.
- Symptom: validation is extremely slow. Action: set `max_utts_evaluation_metrics` and reduce sampler settings for debugging.

Schrödinger Bridge:

- Symptom: config raises about `loss` versus `loss_encoded`/`loss_time`. Action: choose one loss style, not both.
- Symptom: estimator output unsupported. Action: use `estimator_output: data_prediction` unless the code version explicitly supports another mode.

Flow matching:

- Symptom: training behaves like unconditional generation. Action: check `p_cond`; `p_cond=0` drops conditional input.
- Symptom: SSL pretraining target fields are absent. Action: confirm this is intentional; flow model parser can clone input as target when target is missing, but other families cannot.
- Symptom: inference and evaluation differ. Action: `forward()` disables SSL masking; `forward_eval()` enables it when configured.

Maxine BNR:

- Symptom: assertion says only 16k is supported. Action: resample input and config to 16000 Hz.
- Symptom: multi-channel input error. Action: select or downmix to one channel before BNR2.
- Symptom: output has edge/padding artifacts. Action: verify 10 ms alignment padding and inspect original length trimming.

## Lhotse Problems

Symptoms:

- `lhotse` import failure.
- Missing `target_signal` in Lhotse batches.
- CutSet paths fail after moving manifests.
- Shar export or loading fails.
- Distributed training duplicates or skips unexpectedly.
- Online augmentation drops samples.

Actions:

- Install Lhotse only for CutSet/Shar/online-augmentation workflows.
- Ensure every Cut has custom `target_recording` when target audio is required.
- Use `reference_recording` and `embedding_vector` custom fields only when the model/dataset expects them.
- Keep relative CutSet recording sources valid relative to the CutSet file, or convert with absolute paths for Shar export.
- Set `trainer.use_distributed_sampler=false` with Lhotse.
- For Shar/infinite-style data, bound training with max steps or limit batches.
- When using nested `input_cfg`, ensure `reweight_temperature` list length matches maximum nesting depth.
- Online augmentation needs compatible RIR/noise manifests and can change durations or clipping behavior; smoke test with a small `num_samples` materialization.

## Augmentation-Saving Problems

Symptoms:

- `input_cuts` or `output_cuts` assertion failure.
- Input cuts are not `MonoCut`.
- Input recording source path is absolute.
- Output parent directory missing.
- Output order differs from input.

Actions:

- Provide `+input_cuts` and `+output_cuts`; create the output parent directory first.
- Use a `.jsonl` CutSet of simple `MonoCut` entries.
- Keep input recording sources relative to the CutSet path and ensure files exist.
- Use `+num_samples` for a bounded smoke test.
- The script disables bucketing and resets filters for deterministic one-to-one output; if output counts differ, inspect dataloader failures and augmentation filters.

## Multi-Channel Problems

Symptoms:

- Shape errors from `(B, T)` versus `(B, C, T)`.
- Channel count varies across samples.
- Target and processed signals have different channel counts.
- BNR rejects multi-channel input.
- Lhotse conversion complains about single-channel selector values or mismatched sampling rates.

Actions:

- Use channel selectors to normalize channel counts before model input or evaluation.
- For list-valued paths, ensure sample rates match across files that form one multi-channel recording.
- Use flex-channel model/config variants when channel count variability is intentional.
- For evaluation, select comparable processed and target channels.
- For BNR, select one channel or downmix before the model.
- For Lhotse conversion, a single-channel recording only accepts selector `[0]` or equivalent single-channel selection.

## Output Safety Problems

Symptoms:

- Output directory is inside input data and hard to distinguish from source.
- Existing processed directory prevents processing.
- `overwrite_output=true` would replace previous outputs.
- Output manifest path equals input manifest path.
- Long job destination is ambiguous.

Actions:

- Run the bundled checker with `--output-dir` and `--output-manifest` before processing.
- Choose an explicit output directory outside the input tree when possible.
- Keep output manifest separate from input manifest.
- Require user approval before setting `overwrite_output=true`.
- For long processing, run a `max_utts` smoke test into a temporary output first.

## Safe Recovery Checklist

Before a long audio job, confirm:

- Environment imports NeMo and PyTorch sees the intended device.
- Manifest checker passes with expected key, duration, file, and output-path checks.
- Model source is explicit: local `.nemo` path or approved pretrained name.
- Dataset keys and channel selectors match actual data.
- Sample rate matches model family, especially BNR 16 kHz.
- Lhotse targets/reference/embedding fields exist if using Lhotse.
- Batch size, sampler cost, and metric limits fit memory/time budget.
- Output paths are explicit, safe, and not overwriting needed artifacts.
- Evaluation metric dependencies are installed only for metrics being used.
