# Troubleshooting

## `--dataset` is required

### Symptom
- `scripts/train.py` exits with argparse usage text.

### Likely cause
- The training parser requires at least one dataset name.

### Recovery
- Pass `--dataset` / `-dt` explicitly.
- For quick command construction, run `scripts/cogdl_cli_smoke.py` first to confirm the parser shape.

## Unknown model or dataset

### Symptom
- `NotImplementedError: Failed to import ... model.`
- `NotImplementedError: Failed to import ... dataset.`

### Likely cause
- The name is not in the supported registry or the wrapper/model pair is incomplete.

### Recovery
- Check the model and dataset names against the verified registries.
- If the model has no default wrapper, pass `--mw` and `--dw` explicitly.
- If the user only needs a plan, do not execute training until the registry and wrapper choices are known.

## Wrapper mismatch or missing wrapper

### Symptom
- `NotImplementedError("`model wrapper(--mw)` must be specified.")`
- `NotImplementedError("`data wrapper(--dw)` must be specified.")`

### Likely cause
- The selected model does not map to the default wrapper configuration.
- The user overrode a wrapper name that is not compatible with the model.

### Recovery
- Use the wrapper defaults table in `references/api-and-cli.md`.
- Route wrapper-specific debugging to `training-wrappers-and-customization` when the issue is not just a CLI choice.

## Dataset download or cache writes

### Symptom
- First use of a built-in dataset triggers a download or on-disk processing.

### Likely cause
- CogDL dataset loaders populate raw/processed files on demand.

### Recovery
- Warn the user before running when network or cache writes are not allowed.
- Prefer a no-network dry plan, or use a previously cached dataset.
- If the user asks for a command only, make the download dependency explicit instead of pretending the run is offline.

## Checkpoint, embedding, and log writes

### Symptom
- The run fails when creating `--checkpoint-path`, `--save-emb-path`, or `--log-path` outputs.

### Likely cause
- The target directory does not exist or is not writable.

### Recovery
- Choose writable paths before running.
- Remember that `resume_training` only works when the checkpoint matches the current model shape and compatible training settings.
- Treat these flags as file-write surfaces, not read-only metadata.

## CPU vs GPU device flags

### Symptom
- A user passes `--devices` but expects CPU behavior.

### Likely cause
- `--devices` is a GPU-selection flag; `--cpu` is the explicit CPU override.
- Distributed settings and device settings interact with the trainer, not the parser.

### Recovery
- Use `--cpu` for the safest fallback plan.
- Mention `--devices` only when GPU execution is intended and available.
- Do not claim CUDA acceleration is verified unless the environment actually exposes it.

## Optuna / matplotlib compatibility

### Symptom
- AutoML import or plotting-adjacent compatibility problems appear in modern environments.

### Likely cause
- The repository's Optuna stack can be sensitive to newer matplotlib releases.

### Recovery
- Treat Optuna as an optional dependency surface.
- If the user only wants a plan, describe the `search_space(trial)` contract without executing it.
- If a run needs Optuna and the environment is unstable, stop and report the dependency issue rather than pretending the search worked.

## Validation-metric confusion in AutoML

### Symptom
- AutoML raises `KeyError("Unable to find validation metrics")`.

### Likely cause
- The result dictionary did not expose a key containing `Val` or `val`, and no explicit `metric` was provided.

### Recovery
- Set `metric=` explicitly when the result schema is known.
- Confirm the selected task prints a validation metric before running `n_trials`.
