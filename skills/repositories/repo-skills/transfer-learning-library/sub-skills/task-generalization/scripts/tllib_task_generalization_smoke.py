#!/usr/bin/env python3
"""Small CPU smoke checks for TLLib task-generalization APIs.

The script imports the installed ``tllib`` package and runs tiny tensor checks for
regularization, normalization, reweighting, and CORAL components. It does not
load datasets, download checkpoints, or run benchmark training.
"""

from __future__ import annotations

import argparse
import copy
import json
import math
import sys
from collections import OrderedDict


def _require_finite_scalar(name, value):
    import torch

    if not torch.is_tensor(value):
        raise AssertionError(f"{name}: expected a torch.Tensor, got {type(value)!r}")
    if value.dim() != 0:
        raise AssertionError(f"{name}: expected scalar tensor, got shape {tuple(value.shape)}")
    if not torch.isfinite(value).item():
        raise AssertionError(f"{name}: expected finite scalar, got {value.item()!r}")
    return float(value.detach().cpu())


def _require_shape(name, value, expected):
    shape = tuple(value.shape)
    if shape != tuple(expected):
        raise AssertionError(f"{name}: expected shape {expected}, got {shape}")
    return shape


def check_regularization(verbose=False):
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    from tllib.regularization.delta import (
        AttentionBehavioralRegularization,
        BehavioralRegularization,
        IntermediateLayerGetter,
        L2Regularization,
        SPRegularization,
    )
    from tllib.regularization.bss import BatchSpectralShrinkage
    from tllib.regularization.co_tuning import CoTuningLoss
    from tllib.regularization.knowledge_distillation import KnowledgeDistillationLoss
    from tllib.regularization.bi_tuning import Classifier as BiClassifier, BiTuning

    torch.manual_seed(7)
    results = {}

    model = nn.Sequential(nn.Linear(4, 3), nn.ReLU(), nn.Linear(3, 2))
    results["l2"] = _require_finite_scalar("L2Regularization", L2Regularization(model)())

    source_model = nn.Sequential(OrderedDict([("fc", nn.Linear(4, 3))]))
    target_model = copy.deepcopy(source_model)
    with torch.no_grad():
        for p in target_model.parameters():
            p.add_(0.05)
    results["l2_sp"] = _require_finite_scalar("SPRegularization", SPRegularization(source_model, target_model)())

    source_maps = OrderedDict([("layer", torch.randn(2, 3, 4, 4))])
    target_maps = OrderedDict([("layer", source_maps["layer"] + 0.1)])
    results["behavioral"] = _require_finite_scalar(
        "BehavioralRegularization", BehavioralRegularization()(source_maps, target_maps)
    )
    attention = [torch.ones(3)]
    results["attention_behavioral"] = _require_finite_scalar(
        "AttentionBehavioralRegularization", AttentionBehavioralRegularization(attention)(source_maps, target_maps)
    )

    probe = nn.Sequential(OrderedDict([("fc1", nn.Linear(4, 3)), ("relu", nn.ReLU()), ("fc2", nn.Linear(3, 2))]))
    getter = IntermediateLayerGetter(probe, return_layers=["fc1"], keep_output=True)
    layer_outputs, final_output = getter(torch.randn(2, 4))
    _require_shape("IntermediateLayerGetter.fc1", layer_outputs["fc1"], (2, 3))
    _require_shape("IntermediateLayerGetter.output", final_output, (2, 2))
    results["intermediate_layer_getter"] = True

    features = torch.randn(5, 3)
    results["bss"] = _require_finite_scalar("BatchSpectralShrinkage", BatchSpectralShrinkage(k=1)(features))

    source_logits = torch.randn(4, 5)
    relationship_targets = F.softmax(torch.randn(4, 5), dim=1)
    results["co_tuning"] = _require_finite_scalar("CoTuningLoss", CoTuningLoss()(source_logits, relationship_targets))

    student_logits = torch.randn(4, 5)
    teacher_logits = torch.randn(4, 5)
    results["knowledge_distillation"] = _require_finite_scalar(
        "KnowledgeDistillationLoss", KnowledgeDistillationLoss(T=2.0)(student_logits, teacher_logits)
    )

    class TinyBackbone(nn.Module):
        out_features = 4

        def __init__(self):
            super().__init__()
            self.fc = nn.Linear(4, 4)

        def forward(self, x):
            x = self.fc(x.view(x.size(0), 4))
            return x.view(x.size(0), 4, 1, 1)

    encoder_q = BiClassifier(TinyBackbone(), num_classes=2, projection_dim=3)
    encoder_k = BiClassifier(TinyBackbone(), num_classes=2, projection_dim=3)
    bituning = BiTuning(encoder_q, encoder_k, num_classes=2, K=2, m=0.9, T=0.2)
    y_q, logits_z, logits_y, labels_c = bituning(torch.randn(2, 4), torch.randn(2, 4), torch.tensor([0, 1]))
    _require_shape("BiTuning.y_q", y_q, (2, 2))
    _require_shape("BiTuning.logits_z", logits_z, (2, 5))
    _require_shape("BiTuning.logits_y", logits_y, (2, 5))
    _require_shape("BiTuning.labels_c", labels_c, (2, 5))
    if not all(torch.isfinite(t).all().item() for t in (y_q, logits_z, logits_y, labels_c)):
        raise AssertionError("BiTuning: expected finite outputs")
    results["bi_tuning"] = True

    if verbose:
        print("regularization checks passed", file=sys.stderr)
    return results


