#!/usr/bin/env python3
"""Tiny BAE/CUDA sparse-LM readiness and convergence smoke.

The default mode skips successfully with an actionable diagnostic when CUDA or
BAE is absent. ``--check-only`` is the explicit readiness gate and returns
nonzero for missing prerequisites. See the nearest ../SKILL.md.
"""
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass

import torch


@dataclass
class Readiness:
    ok: bool
    message: str
    pypose: object | None = None
    pcg: object | None = None
    psjac: object | None = None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check BAE/CUDA and run a tiny sparse PyPose LM smoke."
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Only check sparse readiness; return nonzero when unavailable.",
    )
    parser.add_argument(
        "--device",
        default="cuda",
        help="CUDA device, for example cuda or cuda:0 (default: cuda).",
    )
    parser.add_argument(
        "--steps",
        type=int,
        default=6,
        help="Maximum sparse LM iterations (default: 6).",
    )
    parser.add_argument(
        "--maxiter",
        type=int,
        default=100,
        help="PCG iteration limit for the tiny fixture (default: 100).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=11,
        help="Torch seed for the deterministic fixture (default: 11).",
    )
    return parser.parse_args()


def check_readiness(device_name: str, maxiter: int) -> Readiness:
    try:
        import pypose as pp
    except Exception as exc:
        return Readiness(False, f"PyPose import failed: {type(exc).__name__}: {exc}")

    try:
        requested = torch.device(device_name)
    except RuntimeError as exc:
        return Readiness(False, f"invalid device {device_name!r}: {exc}", pypose=pp)
    if requested.type != "cuda":
        return Readiness(
            False,
            f"sparse LM requires a CUDA device, but {device_name!r} was requested",
            pypose=pp,
        )
    if not torch.cuda.is_available():
        return Readiness(
            False,
            "CUDA is unavailable (sparse LM has no CPU substitute)",
            pypose=pp,
        )
    try:
        # Validate the explicitly requested ordinal before importing BAE, whose
        # initialization can allocate/cache CUDA state.
        index = torch.cuda.current_device() if requested.index is None else requested.index
        if index < 0 or index >= torch.cuda.device_count():
            return Readiness(
                False,
                f"CUDA device {device_name!r} is not visible; "
                f"visible device count is {torch.cuda.device_count()}",
                pypose=pp,
            )
        torch.cuda.set_device(index)
    except Exception as exc:
        return Readiness(
            False,
            f"CUDA device {device_name!r} cannot be selected: "
            f"{type(exc).__name__}: {exc}",
            pypose=pp,
        )
    try:
        import bae  # noqa: F401  # optional backend probe
    except Exception as exc:
        return Readiness(
            False,
            f"BAE import failed; install a CUDA-compatible bae (verified: 0.2.1): "
            f"{type(exc).__name__}: {exc}",
            pypose=pp,
        )
    try:
        from pypose.autograd.function import psjac
        from pypose.optim.solver import PCG

        solver = PCG(maxiter=maxiter, tol=1e-5)
    except Exception as exc:
        return Readiness(
            False,
            f"BAE is present but PyPose PCG/psjac is unavailable: "
            f"{type(exc).__name__}: {exc}",
            pypose=pp,
        )
    return Readiness(
        True,
        f"ready: pypose={pp.__version__}, torch={torch.__version__}, "
        f"cuda={torch.cuda.get_device_name(index)}; BAE/PCG/psjac resolved",
        pypose=pp,
        pcg=solver,
        psjac=psjac,
    )


def run_smoke(readiness: Readiness, device_name: str, steps: int, seed: int) -> int:
    assert readiness.pypose is not None
    assert readiness.pcg is not None
    assert readiness.psjac is not None
    if steps < 1:
        print("error: --steps must be positive", file=sys.stderr)
        return 2

    pp = readiness.pypose
    device = torch.device(device_name)
    torch.manual_seed(seed)
    dtype = torch.float64

    # The decorator is deliberately row-local. Probe it on an ordinary tensor
    # first: the BAE sparse graph tracer has special TrackingTensor semantics,
    # while the identity model below is the smallest reliable backend smoke.
    @readiness.psjac
    def identity_factor(values: torch.Tensor) -> torch.Tensor:
        return values

    probe = torch.arange(4, dtype=dtype, device=device).unsqueeze(-1)
    torch.testing.assert_close(identity_factor(probe), probe)

    class SparseIdentity(torch.nn.Module):
        def __init__(self, initial: torch.Tensor) -> None:
            super().__init__()
            self.x = pp.Parameter(initial, sjac=True)

        def forward(self) -> torch.Tensor:
            return self.x

    truth = torch.linspace(-0.8, 0.8, 8, dtype=dtype, device=device).unsqueeze(-1)
    initial = truth + 0.1
    model = SparseIdentity(initial).to(device)

    try:
        from pypose.optim import LM
        from pypose.optim.strategy import Constant

        optimizer = LM(
            model,
            solver=readiness.pcg,
            strategy=Constant(damping=1e-6),
            sparse=True,
        )
        with torch.no_grad():
            initial_loss = optimizer.model.loss(input=(), target=truth).item()
        losses = []
        for _ in range(steps):
            loss = optimizer.step(input=(), target=truth)
            value = float(loss)
            if not torch.isfinite(loss):
                raise AssertionError(f"non-finite sparse LM loss: {value}")
            losses.append(value)
            if value < 1e-20:
                break
        final_loss = losses[-1]
        if not final_loss < initial_loss:
            raise AssertionError(
                f"sparse loss did not decrease: {initial_loss} -> {final_loss}"
            )
        torch.testing.assert_close(model.x.tensor(), truth, rtol=1e-4, atol=1e-4)
        print(
            f"sparse LM smoke passed: {readiness.message}; "
            f"loss={initial_loss:.3e}->{final_loss:.3e}, steps={len(losses)}"
        )
        return 0
    except Exception as exc:
        print(
            f"sparse LM smoke failed after readiness passed: "
            f"{type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        return 1


def main() -> int:
    args = parse_args()
    if args.steps < 1 or args.maxiter < 1:
        print("error: --steps and --maxiter must be positive", file=sys.stderr)
        return 2
    readiness = check_readiness(args.device, args.maxiter)
    if not readiness.ok:
        diagnostic = (
            f"sparse LM smoke skipped: {readiness.message}. "
            "Use --check-only to make missing sparse readiness return nonzero."
        )
        print(diagnostic, file=sys.stderr)
        return 2 if args.check_only else 0
    print(f"sparse LM readiness {readiness.message}")
    if args.check_only:
        return 0
    return run_smoke(readiness, args.device, args.steps, args.seed)


if __name__ == "__main__":
    raise SystemExit(main())
