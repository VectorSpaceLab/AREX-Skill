# Training recipe troubleshooting

## Common issues

- **Stage logic is confusing**
  - Read `references/recipes.md` first for the stage-based pattern.
  - Inspect a user-provided recipe script only when the user is actually working from a recipe checkout.
  - The `stage` variable usually determines which data-prep or training steps rerun.

- **The recipe expects a missing dataset helper package**
  - SMS-WSJ often needs `sms_wsj` and `lazy_dataset`.
  - Some AVSpeech or DAMP-VSEP flows need `librosa` or video tooling.
  - Install only the helper package required by the selected recipe.

- **`asteroid.data` will not import**
  - Run `python scripts/install_runtime.py` from the skill output so the runtime extras are installed.
  - Some dataset modules import `librosa` at module load time.

- **A recipe wants CUDA but the host is CPU-only**
  - Most Asteroid recipes can still be read, planned, or smoke-tested on CPU.
  - Do not claim a GPU-backed run unless the actual recipe step was verified on GPU.

- **`compute_wer` or ASR-side metrics are unavailable**
  - Some LibriMix recipe variants need `espnet_model_zoo`, `jiwer`, or other optional ASR packages.
  - If WER is not the task, skip that branch.

- **Music recipes run out of memory**
  - X-UMX and related music workflows can be memory heavy.
  - Use the recipe docs as guidance and keep verification light unless the user explicitly wants the full path.

- **The data directory is huge or missing**
  - Provide a realistic `storage_dir` or equivalent dataset root before starting stage 0.
  - When in doubt, use a dry-run or a config review rather than attempting a full download.

## Safe recipe review habits

- Prefer reading the stage flow and config first.
- Prefer a tiny synthetic `System` smoke for environment checks.
- When you only need a self-contained runtime check, prefer `scripts/smoke_training.py` from the root skill.
- Keep the original repo's heavy data download and training steps out of the public runtime skill unless the user explicitly needs them.
