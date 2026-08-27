#!/usr/bin/env python3
"""Small CPU smoke checks for TLLib self-training APIs.

The script imports the installed ``tllib`` package and runs tiny tensor checks for
pseudo-label, consistency, teacher, weak/strong, class-confusion, dynamic
thresholding, class-balance, and DST losses/helpers. It does not load datasets,
download checkpoints, convert external files, or run benchmark training.
"""

from __future__ import annotations

import argparse
import json
import sys


def _require_finite_scalar(name, value):
    import torch

    if not torch.is_tensor(value):
        raise AssertionError("{}: expected a torch.Tensor, got {!r}".format(name, type(value)))
    if value.dim() != 0:
        raise AssertionError("{}: expected scalar tensor, got shape {}".format(name, tuple(value.shape)))
    if not torch.isfinite(value).item():
        raise AssertionError("{}: expected finite scalar, got {!r}".format(name, value.item()))
    return float(value.detach().cpu())


def _require_shape(name, value, expected):
    shape = tuple(value.shape)
    expected = tuple(expected)
    if shape != expected:
        raise AssertionError("{}: expected shape {}, got {}".format(name, expected, shape))
    return list(shape)


def check_pseudo_label(verbose=False):
    import torch
    from tllib.self_training.pseudo_label import ConfidenceBasedSelfTrainingLoss

    logits_train = torch.tensor(
        [[1.2, 0.1, -0.2], [0.0, 1.1, 0.2], [0.4, 0.2, 0.1]], dtype=torch.float32
    )
    logits_target = torch.tensor(
        [[5.0, 0.1, -1.0], [0.2, 4.8, -0.2], [0.3, 0.2, 0.1]], dtype=torch.float32
    )
    criterion = ConfidenceBasedSelfTrainingLoss(threshold=0.80)
    loss, mask, pseudo = criterion(logits_train, logits_target)

    result = {
        "loss": _require_finite_scalar("ConfidenceBasedSelfTrainingLoss", loss),
        "mask_shape": _require_shape("pseudo_label.mask", mask, (3,)),
        "pseudo_shape": _require_shape("pseudo_label.pseudo", pseudo, (3,)),
        "mask_sum": float(mask.sum().item()),
        "pseudo_labels": [int(v) for v in pseudo.detach().cpu().tolist()],
    }
    if result["mask_sum"] != 2.0:
        raise AssertionError("pseudo-label: expected exactly two selected samples, got {}".format(result["mask_sum"]))
    if verbose:
        print("pseudo-label checks passed", file=sys.stderr)
    return result


def check_consistency(verbose=False):
    import torch
    from tllib.self_training.pi_model import ConsistencyLoss, L2ConsistencyLoss, sigmoid_warm_up

    p1 = torch.softmax(torch.tensor([[2.0, 0.0, -1.0], [0.2, 1.0, 0.0]], dtype=torch.float32), dim=1)
    p2 = torch.softmax(torch.tensor([[1.7, 0.2, -0.8], [0.0, 1.2, -0.1]], dtype=torch.float32), dim=1)
    mask = torch.tensor([1.0, 0.0], dtype=torch.float32)

    l2_loss = L2ConsistencyLoss()(p1, p2, mask=mask)

    def l1_distance(a, b):
        return (a - b).abs().sum(dim=1)

    per_sample = ConsistencyLoss(l1_distance, reduction="none")(p1, p2, mask=mask)
    _require_shape("ConsistencyLoss.none", per_sample, (2,))
    if per_sample[1].item() != 0.0:
        raise AssertionError("ConsistencyLoss: masked sample should be zero")

    warmup = sigmoid_warm_up(current_epoch=5, warm_up_epochs=10)
    if not (0.0 < warmup < 1.0):
        raise AssertionError("sigmoid_warm_up: expected value in (0, 1), got {}".format(warmup))

    result = {
        "l2_loss": _require_finite_scalar("L2ConsistencyLoss", l2_loss),
        "custom_loss_shape": list(per_sample.shape),
        "warmup_epoch_5_of_10": float(warmup),
    }
    if verbose:
        print("consistency checks passed", file=sys.stderr)
    return result


def check_ema_teacher(verbose=False):
    import torch
    import torch.nn as nn
    from tllib.self_training.mean_teacher import EMATeacher

    torch.manual_seed(13)
    model = nn.Linear(4, 2)
    teacher = EMATeacher(model, alpha=0.5)
    x = torch.ones(3, 4)
    teacher_out = teacher(x)
    _require_shape("EMATeacher.forward", teacher_out, (3, 2))

    before = [p.detach().clone() for p in teacher.teacher.parameters()]
    with torch.no_grad():
        for p in model.parameters():
            p.add_(1.0)
    teacher.update()
    after = [p.detach().clone() for p in teacher.teacher.parameters()]

    changed = [not torch.allclose(a, b) for a, b in zip(before, after)]
    if not all(changed):
        raise AssertionError("EMATeacher.update: expected every teacher parameter to change after student update")
    if any(p.requires_grad for p in teacher.teacher.parameters()):
        raise AssertionError("EMATeacher: teacher parameters should not require gradients")

    result = {"forward_shape": [3, 2], "updated_parameters": len(after), "alpha": float(teacher.alpha)}
    if verbose:
        print("EMA teacher checks passed", file=sys.stderr)
    return result


