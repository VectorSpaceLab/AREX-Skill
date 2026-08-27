# Troubleshooting

## Purpose

Use this reference when a BasicTS launch or evaluation run fails, the checkpoint cannot be found, or a config choice does not match the dataset.

## Common failures

### 1) Dataset files are missing

**Symptoms**
- `FileNotFoundError` from `BasicTSForecastingDataset`, `BasicTSImputationDataset`, or `UEADataset`
- a message about not being able to load `train_data.npy`, `test_inputs.npy`, or a similar file

**Likely cause**
- `dataset_name` points to a folder that does not exist
- `dataset_params["data_file_path"]` is wrong or omitted
- the dataset type does not match the file layout on disk

**Recovery**
- Verify the dataset folder exists.
- Confirm the file naming convention for the selected task.
- If you are using a temporary fixture, make sure the helper wrote all required split files.

### 2) GPU or MLU flags are confusing the launcher

**Symptoms**
- a `ValueError` about `gpus` and `mlus`
- the run starts on a different device than expected

**Likely cause**
- both GPU and MLU settings were supplied
- the config still carries a device setting from an earlier example

**Recovery**
- Use `gpus=None` for CPU smoke.
- Set only one device family at a time.
- Re-run the config with a clean set of launcher arguments.

### 3) `num_epochs` and `num_steps` are both set

**Symptoms**
- a `ValueError` mentioning that `num_epochs` and `num_steps` cannot both be set

**Likely cause**
- the config copied defaults from two examples

**Recovery**
- Choose one training unit.
- Use `num_epochs` for ordinary smoke runs.
- Use `num_steps` only for step-based foundation-model style runs.

### 4) Evaluation cannot find the checkpoint

**Symptoms**
- `OSError: Ckpt file does not exist`
- evaluation silently reloads the wrong checkpoint path

**Likely cause**
- `launch_evaluation` received an invalid `ckpt_path`
- the checkpoint directory was cleaned up after training
- the best-validation checkpoint name was mis-typed

**Recovery**
- Locate the actual checkpoint file under the run's checkpoint directory.
- Pass that exact path to `launch_evaluation`.
- If you want the best checkpoint after training, make sure validation ran and the run directory still exists.

### 5) Forecasting timestamps do not match the model or dataset

**Symptoms**
- tensor shape errors in the forward pass
- a model complains about missing `inputs_timestamps` or `targets_timestamps`

**Likely cause**
- `use_timestamps` does not match the dataset files
- the chosen model expects timestamps but the fixture does not provide them

**Recovery**
- Either provide timestamps in the dataset fixture or disable `use_timestamps`.
- Match the model choice to the available dataset fields.

### 6) Batch size expectations are inconsistent

**Symptoms**
- train/val/test loaders use a different batch size than you expected
- a copied example appears to ignore the value you changed

**Likely cause**
- the top-level `batch_size` shortcut overrides the per-loader defaults

**Recovery**
- Use `batch_size` when you want one value for all loaders.
- Use `train_batch_size`, `val_batch_size`, and `test_batch_size` only when you want different values.

### 7) The run looks CPU-only

**Symptoms**
- CUDA is not used even though you expected it
- `torch.cuda.is_available()` is false

**Likely cause**
- the config left `gpus=None`
- the environment is the CPU smoke environment used by this skill draft

**Recovery**
- Treat the CPU smoke as a launch-path check, not as GPU verification.
- Move to a GPU-capable environment only when the task truly needs GPU execution.

## What to check first

1. The dataset folder and file names.
2. The task config class.
3. The checkpoint path.
4. The device flags.
5. Whether you used `num_epochs` or `num_steps`.

## When to switch sub-skills

- Dataset layout or fixture generation issues → `data-preparation`
- Custom model outputs or `forward` signature issues → `model-development`
- Callback, metric, scaler, or taskflow hook issues → `pipeline-extension`
