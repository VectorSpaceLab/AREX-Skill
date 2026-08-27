#!/usr/bin/env python3
"""Check pix2pixHD imports, lightweight API access, and CUDA availability.

Run from any directory with an explicit --repo-root. The script only imports
modules and runs tiny smoke checks; it does not launch training or inference.
"""

from __future__ import annotations

import argparse
import importlib
import io
import json
import sys
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace


def resolve_repo_root(raw: str) -> Path:
    root = Path(raw).expanduser().resolve()
    if not root.exists():
        raise SystemExit(f"repo root does not exist: {root}")
    required = ["README.md", "options", "data", "models", "util"]
    missing = [item for item in required if not (root / item).exists()]
    if missing:
        raise SystemExit(f"repo root is missing expected pix2pixHD paths: {', '.join(missing)}")
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    return root


def import_or_fail(module_name: str):
    try:
        return importlib.import_module(module_name)
    except Exception as exc:
        raise SystemExit(f"[import-error] {module_name}: {exc}") from exc


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check pix2pixHD imports and a few safe runtime facts.")
    parser.add_argument("--repo-root", required=True, help="Path to the pix2pixHD checkout.")
    parser.add_argument("--skip-cuda", action="store_true", help="Skip the CUDA allocation smoke.")
    parser.add_argument("--probe-legacy-resize", action="store_true", help="Probe the deprecated resize_and_crop transform branch.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of human-readable text.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = resolve_repo_root(args.repo_root)

    torch = import_or_fail("torch")
    torchvision = import_or_fail("torchvision")
    dominate = import_or_fail("dominate")
    sklearn = import_or_fail("sklearn")
    import_or_fail("options.test_options")
    import_or_fail("data.aligned_dataset")
    import_or_fail("models.networks")
    import_or_fail("util.util")

    report: dict[str, object] = {
        "repo_root": str(repo_root),
        "python": sys.version.split()[0],
        "torch": getattr(torch, "__version__", None),
        "torchvision": getattr(torchvision, "__version__", None),
        "dominate": getattr(dominate, "__version__", None),
        "sklearn": getattr(sklearn, "__version__", None),
        "cuda_available": bool(torch.cuda.is_available()),
        "cuda_device_count": int(torch.cuda.device_count()) if torch.cuda.is_available() else 0,
        "imports": ["torch", "torchvision", "dominate", "sklearn", "options.test_options", "data.aligned_dataset", "models.networks", "util.util"],
        "warnings": [],
    }

    if torch.cuda.is_available() and not args.skip_cuda:
        x = torch.empty((1,), device="cuda")
        report["cuda_device_name"] = torch.cuda.get_device_name(0)
        report["cuda_device_capability"] = list(torch.cuda.get_device_capability(0))
        report["cuda_tensor_device"] = str(x.device)
    elif args.skip_cuda:
        report["warnings"].append("CUDA smoke was skipped by request.")
    else:
        report["warnings"].append("CUDA is unavailable; training, inference, and feature workflows are CUDA-first in this repository.")

    from models.networks import define_G

    with redirect_stdout(io.StringIO()):
        net = define_G(1, 3, 8, "global", n_downsample_global=1, n_blocks_global=1, norm="instance", gpu_ids=[])
    out = net(torch.randn(1, 1, 64, 64))
    report["tiny_generator_output"] = list(out.shape)

    if args.probe_legacy_resize:
        from data.base_dataset import get_transform

        legacy_opt = SimpleNamespace(
            resize_or_crop="resize_and_crop",
            loadSize=4,
            fineSize=2,
            isTrain=False,
            no_flip=True,
            n_downsample_global=4,
            n_local_enhancers=1,
            netG="global",
        )
        try:
            get_transform(legacy_opt, {"crop_pos": (0, 0), "flip": False}, normalize=False)
            report["legacy_resize"] = "available"
        except Exception as exc:
            report["legacy_resize"] = f"unavailable: {exc}"
            report["warnings"].append("resize_and_crop uses a deprecated torchvision API in this repo checkout.")

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"[ok] repo-root: {report['repo_root']}")
        print(f"[ok] python: {report['python']}")
        print(f"[ok] torch: {report['torch']}")
        print(f"[ok] torchvision: {report['torchvision']}")
        print(f"[ok] dominate: {report['dominate']}")
        print(f"[ok] sklearn: {report['sklearn']}")
        print(f"[ok] cuda_available: {report['cuda_available']}")
        if report.get("cuda_device_name"):
            print(f"[ok] cuda_device: {report['cuda_device_name']} {tuple(report['cuda_device_capability'])}")
        print(f"[ok] tiny_generator_output: {tuple(report['tiny_generator_output'])}")
        for warning in report["warnings"]:
            print(f"[warning] {warning}")
        if report.get("legacy_resize"):
            print(f"[ok] legacy_resize: {report['legacy_resize']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
