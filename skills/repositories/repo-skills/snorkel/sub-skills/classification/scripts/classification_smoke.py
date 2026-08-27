#!/usr/bin/env python3
"""Tiny CPU-only smoke for Snorkel classification APIs."""

from __future__ import annotations

import json
import random
import tempfile
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn

from snorkel.analysis import Scorer, get_label_buckets, get_label_instances, metric_score
from snorkel.classification.data import DictDataLoader, DictDataset
from snorkel.classification.loss import cross_entropy_with_probs
from snorkel.classification.multitask_classifier import MultitaskClassifier
from snorkel.classification.task import Operation, Task
from snorkel.classification.training.trainer import Trainer
from snorkel.utils import filter_labels, preds_to_probs, probs_to_preds, to_int_label_array


TASK_NAME = "demo_task"
DATASET_NAME = "SmokeDataset"


def _ensure(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _build_dataset(split: str, X: torch.Tensor, Y: torch.Tensor) -> DictDataset:
    return DictDataset.from_tensors(
        X,
        Y,
        split=split,
        task_name=TASK_NAME,
        dataset_name=DATASET_NAME,
    )


def _build_model() -> MultitaskClassifier:
    module_pool = nn.ModuleDict(
        {
            "hidden": nn.Sequential(nn.Linear(2, 4), nn.ReLU()),
            "head": nn.Linear(4, 2),
        }
    )
    op_sequence = [
        Operation(
            module_name="hidden",
            inputs=[("_input_", "input_data")],
            name="hidden",
        ),
        Operation(module_name="head", inputs=["hidden"], name="logits"),
    ]
    task = Task(
        name=TASK_NAME,
        module_pool=module_pool,
        op_sequence=op_sequence,
        scorer=Scorer(metrics=["accuracy"]),
        loss_func=cross_entropy_with_probs,
    )
    return MultitaskClassifier([task], device=-1, dataparallel=False)


def _validate_analysis_helpers() -> None:
    golds = np.array([0, 0, 1, 1])
    preds = np.array([0, 1, 1, 0])
    x = np.arange(4).reshape(-1, 1)

    _ensure(
        np.array_equal(
            to_int_label_array(np.array([[0.0], [1.0]])), np.array([0, 1])
        ),
        "to_int_label_array failed",
    )
    _ensure(
        np.array_equal(
            preds_to_probs(np.array([0, 1]), 2), np.array([[1, 0], [0, 1]])
        ),
        "preds_to_probs failed",
    )
    _ensure(
        np.array_equal(
            probs_to_preds(np.array([[0.1, 0.9], [0.8, 0.2]])), np.array([1, 0])
        ),
        "probs_to_preds failed",
    )

    filtered = filter_labels(
        label_dict={"golds": np.array([-1, 0, 1]), "preds": np.array([0, -1, 1])},
        filter_dict={"golds": [-1], "preds": [-1]},
    )
    _ensure(filtered["golds"].tolist() == [1], "filter_labels failed")

    buckets = get_label_buckets(golds, preds)
    _ensure((0, 1) in buckets, "get_label_buckets missing expected bucket")
    instances = get_label_instances((0, 1), x, golds, preds)
    _ensure(instances.shape[0] == 1 and instances[0, 0] == 1, "get_label_instances failed")

    scorer = Scorer(metrics=["accuracy", "coverage"])
    scores = scorer.score(golds=golds, preds=preds, probs=preds_to_probs(preds, 2))
    _ensure("accuracy" in scores and "coverage" in scores, "Scorer failed")
    _ensure(
        metric_score(golds, preds, probs=preds_to_probs(preds, 2), metric="accuracy")
        == 0.5,
        "metric_score failed",
    )


def _train_with_trainer(
    model: MultitaskClassifier,
    train_dl: DictDataLoader,
    valid_dl: DictDataLoader,
    log_dir: Path,
    checkpoint_dir: Path,
) -> dict:
    trainer = Trainer(
        n_epochs=1,
        progress_bar=False,
        batch_scheduler="sequential",
        logging=True,
        log_writer="json",
        log_writer_config={"log_dir": str(log_dir), "run_name": "smoke_run"},
        checkpointing=True,
        checkpointer_config={
            "checkpoint_dir": str(checkpoint_dir),
            "checkpoint_metric": f"{TASK_NAME}/{DATASET_NAME}/valid/accuracy:max",
        },
    )
    trainer.fit(model, [train_dl, valid_dl])

    scores = model.score([valid_dl])
    log_file = log_dir / "smoke_run" / "log.json"
    checkpoint_files = sorted(path.name for path in checkpoint_dir.glob("*.pth"))
    _ensure(log_file.exists(), "Trainer did not write log.json")
    _ensure(checkpoint_files, "Trainer did not write any checkpoint file")

    return {
        "mode": "trainer",
        "scores": {k: float(v) for k, v in scores.items()},
        "log_written": True,
        "checkpoint_files": checkpoint_files,
    }


def run_smoke() -> dict:
    random.seed(7)
    np.random.seed(7)
    torch.manual_seed(7)

    X_train = torch.tensor(
        [
            [0.0, 0.0],
            [0.0, 1.0],
            [1.0, 0.0],
            [1.0, 1.0],
            [2.0, 0.0],
            [2.0, 1.0],
        ],
        dtype=torch.float32,
    )
    Y_train = torch.tensor(
        [
            [0.95, 0.05],
            [0.80, 0.20],
            [0.20, 0.80],
            [0.10, 0.90],
            [0.05, 0.95],
            [0.05, 0.95],
        ],
        dtype=torch.float32,
    )
    X_valid = torch.tensor(
        [
            [0.0, 0.0],
            [0.0, 1.0],
            [1.0, 0.0],
            [1.0, 1.0],
        ],
        dtype=torch.float32,
    )
    Y_valid = torch.tensor([0, 0, 1, 1], dtype=torch.long)

    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        log_dir = root / "logs"
        checkpoint_dir = root / "checkpoints"

        train_ds = _build_dataset("train", X_train, Y_train)
        valid_ds = _build_dataset("valid", X_valid, Y_valid)
        train_dl = DictDataLoader(train_ds, batch_size=2, shuffle=False)
        valid_dl = DictDataLoader(valid_ds, batch_size=2, shuffle=False)

        model = _build_model()
        report = _train_with_trainer(model, train_dl, valid_dl, log_dir, checkpoint_dir)
        _validate_analysis_helpers()

        predictions = model.predict(valid_dl, return_preds=True)
        golds = predictions["golds"][TASK_NAME].numpy().astype(int)
        preds = predictions["preds"][TASK_NAME].numpy().astype(int)
        probs = predictions["probs"][TASK_NAME].numpy()
        _ensure(golds.shape == preds.shape, "predict shapes do not match")
        _ensure(probs.shape == (len(golds), 2), "predict probabilities have wrong shape")

        summary = {
            "mode": report["mode"],
            "scores": report["scores"],
            "log_written": report["log_written"],
            "checkpoint_files": report["checkpoint_files"],
        }
        print(json.dumps(summary, sort_keys=True))
        return summary


if __name__ == "__main__":
    run_smoke()