def check_uda_and_mcc(verbose=False):
    import torch
    from tllib.self_training.uda import StrongWeakConsistencyLoss
    from tllib.self_training.mcc import MinimumClassConfusionLoss
    from tllib.self_training.cc_loss import CCConsistency

    logits_weak = torch.tensor(
        [[4.0, 0.2, -0.2], [0.1, 3.5, 0.0], [0.3, 0.2, 0.1], [0.2, -0.1, 3.7]], dtype=torch.float32
    )
    logits_strong = torch.tensor(
        [[3.6, 0.4, -0.1], [0.0, 3.2, 0.2], [0.2, 0.3, 0.0], [0.0, 0.1, 3.1]], dtype=torch.float32
    )

    uda = StrongWeakConsistencyLoss(threshold=0.70, temperature=0.85)
    uda_loss = uda(logits_strong, logits_weak)

    mcc = MinimumClassConfusionLoss(temperature=2.0)
    mcc_loss = mcc(logits_weak)

    cc = CCConsistency(temperature=2.0, thr=0.5)
    cc_loss, cc_ratio = cc(logits_weak, logits_strong)
    if not hasattr(cc_ratio, "item"):
        raise AssertionError("CCConsistency: expected non-empty mask ratio tensor in this fixture")

    result = {
        "uda": _require_finite_scalar("StrongWeakConsistencyLoss", uda_loss),
        "mcc": _require_finite_scalar("MinimumClassConfusionLoss", mcc_loss),
        "cc_consistency": _require_finite_scalar("CCConsistency.loss", cc_loss),
        "cc_mask_ratio": float(cc_ratio.detach().cpu()),
    }
    if verbose:
        print("UDA/MCC checks passed", file=sys.stderr)
    return result


def check_dynamic_thresholding(verbose=False):
    import torch
    from tllib.self_training.flexmatch import DynamicThresholdingModule

    module = DynamicThresholdingModule(
        threshold=0.95,
        warmup=False,
        mapping_func=lambda x: x / (2 - x),
        num_classes=3,
        n_unlabeled_samples=6,
        device=torch.device("cpu"),
    )
    pseudo = torch.tensor([0, 1, 2, 1], dtype=torch.long)
    initial_thresholds = module.get_threshold(pseudo)
    _require_shape("DynamicThresholdingModule.initial_thresholds", initial_thresholds, (4,))
    if not torch.isfinite(initial_thresholds).all().item():
        raise AssertionError("DynamicThresholdingModule: expected finite thresholds")

    idxes = torch.tensor([0, 1, 2, 5], dtype=torch.long)
    selected_mask = torch.tensor([1, 0, 1, 1], dtype=torch.long)
    module.update(idxes, selected_mask, pseudo)
    expected_outputs = torch.tensor([0, -1, 2, -1, -1, 1], dtype=torch.long)
    if not torch.equal(module.net_outputs.cpu(), expected_outputs):
        raise AssertionError(
            "DynamicThresholdingModule.update: expected {}, got {}".format(
                expected_outputs.tolist(), module.net_outputs.cpu().tolist()
            )
        )
    updated_thresholds = module.get_threshold(pseudo)
    _require_shape("DynamicThresholdingModule.updated_thresholds", updated_thresholds, (4,))

    result = {
        "initial_thresholds": [float(v) for v in initial_thresholds.detach().cpu().tolist()],
        "updated_thresholds": [float(v) for v in updated_thresholds.detach().cpu().tolist()],
        "state": [int(v) for v in module.net_outputs.detach().cpu().tolist()],
    }
    if verbose:
        print("dynamic-threshold checks passed", file=sys.stderr)
    return result


def check_class_balance_and_dst(verbose=False):
    import torch
    from tllib.self_training.self_ensemble import ClassBalanceLoss
    from tllib.self_training.dst import WorstCaseEstimationLoss

    probs = torch.softmax(torch.tensor([[2.0, 0.0, -1.0], [0.1, 2.2, 0.0], [0.0, 0.1, 2.1]], dtype=torch.float32), dim=1)
    balance_loss = ClassBalanceLoss(num_classes=3)(probs)

    y_l = torch.tensor([[2.5, 0.1, -0.2], [0.0, 2.0, 0.2]], dtype=torch.float32)
    y_l_adv = torch.tensor([[2.0, 0.0, 0.1], [0.1, 1.7, 0.0]], dtype=torch.float32)
    y_u = torch.tensor([[2.1, 0.1, 0.0], [0.0, 0.1, 2.2]], dtype=torch.float32)
    y_u_adv = torch.tensor([[0.4, 1.2, 0.1], [1.0, 0.3, 0.4]], dtype=torch.float32)
    wce_loss = WorstCaseEstimationLoss(eta_prime=2.0)(y_l, y_l_adv, y_u, y_u_adv)

    result = {
        "class_balance": _require_finite_scalar("ClassBalanceLoss", balance_loss),
        "dst_worst_case": _require_finite_scalar("WorstCaseEstimationLoss", wce_loss),
    }
    if verbose:
        print("class-balance/DST checks passed", file=sys.stderr)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description="Run tiny CPU checks for TLLib self-training APIs.")
    parser.add_argument("--verbose", action="store_true", help="print progress messages to stderr")
    args = parser.parse_args(argv)

    import torch
    import tllib

    summary = {
        "status": "ok",
        "tllib_version": getattr(tllib, "__version__", "unknown"),
        "torch_version": torch.__version__,
        "checks": {
            "pseudo_label": check_pseudo_label(args.verbose),
            "consistency": check_consistency(args.verbose),
            "ema_teacher": check_ema_teacher(args.verbose),
            "uda_and_mcc": check_uda_and_mcc(args.verbose),
            "dynamic_thresholding": check_dynamic_thresholding(args.verbose),
            "class_balance_and_dst": check_class_balance_and_dst(args.verbose),
        },
        "notes": [
            "CPU component smoke only; no dataset, checkpoint, pretrained download, MoCo conversion, or benchmark training was run.",
            "Full SSL workflows require user-provided data/model loaders and usually CUDA for practical training.",
        ],
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
