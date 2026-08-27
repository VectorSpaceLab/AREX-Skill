#!/usr/bin/env python3
"""Deterministic CPU smoke test for Optimum FX graph transformations.

This script uses a tiny local torch.nn.Module. It does not download models,
train, write artifacts, require credentials, or require CUDA.
"""

from __future__ import annotations

import argparse
import operator
import sys
from typing import Iterable


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run a local CPU smoke test for Optimum FX transformations using a tiny "
            "torch.nn.Module and no Hub downloads."
        )
    )
    parser.add_argument(
        "--skip-reverse",
        action="store_true",
        help="Only test the forward truediv-to-mul rewrite; skip reverse=True restoration.",
    )
    parser.add_argument(
        "--check-compose",
        action="store_true",
        help="Also test a reversible compose chain with ChangeTrueDivToMulByInverse and FuseBiasInLinear.",
    )
    parser.add_argument("--rtol", type=float, default=1e-5, help="Relative tolerance for torch.testing.assert_close.")
    parser.add_argument("--atol", type=float, default=1e-6, help="Absolute tolerance for torch.testing.assert_close.")
    parser.add_argument("--dump-code", action="store_true", help="Print FX generated code for debugging.")
    return parser.parse_args()


def count_target_nodes(graph_module, target) -> int:
    return sum(1 for node in graph_module.graph.nodes if node.op == "call_function" and node.target == target)


def count_linear_biases(graph_module, torch_mod) -> int:
    return sum(int(module.bias is not None) for module in graph_module.modules() if isinstance(module, torch_mod.nn.Linear))


def flatten_tensors(value) -> Iterable:
    try:
        import torch
    except Exception:  # pragma: no cover - import failure is handled in main
        torch = None

    if torch is not None and isinstance(value, torch.Tensor):
        yield value
    elif isinstance(value, dict):
        for key in sorted(value):
            yield from flatten_tensors(value[key])
    elif isinstance(value, (tuple, list)):
        for item in value:
            yield from flatten_tensors(item)


def assert_outputs_close(actual, expected, torch_mod, *, rtol: float, atol: float) -> None:
    actual_tensors = list(flatten_tensors(actual))
    expected_tensors = list(flatten_tensors(expected))
    if len(actual_tensors) != len(expected_tensors):
        raise AssertionError(f"tensor output count mismatch: {len(actual_tensors)} != {len(expected_tensors)}")
    if not actual_tensors:
        raise AssertionError("no tensor outputs found to compare")
    for index, (actual_tensor, expected_tensor) in enumerate(zip(actual_tensors, expected_tensors)):
        torch_mod.testing.assert_close(actual_tensor, expected_tensor, rtol=rtol, atol=atol, msg=f"output[{index}]")


class TinyDivLinearModule:  # filled after torch import so --help does not import torch
    pass


