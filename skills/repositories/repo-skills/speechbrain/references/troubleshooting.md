# Cross-cutting SpeechBrain troubleshooting

Use this reference for failures that are not owned by a single workflow. For workflow-specific problems, continue to the relevant sub-skill troubleshooting page.

## Import fails before any SpeechBrain code runs

Symptoms:

- `ModuleNotFoundError: No module named 'torch'`
- `ModuleNotFoundError: No module named 'hyperpyyaml'`
- `ImportError` from optional integrations

Recovery:

1. Confirm you are running the intended Python environment: `python -c "import sys; print(sys.executable); print(sys.version)"`.
2. Install the base package dependencies or reinstall SpeechBrain in the active environment.
3. Run `python -m pip check`.
4. For Hugging Face integration errors, install `transformers` only if the selected workflow needs HF model wrappers.
5. Do not install all recipe extras unless the selected recipe specifically needs them.

## Torch/Torchaudio mismatch

Symptoms:

- `ImportError` or shared-library errors importing `torch` or `torchaudio`.
- `torch.cuda.is_available()` is false despite visible GPUs.
- `torchaudio` version does not match Torch.

Recovery:

1. Install Torch and Torchaudio from the same release and backend family.
2. For CPU-only checks, use CPU wheels and do not expect CUDA availability.
3. For CUDA tasks, verify the driver and wheel/toolkit compatibility before installing SpeechBrain.
4. Run a small allocation probe on the target backend before attempting a recipe.

## Audio file loading or saving fails

Symptoms:

- `RuntimeError: Failed to load audio from ...`
- Unsupported format/codec errors.
- Unexpected channel/time tensor shape.

Recovery:

1. Use `from speechbrain.dataio import audio_io`; prefer `audio_io.load`, `audio_io.save`, and `audio_io.info`.
2. Check `audio_io.info(path)` to confirm sample rate, frames, channels, subtype, and format.
3. For mono/stereo shape issues, set `channels_first` and `always_2d` intentionally.
4. Convert unsupported formats to WAV/FLAC before loading.
5. Run `python sub-skills/data-audio-pipelines/scripts/audio_io_roundtrip.py` to isolate package/backend issues from user data issues.

## HyperPyYAML fails to load

Symptoms:

- `!PLACEHOLDER` errors.
- Import errors from `!new:` or `!name:` tags.
- Overrides appear ignored.

Recovery:

1. Remember that HyperPyYAML can construct Python objects; treat untrusted YAML as executable code.
2. Replace every `!PLACEHOLDER` through command-line overrides or by editing the YAML.
3. Keep recipe command ordering as `python train.py hparams.yaml --override value`.
4. Use `speechbrain.parse_arguments` / `RunOptions.from_command_line_args` semantics: known runtime options become run options; unknown names become YAML override text.
5. Validate paths relative to the working directory used to launch the recipe.

## Pretrained model fetch fails

Symptoms:

- Hugging Face download/auth errors.
- Symlink/copy failures in model cache.
- `foreign_class` fails to import custom code.

Recovery:

1. Decide whether network access is allowed. If not, use a local model folder and `FetchConfig(allow_network=False)`.
2. Pin revisions for reproducible remote loads.
3. Use `LocalStrategy.COPY` if symlink creation is not allowed.
4. Use `foreign_class` only for trusted sources because it downloads and executes external Python code.
5. Separate model fetch/cache errors from model forward-pass errors by first running `download_only=True` where appropriate.

## Recipe scripts are slow or download large data

Symptoms:

- Recipe starts downloading a dataset or pretrained checkpoint unexpectedly.
- Training runs for too long during a smoke check.
- GPU memory errors on full recipes.

Recovery:

1. Use the recipe README and `tests/recipes/*.csv` debug flags to find a tiny-data path.
2. Prefer `--skip_prep=True` when using already prepared fixtures or when data prep is out of scope.
3. Use `--debug`, `--debug_batches`, `--debug_epochs`, or recipe-specific small overrides before a full run.
4. Install only the selected recipe's `extra_requirements.txt`.
5. For CUDA/DDP, validate a single-GPU run before `torchrun`.

## Distributed or multi-GPU launch hangs

Symptoms:

- Processes wait forever around data preparation or checkpointing.
- DDP/NCCL errors on startup.
- Batch size is unexpectedly multiplied by number of GPUs.

Recovery:

1. Use `torchrun` for DDP; avoid PyTorch `DataParallel` for new work.
2. Ensure dataset preparation runs through `run_on_main` or equivalent main-process guards.
3. In DDP, batch size is per process/GPU, not divided across GPUs as in `DataParallel`.
4. For multi-node runs, verify `--nnodes`, `--node_rank`, `--master_addr`, and `--master_port`.
5. Use `speechbrain.utils.distributed.infer_device()` and logged rank-prefixed messages to debug device placement.
