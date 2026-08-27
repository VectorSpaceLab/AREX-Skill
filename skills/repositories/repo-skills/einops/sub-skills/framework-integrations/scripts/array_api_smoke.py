#!/usr/bin/env python3
"""Deterministic smoke checks for einops.array_api.

Default mode checks NumPy's Array API support when NumPy 2.x is installed.
Optional framework modes skip clearly when the requested optional dependency is
missing or does not expose ``__array_namespace__`` tensors.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from typing import Callable, Iterable


@dataclass
class Outcome:
    name: str
    status: str  # PASS, SKIP, FAIL
    message: str


def _version_tuple(version: str) -> tuple[int, ...]:
    parts: list[int] = []
    for chunk in version.split("."):
        digits = "".join(ch for ch in chunk if ch.isdigit())
        if digits == "":
            break
        parts.append(int(digits))
    return tuple(parts)


def _skip(name: str, message: str) -> Outcome:
    return Outcome(name, "SKIP", message)


def _pass(name: str, message: str) -> Outcome:
    return Outcome(name, "PASS", message)


def _fail(name: str, exc: BaseException) -> Outcome:
    return Outcome(name, "FAIL", f"{type(exc).__name__}: {exc}")


def _numpy_assert_allclose(actual, expected, label: str) -> None:
    import numpy as np

    if not np.allclose(actual, expected):
        raise AssertionError(f"{label} mismatch: actual={actual!r}, expected={expected!r}")


def _asnumpy_safe(tensor):
    """Use einops.array_api.asnumpy, with a NumPy fallback for older namespaces."""

    import numpy as np
    from einops import array_api as AA

    try:
        return AA.asnumpy(tensor)
    except Exception:
        return np.asarray(tensor)


def _require_array_namespace(name: str, tensor) -> None:
    if not hasattr(tensor, "__array_namespace__"):
        raise RuntimeError(
            f"{name} tensor type {type(tensor)!r} does not expose __array_namespace__; "
            "use ordinary top-level einops dispatch for this framework or choose a true Array API tensor"
        )
    xp = tensor.__array_namespace__()
    missing = [op for op in ["reshape", "permute_dims", "expand_dims", "broadcast_to", "stack", "concat"] if not hasattr(xp, op)]
    if missing:
        raise RuntimeError(f"{name} Array API namespace is missing required operations: {missing}")


def _run_array_api_checks(name: str, make_tensor: Callable[[object], object]) -> Outcome:
    try:
        import numpy as np
        from einops import array_api as AA

        base = np.arange(2 * 3 * 4, dtype=np.float32).reshape(2, 3, 4)
        x = make_tensor(base)
        _require_array_namespace(name, x)

        y = AA.rearrange(x, "b c t -> b t c")
        _numpy_assert_allclose(_asnumpy_safe(y), np.transpose(base, (0, 2, 1)), "rearrange")

        z = AA.reduce(x, "b c t -> b c", "sum")
        _numpy_assert_allclose(_asnumpy_safe(z), base.sum(axis=2), "reduce-sum")

        small = np.arange(6, dtype=np.float32).reshape(2, 3)
        repeated = AA.repeat(make_tensor(small), "b c -> b c r", r=2)
        _numpy_assert_allclose(_asnumpy_safe(repeated), np.broadcast_to(small[..., None], (2, 3, 2)), "repeat")

        first = np.arange(2 * 3, dtype=np.float32).reshape(2, 3)
        second = np.arange(2 * 3 * 4, dtype=np.float32).reshape(2, 3, 4)
        packed, packed_shapes = AA.pack([make_tensor(first), make_tensor(second)], "b c *")
        if list(packed_shapes) != [(), (4,)]:
            raise AssertionError(f"unexpected packed shapes: {packed_shapes!r}")
        expected_packed = np.concatenate([first.reshape(2, 3, 1), second], axis=2)
        _numpy_assert_allclose(_asnumpy_safe(packed), expected_packed, "pack")

        unpacked = AA.unpack(packed, packed_shapes, "b c *")
        _numpy_assert_allclose(_asnumpy_safe(unpacked[0]), first, "unpack-first")
        _numpy_assert_allclose(_asnumpy_safe(unpacked[1]), second, "unpack-second")

        return _pass(name, "Array API rearrange/reduce/repeat/pack/unpack smoke passed")
    except RuntimeError as exc:
        if "__array_namespace__" in str(exc) or "Array API namespace" in str(exc):
            return _skip(name, str(exc))
        return _fail(name, exc)
    except Exception as exc:  # noqa: BLE001 - script reports deterministic failures to user
        return _fail(name, exc)


def _numpy_case() -> Outcome:
    try:
        import numpy as np
    except ModuleNotFoundError as exc:
        return _skip("numpy", f"optional dependency not installed: {exc}")

    if _version_tuple(np.__version__) < (2, 0):
        return _skip("numpy", f"NumPy {np.__version__} is installed; NumPy Array API smoke requires NumPy >= 2.0")

    return _run_array_api_checks("numpy", lambda array: np.asarray(array))


def _torch_case() -> Outcome:
    try:
        import torch
    except ModuleNotFoundError as exc:
        return _skip("torch", f"optional dependency not installed: {exc}")

    return _run_array_api_checks("torch", lambda array: torch.asarray(array))


def _tensorflow_case() -> Outcome:
    try:
        import tensorflow as tf
    except ModuleNotFoundError as exc:
        return _skip("tensorflow", f"optional dependency not installed: {exc}")

    return _run_array_api_checks("tensorflow", lambda array: tf.convert_to_tensor(array))


def _jax_case() -> Outcome:
    try:
        import jax.numpy as jnp
    except ModuleNotFoundError as exc:
        return _skip("jax", f"optional dependency not installed: {exc}")

    return _run_array_api_checks("jax", lambda array: jnp.asarray(array))


def _paddle_case() -> Outcome:
    try:
        import paddle
    except ModuleNotFoundError as exc:
        return _skip("paddle", f"optional dependency not installed: {exc}")

    return _run_array_api_checks("paddle", lambda array: paddle.to_tensor(array))


def _oneflow_case() -> Outcome:
    try:
        import oneflow as flow
    except ModuleNotFoundError as exc:
        return _skip("oneflow", f"optional dependency not installed: {exc}")

    return _run_array_api_checks("oneflow", lambda array: flow.tensor(array))


def _flax_case() -> Outcome:
    try:
        import flax  # noqa: F401
    except ModuleNotFoundError as exc:
        return _skip("flax", f"optional dependency not installed: {exc}")
    return _skip("flax", "Flax is a layer library over JAX arrays, not a separate Array API tensor namespace; use --framework jax")


CASES: dict[str, Callable[[], Outcome]] = {
    "numpy": _numpy_case,
    "torch": _torch_case,
    "tensorflow": _tensorflow_case,
    "jax": _jax_case,
    "paddle": _paddle_case,
    "oneflow": _oneflow_case,
    "flax": _flax_case,
}


def _selected(framework: str) -> Iterable[str]:
    if framework == "all":
        return CASES.keys()
    return [framework]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run deterministic einops.array_api smoke checks.")
    parser.add_argument(
        "--framework",
        choices=["all", *CASES.keys()],
        default="numpy",
        help="Array API provider to smoke-check. Missing optional providers are reported as SKIP. Default: numpy.",
    )
    args = parser.parse_args(argv)

    outcomes = [CASES[name]() for name in _selected(args.framework)]
    for outcome in outcomes:
        print(f"[{outcome.status}] {outcome.name}: {outcome.message}")

    failed = [outcome for outcome in outcomes if outcome.status == "FAIL"]
    print(
        "summary: "
        f"pass={sum(o.status == 'PASS' for o in outcomes)} "
        f"skip={sum(o.status == 'SKIP' for o in outcomes)} "
        f"fail={len(failed)}"
    )
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
