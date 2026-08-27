#!/usr/bin/env python3
"""Safe runtime preflight for deep-daze.

This script checks install/import identity, dependency presence, CLIP model
registry, tokenizer shape, package data, Torch backend status, and the imagine
console-script entry point. It never calls deep_daze.clip.load, never constructs
Imagine, never downloads CLIP checkpoints, and never generates images.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import importlib.util
import json
import sys
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

EXPECTED_MODELS = ["RN50", "RN101", "RN50x4", "ViT-B/32", "ViT-L/14"]
EXPECTED_TOKEN_SHAPE = (1, 77)
EXPECTED_CONSOLE_VALUE = "deep_daze.cli:main"

DEPENDENCIES: Sequence[Tuple[str, str, Sequence[str]]] = (
    ("deep-daze", "deep_daze", ("deep-daze",)),
    ("torch", "torch", ("torch",)),
    ("torchvision", "torchvision", ("torchvision",)),
    ("siren-pytorch", "siren_pytorch", ("siren-pytorch", "siren_pytorch")),
    ("torch_optimizer", "torch_optimizer", ("torch_optimizer", "torch-optimizer")),
    ("fire", "fire", ("fire",)),
    ("ftfy", "ftfy", ("ftfy",)),
    ("regex", "regex", ("regex",)),
    ("einops", "einops", ("einops",)),
    ("imageio", "imageio", ("imageio",)),
    ("tqdm", "tqdm", ("tqdm",)),
)


@dataclass
class CheckResult:
    name: str
    status: str
    detail: str
    data: Optional[Dict[str, Any]] = None

    def as_dict(self) -> Dict[str, Any]:
        out = {"name": self.name, "status": self.status, "detail": self.detail}
        if self.data is not None:
            out["data"] = self.data
        return out


def version_for(candidates: Iterable[str]) -> Optional[str]:
    for candidate in candidates:
        try:
            return metadata.version(candidate)
        except metadata.PackageNotFoundError:
            continue
    return None


def module_available(module_name: str) -> bool:
    return importlib.util.find_spec(module_name) is not None


def dependency_checks() -> List[CheckResult]:
    results: List[CheckResult] = []
    for label, module_name, dists in DEPENDENCIES:
        has_module = module_available(module_name)
        version = version_for(dists)
        if has_module:
            detail = f"module {module_name!r} import spec found"
            if version:
                detail += f", version {version}"
            results.append(
                CheckResult(
                    name=f"dependency:{label}",
                    status="ok",
                    detail=detail,
                    data={"module": module_name, "version": version},
                )
            )
        else:
            results.append(
                CheckResult(
                    name=f"dependency:{label}",
                    status="fail",
                    detail=f"module {module_name!r} import spec not found",
                    data={"module": module_name, "version": version},
                )
            )
    return results


def distribution_check() -> CheckResult:
    try:
        version = metadata.version("deep-daze")
        return CheckResult(
            "distribution:deep-daze",
            "ok",
            f"installed distribution deep-daze version {version}",
            {"version": version},
        )
    except metadata.PackageNotFoundError:
        return CheckResult(
            "distribution:deep-daze",
            "fail",
            "installed distribution deep-daze was not found by importlib.metadata",
        )


def import_check() -> Tuple[CheckResult, Optional[Any]]:
    try:
        module = importlib.import_module("deep_daze")
    except Exception as exc:  # noqa: BLE001 - diagnostic script should report any import failure.
        return (
            CheckResult(
                "import:deep_daze",
                "fail",
                f"import deep_daze failed: {exc.__class__.__name__}: {exc}",
            ),
            None,
        )

    exports = {name: hasattr(module, name) for name in ("DeepDaze", "Imagine")}
    status = "ok" if all(exports.values()) else "fail"
    missing = [name for name, present in exports.items() if not present]
    detail = "deep_daze imports and exports DeepDaze and Imagine"
    if missing:
        detail = "deep_daze imported but missing exports: " + ", ".join(missing)
    return CheckResult("import:deep_daze", status, detail, {"exports": exports}), module


def clip_checks() -> List[CheckResult]:
    try:
        clip = importlib.import_module("deep_daze.clip")
    except Exception as exc:  # noqa: BLE001
        return [
            CheckResult(
                "import:deep_daze.clip",
                "fail",
                f"import deep_daze.clip failed: {exc.__class__.__name__}: {exc}",
            )
        ]

    results: List[CheckResult] = [
        CheckResult("import:deep_daze.clip", "ok", "deep_daze.clip imports")
    ]

    try:
        models = list(clip.available_models())
    except Exception as exc:  # noqa: BLE001
        results.append(
            CheckResult(
                "clip:available_models",
                "fail",
                f"available_models() failed: {exc.__class__.__name__}: {exc}",
            )
        )
    else:
        status = "ok" if models == EXPECTED_MODELS else "warn"
        detail = "available_models() matches expected registry"
        if status == "warn":
            detail = f"available_models() returned {models!r}; expected {EXPECTED_MODELS!r}"
        results.append(
            CheckResult(
                "clip:available_models",
                status,
                detail,
                {"models": models, "expected": EXPECTED_MODELS},
            )
        )

    try:
        tokens = clip.tokenize("a house")
        shape = tuple(int(x) for x in tokens.shape)
    except Exception as exc:  # noqa: BLE001
        results.append(
            CheckResult(
                "clip:tokenize_shape",
                "fail",
                f"tokenize('a house') failed: {exc.__class__.__name__}: {exc}",
            )
        )
    else:
        status = "ok" if shape == EXPECTED_TOKEN_SHAPE else "fail"
        detail = f"tokenize('a house') shape is {shape}"
        results.append(
            CheckResult(
                "clip:tokenize_shape",
                status,
                detail,
                {"shape": list(shape), "expected": list(EXPECTED_TOKEN_SHAPE)},
            )
        )

    try:
        from importlib import resources

        bpe = resources.files("deep_daze").joinpath("data", "bpe_simple_vocab_16e6.txt")
        present = bpe.is_file()
    except Exception as exc:  # noqa: BLE001
        results.append(
            CheckResult(
                "package_data:bpe_vocab",
                "fail",
                f"could not inspect BPE package data: {exc.__class__.__name__}: {exc}",
            )
        )
    else:
        results.append(
            CheckResult(
                "package_data:bpe_vocab",
                "ok" if present else "fail",
                "BPE vocabulary package data is present" if present else "BPE vocabulary package data is missing",
            )
        )

    return results


def torch_backend_check() -> CheckResult:
    try:
        torch = importlib.import_module("torch")
    except Exception as exc:  # noqa: BLE001
        return CheckResult(
            "torch:backend_status",
            "fail",
            f"import torch failed: {exc.__class__.__name__}: {exc}",
        )

    cuda_available = bool(torch.cuda.is_available())
    cuda_device_count = int(torch.cuda.device_count()) if hasattr(torch.cuda, "device_count") else 0
    selected_device = "cuda" if cuda_available else "cpu"

    mps_available: Optional[bool]
    try:
        mps_available = bool(torch.backends.mps.is_available())  # type: ignore[attr-defined]
    except Exception:  # noqa: BLE001
        mps_available = None

    data = {
        "torch_version": getattr(torch, "__version__", None),
        "cuda_available": cuda_available,
        "cuda_device_count": cuda_device_count,
        "mps_available": mps_available,
        "deep_daze_selected_device": selected_device,
        "jit_will_be_disabled_by_imagine_default": "1.7.1" not in str(getattr(torch, "__version__", "")),
    }
    detail = (
        f"torch {data['torch_version']} reports cuda_available={cuda_available}; "
        f"deep-daze would select {selected_device}"
    )
    return CheckResult("torch:backend_status", "ok", detail, data)


def console_script_check() -> CheckResult:
    try:
        entry_points = metadata.entry_points()
        if hasattr(entry_points, "select"):
            matches = list(entry_points.select(group="console_scripts", name="imagine"))
        else:
            matches = [ep for ep in entry_points.get("console_scripts", []) if ep.name == "imagine"]
    except Exception as exc:  # noqa: BLE001
        return CheckResult(
            "console_script:imagine",
            "fail",
            f"could not inspect console scripts: {exc.__class__.__name__}: {exc}",
        )

    values = [getattr(ep, "value", "") for ep in matches]
    if EXPECTED_CONSOLE_VALUE in values:
        return CheckResult(
            "console_script:imagine",
            "ok",
            f"console script imagine points to {EXPECTED_CONSOLE_VALUE}",
            {"values": values},
        )
    if values:
        return CheckResult(
            "console_script:imagine",
            "warn",
            f"console script imagine exists but points to {values!r}",
            {"values": values, "expected": EXPECTED_CONSOLE_VALUE},
        )
    return CheckResult(
        "console_script:imagine",
        "warn",
        "console script imagine was not found in importlib.metadata entry points",
        {"values": [], "expected": EXPECTED_CONSOLE_VALUE},
    )


def run_checks() -> List[CheckResult]:
    results: List[CheckResult] = []
    results.append(distribution_check())
    results.extend(dependency_checks())
    import_result, _module = import_check()
    results.append(import_result)
    results.extend(clip_checks())
    results.append(torch_backend_check())
    results.append(console_script_check())
    return results


def print_text(results: Sequence[CheckResult]) -> None:
    for result in results:
        print(f"[{result.status.upper():4}] {result.name}: {result.detail}")
        if result.data:
            for key, value in result.data.items():
                print(f"       {key}: {value}")


def exit_code(results: Sequence[CheckResult], strict: bool) -> int:
    bad = {"fail"}
    if strict:
        bad.add("warn")
    return 1 if any(result.status in bad for result in results) else 0


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Safely inspect a deep-daze runtime without CLIP checkpoint downloads "
            "or image generation."
        )
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="print machine-readable JSON instead of human-readable lines",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="exit nonzero on warnings as well as failures",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    results = run_checks()
    if args.json:
        print(json.dumps([result.as_dict() for result in results], indent=2, sort_keys=True))
    else:
        print_text(results)
    return exit_code(results, strict=args.strict)


if __name__ == "__main__":
    raise SystemExit(main())