def build_tiny_module(torch_mod):
    class _TinyDivLinear(torch_mod.nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.linear = torch_mod.nn.Linear(4, 4)

        def forward(self, x):
            return self.linear(x) / 4.0

    return _TinyDivLinear()


def trace_tiny_module(torch_mod):
    torch_mod.manual_seed(0)
    model = build_tiny_module(torch_mod).eval()
    x = torch_mod.randn(2, 4)
    with torch_mod.no_grad():
        expected = model(x)
    traced = torch_mod.fx.symbolic_trace(model)
    return model, traced, x, expected


def run_truediv_smoke(torch_mod, optim, args: argparse.Namespace) -> None:
    _, traced, x, expected = trace_tiny_module(torch_mod)
    before_truediv = count_target_nodes(traced, operator.truediv)
    before_mul = count_target_nodes(traced, operator.mul)
    if before_truediv < 1:
        raise AssertionError("expected the tiny traced graph to contain at least one operator.truediv node")

    if args.dump_code:
        print("--- original graph code ---")
        print(traced.code)

    transformation = optim.ChangeTrueDivToMulByInverse()
    transformed = transformation(traced)
    transformed.graph.lint()
    transformed.recompile()

    after_truediv = count_target_nodes(transformed, operator.truediv)
    after_mul = count_target_nodes(transformed, operator.mul)
    if after_truediv != 0:
        raise AssertionError(f"expected all static truediv nodes to be rewritten, found {after_truediv}")
    if after_mul < before_mul + before_truediv:
        raise AssertionError("expected multiplication node count to increase after truediv rewrite")

    with torch_mod.no_grad():
        actual = transformed(x)
    assert_outputs_close(actual, expected, torch_mod, rtol=args.rtol, atol=args.atol)

    if args.dump_code:
        print("--- transformed graph code ---")
        print(transformed.code)

    print(
        f"[ok] ChangeTrueDivToMulByInverse rewrote {before_truediv} truediv node(s) "
        f"to mul and preserved output"
    )

    if args.skip_reverse:
        return

    restored = transformation(transformed, reverse=True)
    restored.graph.lint()
    restored.recompile()
    restored_truediv = count_target_nodes(restored, operator.truediv)
    restored_mul = count_target_nodes(restored, operator.mul)
    if restored_truediv != before_truediv or restored_mul != before_mul:
        raise AssertionError(
            "reverse=True did not restore original truediv/mul counts: "
            f"expected ({before_truediv}, {before_mul}), got ({restored_truediv}, {restored_mul})"
        )
    with torch_mod.no_grad():
        restored_output = restored(x)
    assert_outputs_close(restored_output, expected, torch_mod, rtol=args.rtol, atol=args.atol)

    if args.dump_code:
        print("--- restored graph code ---")
        print(restored.code)

    print("[ok] reverse=True restored graph operator counts and preserved output")


def run_compose_smoke(torch_mod, optim, args: argparse.Namespace) -> None:
    _, traced, x, expected = trace_tiny_module(torch_mod)
    original_code = traced.code
    original_bias_count = count_linear_biases(traced, torch_mod)
    if original_bias_count != 1:
        raise AssertionError(f"expected one biased linear in the tiny graph, found {original_bias_count}")

    chain = optim.compose(optim.ChangeTrueDivToMulByInverse(), optim.FuseBiasInLinear(), inplace=False)
    if not getattr(chain, "preserves_computation", False):
        raise AssertionError("expected the reversible composed chain to preserve computation")

    transformed = chain(traced)
    transformed.graph.lint()
    transformed.recompile()
    if traced.code != original_code:
        raise AssertionError("compose(..., inplace=False) unexpectedly mutated the original traced graph code")
    if count_linear_biases(transformed, torch_mod) != 0:
        raise AssertionError("expected FuseBiasInLinear in the compose chain to remove linear bias")
    if count_target_nodes(transformed, operator.truediv) != 0:
        raise AssertionError("expected ChangeTrueDivToMulByInverse in the compose chain to remove truediv nodes")

    with torch_mod.no_grad():
        transformed_output = transformed(x)
    assert_outputs_close(transformed_output, expected, torch_mod, rtol=args.rtol, atol=args.atol)

    restored = chain(transformed, reverse=True)
    restored.graph.lint()
    restored.recompile()
    if count_linear_biases(restored, torch_mod) != original_bias_count:
        raise AssertionError("reverse=True did not restore the original linear bias count")
    if count_target_nodes(restored, operator.truediv) != count_target_nodes(traced, operator.truediv):
        raise AssertionError("reverse=True did not restore the original truediv count")

    with torch_mod.no_grad():
        restored_output = restored(x)
    assert_outputs_close(restored_output, expected, torch_mod, rtol=args.rtol, atol=args.atol)

    if args.dump_code:
        print("--- compose transformed graph code ---")
        print(transformed.code)
        print("--- compose restored graph code ---")
        print(restored.code)

    print("[ok] compose(..., inplace=False) preserved output, fused bias, and restored with reverse=True")


def main() -> int:
    args = parse_args()
    try:
        import torch
        from optimum.fx import optimization as optim
    except Exception as exc:
        print(f"[error] failed to import required FX dependencies: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2

    torch.set_grad_enabled(False)
    try:
        torch.use_deterministic_algorithms(True)
    except Exception:
        pass

    try:
        run_truediv_smoke(torch, optim, args)
        if args.check_compose:
            run_compose_smoke(torch, optim, args)
    except Exception as exc:
        print(f"[error] FX transform smoke failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
