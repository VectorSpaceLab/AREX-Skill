#!/usr/bin/env python3
"""Run source-independent supervised model contract and optional forward checks.

This helper never imports the repository checkout, trains, downloads, loads a
checkpoint, or writes a file. By default it verifies torch/device policy and
prints the input/output contract. An optional externally installed factory can
be supplied for a tiny forward check; the factory must be a local-only callable
with signature ``factory(model_name, device) -> torch.nn.Module``.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.util
from pathlib import Path
import sys
from typing import Any, Dict, Iterable, Tuple


MODELS: Dict[str, Dict[str, Any]] = {
    "Physnet": {
        "input": "N,C,T,H,W",
        "shape": (1, 3, 32, 32, 32),
        "output": "tensor or tuple whose first tensor is rPPG",
        "note": "production geometry commonly uses 128 frames and NCDHW",
    },
    "iBVPNet": {
        "input": "N,C,T,H,W",
        "shape": (1, 3, 33, 72, 72),
        "output": "rPPG with one fewer time sample than input",
        "note": "the trainer appends a final frame before this difference-based model",
    },
    "FactorizePhys": {
        "input": "N,C,T,H,W",
        "shape": (1, 3, 33, 72, 72),
        "output": "rPPG plus embeddings; FSAM may add auxiliary outputs",
        "note": "production geometry commonly uses 160 frames; standard and Big differ",
    },
    "Tscan": {
        "input": "N*T,C,H,W",
        "shape": (10, 6, 72, 72),
        "output": "one prediction per flattened frame",
        "note": "TSCAN separates first-three diff and last-three appearance channels",
    },
    "EfficientPhys": {
        "input": "N*T,C,H,W",
        "shape": (11, 3, 72, 72),
        "output": "one prediction per usable flattened frame",
        "note": "the trainer supplies one repeated frame because the model differences time",
    },
    "DeepPhys": {
        "input": "N*T,C,H,W",
        "shape": (10, 6, 72, 72),
        "output": "one prediction per flattened frame",
        "note": "first-three motion and last-three appearance channels are required",
    },
    "BigSmall": {
        "input": "(big N*T,C,H,W, small N*T,C,H,W)",
        "shape": ((3, 3, 144, 144), (3, 3, 9, 9)),
        "output": "AU logits, BVP regression, respiration regression",
        "note": "the production model is fixed around three-frame segments",
    },
    "PhysFormer": {
        "input": "N,C,T,H,W",
        "shape": (1, 3, 32, 128, 128),
        "output": "rPPG plus three attention-score tensors",
        "note": "tiny shape is only a construction probe; production examples use 160x128x128",
    },
    "PhysMamba": {
        "input": "N,C,T,H,W",
        "shape": (1, 3, 32, 32, 32),
        "output": "rPPG",
        "note": "required CUDA/Mamba backend; this probe refuses CPU PhysMamba",
    },
    "RhythmFormer": {
        "input": "N,T,C,H,W",
        "shape": (1, 32, 3, 128, 128),
        "output": "rPPG",
        "note": "production examples use 160x128x128 and NDCHW",
    },
}

OPTIONAL_BACKEND = ("mamba_ssm", "causal_conv1d", "timm")


def parse_args() -> argparse.Namespace:
    """Parse safe, non-writing smoke options."""
    parser = argparse.ArgumentParser(
        description=(
            "Check supervised model names, tensor contracts, and one requested "
            "device without training, downloading, checkpoint access, or writes."
        )
    )
    parser.add_argument(
        "--model",
        action="append",
        choices=sorted(MODELS),
        default=None,
        help="Exact MODEL.NAME; repeat to check multiple models (default: Tscan).",
    )
    parser.add_argument(
        "--device",
        default="cpu",
        help="One device, e.g. cpu or cuda:0 (default: cpu); comma lists are rejected.",
    )
    parser.add_argument(
        "--forward",
        action="store_true",
        help="Run one no-grad forward using an external installed factory.",
    )
    parser.add_argument(
        "--factory",
        metavar="MODULE:CALLABLE",
        help=(
            "Optional external factory used with --forward. It must return a "
            "torch.nn.Module for (model_name, device); no checkout module is accepted."
        ),
    )
    parser.add_argument("--frames", type=int, help="Override the synthetic temporal size.")
    parser.add_argument("--height", type=int, help="Override synthetic frame height.")
    parser.add_argument("--width", type=int, help="Override synthetic frame width.")
    return parser.parse_args()


def _under(path: Path, parent: Path) -> bool:
    """Return whether path is inside parent without requiring Python 3.9 APIs."""
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def choose_device(name: str):
    """Validate one requested torch device and return it."""
    if not name or "," in name:
        raise ValueError("--device must name exactly one device, not a comma-separated list")
    try:
        import torch
    except Exception as exc:  # pragma: no cover - depends on environment
        raise RuntimeError(
            "PyTorch is required for device/forward checks; install the prepared "
            "torch build in a user-approved environment."
        ) from exc
    try:
        device = torch.device(name)
    except Exception as exc:
        raise ValueError(f"invalid torch device {name!r}: {exc}") from exc
    if device.type == "cuda":
        if not torch.cuda.is_available():
            raise RuntimeError(
                f"{name} was requested but CUDA is unavailable; inspect the torch "
                "build/driver. This script will not fall back to CPU."
            )
        count = torch.cuda.device_count()
        if device.index is None:
            raise ValueError("request a single CUDA index, for example cuda:0")
        if device.index < 0 or device.index >= count:
            raise ValueError(f"{name} is outside the {count} visible CUDA device(s)")
    elif device.type not in {"cpu", "mps"}:
        raise ValueError(f"unsupported smoke device {device}; use cpu or one cuda:N/mps device")
    return torch, device


def check_optional_backend(model_name: str) -> Tuple[bool, str]:
    """Report PhysMamba's required imports without attempting installation."""
    if model_name != "PhysMamba":
        return True, ""
    missing = []
    for module_name in OPTIONAL_BACKEND:
        if importlib.util.find_spec(module_name) is None:
            missing.append(module_name)
    if missing:
        return False, (
            "PhysMamba requires CUDA plus installed imports "
            f"{', '.join(OPTIONAL_BACKEND)}; missing: {', '.join(missing)}. "
            "Check the documented PyTorch 2.1.2+cu121 / causal-conv1d 1.0.0 / "
            "mamba-ssm 2.2.2 target and do not use CPU as a substitute."
        )
    return True, "PhysMamba optional imports are present; verify ABI and CUDA before training."


