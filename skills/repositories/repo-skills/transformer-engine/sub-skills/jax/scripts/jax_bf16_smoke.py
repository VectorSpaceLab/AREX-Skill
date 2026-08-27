#!/usr/bin/env python3
"""Tiny Transformer Engine JAX BF16 DenseGeneral smoke.

This script depends only on installed Python packages. It does not read the
Transformer Engine source tree, examples, tests, or documentation.

Framework imports happen after argument parsing so --help works even when JAX
is not yet installed in the active Python environment.
"""

from __future__ import annotations

import argparse
import os
import sys
from typing import Iterable


def _is_cuda_like(device: object) -> bool:
    platform = getattr(device, "platform", "")
    text = f"{platform} {device}".lower()
    return "gpu" in text or "cuda" in text


def _select_device(jax_module, requested: str):
    devices = list(jax_module.devices())
    if requested in {"cuda", "gpu"}:
        cuda_devices = [dev for dev in devices if _is_cuda_like(dev)]
        if not cuda_devices:
            visible = ", ".join(str(dev) for dev in devices) or "<none>"
            raise SystemExit(
                f"requested --device {requested!r}, but no CUDA/GPU JAX devices are visible; "
                f"visible devices: {visible}"
            )
        return cuda_devices[0]
    if requested == "cpu":
        cpu_devices = [dev for dev in devices if getattr(dev, "platform", "") == "cpu"]
        if not cpu_devices:
            raise SystemExit("requested --device 'cpu', but no CPU JAX device is visible")
        return cpu_devices[0]
    if requested == "any":
        if not devices:
            raise SystemExit("no JAX devices are visible")
        return devices[0]
    raise SystemExit(f"unsupported --device {requested!r}")


def _tree_all_finite(jax_module, jnp_module, tree) -> bool:
    leaves = jax_module.tree_util.tree_leaves(tree)
    if not leaves:
        return True
    checks = [jnp_module.all(jnp_module.isfinite(jnp_module.asarray(leaf))) for leaf in leaves]
    return bool(jax_module.device_get(jnp_module.all(jnp_module.stack(checks))))


def _recipe_support_lines() -> Iterable[str]:
    try:
        from transformer_engine.jax.quantize import (  # pylint: disable=import-outside-toplevel
            ScalingMode,
            get_supported_quantization_recipes,
            is_scaling_mode_supported,
        )
    except Exception as exc:  # pragma: no cover - diagnostic only
        yield f"recipe_probe_import_error={type(exc).__name__}: {exc}"
        return

    try:
        recipes = [type(recipe).__name__ for recipe in get_supported_quantization_recipes()]
        yield f"supported_quantization_recipes={recipes}"
    except Exception as exc:  # pragma: no cover - diagnostic only
        yield f"supported_quantization_recipes_error={type(exc).__name__}: {exc}"

    modes = [
        ScalingMode.DELAYED_TENSOR_SCALING,
        ScalingMode.CURRENT_TENSOR_SCALING,
        ScalingMode.MXFP8_1D_SCALING,
        ScalingMode.NVFP4_1D_SCALING,
    ]
    for mode in modes:
        try:
            ok, reason = is_scaling_mode_supported(mode)
            yield f"scaling_mode={mode.name} supported={ok} reason={reason!r}"
        except Exception as exc:  # pragma: no cover - diagnostic only
            yield f"scaling_mode={mode.name} error={type(exc).__name__}: {exc}"


def run(args: argparse.Namespace) -> None:
    if "XLA_PYTHON_CLIENT_PREALLOCATE" not in os.environ:
        os.environ["XLA_PYTHON_CLIENT_PREALLOCATE"] = "false"

    import jax
    import jax.numpy as jnp

    import transformer_engine.jax as te
    from transformer_engine.jax.flax import DenseGeneral

    if args.batch_size <= 0 or args.in_features <= 0 or args.features <= 0:
        raise SystemExit("--batch-size, --in-features, and --features must be positive")

    device = _select_device(jax, args.device)
    print(f"jax_version={jax.__version__}")
    try:
        import jaxlib

        jaxlib_version = jaxlib.__version__
    except Exception as exc:  # pragma: no cover - diagnostic only
        jaxlib_version = f"unavailable ({type(exc).__name__}: {exc})"
    print(f"jaxlib_version={jaxlib_version}")
    print(f"visible_devices={[str(dev) for dev in jax.devices()]}")
    print(f"selected_device={device}")
    print(f"xla_preallocate={os.environ.get('XLA_PYTHON_CLIENT_PREALLOCATE')}")

    key = jax.random.PRNGKey(args.seed)
    init_key, data_key = jax.random.split(key)

    with jax.default_device(device):
        x = jax.random.normal(
            data_key,
            (args.batch_size, args.in_features),
            dtype=jnp.bfloat16,
        )
        model = DenseGeneral(
            features=args.features,
            use_bias=True,
            dtype=jnp.bfloat16,
        )
        variables = model.init(init_key, x)

    def loss_fn(params, inputs):
        out = model.apply({"params": params}, inputs)
        return jnp.asarray(out, jnp.float32).sum(), out

    grad_fn = jax.jit(jax.value_and_grad(loss_fn, has_aux=True))
    (loss, out), grads = grad_fn(variables["params"], x)
    loss, out, grads = jax.block_until_ready((loss, out, grads))

    if out.shape != (args.batch_size, args.features):
        raise SystemExit(f"unexpected output shape {out.shape}")
    if out.dtype != jnp.bfloat16:
        raise SystemExit(f"unexpected output dtype {out.dtype}; expected bfloat16")
    if not bool(jax.device_get(jnp.isfinite(loss))):
        raise SystemExit(f"loss is not finite: {loss}")
    if not _tree_all_finite(jax, jnp, grads):
        raise SystemExit("gradient tree contains non-finite values")

    print(f"output_shape={tuple(out.shape)}")
    print(f"output_dtype={out.dtype}")
    print(f"loss={float(jax.device_get(loss)):.6f}")
    print("gradients_finite=True")

    for line in _recipe_support_lines():
        print(line)

    print("status=PASS")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--device",
        default="cuda",
        choices=("cuda", "gpu", "cpu", "any"),
        help="Device class to require/select. Default: cuda.",
    )
    parser.add_argument("--features", type=int, default=8, help="Dense output features.")
    parser.add_argument("--batch-size", type=int, default=2, help="Input batch size.")
    parser.add_argument("--in-features", type=int, default=16, help="Input feature width.")
    parser.add_argument("--seed", type=int, default=0, help="PRNG seed.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    run(parse_args(sys.argv[1:] if argv is None else argv))


if __name__ == "__main__":
    main()
