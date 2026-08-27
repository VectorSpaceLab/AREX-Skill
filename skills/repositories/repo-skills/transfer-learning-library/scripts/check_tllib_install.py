#!/usr/bin/env python3
"""Check an installed TLLib environment without downloading data.

This root smoke script verifies TLLib imports, reports dependency versions,
exercises representative CPU APIs, and records optional backend visibility. It
is safe to run from any working directory and does not require the original
repository checkout.
"""

from __future__ import annotations

import argparse
import json
import math
import sys


def _finite(name, value):
    import torch

    if not torch.is_tensor(value) or value.dim() != 0 or not torch.isfinite(value).item():
        raise AssertionError(f"{name} expected finite scalar tensor, got {value!r}")
    return float(value.detach().cpu())


def run_checks() -> dict:
    try:
        import numpy as np
        import torch
        import torchvision
        import tllib
    except Exception as exc:  # pragma: no cover - CLI diagnostic path
        raise RuntimeError("Failed to import tllib/torch/torchvision/numpy") from exc

    info = {
        "tllib_version": getattr(tllib, "__version__", "unknown"),
        "torch_version": torch.__version__,
        "torchvision_version": torchvision.__version__,
        "numpy_version": np.__version__,
        "cuda_available": bool(torch.cuda.is_available()),
        "cuda_device_count": int(torch.cuda.device_count()) if hasattr(torch.cuda, "device_count") else 0,
    }

    warnings = []
    numpy_major_minor = tuple(int(part) for part in np.__version__.split(".")[:2])
    if numpy_major_minor >= (1, 24):
        warnings.append("NumPy lacks deprecated np.float; TLLib 0.4 may fail in GRL/loss code. Use numpy<1.24 or patch deliberately.")

    # Representative CPU API checks.
    from tllib.modules.domain_discriminator import DomainDiscriminator
    from tllib.alignment.dann import DomainAdversarialLoss
    from tllib.modules.kernels import GaussianKernel
    from tllib.alignment.dan import MultipleKernelMaximumMeanDiscrepancy
    from tllib.ranking.hscore import h_score
    from tllib.ranking.leep import log_expected_empirical_prediction
    from tllib.self_training.pseudo_label import ConfidenceBasedSelfTrainingLoss
    from tllib.regularization.delta import L2Regularization

    f_s = torch.randn(4, 8)
    f_t = torch.randn(4, 8)
    disc = DomainDiscriminator(in_feature=8, hidden_size=16)
    loss_dann = DomainAdversarialLoss(disc)(f_s, f_t)
    loss_mmd = MultipleKernelMaximumMeanDiscrepancy([GaussianKernel(alpha=2.0)])(f_s, f_t)

    features = np.array([[1., 0.], [0., 1.], [1., 1.], [0.5, 0.2]], dtype=np.float64)
    labels = np.array([0, 1, 0, 1])
    score_h = float(h_score(features, labels))
    predictions = np.array([[0.8, 0.2], [0.1, 0.9], [0.6, 0.4], [0.3, 0.7]], dtype=np.float64)
    score_leep = float(log_expected_empirical_prediction(predictions, labels))
    if not math.isfinite(score_h) or not math.isfinite(score_leep):
        raise AssertionError("ranking smoke returned non-finite score")

    pseudo = ConfidenceBasedSelfTrainingLoss(threshold=0.0)
    pseudo_out = pseudo(torch.randn(4, 3), torch.softmax(torch.randn(4, 3), dim=1))
    pseudo_loss = pseudo_out[0] if isinstance(pseudo_out, tuple) else pseudo_out
    l2_loss = L2Regularization(torch.nn.Linear(2, 2))()

    checks = {
        "domain_adaptation_dann": _finite("DANN", loss_dann),
        "domain_adaptation_mkmmd": _finite("MK-MMD", loss_mmd),
        "ranking_h_score": score_h,
        "ranking_leep": score_leep,
        "self_training_pseudo_label": _finite("pseudo-label", pseudo_loss),
        "task_regularization_l2": _finite("L2Regularization", l2_loss),
    }

    # Vision model factory compatibility check: record as warning if it fails.
    try:
        from tllib.vision.models.digits import lenet
        model = lenet(pretrained=False)
        with torch.no_grad():
            out = model(torch.randn(1, 1, 28, 28))
        checks["vision_lenet_shape"] = list(out.shape)
    except Exception as exc:  # pragma: no cover - CLI diagnostic path
        warnings.append(f"Vision model factory check failed: {type(exc).__name__}: {exc}")

    return {"status": "ok", "environment": info, "checks": checks, "warnings": warnings}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Run safe import/API checks for an installed TLLib package.")
    parser.add_argument("--json", action="store_true", help="print machine-readable JSON only")
    args = parser.parse_args(argv)

    payload = run_checks()
    if args.json:
        print(json.dumps(payload, sort_keys=True))
    else:
        print("TLLib install check: ok")
        for key, value in payload["environment"].items():
            print(f"  {key}: {value}")
        for key, value in payload["checks"].items():
            print(f"  {key}: {value}")
        for warning in payload["warnings"]:
            print(f"  warning: {warning}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # pragma: no cover - CLI diagnostic path
        print(f"TLLib install check: failed: {exc}", file=sys.stderr)
        raise
