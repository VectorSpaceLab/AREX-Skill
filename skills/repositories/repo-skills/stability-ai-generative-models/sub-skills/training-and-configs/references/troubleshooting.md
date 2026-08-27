# Training and Config Troubleshooting

Use this reference to map config and launcher symptoms to safe recoveries. Prefer the bundled static helper before running `main.py`.

## Missing `target` Key

Symptom:

```text
KeyError: Expected key `target` to instantiate.
```

Likely cause:

- A config object passed to `instantiate_from_config` lacks `target`.
- A nested object under `model.params` has `params` but no `target`.
- A YAML merge accidentally replaced a full target config with only its params.

Recovery:

- Inspect the merged config with `inspect_training_config.py`.
- Add `target: dotted.import.Class` at the object that is being instantiated.
- For optional first-stage/unconditional sentinels, use exactly `__is_first_stage__` or `__is_unconditional__`; do not use arbitrary strings.

## Import Target Typo

Symptoms:

```text
ModuleNotFoundError
ImportError
AttributeError: module ... has no attribute ...
```

Likely cause:

- `target` path has a typo or points to a class not exported by that module.
- The command is not launched from a context where `main.ImageLogger` or `main.SetupCallback` can resolve.
- Optional dependencies for a target are missing.

Recovery:

- Compare the target against `references/api-reference.md`.
- For `main.*` targets, run training as `python main.py` from a setup where the launcher appends the current working directory to `sys.path`.
- For optional packages such as `sdata`, `wandb`, `open_clip`, `transformers`, `xformers`, or webdataset tooling, decide whether the config actually needs that target before installing anything.

## Config Merge Surprise

Symptoms:

- A dotlist override seems ignored.
- A later YAML file unexpectedly changes a nested target.
- Training uses a different batch size, learning rate, or callback than expected.

Likely cause:

- Merge order is left-to-right for `--base`, then CLI dotlist last.
- `lightning` is popped from the project config and handled separately.
- CLI options with leading dashes are parsed as launcher/trainer args, not dotlist config values.

Recovery:

- Re-run the helper with the exact `--config` order and `--dotlist` tokens.
- Use `key=value` dotlist syntax for config paths.
- Quote shell-sensitive values such as lists, commas, and spaces.
- Keep experiment-specific overrides near the command so the final merged state is visible.

## Dotlist Syntax Errors

Symptoms:

- OmegaConf parse errors.
- Values become strings when numbers/lists were expected.
- Shell expands brackets or commas unexpectedly.

Recovery:

- Use simple scalar overrides where possible: `model.base_learning_rate=5e-5`.
- Quote complex values: `'model.params.log_keys=[txt]'`.
- For Lightning devices, preserve the format expected by the installed Lightning version; examples use `lightning.trainer.devices=0,`.
- If many nested values must change, create a small override YAML and pass it as a later `--base` file.

## Resume Path Invalid

Symptoms:

```text
ValueError: Cannot find ...
AssertionError: ...
IndexError from checkpoint discovery
```

Likely cause:

- `--resume` path does not exist.
- A logdir has no `checkpoints/last**.ckpt` file.
- A checkpoint path is not inside the expected logdir layout.

Recovery:

- Confirm whether the user means same-logdir resume or new-logdir resume.
- For same-logdir resume, use `python main.py --resume logs/run-name` only after checking the logdir has `configs/*.yaml` and `checkpoints/last*.ckpt`.
- For new-logdir resume, use `--base config.yaml -n new_name --resume_from_checkpoint path/to.ckpt`.
- Do not inspect checkpoint tensors or download replacements unless the task explicitly requires it.

## `--name` and `--resume` Conflict

Symptom:

```text
ValueError: -n/--name and -r/--resume cannot be specified both.
```

Recovery:

- Remove `--name` when resuming into the original logdir.
- Use `--resume_from_checkpoint` with `--name` when creating a new log folder from a checkpoint.

## GPU Defaults and Lightning Device Issues

Symptoms:

- Trainer attempts to use GPU unexpectedly.
- `devices` parsing errors.
- CPU-only host fails during trainer setup.

Likely cause:

- The launcher sets `lightning.trainer.accelerator` to `gpu` by default.
- Example configs use `devices: 0,`, which may be interpreted differently across Lightning versions.
- CLI trainer args override config only when they differ from Trainer defaults.

Recovery:

- For static validation, do not run `main.py`; use the helper.
- For CPU-only execution, explicitly set compatible trainer args for the installed Lightning version.
- For GPU execution, confirm `CUDA_VISIBLE_DEVICES`, `accelerator`, and `devices` formatting with the local Lightning version.

## Missing Checkpoint Placeholder

Symptoms:

- File-not-found when constructing `AutoencoderKL` or loading `ckpt_path`.
- A config still contains `CKPT_PATH`.

Recovery:

