#!/usr/bin/env python3
"""Smoke checks for einops framework layers and EinMix constraints.

Default mode is pure Python and does not require optional deep-learning
frameworks: it validates EinMix decomposition and restriction behavior through
the package's internal debugger class. Optional framework modes import only the
requested framework and skip clearly when unavailable.
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


def _skip(name: str, message: str) -> Outcome:
    return Outcome(name, "SKIP", message)


def _pass(name: str, message: str) -> Outcome:
    return Outcome(name, "PASS", message)


def _fail(name: str, exc: BaseException) -> Outcome:
    return Outcome(name, "FAIL", f"{type(exc).__name__}: {exc}")


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _assert_raises(fn: Callable[[], object], expected_message_part: str | None = None) -> None:
    try:
        fn()
    except Exception as exc:  # noqa: BLE001 - smoke only needs to confirm a clear failure
        if expected_message_part is not None and expected_message_part not in str(exc):
            raise AssertionError(
                f"expected message containing {expected_message_part!r}, got {type(exc).__name__}: {exc}"
            ) from exc
        return
    raise AssertionError("expected an exception, but call succeeded")


def _pure_case() -> Outcome:
    try:
        from einops.layers._einmix import _EinmixDebugger

        mixin = _EinmixDebugger("a b c d e -> e d c b a", weight_shape="d a b", d=2, a=3, b=5)
        _assert(mixin.pre_reshape_pattern is None, "unexpected pre-reshape for simple EinMix")
        _assert(mixin.post_reshape_pattern is None, "unexpected post-reshape for simple EinMix")
        _assert(mixin.einsum_pattern == "abcde,dab->edcba", f"unexpected einsum pattern {mixin.einsum_pattern!r}")
        _assert(mixin.saved_weight_shape == [2, 3, 5], f"unexpected weight shape {mixin.saved_weight_shape!r}")
        _assert(mixin.saved_bias_shape is None, f"unexpected bias shape {mixin.saved_bias_shape!r}")

        composite = _EinmixDebugger(
            "b ... (a c) -> b ... (a d)",
            weight_shape="c d",
            bias_shape="a d",
            a=1,
            c=3,
            d=4,
        )
        _assert(
            composite.pre_reshape_pattern == "b ... (a c) -> b ... a c",
            f"unexpected pre pattern {composite.pre_reshape_pattern!r}",
        )
        _assert(
            composite.post_reshape_pattern == "b ... a d -> b ... (a d)",
            f"unexpected post pattern {composite.post_reshape_pattern!r}",
        )
        _assert(composite.saved_weight_shape == [3, 4], f"unexpected composite weight {composite.saved_weight_shape!r}")
        _assert(composite.saved_bias_shape == [1, 1, 4], f"unexpected composite bias {composite.saved_bias_shape!r}")

        _assert_raises(
            lambda: _EinmixDebugger("a b c -> c b a", weight_shape="a b", a=2),
            "Dimension b of weight should be specified",
        )
        _assert_raises(
            lambda: _EinmixDebugger("a b c -> c b a", weight_shape="w a", a=2, w=3),
            "Weight axes",
        )
        _assert_raises(
            lambda: _EinmixDebugger("(...) a -> ... a", weight_shape="a", a=1),
            "Ellipsis on left side",
        )
        _assert_raises(
            lambda: _EinmixDebugger("a -> a", weight_shape="(a)", a=1),
            "Parenthesis is not allowed in weight shape",
        )
        _assert_raises(
            lambda: _EinmixDebugger("a 2 -> a", weight_shape="a", a=1),
            "Anonymous axes",
        )
        _assert_raises(
            lambda: _EinmixDebugger("a -> a", weight_shape="a", bias_shape="missing", a=1),
            "Bias axes",
        )

        return _pass("pure", "EinMix decomposition and restriction checks passed")
    except Exception as exc:  # noqa: BLE001
        return _fail("pure", exc)


def _torch_case() -> Outcome:
    try:
        import torch
        from einops.layers.torch import EinMix, Rearrange, Reduce
    except ModuleNotFoundError as exc:
        return _skip("torch", f"optional dependency not installed: {exc}")
    except Exception as exc:  # noqa: BLE001
        return _fail("torch", exc)

    try:
        x = torch.arange(2 * 3 * 4, dtype=torch.float32).reshape(2, 3, 4)
        y = Rearrange("b c t -> b t c")(x)
        _assert(tuple(y.shape) == (2, 4, 3), f"unexpected Rearrange shape {tuple(y.shape)}")
        z = Reduce("b c t -> b c", "sum")(x)
        _assert(tuple(z.shape) == (2, 3), f"unexpected Reduce shape {tuple(z.shape)}")
        mix = EinMix("b t c -> b t cout", weight_shape="c cout", bias_shape="cout", c=4, cout=5)
        mixed = mix(x)
        _assert(tuple(mixed.shape) == (2, 3, 5), f"unexpected EinMix shape {tuple(mixed.shape)}")
        scripted = torch.jit.script(Rearrange("b c t -> b t c"))
        _assert(tuple(scripted(x).shape) == (2, 4, 3), "scripted Rearrange returned wrong shape")
        return _pass("torch", "Torch Rearrange/Reduce/EinMix CPU smoke and scripted Rearrange passed")
    except Exception as exc:  # noqa: BLE001
        return _fail("torch", exc)


def _tensorflow_case() -> Outcome:
    try:
        import tensorflow as tf
        from einops.layers.keras import keras_custom_objects
        from einops.layers.tensorflow import EinMix, Rearrange, Reduce
    except ModuleNotFoundError as exc:
        return _skip("tensorflow", f"optional dependency not installed: {exc}")
    except Exception as exc:  # noqa: BLE001
        return _fail("tensorflow", exc)

    try:
        x = tf.reshape(tf.range(2 * 3 * 4, dtype=tf.float32), (2, 3, 4))
        y = Rearrange("b c t -> b t c")(x)
        _assert(tuple(y.shape) == (2, 4, 3), f"unexpected Rearrange shape {tuple(y.shape)}")
        z = Reduce("b c t -> b c", "sum")(x)
        _assert(tuple(z.shape) == (2, 3), f"unexpected Reduce shape {tuple(z.shape)}")
        mix = EinMix("b t c -> b t cout", weight_shape="c cout", bias_shape="cout", c=4, cout=5)
        mixed = mix(x)
        _assert(tuple(mixed.shape) == (2, 3, 5), f"unexpected EinMix shape {tuple(mixed.shape)}")
        _assert("Rearrange" in keras_custom_objects, "keras_custom_objects missing Rearrange")
        return _pass("tensorflow", f"TensorFlow layers CPU smoke passed with tf.__version__={tf.__version__}")
    except Exception as exc:  # noqa: BLE001
        return _fail("tensorflow", exc)


def _jax_case() -> Outcome:
    try:
        import jax.numpy as jnp
        from einops import rearrange
    except ModuleNotFoundError as exc:
        return _skip("jax", f"optional dependency not installed: {exc}")
    except Exception as exc:  # noqa: BLE001
        return _fail("jax", exc)

    try:
        x = jnp.arange(2 * 3 * 4, dtype=jnp.float32).reshape(2, 3, 4)
        y = rearrange(x, "b c t -> b t c")
        _assert(tuple(y.shape) == (2, 4, 3), f"unexpected JAX rearrange shape {tuple(y.shape)}")
        return _pass("jax", "JAX top-level backend smoke passed; use --framework flax for Flax layers")
    except Exception as exc:  # noqa: BLE001
        return _fail("jax", exc)


def _flax_case() -> Outcome:
    try:
        import jax
        import jax.numpy as jnp
        from flax import linen as nn
        from einops.layers.flax import EinMix, Rearrange, Reduce
    except ModuleNotFoundError as exc:
        return _skip("flax", f"optional dependency not installed: {exc}")
    except Exception as exc:  # noqa: BLE001
        return _fail("flax", exc)

    try:
        class Block(nn.Module):
            @nn.compact
            def __call__(self, x):
                x = Rearrange("b c t -> b t c")(x)
                x = EinMix("b t c -> b t cout", weight_shape="c cout", bias_shape="cout", sizes={"c": 3, "cout": 5})(x)
                return Reduce("b t cout -> b", "mean", sizes={"cout": 5})(x)

        model = Block()
        x = jnp.ones((2, 3, 4), dtype=jnp.float32)
        params = model.init(jax.random.PRNGKey(0), x)
        y = model.apply(params, x)
        _assert(tuple(y.shape) == (2,), f"unexpected Flax output shape {tuple(y.shape)}")
        return _pass("flax", "Flax Rearrange/Reduce/EinMix smoke passed")
    except Exception as exc:  # noqa: BLE001
        return _fail("flax", exc)


def _paddle_case() -> Outcome:
    try:
        import paddle
        from einops.layers.paddle import EinMix, Rearrange, Reduce
    except ModuleNotFoundError as exc:
        return _skip("paddle", f"optional dependency not installed: {exc}")
    except Exception as exc:  # noqa: BLE001
        return _fail("paddle", exc)

    try:
        x = paddle.arange(2 * 3 * 4, dtype="float32").reshape([2, 3, 4])
        y = Rearrange("b c t -> b t c")(x)
        _assert(tuple(y.shape) == (2, 4, 3), f"unexpected Rearrange shape {tuple(y.shape)}")
        z = Reduce("b c t -> b c", "sum")(x)
        _assert(tuple(z.shape) == (2, 3), f"unexpected Reduce shape {tuple(z.shape)}")
        mix = EinMix("b t c -> b t cout", weight_shape="c cout", bias_shape="cout", c=4, cout=5)
        mixed = mix(x)
        _assert(tuple(mixed.shape) == (2, 3, 5), f"unexpected EinMix shape {tuple(mixed.shape)}")
        return _pass("paddle", "Paddle layers CPU smoke passed")
    except Exception as exc:  # noqa: BLE001
        return _fail("paddle", exc)


def _oneflow_case() -> Outcome:
    try:
        import oneflow as flow
        from einops.layers.oneflow import EinMix, Rearrange, Reduce
    except ModuleNotFoundError as exc:
        return _skip("oneflow", f"optional dependency not installed: {exc}")
    except Exception as exc:  # noqa: BLE001
        return _fail("oneflow", exc)

    try:
        x = flow.arange(2 * 3 * 4, dtype=flow.float32).reshape(2, 3, 4)
        y = Rearrange("b c t -> b t c")(x)
        _assert(tuple(y.shape) == (2, 4, 3), f"unexpected Rearrange shape {tuple(y.shape)}")
        z = Reduce("b c t -> b c", "sum")(x)
        _assert(tuple(z.shape) == (2, 3), f"unexpected Reduce shape {tuple(z.shape)}")
        mix = EinMix("b t c -> b t cout", weight_shape="c cout", bias_shape="cout", c=4, cout=5)
        mixed = mix(x)
        _assert(tuple(mixed.shape) == (2, 3, 5), f"unexpected EinMix shape {tuple(mixed.shape)}")
        return _pass("oneflow", "OneFlow layers CPU smoke passed")
    except Exception as exc:  # noqa: BLE001
        return _fail("oneflow", exc)


CASES: dict[str, Callable[[], Outcome]] = {
    "pure": _pure_case,
    "torch": _torch_case,
    "tensorflow": _tensorflow_case,
    "jax": _jax_case,
    "flax": _flax_case,
    "paddle": _paddle_case,
    "oneflow": _oneflow_case,
}


def _selected(framework: str) -> Iterable[str]:
    if framework == "all":
        return CASES.keys()
    return [framework]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run einops layer and EinMix smoke checks.")
    parser.add_argument(
        "--framework",
        choices=["all", *CASES.keys()],
        default="pure",
        help="Framework layer smoke to run. Missing optional frameworks are reported as SKIP. Default: pure.",
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
