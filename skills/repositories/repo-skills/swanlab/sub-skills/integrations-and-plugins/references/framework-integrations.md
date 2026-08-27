# Framework integrations

Use this reference when the user wants a SwanLab callback/logger inside a training framework. Keep base `swanlab.init`, credential setup, media object details, and sync/export topics in the sibling skills.

## Shared adapter rules

- Import adapters from their module-specific paths; the integration package root is not an aggregate export surface.
- Most adapters accept familiar SwanLab init kwargs such as `project`, `workspace`, `experiment_name`, `description`, `log_dir`, `mode`, and `tags`; legacy `logdir` is accepted by many adapters but should be replaced with `log_dir`.
- If the adapter can auto-init, it starts or reuses a SwanLab run on the first framework hook. If the user already calls `swanlab.init(...)`, the adapter normally reuses that active run.
- Distributed adapters guard logging on rank zero, world-process-zero, or the framework's main-process hook. Do not add extra `swanlab.log(...)` calls in every worker unless the user intentionally wants per-worker runs.
- Optional framework packages are not SwanLab's base dependencies. An import error that names `accelerate`, `lightning`, `mmengine`, `paddlenlp`, `ray[tune]`, or another framework means the training environment is missing that framework.

## Adapter map

| Framework | Import | Attach point | Key behavior and caveats |
| --- | --- | --- | --- |
| Hugging Face Transformers | `from swanlab.integration.transformers import SwanLabCallback` | `Trainer(..., callbacks=[SwanLabCallback(...)])` | Rewrites keys into `train/`, `eval/`, `test/`, logs one-shot values under `single_value/`, records `transformers_last_checkpoint`, auto-inits, and logs only when `state.is_world_process_zero` is true. |
| PaddleNLP | `from swanlab.integration.paddlenlp import SwanLabCallback` | PaddleNLP `Trainer` callbacks | Mirrors the Transformers adapter, including metric rewriting, pending config flush, checkpoint path capture, auto-init, and main-process guard. |
| PyTorch Lightning | `from swanlab.integration.pytorch_lightning import SwanLabLogger` | `Trainer(logger=SwanLabLogger(...))` | Implements the Lightning logger interface: `experiment`, `log_hyperparams`, `log_metrics`, `log_image`, `log_audio`, `log_text`, `finalize`. Uses Lightning rank-zero wrappers. `finalize` calls `swanlab.finish()` and warns on non-success status. |
| Keras | `from swanlab.integration.keras import SwanLabCallback` | `model.fit(..., callbacks=[SwanLabCallback(...)])` | Supports `log_freq="epoch"`, `"batch"`, or a positive integer; tracks global step, learning rate when available, and pending config; auto-inits on first log hook. |
| FastAI | `from swanlab.integration.fastai import SwanLabCallback` | Add to the learner callback list | Captures learner metadata/config in `before_fit`, logs batch/epoch metrics, and auto-inits if needed. Use only on the learner that actually trains. |
| Stable-Baselines3 | `from swanlab.integration.sb3 import SwanLabCallback` | `model.learn(callback=SwanLabCallback(...))` | Installs a SwanLab output format alongside the SB3 logger, logs numeric records, and captures model hyperparameters. |
| Accelerate | `from swanlab.integration.accelerate import SwanLabTracker` | `Accelerator(log_with=SwanLabTracker(...))` or the tracker path expected by Accelerate | Implements `GeneralTracker`: `store_init_configuration`, `log`, and `finish`. Uses `main_process_only` so distributed workers do not duplicate metrics. |
| MMEngine | `custom_imports = dict(imports=["swanlab.integration.mmengine"], allow_failed_imports=False)` plus `type="SwanlabVisBackend"` | MMEngine visualizer backend config | Registers `SwanlabVisBackend`, auto-inits from `init_kwargs`, flattens config dictionaries, and forwards scalar/image calls. |
| Ultralytics | `from swanlab.integration.ultralytics import add_swanlab_callback, return_swanlab_callback` | `add_swanlab_callback(model, ...)` or return callback dict for Ultralytics callback registration | Logs train/validation metrics and plots, de-duplicates plots by timestamp, and auto-inits if no active run exists. |
| Ray Tune | `from swanlab.integration.ray import SwanLabLoggerCallback` | `tune.RunConfig(callbacks=[SwanLabLoggerCallback(...)])` | Starts one logging actor per trial, queues result dictionaries, filters unsupported values, and requires a `project` argument or `SWANLAB_PROJ_NAME`. Missing Ray should suggest `pip install 'ray[tune]'`. |
| Torchtune | `from swanlab.integration.torchtune import SwanLabLogger` | Torchtune `MetricLoggerInterface` slot | Uses rank 0 only, logs config/dicts/scalars, resolves OmegaConf-like config objects when possible, and finishes on `close()`. |
| LightGBM | `from swanlab.integration.lightgbm import SwanLabCallback` | Add `SwanLabCallback(...)` to LightGBM callbacks | Records `FRAMEWORK=lightgbm`, optionally logs params, and logs evaluation tuples with dataset/metric names. Requires an active SwanLab run before the callback can log. |
| XGBoost | `from swanlab.integration.xgboost import SwanLabCallback` | XGBoost training callback list | Logs model config, evaluation metrics, and optionally feature-importance charts with `importance_type` defaulting to `gain`. |
| CatBoost | `from swanlab.integration.catboost import SwanLabCallback` | CatBoost callback API | Records optional params once, sets `FRAMEWORK=catboost`, and logs the latest metric values per stage. Requires an active SwanLab run. |

## Choosing auto-init versus explicit init

Use explicit initialization when the user needs precise settings, credentials, local/offline/disabled mode, or shared callbacks:

```python
import swanlab
from swanlab.plugin import CSVWriter
from swanlab.integration.transformers import SwanLabCallback

csv = CSVWriter(dir="reports", filename="runs.csv")
swanlab.init(project="demo", mode="offline", callbacks=[csv])
trainer.add_callback(SwanLabCallback())
```

Use adapter auto-init when the framework owns the lifecycle and the only SwanLab-specific inputs are simple init kwargs:

```python
from swanlab.integration.keras import SwanLabCallback

model.fit(train_data, callbacks=[SwanLabCallback(project="demo", mode="offline")])
```

## Optional dependency interpretation

- Import errors raised while importing an adapter are environment errors. Install the named framework package in the training environment before changing callback arguments.
- Some modules load without the framework package because the package is only needed once the framework invokes hooks. The user still needs the framework installed for real training.
- For package names with import/distribution spelling differences, install the framework's normal distribution name even if the Python import uses underscores, for example Stable-Baselines3 imports as `stable_baselines3`.

## Response checklist

When answering an integration request:

1. Name the exact adapter class or helper.
2. Show the module-specific import line.
3. State whether the adapter auto-inits or expects an active run.
4. Call out distributed rank/main-process behavior.
5. Mention missing framework packages before debugging SwanLab settings or callback arguments.
