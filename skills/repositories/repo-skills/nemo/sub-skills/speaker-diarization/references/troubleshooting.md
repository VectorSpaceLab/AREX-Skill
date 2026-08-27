# Speaker Troubleshooting

Use this reference for NeMo speaker recognition, diarization, VAD, Sortformer, ASR+diarization, forced alignment, manifest, and Hydra failures. It distills evidence from speaker docs/examples/configs, model source, forced-aligner source, and speaker tests.

## First Triage

1. Validate the manifest with `../scripts/check_speaker_manifest.py` before running NeMo.
2. Identify the workflow owner: Sortformer, clustering diarizer, speaker recognition, VAD, ASR+diarization, or forced alignment.
3. Check whether the workflow requires checkpoint downloads, GPU/CUDA, optional libraries, or dataset-specific files.
4. Print or inspect the final Hydra config before long jobs. Speaker examples log `OmegaConf.to_yaml(cfg)` at startup.
5. Reduce to one short audio file or one manifest line, batch size 1, and local checkpoints when debugging.

## Install and Import Failures

Symptoms:

- `ModuleNotFoundError: nemo`, `No module named lightning`, `No module named omegaconf`, missing `torch`, missing ASR/speaker utilities.
- Import succeeds but model loading fails for optional audio/scoring dependencies.

Actions:

- Use a NeMo Speech environment with Python 3.12+, PyTorch 2.7+, and a compatible CUDA stack for training and recommended inference.
- Confirm `import nemo` and `import nemo.collections.asr` work before running scripts.
- Install optional dependencies only for the workflow that needs them: audio decoding, `soundfile`, `librosa`, `sox`, `scipy`, `sklearn`, `pyctcdecode`, KenLM, Lhotse, or diarization/scoring packages may be needed by specific paths.
- Avoid broad dependency upgrades inside a shared environment. Create a fresh environment for heavyweight speaker training or forced alignment if imports conflict.
- If using local `.nemo` files, verify the file exists and is readable; if using pretrained names, expect network/cache access unless assets are already cached.

## GPU, CUDA, and Backend Failures

Symptoms:

- CUDA out of memory, slow CPU inference, `torch.cuda.is_available()` false, NCCL/DDP errors, precision errors, unsupported BF16, checkpoint/device mismatch.

Actions:

- For inference, start with `batch_size=1`, `num_workers=0`, and a short manifest.
- For Sortformer inference, batch size 1 is also the safer setting when reproducing DER because it maximizes inference window length.
- For VAD/ASR+diarization/forced alignment on long audio, split long audio into smaller manifest segments or reduce batch size.
- For training, use `trainer.accelerator=gpu`, set `trainer.devices` to available GPU count, and choose `trainer.precision=32`, `bf16`, or `bf16-mixed` only if hardware supports it.
- If DDP hangs or complains about unused parameters, match the example config strategy. Some Sortformer configs use `ddp_find_unused_parameters_true`; recognition configs commonly use `ddp`.
- Do not assume compiled optional backends are installed. This generated skill was created from a minimal inspection environment and documents optional-heavy workflows generically.

## Manifest and Schema Failures

Symptoms:

- Missing `audio_filepath`, `text`, `label`, or `rttm_filepath` errors.
- DER is missing or all zeros, oracle VAD produces no labels, cpWER cannot run, output files overwrite each other.

Actions:

- Run `check_speaker_manifest.py` with the closest task mode:
  - `--task diarization-eval --require-rttm --check-rttm-speakers`;
  - `--task recognition --require-label`;
  - `--task forced-alignment`;
  - `--task asr-diarization --require-rttm --require-ctm`.
- Use `audio_filepath` in every line. Add `offset` and `duration` for segmented/long-audio cases.
- Add `text` for forced alignment unless using `align_using_pred_text=True`.
- Add `label` for speaker recognition training/enrollment; use `infer` for test/inference manifests.
- Use unique `uniq_id` values when multiple manifest lines reference the same long audio file.
- Keep audio, RTTM, UEM, CTM, and text basenames aligned when using path-list style manifest generation.
- Validate `duration > 0` when present and not `null`; validate `offset >= 0`.
- For ASR+diarization scoring, ensure CTM speaker IDs exactly match RTTM speaker IDs.

## Hydra and CLI Misuse

Symptoms:

- `Key '...' is not in struct`, unresolved `???`, list overrides parsed incorrectly, config path not found, both model path and pretrained name set.

Actions:

- Use `key=value` for existing Hydra fields; use `+key=value` only for new fields.
- Quote list overrides in shell commands: `diarizer.speaker_embeddings.parameters.window_length_in_sec='[1.5,1.0,0.5]'`.
- Do not include spaces around `=` in overrides.
- Set all required `???` fields such as manifest paths, output directories, model paths, and decoder class counts.
- Keep `model_path` and `pretrained_name` mutually exclusive in forced alignment.
- Prefer absolute data/checkpoint paths in user commands for runtime reliability, but never bake local absolute paths into generated skill content.
- If a command was copied from a source example, replace source-relative script/config paths with the user's actual installed/script location or a Python API equivalent.

## Sortformer Diarization Problems

Symptoms:

- Too many/few speakers, unstable speaker labels, poor overlap behavior, DER worse than expected, streaming labels drift.

Actions:

- Confirm the model speaker-count limit. Common Sortformer examples target up to 4 speakers; sessions with more speakers will degrade.
- For streaming Sortformer, tune `chunk_len`, `chunk_right_context`, `fifo_len`, and `spkcache_update_period` cautiously. Lower latency can hurt accuracy.
- Use appropriate post-processing YAML when reproducing model-card DER; default inference only binarizes.
- Set `batch_size=1` for best accuracy and easiest debugging.
- Validate RTTM labels and manifest windows when DER is nonsensical.
- For training, ensure train/dev manifests cover every target speaker count and that `session_len_sec`, `num_spks`, and RTTM windows agree.
- If `soft_label_thres` is too high, the model may become conservative and miss speech; too low can increase false alarms.

