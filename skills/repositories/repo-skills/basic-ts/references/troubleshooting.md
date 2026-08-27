# BasicTS Troubleshooting

## Purpose

Use this reference when a BasicTS workflow fails but you have not yet narrowed the issue to one sub-skill.

## Cross-cutting issues

### Install or import failures

**Symptoms**
- `ImportError` for `basicts`
- missing dependencies such as `easy-torch`, `einops`, `pandas`, or `tables`
- `python -m pip check` reports a broken environment

**Likely cause**
- the package was not installed into the environment you are using
- the environment is missing the runtime dependencies required by BasicTS or the smoke tests

**Recovery**
- Re-run the install check script.
- Confirm the environment Python is the one you expect.
- Reinstall the package and runtime dependencies in the same prefix if necessary.

### Dataset path confusion

**Symptoms**
- `FileNotFoundError` while loading `train_data.npy`, `train_inputs.npy`, or `shape.npy`
- a dataset works in one example but not another

**Likely cause**
- `dataset_name` does not match the folder on disk
- `dataset_params["data_file_path"]` points somewhere else
- the chosen dataset class does not match the file family

**Recovery**
- Check the file layout first.
- Then choose the matching dataset class.
- Use the data-preparation sub-skill to validate the folder.

### Checkpoint confusion

**Symptoms**
- `OSError: Ckpt file does not exist`
- evaluation reloads the wrong file

**Likely cause**
- the checkpoint path was guessed instead of copied from the run directory
- the run directory was removed or never written

**Recovery**
- Locate the actual checkpoint file in the run directory.
- Pass that exact path to the evaluation call.
- Keep `ckpt_save_dir` stable if you need to re-run evaluation later.

### CPU/GPU mismatch

**Symptoms**
- a run stays on CPU when you expected GPU
- CUDA is unavailable in the inspection environment

**Likely cause**
- `gpus=None`
- the inspection environment is intentionally CPU-only

**Recovery**
- Treat the CPU environment as a contract-check environment.
- Move to a GPU-capable environment only when the workflow truly needs it.

### Callback and metric extension failures

**Symptoms**
- hook methods do not fire
- custom metrics cannot find `prediction` or `targets`
- auxiliary losses are ignored

**Likely cause**
- the wrong hook name or callback class was used
- the forward return keys do not match the metric or callback expectations

**Recovery**
- Use `pipeline-extension` for the hook contract.
- Verify the model's output keys.
- Match the metric signature to the keys you actually return.

### Model contract failures

**Symptoms**
- the runner cannot call the model
- the model returns a tensor with the wrong shape
- timestamps or masks are missing

**Likely cause**
- the model does not accept `inputs`
- the model signature and dataset/taskflow do not agree on optional keys

**Recovery**
- Use `model-development` to inspect the forward contract.
- Make sure the taskflow supplies the keys the model expects.

## First checks to run

1. Confirm the package imports.
2. Confirm the dataset folder format.
3. Confirm the checkpoint path.
4. Confirm the model's `forward` contract.
5. Confirm the callback/metric/scaler hook names if you extended the pipeline.

## Useful bundled helpers

- `scripts/check_basic_ts_install.py`
- `sub-skills/training-evaluation/scripts/run_mini_forecasting_smoke.py`
- `sub-skills/data-preparation/scripts/validate_basicts_dataset.py`
- `sub-skills/model-development/scripts/check_model_contract.py`
- `sub-skills/pipeline-extension/scripts/inspect_pipeline_contract.py`
