# Framework integration recipes

This reference distills Aim's framework adapters into self-contained templates. The templates are intentionally small: they show where Aim objects attach and where names, steps, epochs, and contexts should be made explicit. They are not full training examples.

## Decision tree

1. **Use a framework adapter** when the user's framework is already installed, its callback/logger lifecycle fits the training loop, and scalar metrics are enough for the framework's normal logging hook.
2. **Use direct `Run.track` fallback** when adapter import fails, the user cannot install broad optional dependencies, metrics are custom/non-scalar, media objects must be logged, the framework callback hides the desired step/epoch, or the adapter's parameter names do not match the user's installed Aim version.
3. **Use TensorBoard conversion/sync** when the user already has TensorBoard event files or a TensorBoard writer and does not want to modify or rerun training.
4. **Route to `tracking-sdk`** for full details about Aim object types, repository lifecycle, querying, and supported value semantics.

## Shared adapter conventions

Most adapter constructors accept a target Aim repository and experiment name plus system-tracking options. The exact experiment keyword is adapter-specific:

- Use `experiment` for PyTorch Ignite, PyTorch Lightning/Lightning, Hugging Face, Keras, TensorFlow Keras, XGBoost, CatBoost, LightGBM, Keras Tuner, and Prophet.
- Use `experiment_name` for Optuna, fastai, Paddle, MXNet, stable-baselines3, and ACME.
- Use direct `Run(repo=..., experiment=...)` for plain Python and PyTorch-loop fallback.

Common Aim context convention:

```python
context = {"subset": "train"}  # or "val" / "test"
run.track(value, name="loss", step=global_step, epoch=epoch, context=context)
```

Close a run or logger when the framework does not do it for you, especially in notebooks and repeated experiments.

## Direct `Run.track` fallback for any framework

Use this when the adapter cannot be imported, when only a few metrics are needed, or when framework logs are not shaped correctly for Aim.

```python
from aim import Run

AIM_REPO = "path/to/aim-repo"
run = Run(repo=AIM_REPO, experiment="manual_tracking")
run["hparams"] = {"learning_rate": 1e-3, "batch_size": 32}

for epoch in range(num_epochs):
    for step, batch in enumerate(train_loader):
        loss_value = train_one_step(batch)
        run.track(
            loss_value,
            name="loss",
            step=epoch * len(train_loader) + step,
            epoch=epoch,
            context={"subset": "train"},
        )

    val_loss = evaluate()
    run.track(val_loss, name="loss", epoch=epoch, context={"subset": "val"})

run.close()
```

For media or structured objects, construct Aim objects (`Image`, `Text`, `Distribution`, etc.) in the user code and track them with explicit context. See `tracking-sdk` for the supported object model.

## PyTorch direct helpers

Aim provides direct PyTorch helper functions rather than a training callback for plain PyTorch loops:

```python
from aim import Run
from aim.pytorch import track_gradients_dists, track_params_dists

run = Run(repo="path/to/aim-repo", experiment="pytorch_loop")

for epoch in range(num_epochs):
    for step, (inputs, targets) in enumerate(train_loader):
        loss = train_one_step(inputs, targets)
        global_step = epoch * len(train_loader) + step
        run.track(loss.item(), name="loss", step=global_step, epoch=epoch, context={"subset": "train"})

    # Histogram-like distributions for leaf module weights/biases and gradients.
    track_params_dists(model, run)
    track_gradients_dists(model, run)

run.close()
```

The helpers traverse child modules, collect `weight` and `bias` data or gradients, move CUDA tensors to CPU before conversion, and track them as Aim distributions. Use them sparingly on large models because distribution tracking can add storage and runtime overhead.

## PyTorch Ignite

```python
from aim.pytorch_ignite import AimLogger
from ignite.engine import Events

logger = AimLogger(repo="path/to/aim-repo", experiment="ignite_run")
logger.log_params({"learning_rate": 1e-3, "batch_size": 64})

logger.attach_output_handler(
    trainer,
    event_name=Events.ITERATION_COMPLETED,
    tag="train",
    output_transform=lambda loss: {"loss": loss},
)

logger.attach_output_handler(
    evaluator,
    event_name=Events.EPOCH_COMPLETED,
    tag="validation",
    metric_names=["accuracy", "nll"],
    global_step_transform=lambda *_: trainer.state.iteration,
)
```

Metric names starting with configured train/validation/test prefixes are mapped into Aim `subset` context by the logger. If Ignite or PyTorch is missing, use direct `Run.track` inside engine events.