def synthetic_input(model_name: str, frames: int | None, height: int | None, width: int | None):
    """Build a deterministic tiny input for an externally supplied model."""
    import torch

    spec = MODELS[model_name]["shape"]
    if model_name == "BigSmall":
        big, small = spec
        if frames is not None:
            big = (frames, big[1], big[2], big[3])
            small = (frames, small[1], small[2], small[3])
        if height is not None:
            big = (big[0], big[1], height, big[3])
        if width is not None:
            big = (big[0], big[1], big[2], width)
        values_big = torch.linspace(-0.5, 0.5, steps=max(1, int(torch.tensor(big).prod())))
        values_small = torch.linspace(-0.5, 0.5, steps=max(1, int(torch.tensor(small).prod())))
        return values_big.reshape(big), values_small.reshape(small)

    shape = list(spec)
    if model_name in {"Tscan", "EfficientPhys", "DeepPhys"}:
        if frames is not None:
            shape[0] = frames
        if height is not None:
            shape[2] = height
        if width is not None:
            shape[3] = width
    elif model_name == "RhythmFormer":
        if frames is not None:
            shape[1] = frames
        if height is not None:
            shape[3] = height
        if width is not None:
            shape[4] = width
    else:
        if frames is not None:
            shape[2] = frames
        if height is not None:
            shape[3] = height
        if width is not None:
            shape[4] = width
    count = 1
    for value in shape:
        count *= value
    return torch.linspace(-0.5, 0.5, steps=max(1, count)).reshape(shape)


