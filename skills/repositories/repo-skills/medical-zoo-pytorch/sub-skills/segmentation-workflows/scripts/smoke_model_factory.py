#!/usr/bin/env python3
"""Safe segmentation factory smoke test for MedicalZooPytorch.

This script is CPU-first, argument-driven, and avoids source-checkout-specific
paths. If the MedicalZooPytorch package is not already importable, pass a local
package root with --package-root.
"""

from __future__ import annotations

import argparse
import sys
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace

import torch


@dataclass(frozen=True)
class ModelCase:
    name: str
    in_channels: int
    classes: int
    dim: tuple[int, int, int]
    output_kind: str  # single, pair, vae
    output_dim: tuple[int, int, int] | None = None


MODEL_CASES: dict[str, ModelCase] = {
    "UNET3D": ModelCase("UNET3D", 2, 4, (32, 32, 32), "single"),
    "VNET": ModelCase("VNET", 2, 4, (32, 32, 32), "single"),
    "VNET2": ModelCase("VNET2", 2, 4, (32, 32, 32), "single"),
    "DENSENET1": ModelCase("DENSENET1", 2, 4, (12, 12, 12), "single"),
    "DENSENET2": ModelCase("DENSENET2", 2, 4, (12, 12, 12), "single"),
    "DENSENET3": ModelCase("DENSENET3", 2, 4, (12, 12, 12), "single"),
    "HYPERDENSENET": ModelCase("HYPERDENSENET", 2, 4, (22, 22, 22), "single"),
    "SKIPDENSENET3D": ModelCase("SKIPDENSENET3D", 2, 4, (32, 32, 32), "single"),
    "DENSEVOXELNET": ModelCase("DENSEVOXELNET", 2, 4, (8, 8, 8), "pair"),
    "RESNET3DVAE": ModelCase("RESNET3DVAE", 2, 4, (16, 16, 16), "vae"),
    "RESNETMED3D": ModelCase("RESNETMED3D", 2, 4, (16, 16, 16), "single"),
    "HIGHRESNET": ModelCase("HIGHRESNET", 2, 4, (32, 32, 32), "single"),
}

KNOWN_BROKEN_ALL_CASES: dict[str, str] = {
    "DENSENET2": "source channel math mismatch in DualPathDenseNet",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Smoke the MedicalZooPytorch segmentation factory and a tiny forward pass.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--package-root",
        default=None,
        help="Optional local directory to prepend to sys.path before importing lib.medzoo.",
    )
    parser.add_argument(
        "--model",
        default="UNET3D",
        choices=["all", *MODEL_CASES.keys()],
        help="Run one model or the full segmentation factory smoke set.",
    )
    parser.add_argument("--in-channels", type=int, default=None, help="Override the channel count for single-model runs.")
    parser.add_argument("--classes", type=int, default=None, help="Override the class count for single-model runs.")
    parser.add_argument(
        "--dim",
        nargs=3,
        type=int,
        default=None,
        metavar=("D", "H", "W"),
        help="Override the spatial shape for single-model runs.",
    )
    parser.add_argument("--lr", type=float, default=1e-3, help="Learning rate passed to the factory.")
    parser.add_argument("--opt", choices=("sgd", "adam", "rmsprop"), default="sgd", help="Optimizer passed to the factory.")
    parser.add_argument("--cuda", action="store_true", default=False, help="Move the model and input to CUDA when available.")
    parser.add_argument("--seed", type=int, default=7, help="Random seed for the smoke input.")
    parser.add_argument(
        "--output-dim",
        nargs=3,
        type=int,
        default=None,
        metavar=("D", "H", "W"),
        help="Override the expected output spatial shape for a single-model run.",
    )
    parser.add_argument(
        "--include-known-broken",
        action="store_true",
        default=False,
        help="Also run cases that are known to fail in the source tree.",
    )
    return parser.parse_args()


@contextmanager
def added_sys_path(path: str | None):
    if not path:
        yield
        return
    sys.path.insert(0, path)
    try:
        yield
    finally:
        if sys.path and sys.path[0] == path:
            sys.path.pop(0)


def detect_repo_root() -> str | None:
    here = Path(__file__).resolve()
    for parent in (here.parent, *here.parents):
        if (parent / "lib" / "medzoo" / "__init__.py").is_file():
            return str(parent)
    return None


def load_medzoo(package_root: str | None):
    candidate_roots = [package_root, detect_repo_root()]
    last_error: Exception | None = None
    for root in candidate_roots:
        if root is None:
            continue
        with added_sys_path(root):
            try:
                import lib.medzoo as medzoo  # type: ignore
                return medzoo
            except Exception as exc:  # pragma: no cover - user-facing import diagnostic
                last_error = exc
    raise SystemExit(
        "Unable to import lib.medzoo. Make the MedicalZooPytorch package importable and ensure its optional model-zoo dependencies are installed."
    ) from last_error