## PyTorch Lightning / Lightning

```python
from aim.pytorch_lightning import AimLogger

logger = AimLogger(
    repo="path/to/aim-repo",
    experiment="lightning_run",
    run_name="optional-display-name",
    context_prefixes={"subset": {"train": "train_", "val": "val_", "test": "test_"}},
    context_postfixes={"average": {"macro": "_macro", "weighted": "_weighted"}},
)
trainer = Trainer(max_epochs=5, logger=logger)
trainer.fit(model, train_dataloaders=train_loader, val_dataloaders=val_loader)
```

Lightning metrics such as `self.log("val_loss", loss)` become Aim metric `loss` with context `{"subset": "val"}` under the default prefix mapping. Do not combine deprecated `train_metric_prefix`, `val_metric_prefix`, or `test_metric_prefix` with a custom `context_prefixes` mapping. In distributed training, the logger only writes on rank zero.

Fallback inside a Lightning module:

```python
self.logger.experiment.track(value, name="custom_metric", step=self.global_step, context={"subset": "train"})
```

Use the fallback when the adapter import fails, when custom object tracking is needed, or when prefix/postfix parsing would lose information.

## Hugging Face Transformers

```python
from aim.hugging_face import AimCallback
from transformers import Trainer

callback = AimCallback(repo="path/to/aim-repo", experiment="hf_trainer")
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=eval_dataset,
    compute_metrics=compute_metrics,
    callbacks=[callback],
)
trainer.train()
```

The callback stores sanitized training arguments and model configuration when available. It logs only numeric values from `on_log`; keys starting with `train_`, `eval_`, or `test_` are converted to Aim `subset` contexts. In distributed training, it logs only from the world process zero. Track text, images, or other non-numeric values directly through `callback.experiment.track(...)` or a separate `Run`.

## Keras and TensorFlow Keras

Standalone Keras:

```python
from aim.keras import AimCallback

model.fit(
    x_train,
    y_train,
    validation_data=(x_val, y_val),
    epochs=5,
    callbacks=[AimCallback(repo="path/to/aim-repo", experiment="keras_run")],
)
```

TensorFlow Keras:

```python
from aim.tensorflow import AimCallback

model.fit(
    x_train,
    y_train,
    validation_data=(x_val, y_val),
    epochs=5,
    callbacks=[AimCallback(repo="path/to/aim-repo", experiment="tf_keras_run")],
)
```

The callback logs epoch-end metrics. Keys with `val_` are tracked under context `{"subset": "val"}` with the prefix removed; other logs are tracked under `{"subset": "train"}`. The callback also attempts to log the optimizer learning rate when it can be evaluated.

## Keras Tuner

```python
from aim.keras_tuner import AimCallback

callback = AimCallback(tuner=tuner, repo="path/to/aim-repo", experiment="keras_tuner_run")
tuner.search(train_data, validation_data=validation_data, callbacks=[callback])
```

The callback creates an Aim run when a trial begins, stores the current `trial_id`, logs hyperparameter values, and tracks batch-end logs. Ensure the callback receives the active tuner instance.

## XGBoost

```python
from aim.xgboost import AimCallback
import xgboost as xgb

watchlist = [(dtrain, "train"), (dvalid, "valid")]
xgb.train(
    params,
    dtrain,
    num_boost_round=100,
    evals=watchlist,
    callbacks=[AimCallback(repo="path/to/aim-repo", experiment="xgboost_run")],
)
```

The adapter is a native XGBoost `TrainingCallback`. If the exact step or dataset context is important and the adapter output does not match the user's desired Aim layout, implement a small custom XGBoost callback that calls `Run.track` directly.

## CatBoost

```python
from aim.catboost import AimLogger

logger = AimLogger(
    loss_function="Logloss",
    repo="path/to/aim-repo",
    experiment="catboost_run",
)
model.fit(
    train_data,
    train_labels,
    eval_set=(valid_data, valid_labels),
    log_cout=logger,
    logging_level="Info",
)
```

CatBoost integration works by redirecting training logs through `log_cout`. The logger parses CatBoost text lines into Aim metrics with contexts such as `learn`, `test`, and `best`. If CatBoost's output format changes or parsing misses values, use a CatBoost callback or post-fit direct `Run.track` for the required metrics.

## LightGBM

```python
from aim.lightgbm import AimCallback
import lightgbm as lgb

callback = AimCallback(repo="path/to/aim-repo", experiment="lightgbm_run")
lgb.train(
    params,
    train_set,
    valid_sets=[valid_set],
    num_boost_round=100,
    callbacks=[callback],
)
```

