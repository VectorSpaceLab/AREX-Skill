#!/usr/bin/env python3
"""Tiny CPU smoke for the domain-adaptation API surface."""

from __future__ import annotations

import json
from typing import Any, Dict

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

import tllib
from tllib.alignment.adda import DomainAdversarialLoss as AddaDomainAdversarialLoss
from tllib.alignment.bsp import BatchSpectralPenalizationLoss
from tllib.alignment.cdan import ConditionalDomainAdversarialLoss
from tllib.alignment.coral import CorrelationAlignmentLoss
from tllib.alignment.dan import MultipleKernelMaximumMeanDiscrepancy
from tllib.alignment.dann import DomainAdversarialLoss as DannDomainAdversarialLoss
from tllib.alignment.jan import JointMultipleKernelMaximumMeanDiscrepancy
from tllib.alignment.mcd import ImageClassifierHead, classifier_discrepancy, entropy as mcd_entropy
from tllib.alignment.mdd import ClassificationMarginDisparityDiscrepancy, ImageClassifier as MDDImageClassifier
from tllib.alignment.osbp import ImageClassifier as OSBPImageClassifier, UnknownClassBinaryCrossEntropy
from tllib.alignment.regda import FastPseudoLabelGenerator2d, PseudoLabelGenerator2d, RegressionDisparity
from tllib.modules.domain_discriminator import DomainDiscriminator
from tllib.modules.kernels import GaussianKernel
from tllib.normalization.afn import AdaptiveFeatureNorm
from tllib.reweight.iwan import ImportanceWeightModule
from tllib.reweight.pada import ClassWeightModule
from tllib.self_training.mcc import MinimumClassConfusionLoss
from tllib.vision.models.keypoint_detection.loss import JointsKLLoss