def build_case_args(case: ModelCase, args: argparse.Namespace) -> SimpleNamespace:
    in_channels = args.in_channels if args.in_channels is not None else case.in_channels
    classes = args.classes if args.classes is not None else case.classes
    dim = tuple(args.dim) if args.dim is not None else case.dim
    return SimpleNamespace(
        model=case.name,
        opt=args.opt,
        lr=args.lr,
        inChannels=in_channels,
        classes=classes,
        dim=dim,
    )


def tensor_shape(tensor: torch.Tensor) -> tuple[int, ...]:
    return tuple(int(x) for x in tensor.shape)


def move_to_device(model, device: torch.device):
    return model.to(device)


def smoke_single_case(medzoo, args: argparse.Namespace, case: ModelCase) -> None:
    case_args = build_case_args(case, args)
    model, optimizer = medzoo.create_model(case_args)
    device = torch.device("cuda:0" if args.cuda and torch.cuda.is_available() else "cpu")
    if args.cuda and not torch.cuda.is_available():
        print("CUDA was requested but is not available; continuing on CPU.")
    model = move_to_device(model, device)
    model.eval()

    input_tensor = torch.randn((1, case_args.inChannels, *case_args.dim), device=device)
    with torch.no_grad():
        output = model(input_tensor)

    assert optimizer.param_groups, f"{case.name}: optimizer has no parameter groups"

    if case.output_kind == "single":
        assert isinstance(output, torch.Tensor), f"{case.name}: expected a tensor output"
        assert tensor_shape(output)[0] == 1, f"{case.name}: batch dimension mismatch"
        assert tensor_shape(output)[1] == case_args.classes, f"{case.name}: class dimension mismatch"
        if args.output_dim is not None:
            expected_spatial = tuple(args.output_dim)
        elif case.name == "HYPERDENSENET":
            expected_spatial = tuple(max(1, dim - 18) for dim in case_args.dim)
        else:
            expected_spatial = case.output_dim or case_args.dim
        assert tensor_shape(output)[2:] == expected_spatial, f"{case.name}: spatial shape mismatch"
        print(f"created {case.name}: {tensor_shape(output)}")
        return

    if case.output_kind == "pair":
        assert isinstance(output, tuple) and len(output) == 2, f"{case.name}: expected two outputs"
        first, second = output
        expected_spatial = tuple(args.output_dim) if args.output_dim is not None else (case.output_dim or case_args.dim)
        for index, tensor in enumerate((first, second), start=1):
            assert isinstance(tensor, torch.Tensor), f"{case.name}: output {index} is not a tensor"
            assert tensor_shape(tensor)[0] == 1, f"{case.name}: batch dimension mismatch in output {index}"
            assert tensor_shape(tensor)[1] == case_args.classes, f"{case.name}: class dimension mismatch in output {index}"
            assert tensor_shape(tensor)[2:] == expected_spatial, f"{case.name}: spatial shape mismatch in output {index}"
        print(f"created {case.name}: {tensor_shape(first)} and {tensor_shape(second)}")
        return

    if case.output_kind == "vae":
        assert isinstance(output, tuple) and len(output) == 4, f"{case.name}: expected four outputs"
        seg, vae_out, mu, logvar = output
        assert isinstance(seg, torch.Tensor) and isinstance(vae_out, torch.Tensor)
        assert isinstance(mu, torch.Tensor) and isinstance(logvar, torch.Tensor)
        assert tensor_shape(seg)[0] == 1 and tensor_shape(seg)[1] == case_args.classes and tensor_shape(seg)[2:] == case_args.dim
        assert tensor_shape(vae_out) == tensor_shape(input_tensor), f"{case.name}: VAE reconstruction shape mismatch"
        assert tensor_shape(mu) == tensor_shape(logvar), f"{case.name}: mu/logvar shape mismatch"
        print(f"created {case.name}: {tensor_shape(seg)} / {tensor_shape(vae_out)}")
        return

    raise RuntimeError(f"Unknown output kind for {case.name}: {case.output_kind}")


def smoke_all_cases(medzoo, args: argparse.Namespace) -> None:
    failures: list[tuple[str, str]] = []
    for name, case in MODEL_CASES.items():
        if name in KNOWN_BROKEN_ALL_CASES and not args.include_known_broken:
            print(f"skipping {name}: {KNOWN_BROKEN_ALL_CASES[name]}")
            continue
        try:
            smoke_single_case(medzoo, args, case)
        except Exception as exc:
            failures.append((name, str(exc)))
            print(f"FAILED {name}: {exc}")
    if failures:
        summary = ", ".join(f"{name} ({message})" for name, message in failures)
        raise SystemExit(f"{len(failures)} model(s) failed: {summary}")


def main() -> None:
    args = parse_args()
    torch.manual_seed(args.seed)
    if args.cuda and torch.cuda.is_available():
        torch.cuda.manual_seed_all(args.seed)

    medzoo = load_medzoo(args.package_root)
    if args.model == "all":
        smoke_all_cases(medzoo, args)
    else:
        smoke_single_case(medzoo, args, MODEL_CASES[args.model])


if __name__ == "__main__":
    main()
