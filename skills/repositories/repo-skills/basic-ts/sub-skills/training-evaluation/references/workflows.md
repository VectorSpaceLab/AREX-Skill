# Training and Evaluation Workflows

## Purpose

Read this reference when you need to launch a BasicTS run, choose a task config, evaluate a checkpoint, or understand the high-level flow from config to runner.

## Verified entry points

- `BasicTSLauncher.launch_training(cfg: BasicTSConfig, node_rank: int = 0) -> None`
- `BasicTSLauncher.launch_evaluation(cfg, ckpt_path, gpus=None, batch_size=None)`
- Package version inspected from the installed environment: `1.1.0`

## Task config map

| Task | Config class | Typical dataset class | Notes |
| --- | --- | --- | --- |
| Forecasting | `BasicTSForecastingConfig` | `BasicTSForecastingDataset` | Default path for ETT/PEMS-style time-series forecasting. |
| Classification | `BasicTSClassificationConfig` | `UEADataset` | Uses UEA-style inputs and class labels. |
| Imputation | `BasicTSImputationConfig` | `BasicTSImputationDataset` | Uses masked reconstruction on time series. |
| Foundation model | `BasicTSFoundationModelConfig` | `BasicTSForecastingDataset` | Step-based training defaults and long-horizon style settings. |

## Minimal launch pattern

```python
from basicts import BasicTSLauncher
from basicts.configs import BasicTSForecastingConfig
from basicts.models.DLinear import DLinear, DLinearConfig

model_config = DLinearConfig(input_len=8, output_len=4, num_features=2)

cfg = BasicTSForecastingConfig(
    model=DLinear,
    model_config=model_config,
    dataset_name="tiny_forecasting_smoke",
    input_len=8,
    output_len=4,
    use_timestamps=False,
    gpus=None,
    num_epochs=1,
    batch_size=2,
)

BasicTSLauncher.launch_training(cfg)
```

## How the config is packed

The config classes collect task-specific defaults and shortcut fields before the runner starts.

- `model` and `model_config` are required.
- `dataset_name` identifies the dataset folder or logical name.
- `input_len`, `output_len`, `mask_ratio`, `use_timestamps`, and `batch_size` act as shortcuts for the dataset and runner.
- `ckpt_save_dir` defaults to a checkpoint path under `checkpoints/<model>/<dataset>...` unless you override it.
- `gpus=None` means CPU mode.

## Launching evaluation

Use `launch_evaluation` when you already know the checkpoint file you want to inspect.

```python
BasicTSLauncher.launch_evaluation(cfg, ckpt_path="/path/to/model_best_val_MAE.pt")
```

Common evaluation notes:

- If you pass `gpus`, the launcher switches to GPU mode for evaluation.
- If you do not pass `gpus`, evaluation runs on CPU.
- `batch_size` overrides the test batch size only for that evaluation call.
- The checkpoint path must exist and point to a saved BasicTS checkpoint.

## What happens during training

1. The launcher saves the config for the run.
2. The runner builds the model, dataset, scaler, optimizer, scheduler, and data loaders.
3. Training proceeds through the runner's taskflow and callback hooks.
4. Validation and testing run according to the config intervals.
5. Checkpoints are written under the configured checkpoint directory.
6. If `eval_after_train=True`, the best validation checkpoint is evaluated after training.

## Safe CPU smoke pattern

For a low-risk smoke test, use a temporary tiny dataset and a one-epoch CPU run.

- Keep `gpus=None`.
- Set `num_epochs=1`.
- Use a tiny batch size such as `2`.
- Use a built-in simple forecasting model such as `DLinear`.
- Keep the dataset in a temporary directory so the check does not depend on the source checkout.

The bundled helper `scripts/run_mini_forecasting_smoke.py` follows this pattern.

## Common launch choices

- **Forecasting**: use `BasicTSForecastingConfig` with `input_len`, `output_len`, and optional timestamps.
- **Classification**: use `BasicTSClassificationConfig` with a model head that returns class logits.
- **Imputation**: use `BasicTSImputationConfig` with `mask_ratio` and a reconstruction-capable model.
- **Foundation models**: use `BasicTSFoundationModelConfig` when the workflow is step-based and the model expects its own training defaults.

## When to stop and switch sub-skills

- If the user needs the dataset folder format, go to `data-preparation`.
- If the user needs to alter the model's forward contract, go to `model-development`.
- If the user needs to add callbacks, metrics, or custom taskflow logic, go to `pipeline-extension`.

## Verification cues used for this reference

- Source inspection of `src/basicts/launcher.py` and `src/basicts/configs/*.py`
- Runner behavior in `src/basicts/runners/basicts_runner.py`
- Installed-package signature inspection in the prepared CPU environment
- CPU smoke conventions from `tests/smoke_test/*.py`