class ToyBackbone(nn.Module):
    def __init__(self, out_features: int = 8):
        super().__init__()
        self.out_features = out_features
        self.net = nn.Sequential(
            nn.Conv2d(3, out_features, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_features),
            nn.ReLU(inplace=True),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


class ToyProbabilityDiscriminator(nn.Module):
    def __init__(self, in_features: int):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(in_features, 16),
            nn.ReLU(inplace=True),
            nn.Linear(16, 1),
            nn.Sigmoid(),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


def scalar(value: torch.Tensor) -> float:
    return float(value.detach().cpu().item())


def finite(name: str, value: torch.Tensor) -> float:
    if not torch.isfinite(value).all():
        raise RuntimeError(f"{name} produced non-finite values: {value}")
    return scalar(value)


def grad_norm(tensor: torch.Tensor):
    if tensor.grad is None:
        return None
    return float(tensor.grad.detach().norm().cpu().item())


def smoke_feature_losses() -> Dict[str, Any]:
    batch = 4
    feature_dim = 8
    num_classes = 3

    fs = torch.randn(batch, feature_dim, requires_grad=True)
    ft = torch.randn(batch, feature_dim, requires_grad=True)
    gs = torch.randn(batch, num_classes, requires_grad=True)
    gt = torch.randn(batch, num_classes, requires_grad=True)
    mcd_maps = torch.randn(batch, feature_dim, 4, 4, requires_grad=True)
    weight_logits = torch.randn(batch, num_classes)

    dann_disc = DomainDiscriminator(feature_dim, hidden_size=16)
    dann_loss_fn = DannDomainAdversarialLoss(dann_disc)

    importance_module = ImportanceWeightModule(dann_disc)
    importance_weights = importance_module.get_importance_weight(fs.detach())
    target_weights = torch.ones_like(importance_weights) * importance_weights.mean()
    dann_loss = dann_loss_fn(fs, ft, importance_weights, target_weights)

    adda_disc = ToyProbabilityDiscriminator(feature_dim)
    adda_loss_fn = AddaDomainAdversarialLoss()
    adda_loss = adda_loss_fn(adda_disc(fs), "source") + adda_loss_fn(adda_disc(ft), "target")

    cdan_disc = DomainDiscriminator(feature_dim * num_classes, hidden_size=32)
    cdan_loss_fn = ConditionalDomainAdversarialLoss(cdan_disc)
    cdan_loss = cdan_loss_fn(gs, fs, gt, ft)

    dan_loss_fn = MultipleKernelMaximumMeanDiscrepancy((GaussianKernel(alpha=0.5), GaussianKernel(alpha=1.0)))
    dan_loss = dan_loss_fn(fs, ft)

    jan_loss_fn = JointMultipleKernelMaximumMeanDiscrepancy(
        ((GaussianKernel(alpha=0.5),), (GaussianKernel(alpha=1.0),)),
        linear=False,
    )
    jan_loss = jan_loss_fn((fs, fs * 0.5), (ft, ft * 0.5))

    coral_loss = CorrelationAlignmentLoss()(fs, ft)
    bsp_loss = BatchSpectralPenalizationLoss()(fs, ft)
    afn_loss = AdaptiveFeatureNorm(delta=1.0)(fs) + AdaptiveFeatureNorm(delta=1.0)(ft)
    mcc_loss = MinimumClassConfusionLoss(temperature=2.0)(gt)

    mcd_head1 = ImageClassifierHead(feature_dim, num_classes, bottleneck_dim=16)
    mcd_head2 = ImageClassifierHead(feature_dim, num_classes, bottleneck_dim=16)
    mcd_prob1 = F.softmax(mcd_head1(mcd_maps), dim=1)
    mcd_prob2 = F.softmax(mcd_head2(mcd_maps), dim=1)
    mcd_disc_loss = classifier_discrepancy(mcd_prob1, mcd_prob2)
    mcd_entropy_loss = mcd_entropy(mcd_prob1)

    class_weights = ClassWeightModule(temperature=0.2)(weight_logits.clone())

    osbp_input = torch.randn(batch, 3, 8, 8, requires_grad=True)
    osbp_model = OSBPImageClassifier(ToyBackbone(feature_dim), num_classes=num_classes + 1, bottleneck_dim=16)
    osbp_model.train()
    osbp_logits, osbp_features = osbp_model(osbp_input, grad_reverse=True)
    osbp_loss = UnknownClassBinaryCrossEntropy(t=0.5)(osbp_logits)

    mdd_input_s = torch.randn(batch, 3, 8, 8, requires_grad=True)
    mdd_input_t = torch.randn(batch, 3, 8, 8, requires_grad=True)
    mdd_model = MDDImageClassifier(ToyBackbone(feature_dim), num_classes=num_classes, bottleneck_dim=16, width=16)
    mdd_model.train()
    mdd_s, mdd_s_adv = mdd_model(mdd_input_s)
    mdd_model.step()
    mdd_t, mdd_t_adv = mdd_model(mdd_input_t)
    mdd_loss = ClassificationMarginDisparityDiscrepancy(margin=4.0)(mdd_s, mdd_s_adv, mdd_t, mdd_t_adv)

    loss_tensors = {
        "dann": dann_loss,
        "adda": adda_loss,
        "cdan": cdan_loss,
        "dan": dan_loss,
        "jan": jan_loss,
        "coral": coral_loss,
        "bsp": bsp_loss,
        "afn": afn_loss,
        "mcc": mcc_loss,
        "mcd_discrepancy": mcd_disc_loss,
        "mcd_entropy": mcd_entropy_loss,
        "osbp": osbp_loss,
        "mdd": mdd_loss,
    }
    summary = {name: finite(name, value) for name, value in loss_tensors.items()}
    total = torch.stack(list(loss_tensors.values())).sum()
    total.backward()

    summary["combined"] = scalar(total)
    summary["dann_accuracy"] = float(dann_loss_fn.domain_discriminator_accuracy)
    summary["cdan_accuracy"] = float(cdan_loss_fn.domain_discriminator_accuracy)
    summary["weights"] = {
        "class_weight_max": scalar(class_weights.max()),
        "importance_weight_mean": scalar(importance_weights.mean()),
    }
    summary["gradients"] = {
        "fs": grad_norm(fs),
        "ft": grad_norm(ft),
        "mcd_maps": grad_norm(mcd_maps),
        "dann_discriminator": grad_norm(next(dann_disc.parameters())),
        "cdan_discriminator": grad_norm(next(cdan_disc.parameters())),
        "adda_discriminator": grad_norm(next(adda_disc.parameters())),
        "osbp_input": grad_norm(osbp_input),
        "mdd_input_source": grad_norm(mdd_input_s),
        "mdd_input_target": grad_norm(mdd_input_t),
        "mdd_head": grad_norm(mdd_model.head[0].weight),
    }

    osbp_model.eval()
    mdd_model.eval()
    summary["wrappers"] = {
        "osbp_train_shape": list(osbp_logits.shape),
        "osbp_eval_shape": list(osbp_model(torch.randn(batch, 3, 8, 8)).shape),
        "osbp_feature_shape": list(osbp_features.shape),
        "mdd_train_shape": [list(mdd_s.shape), list(mdd_s_adv.shape)],
        "mdd_eval_shape": list(mdd_model(torch.randn(batch, 3, 8, 8)).shape),
    }

    return summary


def smoke_regda() -> Dict[str, Any]:
    batch = 2
    num_keypoints = 2
    heatmap_size = 8
    source_heatmaps = torch.randn(batch, num_keypoints, heatmap_size, heatmap_size, requires_grad=True)
    source_adv = torch.randn(batch, num_keypoints, heatmap_size, heatmap_size, requires_grad=True)
    target_heatmaps = torch.randn(batch, num_keypoints, heatmap_size, heatmap_size, requires_grad=True)
    target_adv = torch.randn(batch, num_keypoints, heatmap_size, heatmap_size, requires_grad=True)
    criterion = JointsKLLoss()

    generator_name = "PseudoLabelGenerator2d"
    try:
        pseudo_generator = PseudoLabelGenerator2d(num_keypoints, height=heatmap_size, width=heatmap_size, sigma=1)
        regda_loss_fn = RegressionDisparity(pseudo_generator, criterion)
        regda_min = regda_loss_fn(source_heatmaps, source_adv, mode="min")
        regda_max = regda_loss_fn(target_heatmaps, target_adv, mode="max")
    except Exception as exc:
        if "numpy" not in repr(exc).lower() and "int" not in repr(exc).lower():
            raise
        generator_name = "FastPseudoLabelGenerator2d"
        pseudo_generator = FastPseudoLabelGenerator2d(sigma=1)
        regda_loss_fn = RegressionDisparity(pseudo_generator, criterion)
        regda_min = regda_loss_fn(source_heatmaps, source_adv, mode="min")
        regda_max = regda_loss_fn(target_heatmaps, target_adv, mode="max")

    summary = {
        "generator": generator_name,
        "regda_min": finite("regda_min", regda_min),
        "regda_max": finite("regda_max", regda_max),
    }
    total = regda_min + regda_max
    total.backward()
    summary["combined"] = scalar(total)
    summary["gradients"] = {
        "source_heatmaps": grad_norm(source_heatmaps),
        "source_adv": grad_norm(source_adv),
        "target_heatmaps": grad_norm(target_heatmaps),
        "target_adv": grad_norm(target_adv),
    }
    if generator_name == "FastPseudoLabelGenerator2d":
        summary["warning"] = "Fell back to the torch-only pseudo-label generator because the documented helper hit a NumPy alias compatibility issue."
    return summary


def main() -> int:
    torch.manual_seed(7)
    np.random.seed(7)

    summary = {
        "runtime": {
            "tllib": getattr(tllib, "__version__", "unknown"),
            "torch": torch.__version__,
            "numpy": np.__version__,
        },
        "feature_losses": smoke_feature_losses(),
        "regda": smoke_regda(),
    }

    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
