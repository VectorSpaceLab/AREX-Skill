#!/usr/bin/env python3
"""Check a Python environment for core MMDetection usability."""

from __future__ import annotations

import importlib
import importlib.metadata as metadata
import inspect
import sys
from dataclasses import dataclass


@dataclass
class CheckResult:
    name: str
    ok: bool
    detail: str


def version_of(distribution: str) -> str:
    try:
        return metadata.version(distribution)
    except metadata.PackageNotFoundError:
        return "not-installed"


def import_check(module_name: str) -> CheckResult:
    try:
        module = importlib.import_module(module_name)
    except Exception as exc:  # noqa: BLE001 - diagnostic script should show import cause.
        return CheckResult(module_name, False, f"{type(exc).__name__}: {exc}")
    version = getattr(module, "__version__", version_of(module_name))
    return CheckResult(module_name, True, str(version))


def main() -> int:
    print(f"python={sys.version.split()[0]}")
    checks = [import_check(name) for name in ["torch", "mmcv", "mmengine", "mmdet"]]

    for result in checks:
        status = "ok" if result.ok else "FAIL"
        print(f"{status:4} {result.name}: {result.detail}")

    if not all(result.ok for result in checks):
        print("\nFix failed imports before loading configs or checkpoints.", file=sys.stderr)
        return 1

    import mmcv
    import mmengine
    import mmdet
    import torch
    from mmdet.apis import DetInferencer, inference_detector, init_detector
    from mmdet.structures import DetDataSample
    from mmdet.structures.bbox import HorizontalBoxes

    print("\nversions:")
    print(f"  mmdet={mmdet.__version__}")
    print(f"  mmcv={mmcv.__version__}")
    print(f"  mmengine={mmengine.__version__}")
    print(f"  torch={torch.__version__}")
    print(f"  torch_cuda_available={torch.cuda.is_available()}")

    print("\napi_signatures:")
    print(f"  DetInferencer.__init__{inspect.signature(DetInferencer.__init__)}")
    print(f"  DetInferencer.__call__{inspect.signature(DetInferencer.__call__)}")
    print(f"  init_detector{inspect.signature(init_detector)}")
    print(f"  inference_detector{inspect.signature(inference_detector)}")
    print(f"  structures={DetDataSample.__name__},{HorizontalBoxes.__name__}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