def check_normalization(verbose=False):
    import torch
    import torch.nn as nn
    from tllib.normalization.ibn import InstanceBatchNorm2d
    from tllib.normalization.mixstyle import MixStyle
    from tllib.normalization.stochnorm import StochNorm2d, convert_model

    torch.manual_seed(11)
    results = {}

    x = torch.randn(4, 3, 4, 4)
    mix = MixStyle(p=1.0, alpha=0.5)
    mix.train()
    mixed = mix(x)
    _require_shape("MixStyle.train", mixed, x.shape)
    if not torch.isfinite(mixed).all().item():
        raise AssertionError("MixStyle: non-finite training output")
    mix.eval()
    unchanged = mix(x)
    if not torch.allclose(unchanged, x):
        raise AssertionError("MixStyle: eval mode should return unchanged input")
    results["mixstyle"] = True

    ibn = InstanceBatchNorm2d(planes=4, ratio=0.5)
    ibn.train()
    ibn_out = ibn(torch.randn(4, 4, 4, 4))
    _require_shape("InstanceBatchNorm2d", ibn_out, (4, 4, 4, 4))
    if not torch.isfinite(ibn_out).all().item():
        raise AssertionError("InstanceBatchNorm2d: non-finite output")
    results["ibn"] = True

    stoch = StochNorm2d(num_features=3, p=0.5)
    stoch.eval()
    stoch_out = stoch(x)
    _require_shape("StochNorm2d.eval", stoch_out, x.shape)
    if not torch.isfinite(stoch_out).all().item():
        raise AssertionError("StochNorm2d eval: non-finite output")
    results["stochnorm_eval"] = True

    model = nn.Sequential(nn.Conv2d(3, 3, kernel_size=1), nn.BatchNorm2d(3), nn.ReLU())
    converted = convert_model(model, p=0.5)
    converted.eval()
    if not any(isinstance(m, StochNorm2d) for m in converted.modules()):
        raise AssertionError("convert_model: expected at least one StochNorm2d module")
    converted_out = converted(x)
    _require_shape("convert_model.eval", converted_out, x.shape)
    results["stochnorm_convert_eval"] = True

    if verbose:
        print("normalization checks passed", file=sys.stderr)
    return results


def check_reweight_and_coral(verbose=False):
    import torch
    from tllib.alignment.coral import CorrelationAlignmentLoss
    from tllib.reweight.groupdro import AutomaticUpdateDomainWeightModule

    results = {}

    module = AutomaticUpdateDomainWeightModule(num_domains=3, eta=0.1, device=torch.device("cpu"))
    losses = torch.tensor([1.0, 0.2], dtype=torch.float32)
    idxes = [0, 2]
    module.update(losses, idxes)
    weights = module.get_domain_weight(idxes)
    if weights.shape != losses.shape:
        raise AssertionError(f"GroupDRO weights: expected shape {tuple(losses.shape)}, got {tuple(weights.shape)}")
    if not torch.isfinite(weights).all().item() or not torch.all(weights >= 0).item():
        raise AssertionError("GroupDRO weights: expected finite non-negative weights")
    if not math.isclose(float(weights.sum()), 1.0, rel_tol=1e-5, abs_tol=1e-5):
        raise AssertionError(f"GroupDRO weights: expected normalized selected weights, got sum={float(weights.sum())}")
    results["groupdro"] = [float(v) for v in weights.detach().cpu()]

    coral = CorrelationAlignmentLoss()
    source_features = torch.randn(6, 4)
    target_features = source_features + 0.1 * torch.randn(6, 4)
    results["coral"] = _require_finite_scalar("CorrelationAlignmentLoss", coral(source_features, target_features))

    if verbose:
        print("reweight/CORAL checks passed", file=sys.stderr)
    return results


def main(argv=None):
    parser = argparse.ArgumentParser(description="Run tiny CPU checks for TLLib task-generalization APIs.")
    parser.add_argument("--verbose", action="store_true", help="print progress messages to stderr")
    args = parser.parse_args(argv)

    import torch
    import tllib

    summary = {
        "status": "ok",
        "tllib_version": getattr(tllib, "__version__", "unknown"),
        "torch_version": torch.__version__,
        "checks": {
            "regularization": check_regularization(args.verbose),
            "normalization": check_normalization(args.verbose),
            "reweight_and_coral": check_reweight_and_coral(args.verbose),
        },
        "notes": [
            "CPU component smoke only; no dataset, checkpoint, pretrained download, or benchmark training was run.",
            "StochNorm is checked in eval mode on CPU because TLLib 0.4 training forward uses a CUDA mask.",
        ],
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
