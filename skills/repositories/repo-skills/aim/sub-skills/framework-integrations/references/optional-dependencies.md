# Optional dependency boundaries

Aim's base SDK can track values directly, but most framework adapters require the user's training framework to be installed. Do not install broad ML stacks unless the user explicitly wants that framework callback or a live training check.

## Safe diagnostic workflow

1. Check the user's requested framework and whether the adapter is necessary.
2. Run a lightweight package presence check before importing heavy frameworks:

   ```bash
   python scripts/aim_integration_snippets.py --check-optional
   ```

3. If the user wants an adapter import check and accepts framework import side effects, add:

   ```bash
   python scripts/aim_integration_snippets.py --check-optional --import-adapters
   ```

4. If a package is missing, either install only the needed optional dependency in the user's environment or switch to direct `Run.track` fallback.
5. Do not treat missing optional dependencies as a base Aim failure.

## Adapter dependency table

| Capability | Public import | Required optional package import(s) | Typical package name(s) | Import behavior when missing | Notes |
| --- | --- | --- | --- | --- | --- |
| Plain PyTorch loop helpers | `from aim.pytorch import track_params_dists, track_gradients_dists` | `torch` is needed by the user's model, not by the helper import itself | `torch` | Helper module is lightweight; model code fails if PyTorch is absent | Use with direct `Run.track`; no training callback is provided for plain PyTorch. |
| PyTorch Ignite | `from aim.pytorch_ignite import AimLogger` | `torch`, `ignite` | `torch`, `pytorch-ignite` | Aim raises `RuntimeError` asking to install PyTorch or PyTorch Ignite | Use `attach_output_handler` and `attach_opt_params_handler`. |
| PyTorch Lightning / Lightning | `from aim.pytorch_lightning import AimLogger` | `lightning` or `pytorch_lightning` | `lightning` or `pytorch-lightning` | Aim raises `RuntimeError` asking to install `pytorch-lightning` or `lightning` | Adapter prefers the `lightning` package when present, then falls back to `pytorch_lightning`. |
| Hugging Face Transformers | `from aim.hugging_face import AimCallback` | `transformers` | `transformers` | Aim raises `RuntimeError` asking to install Transformers | Logs numeric trainer values only; non-numeric payloads need direct tracking. |
| Keras | `from aim.keras import AimCallback` | `keras` | `keras` | Aim raises `RuntimeError` asking to install Keras | Uses standalone Keras callback import. |
| TensorFlow Keras | `from aim.tensorflow import AimCallback` | `tensorflow` | `tensorflow` | Aim raises `RuntimeError` asking to install TensorFlow | Uses `tensorflow.keras.callbacks.Callback`. |
| Keras Tuner | `from aim.keras_tuner import AimCallback` | `kerastuner` | `keras-tuner` | Aim raises `RuntimeError` asking to install Keras Tuner | Pass the active tuner instance to the callback. |
| XGBoost | `from aim.xgboost import AimCallback` | `xgboost` | `xgboost` | Aim raises `RuntimeError` asking to install XGBoost | Native `TrainingCallback`. |
| CatBoost | `from aim.catboost import AimLogger` | `catboost` for actual training | `catboost` | Adapter import can succeed without CatBoost because it is a log handler; training import fails if CatBoost is absent | Pass logger through CatBoost `log_cout`. |
| LightGBM | `from aim.lightgbm import AimCallback` | `lightgbm` | `lightgbm` | Aim raises `RuntimeError` asking to install LightGBM | Native LightGBM callback with `order=25`. |
| Optuna | `from aim.optuna import AimCallback` | `optuna` | `optuna` | Missing Optuna is a normal Python import failure before callback construction | Callback itself is marked experimental by Optuna decorators. |
| fastai | `from aim.fastai import AimCallback` | `fastai`, `fastcore` | `fastai` | Aim raises `RuntimeError` asking to install fastai | Gathers learner configuration and logs recorder metrics. |
| PaddlePaddle | `from aim.paddle import AimCallback` | `paddle` | `paddlepaddle` | Missing Paddle is a normal Python import failure | Uses Paddle HAPI callback lifecycle. |
| MXNet | `from aim.mxnet import AimLoggingHandler` | `mxnet` | `mxnet` | Missing MXNet is a normal Python import failure | Uses Gluon estimator event handlers. |
| Prophet | `from aim.prophet import AimLogger` | Prophet model object from user's code | `prophet` | Adapter import does not construct Prophet; user's model import fails if Prophet is absent | Logger stores model attributes and user-provided metrics. |
| stable-baselines3 | `from aim.sb3 import AimCallback` | `stable_baselines3` | `stable-baselines3` | Missing stable-baselines3 is a normal Python import failure | Replaces model logger with an Aim output format. |
| ACME | `from aim.acme import AimCallback, AimWriter` | `acme` | commonly `dm-acme` variants | Missing ACME is a normal Python import failure | Use an Aim-backed logger factory. |
| TensorBoard conversion | `aim convert --repo <repo> tensorboard --logdir <logdir>` | `tensorflow`, `tensorboard` event tooling | `tensorflow`, `tensorboard` | Conversion prints an error if TensorFlow import fails | Offline conversion reads event files and writes Aim runs. |
| TensorBoard live sync | `from aim.ext.tensorboard_tracker import Run` | TensorBoard event-processing modules; TensorFlow may be needed in the environment that writes/reads events | `tensorboard`, often `tensorflow` | Import or runtime processing fails if event tooling is absent | Starts a watcher resource; use only when live sync is desired. |

