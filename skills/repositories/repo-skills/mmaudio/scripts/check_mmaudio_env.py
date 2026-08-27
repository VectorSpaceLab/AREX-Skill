#!/usr/bin/env python3
"""Safe MMAudio environment checker.

This script verifies importability, core package metadata, model variant names,
sequence facts, optional CUDA availability, and optional asset-path presence. It
does not download weights, construct the model, launch servers, or run training.

Examples:
  python check_mmaudio_env.py
  python check_mmaudio_env.py --require-cuda --check-av-bench
  python check_mmaudio_env.py --workdir /path/to/MMAudio --check-assets --json
"""

from __future__ import annotations

import argparse
import json
import sys
from importlib import import_module
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any


REQUIRED_ASSETS_BY_VARIANT = {
    "small_16k": [
        "weights/mmaudio_small_16k.pth",
        "ext_weights/v1-16.pth",
        "ext_weights/best_netG.pt",
        "ext_weights/synchformer_state_dict.pth",
    ],
    "small_44k": [
        "weights/mmaudio_small_44k.pth",
        "ext_weights/v1-44.pth",
        "ext_weights/synchformer_state_dict.pth",
    ],
    "medium_44k": [
        "weights/mmaudio_medium_44k.pth",
        "ext_weights/v1-44.pth",
        "ext_weights/synchformer_state_dict.pth",
    ],
    "large_44k": [
        "weights/mmaudio_large_44k.pth",
        "ext_weights/v1-44.pth",
        "ext_weights/synchformer_state_dict.pth",
    ],
    "large_44k_v2": [
        "weights/mmaudio_large_44k_v2.pth",
        "ext_weights/v1-44.pth",
        "ext_weights/synchformer_state_dict.pth",
    ],
}


def package_version(name: str) -> str | None:
    try:
        return version(name)
    except PackageNotFoundError:
        return None


def try_import(module: str) -> tuple[bool, str | None]:
    try:
        import_module(module)
        return True, None
    except Exception as exc:  # noqa: BLE001 - diagnostics should preserve error class/message.
        return False, f"{type(exc).__name__}: {exc}"


def check_cuda(require_cuda: bool) -> dict[str, Any]:
    result: dict[str, Any] = {"checked": True, "required": require_cuda}
    ok, err = try_import("torch")
    if not ok:
        result.update({"available": False, "error": err})
        return result
    import torch

    result["torch_version"] = torch.__version__
    result["available"] = bool(torch.cuda.is_available())
    result["device_count"] = int(torch.cuda.device_count()) if result["available"] else 0
    if result["available"]:
        result["device0"] = torch.cuda.get_device_name(0)
        try:
            x = torch.ones((1,), device="cuda")
            result["allocation_ok"] = bool(float(x.item()) == 1.0)
        except Exception as exc:  # noqa: BLE001
            result["allocation_ok"] = False
            result["allocation_error"] = f"{type(exc).__name__}: {exc}"
    else:
        result["allocation_ok"] = False
    return result


def check_assets(workdir: Path, variant: str) -> dict[str, Any]:
    required = REQUIRED_ASSETS_BY_VARIANT[variant]
    rows = []
    for rel in required:
        path = workdir / rel
        rows.append({"path": rel, "exists": path.exists(), "size_bytes": path.stat().st_size if path.exists() else None})
    return {"workdir": str(workdir), "variant": variant, "required": rows}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check MMAudio imports, CUDA, and optional asset paths without running the model.")
    parser.add_argument("--require-cuda", action="store_true", help="Return non-zero when CUDA is unavailable or allocation fails.")
    parser.add_argument("--check-av-bench", action="store_true", help="Also verify the external av_bench package used by training/evaluation metrics.")
    parser.add_argument("--check-assets", action="store_true", help="Check checkpoint/asset file presence under --workdir without downloading.")
    parser.add_argument("--variant", choices=sorted(REQUIRED_ASSETS_BY_VARIANT), default="large_44k_v2", help="Variant to use for --check-assets.")
    parser.add_argument("--workdir", type=Path, default=Path.cwd(), help="Directory containing weights/ and ext_weights/ when --check-assets is used.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON only.")
    args = parser.parse_args(argv)

    modules = [
        "mmaudio",
        "mmaudio.eval_utils",
        "mmaudio.model.networks",
        "mmaudio.model.sequence_config",
        "mmaudio.data.extracted_audio",
        "mmaudio.data.extracted_vgg",
    ]
    if args.check_av_bench:
        modules.append("av_bench")

    imports = {module: {"ok": ok, "error": err} for module in modules for ok, err in [try_import(module)]}
    cuda = check_cuda(args.require_cuda)

    report: dict[str, Any] = {
        "python": sys.version.split()[0],
        "packages": {
            "mmaudio": package_version("mmaudio"),
            "torch": package_version("torch"),
            "torchvision": package_version("torchvision"),
            "torchaudio": package_version("torchaudio"),
            "torchcodec": package_version("torchcodec"),
            "av_bench": package_version("av_bench"),
        },
        "imports": imports,
        "cuda": cuda,
    }

    if imports.get("mmaudio.eval_utils", {}).get("ok"):
        from mmaudio.eval_utils import all_model_cfg
        report["model_variants"] = sorted(all_model_cfg)
    if imports.get("mmaudio.model.sequence_config", {}).get("ok"):
        from mmaudio.model.sequence_config import CONFIG_16K, CONFIG_44K
        report["sequence"] = {
            "16k": {
                "sampling_rate": CONFIG_16K.sampling_rate,
                "latent_seq_len": CONFIG_16K.latent_seq_len,
                "clip_seq_len": CONFIG_16K.clip_seq_len,
                "sync_seq_len": CONFIG_16K.sync_seq_len,
                "num_audio_frames": CONFIG_16K.num_audio_frames,
            },
            "44k": {
                "sampling_rate": CONFIG_44K.sampling_rate,
                "latent_seq_len": CONFIG_44K.latent_seq_len,
                "clip_seq_len": CONFIG_44K.clip_seq_len,
                "sync_seq_len": CONFIG_44K.sync_seq_len,
                "num_audio_frames": CONFIG_44K.num_audio_frames,
            },
        }
    if args.check_assets:
        report["assets"] = check_assets(args.workdir, args.variant)

    failures = []
    for module, row in imports.items():
        if not row["ok"]:
            failures.append(f"import failed for {module}: {row['error']}")
    if args.require_cuda and (not cuda.get("available") or not cuda.get("allocation_ok")):
        failures.append("CUDA was required but was unavailable or allocation failed")
    if args.check_assets:
        missing = [row["path"] for row in report["assets"]["required"] if not row["exists"]]
        if missing:
            failures.append("missing assets: " + ", ".join(missing))

    report["ok"] = not failures
    report["failures"] = failures

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("MMAudio environment check")
        print("ok:", report["ok"])
        print("python:", report["python"])
        print("packages:", report["packages"])
        print("model_variants:", report.get("model_variants"))
        print("cuda:", report["cuda"])
        if args.check_assets:
            print("assets:", json.dumps(report["assets"], indent=2))
        if failures:
            print("failures:")
            for failure in failures:
                print("-", failure)

    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
