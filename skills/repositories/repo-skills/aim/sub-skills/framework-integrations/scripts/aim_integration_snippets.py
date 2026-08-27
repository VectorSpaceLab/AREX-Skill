#!/usr/bin/env python3
"""Print Aim framework integration skeletons and optional dependency diagnostics.

This helper is intentionally side-effect-light. By default it imports only the
Python standard library and prints templates. Optional framework packages are
not imported unless --import-adapters is supplied together with
--check-optional.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.util
import json
import sys
import textwrap
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional


@dataclass(frozen=True)
class DependencyProbe:
    key: str
    label: str
    modules: List[str]
    packages: List[str]
    adapter: Optional[str]
    notes: str


DEPENDENCIES: List[DependencyProbe] = [
    DependencyProbe(
        "pytorch",
        "PyTorch direct helpers",
        ["torch"],
        ["torch"],
        "aim.pytorch",
        "Aim helper import is lightweight; torch is needed by the user's model code.",
    ),
    DependencyProbe(
        "pytorch_ignite",
        "PyTorch Ignite",
        ["torch", "ignite"],
        ["torch", "pytorch-ignite"],
        "aim.pytorch_ignite",
        "Adapter raises RuntimeError when torch or ignite is missing.",
    ),
    DependencyProbe(
        "lightning",
        "PyTorch Lightning / Lightning",
        ["lightning", "pytorch_lightning"],
        ["lightning or pytorch-lightning"],
        "aim.pytorch_lightning",
        "Either lightning or pytorch_lightning can satisfy the adapter.",
    ),
    DependencyProbe(
        "hugging_face",
        "Hugging Face Transformers",
        ["transformers"],
        ["transformers"],
        "aim.hugging_face",
        "Adapter logs numeric Trainer values and skips non-numeric payloads.",
    ),
    DependencyProbe("keras", "Keras", ["keras"], ["keras"], "aim.keras", "Standalone Keras callback."),
    DependencyProbe(
        "tensorflow",
        "TensorFlow Keras",
        ["tensorflow"],
        ["tensorflow"],
        "aim.tensorflow",
        "TensorFlow Keras callback and TensorBoard conversion commonly require tensorflow.",
    ),
    DependencyProbe(
        "keras_tuner",
        "Keras Tuner",
        ["kerastuner"],
        ["keras-tuner"],
        "aim.keras_tuner",
        "Pass the active tuner instance to AimCallback.",
    ),
    DependencyProbe("xgboost", "XGBoost", ["xgboost"], ["xgboost"], "aim.xgboost", "Native XGBoost TrainingCallback."),
    DependencyProbe(
        "catboost",
        "CatBoost",
        ["catboost"],
        ["catboost"],
        "aim.catboost",
        "AimLogger is a log_cout handler; adapter import may work even before catboost is installed.",
    ),
    DependencyProbe("lightgbm", "LightGBM", ["lightgbm"], ["lightgbm"], "aim.lightgbm", "Native LightGBM callback."),
    DependencyProbe("optuna", "Optuna", ["optuna"], ["optuna"], "aim.optuna", "Supports single-run and multirun study logging."),
    DependencyProbe("fastai", "fastai", ["fastai", "fastcore"], ["fastai"], "aim.fastai", "fastai learner callback."),
    DependencyProbe("paddle", "PaddlePaddle", ["paddle"], ["paddlepaddle"], "aim.paddle", "Paddle HAPI callback."),
    DependencyProbe("mxnet", "MXNet", ["mxnet"], ["mxnet"], "aim.mxnet", "Gluon estimator event handler."),
    DependencyProbe("prophet", "Prophet", ["prophet"], ["prophet"], "aim.prophet", "Adapter expects a Prophet model object supplied by user code."),
    DependencyProbe(
        "sb3",
        "stable-baselines3",
        ["stable_baselines3"],
        ["stable-baselines3"],
        "aim.sb3",
        "Reinforcement-learning logger callback.",
    ),
    DependencyProbe("acme", "ACME", ["acme"], ["dm-acme variants"], "aim.acme", "Aim-backed ACME logger factory."),
    DependencyProbe(
        "tensorboard",
        "TensorBoard conversion/sync",
        ["tensorboard", "tensorflow"],
        ["tensorboard", "tensorflow"],
        "aim.ext.tensorboard_tracker",
        "Offline conversion requires TensorFlow import support; live sync uses TensorBoard event tooling.",
    ),
]


TEMPLATES: Dict[str, str] = {
    "direct": r'''
from aim import Run

run = Run(repo="path/to/aim-repo", experiment="manual_tracking")
run["hparams"] = {"learning_rate": 1e-3, "batch_size": 32}

for epoch in range(num_epochs):
    for step, batch in enumerate(train_loader):
        loss_value = train_one_step(batch)
        global_step = epoch * len(train_loader) + step
        run.track(loss_value, name="loss", step=global_step, epoch=epoch, context={"subset": "train"})

    val_loss = evaluate()
    run.track(val_loss, name="loss", epoch=epoch, context={"subset": "val"})

run.close()
''',
    "pytorch": r'''
from aim import Run
from aim.pytorch import track_gradients_dists, track_params_dists

run = Run(repo="path/to/aim-repo", experiment="pytorch_loop")

for epoch in range(num_epochs):
    for step, (inputs, targets) in enumerate(train_loader):
        loss = train_one_step(inputs, targets)
        global_step = epoch * len(train_loader) + step
        run.track(loss.item(), name="loss", step=global_step, epoch=epoch, context={"subset": "train"})

    track_params_dists(model, run)
    track_gradients_dists(model, run)

run.close()
''',
    "pytorch_ignite": r'''
from aim.pytorch_ignite import AimLogger
from ignite.engine import Events

logger = AimLogger(repo="path/to/aim-repo", experiment="ignite_run")
logger.log_params({"learning_rate": 1e-3})
logger.attach_output_handler(
    trainer,
    event_name=Events.ITERATION_COMPLETED,
    tag="train",
    output_transform=lambda loss: {"loss": loss},
)
''',
    "lightning": r'''
from aim.pytorch_lightning import AimLogger

logger = AimLogger(
    repo="path/to/aim-repo",
    experiment="lightning_run",
    context_prefixes={"subset": {"train": "train_", "val": "val_", "test": "test_"}},
)
trainer = Trainer(max_epochs=5, logger=logger)
trainer.fit(model, train_dataloaders=train_loader, val_dataloaders=val_loader)

# Direct custom metric fallback:
# self.logger.experiment.track(value, name="custom_metric", step=self.global_step, context={"subset": "train"})
''',
    "hugging_face": r'''
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
''',
    "keras": r'''
from aim.keras import AimCallback

model.fit(
    x_train,
    y_train,
    validation_data=(x_val, y_val),
    epochs=5,
    callbacks=[AimCallback(repo="path/to/aim-repo", experiment="keras_run")],
)
''',
    "tensorflow": r'''
from aim.tensorflow import AimCallback

model.fit(
    x_train,
    y_train,
    validation_data=(x_val, y_val),
    epochs=5,
    callbacks=[AimCallback(repo="path/to/aim-repo", experiment="tf_keras_run")],
)
''',
    "keras_tuner": r'''
from aim.keras_tuner import AimCallback

callback = AimCallback(tuner=tuner, repo="path/to/aim-repo", experiment="keras_tuner_run")
tuner.search(train_data, validation_data=validation_data, callbacks=[callback])
''',
    "xgboost": r'''
from aim.xgboost import AimCallback
import xgboost as xgb

xgb.train(
    params,
    dtrain,
    num_boost_round=100,
    evals=[(dtrain, "train"), (dvalid, "valid")],
    callbacks=[AimCallback(repo="path/to/aim-repo", experiment="xgboost_run")],
)
''',
    "catboost": r'''
from aim.catboost import AimLogger

logger = AimLogger(loss_function="Logloss", repo="path/to/aim-repo", experiment="catboost_run")
model.fit(train_data, train_labels, eval_set=(valid_data, valid_labels), log_cout=logger, logging_level="Info")
''',
    "lightgbm": r'''
from aim.lightgbm import AimCallback
import lightgbm as lgb

callback = AimCallback(repo="path/to/aim-repo", experiment="lightgbm_run")
lgb.train(params, train_set, valid_sets=[valid_set], num_boost_round=100, callbacks=[callback])
''',
    "optuna": r'''
from aim.optuna import AimCallback

callback = AimCallback(metric_name="objective", experiment_name="optuna_study")
study.optimize(objective, n_trials=50, callbacks=[callback])
callback.close()
''',
    "fastai": r'''
from aim.fastai import AimCallback

callback = AimCallback(repo="path/to/aim-repo", experiment_name="fastai_run")
learn = cnn_learner(dls, arch, metrics=accuracy, cbs=callback)
learn.fit_one_cycle(epochs)
''',
    "paddle": r'''
from aim.paddle import AimCallback

callback = AimCallback(repo="path/to/aim-repo", experiment_name="paddle_run")
model.fit(train_dataset, eval_dataset, batch_size=64, callbacks=callback)
''',
    "mxnet": r'''
from aim.mxnet import AimLoggingHandler

handler = AimLoggingHandler(log_interval=1, repo="path/to/aim-repo", experiment_name="mxnet_run", metrics=metrics)
estimator.fit(train_data=train_loader, val_data=valid_loader, epochs=epochs, event_handlers=[handler])
''',
    "prophet": r'''
from aim.prophet import AimLogger

model = Prophet(**model_config)
logger = AimLogger(prophet_model=model, repo="path/to/aim-repo", experiment="prophet_run")
model.fit(train_frame)
logger.track_metrics({"mape": mape, "rmse": rmse}, context={"subset": "val"})
''',
    "sb3": r'''
from aim.sb3 import AimCallback

callback = AimCallback(repo="path/to/aim-repo", experiment_name="sb3_run")
model.learn(total_timesteps=10_000, callback=callback)
''',
    "acme": r'''
from aim.acme import AimCallback, AimWriter

callback = AimCallback(repo="path/to/aim-repo", experiment_name="acme_run", args={"seed": seed})
aim_run = callback.experiment

def logger_factory(name, steps_key=None, task_id=None):
    return AimWriter(aim_run, name, steps_key, task_id)
''',
    "tensorboard": r'''
# Offline conversion; put --repo before the tensorboard subcommand.
aim convert --repo path/to/aim-repo tensorboard --logdir path/to/tensorboard-logdir

# Live sync from Python, only when a process should watch a TensorBoard logdir.
from aim.ext.tensorboard_tracker import Run as AimTensorBoardRun
run = AimTensorBoardRun(sync_tensorboard_log_dir="path/to/tensorboard-logdir", repo="path/to/aim-repo", experiment="tb_sync")
try:
    pass  # keep process alive while the TensorBoard writer is active
finally:
    run.close()
''',
}


def has_module(module_name: str) -> bool:
    try:
        return importlib.util.find_spec(module_name) is not None
    except (ImportError, AttributeError, ValueError):
        return False


def adapter_import_status(adapter: Optional[str]) -> Optional[Dict[str, object]]:
    if not adapter:
        return None
    try:
        importlib.import_module(adapter)
    except Exception as exc:  # explicit diagnostic mode; report any import-time failure
        return {"ok": False, "error_type": type(exc).__name__, "message": str(exc).replace("\n", " ")}
    return {"ok": True, "error_type": None, "message": "import succeeded"}


def dependency_report(import_adapters: bool = False) -> List[Dict[str, object]]:
    report: List[Dict[str, object]] = []
    for probe in DEPENDENCIES:
        modules = {module: has_module(module) for module in probe.modules}
        item: Dict[str, object] = {
            "key": probe.key,
            "label": probe.label,
            "modules": modules,
            "packages": probe.packages,
            "adapter": probe.adapter,
            "notes": probe.notes,
        }
        if import_adapters:
            item["adapter_import"] = adapter_import_status(probe.adapter)
        report.append(item)
    return report


def print_dependency_report(report: Iterable[Dict[str, object]]) -> None:
    for item in report:
        modules = item["modules"]
        assert isinstance(modules, dict)
        module_bits = ", ".join(f"{name}={'yes' if ok else 'no'}" for name, ok in modules.items())
        print(f"[{item['key']}] {item['label']}")
        print(f"  modules: {module_bits}")
        print(f"  install hint: {', '.join(item['packages'])}")
        print(f"  adapter: {item['adapter'] or 'none'}")
        if "adapter_import" in item:
            status = item["adapter_import"]
            assert isinstance(status, dict)
            print(f"  adapter import: {'ok' if status['ok'] else 'failed'} ({status['message']})")
        print(f"  note: {item['notes']}")


def normalized_template(name: str) -> str:
    return textwrap.dedent(TEMPLATES[name]).strip() + "\n"


def print_templates(names: Iterable[str]) -> None:
    for name in names:
        print(f"# --- {name} ---")
        print(normalized_template(name))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Print Aim integration code skeletons and optional dependency diagnostics.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--list", action="store_true", help="List available template ids and exit.")
    parser.add_argument(
        "--template",
        choices=["all"] + sorted(TEMPLATES),
        help="Print one template, or all templates.",
    )
    parser.add_argument(
        "--check-optional",
        action="store_true",
        help="Check optional dependency module presence without importing adapters by default.",
    )
    parser.add_argument(
        "--import-adapters",
        action="store_true",
        help="With --check-optional, explicitly import Aim adapter modules and report import-time errors.",
    )
    parser.add_argument("--json", action="store_true", help="Emit dependency diagnostics as JSON.")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not any([args.list, args.template, args.check_optional]):
        parser.print_help()
        return 0

    if args.list:
        for name in sorted(TEMPLATES):
            print(name)

    if args.template:
        names = sorted(TEMPLATES) if args.template == "all" else [args.template]
        print_templates(names)

    if args.check_optional:
        report = dependency_report(import_adapters=args.import_adapters)
        if args.json:
            print(json.dumps(report, indent=2, sort_keys=True))
        else:
            print_dependency_report(report)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
