---
name: training-and-data-prep
description: "Guide ClearerVoice-Studio training, fine-tuning, launchers, data
  lists, target speaker extraction, and speech-enhancement data generation
  without starting expensive jobs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Training and Data Prep

Use this sub-skill when a user needs to prepare or sanity-check ClearerVoice-Studio training, fine-tuning, evaluation-only runs, custom data lists, or speech-enhancement data generation. Keep actions cheap unless the user explicitly authorizes a training/evaluation job.

## Route First

- Use this sub-skill for local training and fine-tuning of speech enhancement, speech separation, speech super-resolution, offline target speaker extraction, online target speaker extraction, training-list construction, and config/list checks.
- Route packaged pretrained ClearVoice API inference to `clearvoice-inference`; this sub-skill only covers the repository's training-side inference launchers used for checkpoints and custom configs.
- Route PESQ/STOI/SI-SDR/SDR-style objective scoring and benchmark metric interpretation to `speechscore-metrics`; this sub-skill only prepares outputs and lists for metrics.
- Do not start full training, distributed evaluation, data mixing, or RIR/noisy generation without user confirmation about GPUs, runtime, dataset paths, output mutation, and checkpoint overwrite risk.

## Fast Operating Flow

1. Identify the task family: speech enhancement (SE), speech separation (SS), speech super-resolution (SR), offline target speaker extraction (TSE), online TSE, or speech-enhancement data generation.
2. Read the relevant reference below before editing configs or proposing a command.
3. Use `scripts/inspect_training_config.py` on the chosen YAML/JSON config before launch, especially when changing sample rates, data paths, checkpoint paths, or TSE modalities.
4. Use `scripts/make_scp_list.py` to build one-path-per-line inference lists or SR lists from local audio/video directories; for paired SE/SS training lists, write or validate the multi-column format described in the references.
5. For any launcher copied from memory, replace hard-coded GPU IDs, `n_gpu`, and `master_port`; set `checkpoint_dir`, `train_from_last_checkpoint`, and init/fine-tune settings deliberately.
6. For TSE, verify that the CSV/list partitions, audio directory, and modality/reference directory match the selected cue before discussing training.

## Bundled References and Scripts

- Read [references/training-workflows.md](references/training-workflows.md) when choosing or adapting SE/SS/SR train, fine-tune, resume, and training-side inference commands.
- Read [references/config-and-data-formats.md](references/config-and-data-formats.md) when editing YAML/JSON configs, creating `.scp` files, or diagnosing sampling-rate/list mismatches.
- Read [references/data-generation.md](references/data-generation.md) before running additive-noise or reverb-noisy speech-enhancement data generation, because those scripts write new output trees.
- Read [references/target-speaker-extraction.md](references/target-speaker-extraction.md) when preparing offline or online TSE configs, modality directories, mixture CSV files, checkpoint init/resume, or evaluation-only runs.
- Read [references/troubleshooting.md](references/troubleshooting.md) when a launch fails on CUDA, distributed setup, missing paths, FFmpeg/media dependencies, checkpoints, sample rates, or TSE modality data.
- Run [scripts/inspect_training_config.py](scripts/inspect_training_config.py) before launch to summarize a YAML/JSON training or inference config, detect likely path fields, and optionally warn about missing paths without importing training modules.
- Run [scripts/make_scp_list.py](scripts/make_scp_list.py) to create sorted one-path-per-line audio/video lists safely; it dry-runs by default and writes only when explicitly requested.

## Safety Rules

- Treat repository launchers as templates, not turnkey commands: they contain fixed GPU IDs and dynamic master ports that often need editing.
- Prefer `torchrun` on modern PyTorch if the legacy distributed launcher is unavailable, but keep equivalent values for process count, visible devices, and rendezvous/master port.
- Keep all data paths, checkpoint paths, and generated-output paths explicit and user-owned; never assume example paths are valid.
- For fine-tuning, distinguish resume (`train_from_last_checkpoint=1`, optimizer state restored) from weight initialization (`init_checkpoint_path` or `init_from`, optimizer reset/new run).
- For data generation, work on copied configs/lists and a new output directory or run number; generation scripts mutate outputs and may overwrite or append files.
