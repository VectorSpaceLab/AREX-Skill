# Troubleshooting Training and Data Prep

Use this reference when a ClearerVoice-Studio training, fine-tune, training-side inference, TSE, or data-generation setup fails before or during launch.

## Hard-coded GPU IDs and process counts

Symptoms:

- `CUDA error: invalid device ordinal`
- job starts on unexpected GPUs
- distributed job hangs before the first epoch

Actions:

1. Replace launcher `gpu_id`/`CUDA_VISIBLE_DEVICES` with actual available device IDs.
2. Set `n_gpu` or `--nproc_per_node` equal to the number of visible IDs.
3. For one GPU, use one visible ID and one process.
4. Verify `torch.cuda.is_available()` in the environment before launch.
5. If CUDA is unavailable, do not claim the selected training workflow is verified; these models are GPU-oriented.

## Distributed launch and master port failures

Symptoms:

- port already in use
- NCCL initialization errors
- `torch.distributed.launch` deprecation or removal
- process group timeout/hang

Actions:

1. Choose a stable free `--master_port` instead of a time-derived port.
2. Prefer `torchrun` when the legacy launcher is unavailable.
3. Keep `--nproc_per_node` and visible GPU count aligned.
4. Set a single-process launch for debug if the code path still requires distributed initialization.
5. For NCCL errors, check driver/CUDA/PyTorch compatibility and whether all visible GPUs are usable.

## Missing datasets or list paths

Symptoms:

- `FileNotFoundError` for `.scp`, `.csv`, `.wav`, `.mp4`, `.npy`, or checkpoint paths
- config inspector warns about missing path-valued fields
- dataloader reports zero files or crashes on first batch

Actions:

1. Run `scripts/inspect_training_config.py --check-paths` on the selected config.
2. Replace example list/config paths with user-owned paths.
3. For relative paths, run launch commands from the task directory expected by the config, or convert paths to explicit user-owned locations.
4. For inference lists, use one path per row; for training lists, use the task-specific multi-column format.
5. Open the first few list rows and verify the referenced files exist before launching.

## Sampling-rate mismatches

Symptoms:

- poor fine-tune quality despite successful launch
- assertions during reverb generation
- unexpected resampling time or memory use
- model output sounds bandwidth-limited or distorted

Actions:

1. Match SE network sample rate with the noisy/clean pair sample rates.
2. For `MossFormer2_SE_48K`, do not reuse 16 kHz lists unless the intent is to resample or rebuild the dataset for full-band training.
3. For SS, match 8 kHz versus 16 kHz configs to the generated mixture dataset.
4. For SR, check both YAML `sampling_rate` and JSON `supported_sampling_rates`.
5. For TSE, check `audio_sr` and `ref_sr` separately; audio/video alignment depends on both.

## Checkpoint resume, init, and fine-tune issues

Symptoms:

- training restarts from epoch 0 unexpectedly
- optimizer state not restored
- fine-tune loads wrong weights or fails strict loading
- `last_checkpoint` or `last_best_checkpoint.pt` missing

Actions:

1. Decide whether the request is resume or fine-tune.
2. Resume: set `train_from_last_checkpoint=1` and use the existing checkpoint directory.
3. SE/SS fine-tune: set `train_from_last_checkpoint=0`, pass an existing checkpoint file via `init_checkpoint_path`, and use a new checkpoint directory.
4. TSE fine-tune: set YAML `init_from` to a previous checkpoint directory containing `last_best_checkpoint.pt`, and use a new checkpoint directory.
5. If an SR launcher passes an argument not accepted by its parser, remove or implement that argument before launch.
6. Keep a copy of the exact config in the checkpoint directory for reproducibility.

## CUDA/cuDNN unavailable or incompatible

Symptoms:

- `torch.cuda.is_available()` is false
- CUDA driver/runtime mismatch
- cuDNN errors during convolution/RNN/attention layers
- out-of-memory at first batch

Actions:

1. Verify the environment's PyTorch build matches the host CUDA driver.
2. Reduce batch size, `effec_batch_size`, segment length, or number of workers for memory pressure.
3. For GAN and MossFormer2 models, expect substantial GPU memory requirements.
4. Do not treat CPU import success as proof of CUDA training readiness.
5. If a required backend is unavailable, report the block or narrow the scope to config/list preparation.

## FFmpeg and media dependencies

Symptoms:

- SR inference cannot read compressed media
- TSE lip loader returns empty frames
- OpenCV cannot open `.mp4`
- pydub reports decoder errors

Actions:

1. Install or expose FFmpeg for compressed audio/video decoding.
2. Prefer WAV input for training and generation when possible.
3. Verify OpenCV can decode one sample video before TSE launch.
4. Check video path pattern and file extension for lip configs.
5. For online TSE, verify frame resizing settings and image dimensions.

## TSE missing modality/reference directories

Symptoms:

- user provides only audio data for a lip/gesture/EEG config
- `reference_direc` is unset or points to the wrong modality
- dataloader fails on `.mp4`, `.npy`, or EEG array load

Actions:

1. Inspect `network_reference.cue`.
2. Explain the required reference file pattern for that cue.
3. Ask for the matching `reference_direc`, or switch to an audio-only reference-speech config if appropriate.
4. Do not launch lip/gesture/EEG training with only audio directories.
5. For EEG, also verify subject/trial array naming and start offsets.

## Data-generation scripts mutate outputs

Symptoms:

- old and new generated data are mixed
- generated lists point to stale files
- disk fills during generation
- generation outputs do not match downstream SE list format

Actions:

1. Use a new output directory or run number for every experiment.
2. Review `clean_list`, `noise_list`, SNR settings, `total_hours`, `sample_rate`, and output paths before launch.
3. Run a tiny generation first after user approval.
4. Pair final `noisy/` and `target/` files into a two-column SE training list.
5. Preserve the generation config alongside the produced training list.