## Known adapter import messages

The following messages are useful because they indicate optional dependency gaps rather than broken Aim core installation:

- PyTorch Ignite without PyTorch: `This contrib module requires PyTorch to be installed. Please install it with command: pip install torch`.
- PyTorch Ignite without Ignite: `This contrib module requires PyTorch Ignite to be installed. Please install it with command: pip install pytorch-ignite`.
- Lightning without Lightning packages: `This contrib module requires PyTorch Lightning to be installed. Please install it with command: pip install pytorch-lightning or pip install lightning`.
- Hugging Face without Transformers: `This contrib module requires Transformers to be installed. Please install it with command: pip install transformers`.
- Keras without Keras: `This contrib module requires keras to be installed. Please install it with command: pip install keras`.
- TensorFlow Keras without TensorFlow: `This contrib module requires tensorflow to be installed. Please install it with command: pip install tensorflow`.
- XGBoost without XGBoost: `This contrib module requires XGBoost to be installed. Please install it with command: pip install xgboost`.
- LightGBM without LightGBM: `This contrib module requires Lightgbm to be installed. Please install it with command: pip install lightgbm`.
- fastai without fastai: `This contrib module requires fastai to be installed. Please install it with command: pip install fastai`.
- Keras Tuner without Keras Tuner: `This contrib module requires KerasTuner to be installed. Please install it with command: pip install keras-tuner`.
- TensorBoard conversion without TensorFlow: `Could not process TensorBoard logs - failed to import tensorflow module.`

## Signature and keyword guardrails

When generating code, use the adapter's current constructor keyword, not a guessed synonym.

- `experiment`: PyTorch Ignite, PyTorch Lightning/Lightning, Hugging Face, Keras, TensorFlow Keras, Keras Tuner, XGBoost, CatBoost, LightGBM, Prophet.
- `experiment_name`: Optuna, fastai, Paddle, MXNet, stable-baselines3, ACME.
- `run_name` and `run_hash` are specific to the Lightning logger.
- CatBoost `AimLogger` signature includes `loss_function`, `repo`, `experiment`, `system_tracking_interval`, `log_system_params`, `capture_terminal_logs`, and `log_cout`.
- Optuna `AimCallback` supports `metric_name`, `as_multirun`, `repo`, and `experiment_name`; call `close()` between studies in the same process.

If the user gets `TypeError: unexpected keyword argument`, check this list first and switch to direct `Run.track` if the adapter version cannot support the desired layout.

## Install boundaries

- Installing an optional framework can be expensive, version-sensitive, or GPU-sensitive; obtain user approval for package installs.
- Aim logging itself does not require CUDA/ROCm/MPS. The user's training framework may require accelerator-specific dependencies, but that is outside Aim's base requirement.
- Prefer CPU-safe import checks and code review over running full training examples.
- For notebooks, restart the kernel after installing optional dependencies so adapter imports see the new package set.