def load_external_factory(spec_text: str):
    """Load a factory outside the current checkout, without modifying sys.path."""
    if ":" not in spec_text:
        raise ValueError("--factory must use MODULE:CALLABLE syntax")
    module_name, callable_name = spec_text.split(":", 1)
    if not module_name or not callable_name:
        raise ValueError("--factory must use a non-empty MODULE:CALLABLE")
    module_spec = importlib.util.find_spec(module_name)
    if module_spec is None:
        raise ModuleNotFoundError(
            f"external factory module {module_name!r} is not installed; no download is attempted"
        )
    origin = getattr(module_spec, "origin", None)
    if origin and origin not in {"built-in", "frozen"}:
        origin_path = Path(origin).resolve()
        if _under(origin_path, Path.cwd().resolve()):
            raise RuntimeError(
                "refusing a factory resolved inside the current checkout; install or stage "
                "a separate package and pass that package instead"
            )
    module = importlib.import_module(module_name)
    factory = getattr(module, callable_name, None)
    if not callable(factory):
        raise AttributeError(f"{spec_text} does not identify a callable factory")
    return factory


def make_model(factory, model_name: str, device):
    """Call a user factory with the documented two-argument contract."""
    try:
        model = factory(model_name, device)
    except TypeError as first_error:
        try:
            model = factory(model_name)
        except TypeError:
            raise first_error
    import torch
    if not isinstance(model, torch.nn.Module):
        raise TypeError("external factory must return torch.nn.Module")
    return model.to(device).eval()


def tensor_leaves(value: Any) -> Iterable[Any]:
    """Yield tensors nested in common model output tuples."""
    try:
        import torch
    except ImportError:
        return
    if isinstance(value, torch.Tensor):
        yield value
    elif isinstance(value, (tuple, list)):
        for item in value:
            yield from tensor_leaves(item)


def run_forward(factory, model_name: str, device, args: argparse.Namespace) -> None:
    """Run one deterministic no-grad call and validate that a tensor emerged."""
    import torch

    if model_name == "PhysMamba" and device.type != "cuda":
        raise RuntimeError("PhysMamba forward requires one CUDA device; CPU fallback is refused")
    model = make_model(factory, model_name, device)
    data = synthetic_input(model_name, args.frames, args.height, args.width)
    if model_name == "BigSmall":
        data = tuple(item.to(device) for item in data)
    else:
        data = data.to(device)
    with torch.no_grad():
        output = model(data)
    leaves = list(tensor_leaves(output))
    if not leaves:
        raise RuntimeError("forward returned no torch tensor")
    if any(not torch.isfinite(item).all().item() for item in leaves):
        raise RuntimeError("forward returned NaN or infinite values")
    print(f"  forward: PASS ({len(leaves)} tensor output(s); first shape={tuple(leaves[0].shape)})")


def main() -> int:
    """Run requested checks and return a shell-friendly status."""
    args = parse_args()
    models = args.model or ["Tscan"]
    if args.forward and not args.factory:
        print("ERROR: --forward requires --factory MODULE:CALLABLE; no source import is assumed.", file=sys.stderr)
        return 2
    try:
        torch, device = choose_device(args.device)
        if args.frames is not None and args.frames < 2:
            raise ValueError("--frames must be at least 2")
        for value, label in ((args.height, "--height"), (args.width, "--width")):
            if value is not None and value < 2:
                raise ValueError(f"{label} must be at least 2")
        if "PhysMamba" in models and device.type != "cuda":
            raise RuntimeError("PhysMamba is CUDA/Mamba-only; request one cuda:N device")
        factory = load_external_factory(args.factory) if args.forward else None
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(f"torch={torch.__version__} device={device} models={','.join(models)}")
    failed = False
    for model_name in models:
        spec = MODELS[model_name]
        print(f"{model_name}: contract PASS")
        print(f"  input={spec['input']} shape={spec['shape']}")
        print(f"  output={spec['output']}")
        print(f"  note={spec['note']}")
        backend_ok, backend_message = check_optional_backend(model_name)
        if backend_message:
            print(f"  backend: {'PASS' if backend_ok else 'BLOCKED'} - {backend_message}")
        if not backend_ok:
            failed = True
            continue
        if args.forward:
            try:
                run_forward(factory, model_name, device, args)
            except Exception as exc:
                print(f"  forward: BLOCKED - {type(exc).__name__}: {exc}")
                failed = True
    return 2 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