The callback tracks LightGBM evaluation results. Standard evaluation tuples are tracked by metric name with the data name in context. Cross-validation-style results with standard deviation are tracked as mean/stdv metric variants.

## Optuna

Single Aim run for all trials:

```python
from aim.optuna import AimCallback

callback = AimCallback(metric_name="objective", experiment_name="optuna_study")
study.optimize(objective, n_trials=50, callbacks=[callback])
callback.close()
```

One Aim run per trial, with direct tracking inside the objective:

```python
callback = AimCallback(metric_name="objective", as_multirun=True, experiment_name="optuna_multirun")

@callback.track_in_aim()
def objective(trial):
    x = trial.suggest_float("x", -10, 10)
    callback.experiment.track(x, name="sampled_x", step=trial.number)
    return (x - 2) ** 2

study.optimize(objective, n_trials=20, callbacks=[callback])
```

Use `n_jobs=1` when relying on trial order in a single Aim run.

## fastai

```python
from aim.fastai import AimCallback

callback = AimCallback(repo="path/to/aim-repo", experiment_name="fastai_run")
learn = cnn_learner(dls, arch, metrics=accuracy, cbs=callback)
learn.fit_one_cycle(epochs)
```

The callback gathers learner configuration at fit start, tracks training loss and optimizer hyperparameters after batches, and logs recorder metrics after epochs.

## PaddlePaddle

```python
from aim.paddle import AimCallback

callback = AimCallback(repo="path/to/aim-repo", experiment_name="paddle_run")
model.fit(train_dataset, eval_dataset, batch_size=64, callbacks=callback)
```

The callback logs parameters at train start, train-batch logs under `{"subset": "train"}`, and evaluation logs under `{"subset": "valid"}`. It rejects multi-item list values in logs.

## MXNet Gluon estimator

```python
from aim.mxnet import AimLoggingHandler

handler = AimLoggingHandler(
    log_interval=1,
    repo="path/to/aim-repo",
    experiment_name="mxnet_run",
    metrics=[train_accuracy, train_loss, validation_accuracy],
)
estimator.fit(train_data=train_loader, val_data=valid_loader, epochs=epochs, event_handlers=[handler])
```

The handler logs optimizer and model hyperparameters at train start, then logs metrics by epoch or batch interval. Metric names are split into context and metric name, so verify that MXNet metric names contain the expected context token.

## Prophet

```python
from aim.prophet import AimLogger

model = Prophet(**model_config)
logger = AimLogger(prophet_model=model, repo="path/to/aim-repo", experiment="prophet_run")
model.fit(train_frame)
logger.track_metrics({"mape": mape, "rmse": rmse}, context={"subset": "val"})
```

Prophet is not iterative in the same way as neural-network training. The logger stores model attributes at construction time and provides `track_metrics` for user-computed metrics after fitting or backtesting.

## stable-baselines3

```python
from aim.sb3 import AimCallback

callback = AimCallback(repo="path/to/aim-repo", experiment_name="sb3_run")
model.learn(total_timesteps=10_000, callback=callback)
```

The callback replaces the model logger with an Aim writer. It expects scalar numeric key/value logs, and keys containing a slash are split into an Aim context tag and metric name. If the user's logger keys do not contain slashes, add a custom output format or direct `Run.track` calls.

## ACME

```python
from aim.acme import AimCallback, AimWriter

callback = AimCallback(repo="path/to/aim-repo", experiment_name="acme_run", args={"seed": seed})
aim_run = callback.experiment

def logger_factory(name, steps_key=None, task_id=None):
    return AimWriter(aim_run, name, steps_key, task_id)

experiment_config = experiments.ExperimentConfig(
    builder=builder,
    environment_factory=environment_factory,
    network_factory=network_factory,
    logger_factory=logger_factory,
    seed=seed,
    max_num_actor_steps=max_steps,
)
```

The Aim writer tracks ACME logging data with context `{"logger_label": name}`. Confirm ACME logging payloads are values Aim can serialize; otherwise convert them before writing.

## TensorBoard event logs

For existing TensorBoard logs, prefer offline conversion:

```bash
aim convert --repo path/to/aim-repo tensorboard --logdir path/to/tensorboard-logdir
```

For a live TensorBoard writer, use the sync template in `references/tensorboard-and-conversion.md` or the bundled `tensorboard_sync_template.py` script. Do not rerun training just to migrate old logs.
