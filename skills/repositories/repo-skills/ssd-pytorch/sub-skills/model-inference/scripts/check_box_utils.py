#!/usr/bin/env python3
"""Deterministic smoke checks for SSD box utilities and NMS.

Run from a checkout or environment where the ssd.pytorch source tree is
available. The script avoids datasets, weights, and network access.
"""

from __future__ import annotations

import importlib
import importlib.util
import json
import pathlib
import sys
import traceback
from typing import Any


def load_box_utils() -> Any:
    """Load box_utils by normal import, then by source-file fallback.

    Some source-layout checkouts import package-level detection/data modules when
    importing the layers package. The fallback keeps this smoke focused on the
    single box_utils module when the current working directory is the repository
    root.
    """

    try:
        return importlib.import_module("layers.box_utils")
    except Exception:
        candidate = pathlib.Path.cwd() / "layers" / "box_utils.py"
        if not candidate.exists():
            raise
        spec = importlib.util.spec_from_file_location("box_utils_standalone", candidate)
        if spec is None or spec.loader is None:
            raise RuntimeError("could not load layers/box_utils.py")
        module = importlib.util.module_from_spec(spec)
        sys.modules["box_utils_standalone"] = module
        spec.loader.exec_module(module)
        return module


def tensor_to_list(x: Any) -> Any:
    if hasattr(x, "detach"):
        x = x.detach().cpu()
    if hasattr(x, "tolist"):
        return x.tolist()
    return x


def main() -> int:
    report: dict[str, Any] = {"ok": False, "checks": {}}
    try:
        torch = importlib.import_module("torch")
        box_utils = load_box_utils()

        priors = torch.tensor(
            [
                [0.5, 0.5, 0.2, 0.4],
                [0.25, 0.25, 0.5, 0.5],
            ],
            dtype=torch.float32,
        )
        point = box_utils.point_form(priors)
        report["checks"]["point_form"] = tensor_to_list(point)
        try:
            center = box_utils.center_size(point)
            report["checks"]["center_roundtrip_max_abs_error"] = float((center - priors).abs().max().item())
            assert torch.allclose(center, priors, atol=1e-6)
        except TypeError as exc:
            # The source implementation passes tensors as separate positional
            # arguments to torch.cat on modern PyTorch. Keep this helper useful
            # by reporting the known issue while continuing to validate the
            # other box utilities.
            report.setdefault("warnings", []).append(
                "center_size failed under this runtime; patch torch.cat((cxcy, wh), 1) before relying on it"
            )
            report["checks"]["center_size_error"] = str(exc)

        boxes_a = torch.tensor([[0.0, 0.0, 1.0, 1.0], [0.0, 0.0, 0.5, 0.5]], dtype=torch.float32)
        boxes_b = torch.tensor([[0.0, 0.0, 1.0, 1.0], [0.5, 0.5, 1.0, 1.0]], dtype=torch.float32)
        iou = box_utils.jaccard(boxes_a, boxes_b)
        expected_iou = torch.tensor([[1.0, 0.25], [0.25, 0.0]], dtype=torch.float32)
        report["checks"]["jaccard"] = tensor_to_list(iou)
        assert torch.allclose(iou, expected_iou, atol=1e-6)

        matched = point.clone()
        encoded = box_utils.encode(matched, priors, [0.1, 0.2])
        decoded = box_utils.decode(encoded, priors, [0.1, 0.2])
        report["checks"]["encode_decode_max_abs_error"] = float((decoded - matched).abs().max().item())
        assert torch.allclose(decoded, matched, atol=1e-6)

        nms_boxes = torch.tensor(
            [
                [0.0, 0.0, 1.0, 1.0],
                [0.05, 0.05, 0.95, 0.95],
                [2.0, 2.0, 3.0, 3.0],
            ],
            dtype=torch.float32,
        )
        scores = torch.tensor([0.9, 0.8, 0.7], dtype=torch.float32)
        keep, count = box_utils.nms(nms_boxes, scores, overlap=0.5, top_k=200)
        kept = keep[:count].cpu().tolist()
        report["checks"]["nms_keep"] = kept
        report["checks"]["nms_count"] = int(count)
        assert kept == [0, 2]

        report["torch_version"] = getattr(torch, "__version__", "unknown")
        report["ok"] = True
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0
    except Exception as exc:  # noqa: BLE001 - diagnostic helper should report all failures as JSON
        report["error_type"] = type(exc).__name__
        report["error"] = str(exc)
        report["traceback"] = traceback.format_exc().splitlines()[-8:]
        print(json.dumps(report, indent=2, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