## Clustering Diarizer Problems

Symptoms:

- VAD false alarms/misses dominate DER, wrong speaker count, embeddings not saved/found, clustering is slow on long audio.

Actions:

- Decide whether to use model VAD, external VAD, ASR-based VAD, or oracle VAD. Do not configure conflicting VAD sources.
- Tune VAD `onset`, `offset`, `pad_onset`, `pad_offset`, `min_duration_on`, `min_duration_off`, and `smoothing` against a small dev set.
- For oracle VAD, every manifest line must have `rttm_filepath`.
- If speaker count is known, set `num_speakers` in the manifest and `diarizer.clustering.parameters.oracle_num_speakers=True`.
- If speaker count is unknown, set a realistic `max_num_speakers`; too high can over-split speakers.
- For multiscale embeddings, list lengths for window, shift, and weights must match. Use descending windows and matching shifts.
- For long recordings, adjust `chunk_cluster_count` and `embeddings_per_chunk` based on memory.

## Speaker Recognition Problems

Symptoms:

- `labels are not saved to model`, wrong predicted labels, verification threshold unreliable, EER script cannot find embeddings.

Actions:

- Make sure training/enrollment manifests have `label` fields and that labels are consistent across files.
- For classification/fine-tuning, set `model.decoder.num_classes` to the number of training labels when the config requires it.
- When fine-tuning pretrained TitaNet-style models, exclude decoder layers if the class set changes.
- Use `batch_inference()` output order as manifest order; keep trial files and embedding keys aligned.
- Calibrate `verify_speakers(..., threshold=...)` on a dev set. The default threshold is a starting point, not a universal operating point.
- If CPU inference is forced, set `device='cpu'` in API calls but expect slower performance.

## VAD Problems

Symptoms:

- Speech regions are too fragmented, non-speech is labeled as speech, short words disappear, diarization misses turns.

Actions:

- Increase `min_duration_off` to merge short gaps; increase `min_duration_on` to remove short false alarms.
- Adjust `onset` and `offset` separately; onset controls speech start, offset controls speech end.
- Use `pad_onset`/`pad_offset` to avoid clipping speech boundaries.
- Test `median` smoothing for noisy frame predictions.
- Use long-audio splitting if frame-level VAD OOMs.
- If VAD quality is poor but ASR timestamps are reliable, test ASR-based VAD in the ASR+diarization workflow.

## ASR plus Diarization Problems

Symptoms:

- Speaker-attributed transcript has words assigned to wrong speaker, cpWER missing, word timestamps shifted, ASR-based VAD misses speech.

Actions:

- Route ASR model/decoder issues to `../asr/SKILL.md`; keep speaker debugging focused on timestamp-to-speaker mapping.
- Tune `word_ts_anchor_pos` and `word_ts_anchor_offset` if word timestamps systematically lead or lag diarization boundaries.
- Set `fix_word_ts_with_VAD=True` only when a VAD model is configured.
- Confirm `ctm_filepath` exists for every evaluated file when computing WER/cpWER.
- Confirm CTM and RTTM speaker labels match exactly.
- If reference CTM is unavailable, report DER and ASR WER separately rather than claiming cpWER.

## Forced Alignment Problems

Symptoms:

- Missing `text` errors, empty CTM/ASS, invalid output paths, wrong timestamps, model source config errors.

Actions:

- Use the missing-text decision tree in `forced-alignment.md`.
- Set exactly one of `model_path` or `pretrained_name`.
- Set explicit `output_dir` and avoid overwriting existing CTM/ASS outputs.
- Increase `audio_filepath_parts_in_utt_id` when basenames collide.
- Use `additional_segment_grouping_separator` to split long reference text; do not set it to empty string or plain space.
- If output ASS config fails, check `vertical_alignment` and RGB lists.
- If timestamps are poor, verify language/model match, transcript accuracy, sample rate/channel handling, and batch size.

## RTTM/CTM Speaker Mismatch Hard Case

When diarization evaluation has RTTM paths and speaker tags inconsistent with the manifest or CTM:

1. Run `check_speaker_manifest.py manifest.json --task asr-diarization --require-rttm --require-ctm --check-rttm-speakers --check-ctm-speakers --speaker-consistency strict`.
2. Compare manifest-derived IDs, RTTM recording IDs, CTM source IDs, and speaker labels.
3. If RTTM speaker labels are `speaker_0`/`speaker_1` but CTM uses names such as `alice`/`bob`, choose one convention and rewrite one side before scoring.
4. If RTTM basenames differ from audio basenames, either fix paths/recording IDs or provide explicit `uniq_id` consistently.
5. Re-run a one-file evaluation before launching the full set.

## Safe Minimal Reproductions

- Manifest-only: run the bundled checker with task-specific flags.
- API import: `python -c "import nemo; import nemo.collections.asr as asr; print(nemo.__version__)"`.
- Speaker model list: call `EncDecSpeakerLabelModel.list_available_models()` only when network/cache policy allows model metadata access.
- Sortformer one-file inference: one short WAV, `batch_size=1`, local or cached checkpoint.
- Forced alignment one-file inference: one short WAV, known transcript, `save_output_file_formats='[ctm]'` if ASS is not needed.

Do not run full training, large VAD sweeps, network downloads, or source example scripts as validation unless the user explicitly asks and the environment is ready.
