#!/usr/bin/env python3
from __future__ import annotations

import argparse
from typing import Callable

import torch

from ignite.engine import Engine
from ignite.metrics import (
    Accuracy,
    AveragePrecision,
    Fbeta,
    HitRate,
    MetricGroup,
    NDCG,
    Precision,
    PrecisionRecallCurve,
    Recall,
    ROC_AUC,
    SSIM,
)
from ignite.metrics.fairness import DemographicParityDifference, SubgroupAccuracyDifference
from ignite.utils import manual_seed


def run_classification() -> None:
    engine = Engine(lambda engine, batch: batch)
    logits = torch.tensor(
        [
            [2.2, 0.4],
            [0.1, 1.8],
            [1.5, 0.3],
            [0.2, 1.1],
        ]
    )
    targets = torch.tensor([0, 1, 0, 1])

    metrics = {
        "acc": Accuracy(),
        "precision": Precision(average=False),
        "recall": Recall(average=False),
        "f1": Fbeta(beta=1.0),
    }
    for name, metric in metrics.items():
        metric.attach(engine, name)

    state = engine.run([(logits, targets)])
    print(f"metrics_accuracy={float(state.metrics['acc']):.6f}")
    print(f"metrics_precision={state.metrics['precision']}")
    print(f"metrics_recall={state.metrics['recall']}")
    print(f"metrics_f1={float(state.metrics['f1']):.6f}")

    group_engine = Engine(lambda engine, batch: batch)
    group = MetricGroup({"acc": Accuracy(), "precision": Precision(average=False)})
    group.attach(group_engine, "group")
    group_state = group_engine.run([(logits, targets)])
    print(f"metrics_group={group_state.metrics['group']}")

    arithmetic_engine = Engine(lambda engine, batch: batch)
    precision = Precision(average=False)
    recall = Recall(average=False)
    f1_arithmetic = (precision * recall * 2 / (precision + recall + 1e-20)).mean()
    f1_arithmetic.attach(arithmetic_engine, "f1_arithmetic")
    arithmetic_state = arithmetic_engine.run([(logits, targets)])
    print(f"metrics_f1_arithmetic={float(arithmetic_state.metrics['f1_arithmetic']):.6f}")


def run_binary_ranking() -> None:
    engine = Engine(lambda engine, batch: batch)
    y_score = torch.tensor([0.05, 0.20, 0.75, 0.95])
    y_true = torch.tensor([0, 0, 1, 1])
    output_transform: Callable = lambda output: (output[0], output[1])

    ap = AveragePrecision(output_transform=output_transform)
    pr = PrecisionRecallCurve(output_transform=output_transform)
    roc_auc = ROC_AUC(output_transform=output_transform)
    for name, metric in {"ap": ap, "pr_curve": pr, "roc_auc": roc_auc}.items():
        metric.attach(engine, name)

    state = engine.run([(y_score, y_true)])
    print(f"metrics_average_precision={float(state.metrics['ap']):.6f}")
    print(f"metrics_roc_auc={float(state.metrics['roc_auc']):.6f}")
    print(f"metrics_pr_points={len(state.metrics['pr_curve'][0])}")


def run_image() -> None:
    engine = Engine(lambda engine, batch: batch)
    image = torch.rand(2, 3, 8, 8)
    SSIM(data_range=1.0).attach(engine, "ssim")
    state = engine.run([(image, image * 0.9)])
    print(f"metrics_ssim={float(state.metrics['ssim']):.6f}")


def run_fairness() -> None:
    engine = Engine(lambda engine, batch: batch)
    y_pred = torch.tensor(
        [
            [0.9, 0.1],
            [0.1, 0.9],
            [0.8, 0.2],
            [0.2, 0.8],
        ]
    )
    y_true = torch.tensor([0, 1, 1, 0])
    groups = torch.tensor([0, 0, 1, 1])
    SubgroupAccuracyDifference(groups=[0, 1]).attach(engine, "subgroup_acc_diff")
    DemographicParityDifference(groups=[0, 1]).attach(engine, "dp_diff")
    state = engine.run([(y_pred, y_true, groups)])
    print(f"metrics_subgroup_acc_diff={float(state.metrics['subgroup_acc_diff']):.6f}")
    print(f"metrics_demographic_parity_diff={float(state.metrics['dp_diff']):.6f}")


def run_recsys() -> None:
    engine = Engine(lambda engine, batch: batch)
    scores = torch.tensor(
        [
            [0.9, 0.1, 0.2, 0.8],
            [0.1, 0.4, 0.2, 0.3],
        ]
    )
    relevance = torch.tensor(
        [
            [1.0, 0.0, 0.0, 1.0],
            [0.0, 1.0, 0.0, 0.0],
        ]
    )
    HitRate(top_k=[1, 2], ignore_zero_hits=False).attach(engine, "hit_rate")
    NDCG(top_k=[1, 2], ignore_zero_hits=False).attach(engine, "ndcg")
    state = engine.run([(scores, relevance)])
    print(f"metrics_hit_rate={state.metrics['hit_rate']}")
    print(f"metrics_ndcg={state.metrics['ndcg']}")


def run_gpu_info() -> None:
    if torch.cuda.is_available():
        from ignite.metrics import GpuInfo

        engine = Engine(lambda engine, batch: batch)
        GpuInfo().attach(engine, "gpu")
        state = engine.run([(torch.tensor(0), torch.tensor(0))])
        print(f"metrics_gpu={state.metrics['gpu']}")
    else:
        print("metrics_gpu=skipped_no_cuda")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a compact Ignite metrics smoke check.")
    parser.add_argument(
        "--mode",
        choices=("all", "classification", "binary", "image", "fairness", "recsys", "gpu"),
        default="all",
        help="Which metric family to run.",
    )
    args = parser.parse_args()

    manual_seed(0)

    if args.mode in ("all", "classification"):
        run_classification()
    if args.mode in ("all", "binary"):
        run_binary_ranking()
    if args.mode in ("all", "image"):
        run_image()
    if args.mode in ("all", "fairness"):
        run_fairness()
    if args.mode in ("all", "recsys"):
        run_recsys()
    if args.mode in ("all", "gpu"):
        run_gpu_info()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