- Treat `CKPT_PATH` as a required user-provided local path.
- Keep placeholder detection in the static report until the path is supplied.
- Avoid downloading checkpoints as verification; ask the user for an existing path or leave a command template.

## Dataset and WebDataset Placeholder Problems

Symptoms:

- `DATA_PATH` remains in config.
- `sdata` import failure.
- Data pipeline errors about missing URLs, missing keys, or mapper inputs.
- Text/image conditioning keys do not exist in batches.

Likely cause:

- Large configs assume `StableDataModuleFromConfig` plus `sdata` pipelines.
- USER placeholders in `urls`, mapper `key`, `height`, `width`, `txt`, or `cls` were not adapted.
- Validation/test falls back to train config when validation is absent.

Recovery:

- Replace `DATA_PATH` with explicit shard URLs or local files supplied by the user.
- Check mapper outputs against `GeneralConditioner` `input_key` values.
- Reduce shuffle buffers and workers for small local tests.
- Do not import or instantiate `sgm.data.dataset` as validation when `sdata` may be missing; static parse first.

## Train/Test Side Effects

Symptoms:

- `main.py` starts model construction, dataset preparation, downloads, logging, or GPU setup even when the user expected a dry run.
- `trainer.test` starts after training.

Cause:

- The launcher instantiates model/data, calls `data.prepare_data()`, and then runs `trainer.fit` if `--train true`.
- `--no-test` only disables post-training test; it does not prevent model/data construction.

Recovery:

- Use `inspect_training_config.py` for dry checks.
- If executing a minimal run is necessary, set `--train false --no-test true` only with the caveat that instantiation and data preparation can still happen.
- Disable or minimize callbacks that write files or images.

## PyTorch Lightning Version Differences

Symptoms:

- Unsupported trainer args.
- Changed `resume_from_checkpoint` behavior.
- Strategy/callback API mismatches.

Recovery:

- Inspect installed Lightning docs/version before recommending execution-specific flags.
- Prefer config/static reasoning in the skill.
- Move incompatible trainer settings into a small override YAML so they can be adjusted per environment.
- Remember `main.py` conditionally adds `--resume_from_checkpoint` based on Torch version, while Lightning semantics can still vary.

## WandB Optional, Offline, and Debug Behavior

Symptoms:

- WandB import/login errors.
- Unexpected online logging.
- Debug runs move log directories.

Recovery:

- Default to CSV logging by leaving `--wandb false`.
- Use `--debug true` only when interactive debugging is desired; it makes WandB offline when WandB is enabled and moves new debug logs under `debug_runs`.
- For air-gapped machines, keep `lightning.logger` on `CSVLogger` or set WandB offline explicitly.

## xFormers Absent or Attention Fallback Needed

Symptoms:

- Import or runtime errors around `softmax-xformers` or `vanilla-xformers`.
- Attention implementation not available on the host.

Likely cause:

- Example large configs request xFormers-backed attention in `network_config.params.spatial_transformer_attn_type` or first-stage `ddconfig.attn_type`.

Recovery:

- Do not install xFormers as part of static validation.
- If the local environment lacks xFormers, change attention type to a supported non-xFormers variant only after confirming compatibility with the model architecture.
- Document that checkpoint compatibility and memory use may change when attention implementations change.

## Learning Rate Scaling Surprises

Symptoms:

- Actual learning rate differs from `model.base_learning_rate`.

Cause:

- With `--scale_lr true`, the launcher computes `accumulate_grad_batches * ngpu * batch_size * base_learning_rate`.
- Batch size may be under `data.params.batch_size` or `data.params.train.loader.batch_size` depending on data module shape.

Recovery:

- Leave `--scale_lr false` for direct use of `base_learning_rate`.
- If scaling, verify `devices`, `accumulate_grad_batches`, and batch size in the merged config.

## Conditioner/Data Key Mismatch

Symptoms:

```text
KeyError: 'txt'
KeyError: 'cls'
KeyError: 'original_size_as_tuple'
```

Likely cause:

- `GeneralConditioner` embedders request keys not emitted by the data pipeline.
- USER mapper fields were not adjusted for a custom dataset.

Recovery:

- List every `conditioner_config.params.emb_models[*].input_key` or `input_keys`.
- Confirm the data module returns those keys.
- For webdataset configs, confirm postprocessors create `jpg`, `txt`, `original_size_as_tuple`, and `crop_coords_top_left` as required.

## Sampler or Loss Missing for Training

Symptom:

```text
ValueError: Sampler and loss function need to be set for training.
```

Cause:

- `DiffusionEngine` was instantiated with no `sampler_config` or no `loss_fn_config`.

Recovery:

- Add a sampler target such as `sgm.modules.diffusionmodules.sampling.EulerEDMSampler`.
- Add `StandardDiffusionLoss` with `sigma_sampler_config` and `loss_weighting_config`.
- Inspect statically before attempting another run.
