#!/usr/bin/env python3
"""Inspect a Transformer Engine runtime and run tiny BF16 smokes.

This helper stays inside the generated skill tree. It does not depend on the
original repository checkout.
"""

from __future__ import annotations

import argparse
import os
import sys
from importlib import metadata
from typing import Iterable


if "XLA_PYTHON_CLIENT_PREALLOCATE" not in os.environ:
    os.environ["XLA_PYTHON_CLIENT_PREALLOCATE"] = "false"


def dist_version(*names: str) -> str:
    for name in names:
        try:
            return metadata.version(name)
        except metadata.PackageNotFoundError:
            continue
    return "unknown"


def support_line(name: str, result: tuple[bool, str]) -> str:
    ok, reason = result
    return f"{name}=True" if ok else f"{name}=False ({reason})"


def _device_label(torch_mod, device) -> str:
    return f"{torch_mod.cuda.get_device_name(device)} (cuda:{device})"


def run_pytorch(args: argparse.Namespace) -> None:
    if "NVTE_TORCH_COMPILE" not in os.environ:
        os.environ["NVTE_TORCH_COMPILE"] = "0"
        compile_note = "NVTE_TORCH_COMPILE=0 (set before TE import)"
    else:
        compile_note = f"NVTE_TORCH_COMPILE={os.environ['NVTE_TORCH_COMPILE']}"

    import torch
    import transformer_engine.pytorch as te

    if not torch.cuda.is_available():
        raise SystemExit("CUDA is not available for the PyTorch inspection path")

    cuda_index = 0
    torch.cuda.set_device(cuda_index)
    device = torch.device(f"cuda:{cuda_index}")

    print(f"[pytorch] transformer_engine={dist_version('transformer_engine', 'transformer-engine')}")
    print(f"[pytorch] torch={torch.__version__}")
    print(f"[pytorch] cuda={torch.version.cuda}")
    print(f"[pytorch] device={_device_label(torch, cuda_index)}")
    print(f"[pytorch] compute_capability={torch.cuda.get_device_capability(cuda_index)}")
    print(f"[pytorch] cudnn={te.get_cudnn_version()}")
    print(f"[pytorch] {compile_note}")
    print(support_line("[pytorch] bf16", te.is_bf16_available(return_reason=True)))
    print(support_line("[pytorch] fp8", te.is_fp8_available(return_reason=True)))
    print(support_line("[pytorch] mxfp8", te.is_mxfp8_available(return_reason=True)))
    print(support_line("[pytorch] fp8_block_scaling", te.is_fp8_block_scaling_available(return_reason=True)))
    print(support_line("[pytorch] nvfp4", te.is_nvfp4_available(return_reason=True)))

    layer = te.Linear(
        args.pytorch_in_features,
        args.pytorch_out_features,
        bias=True,
        params_dtype=torch.bfloat16,
        device=device,
    )
    x = torch.randn(
        args.pytorch_batch_size,
        args.pytorch_in_features,
        dtype=torch.bfloat16,
        device=device,
        requires_grad=True,
    )
    y = layer(x)
    y.sum().backward()
    torch.cuda.synchronize(device)
    print(
        f"[pytorch] smoke=PASS output_shape={tuple(y.shape)} output_dtype={y.dtype} grad_dtype={None if x.grad is None else x.grad.dtype}"
    )


def _jax_recipe_support_lines() -> Iterable[str]:
    try:
        from transformer_engine.jax.quantize import (  # pylint: disable=import-outside-toplevel
            ScalingMode,
            get_supported_quantization_recipes,
            is_scaling_mode_supported,
        )
    except Exception as exc:  # pragma: no cover - diagnostic only
        yield f"[jax] recipe_probe_import_error={type(exc).__name__}: {exc}"
        return

    try:
        recipes = [type(recipe).__name__ for recipe in get_supported_quantization_recipes()]
        yield f"[jax] supported_quantization_recipes={recipes}"
    except Exception as exc:  # pragma: no cover - diagnostic only
        yield f"[jax] supported_quantization_recipes_error={type(exc).__name__}: {exc}"

    for mode in (
        ScalingMode.DELAYED_TENSOR_SCALING,
        ScalingMode.CURRENT_TENSOR_SCALING,
        ScalingMode.MXFP8_1D_SCALING,
        ScalingMode.NVFP4_1D_SCALING,
    ):
        try:
            ok, reason = is_scaling_mode_supported(mode)
            yield f"[jax] scaling_mode={mode.name} supported={ok} reason={reason!r}"
        except Exception as exc:  # pragma: no cover - diagnostic only
            yield f"[jax] scaling_mode={mode.name} error={type(exc).__name__}: {exc}"


def run_jax(args: argparse.Namespace) -> None:
    import jax
    import jax.numpy as jnp
    import transformer_engine.jax as te
    from transformer_engine.jax.flax import DenseGeneral

    print(f"[jax] transformer_engine={dist_version('transformer_engine', 'transformer-engine')}")
    print(f"[jax] jax={jax.__version__}")
    try:
        import jaxlib

        print(f"[jax] jaxlib={jaxlib.__version__}")
    except Exception as exc:  # pragma: no cover - diagnostic only
        print(f"[jax] jaxlib_import_error={type(exc).__name__}: {exc}")
    print(f"[jax] visible_devices={[str(dev) for dev in jax.devices()]}")
    print(f"[jax] xla_preallocate={os.environ.get('XLA_PYTHON_CLIENT_PREALLOCATE')}")

    key = jax.random.PRNGKey(args.jax_seed)
    x = jax.random.normal(key, (args.jax_batch_size, args.jax_in_features), dtype=jnp.bfloat16)
    model = DenseGeneral(features=args.jax_features, use_bias=True, dtype=jnp.bfloat16)
    variables = model.init(key, x)

    def loss_fn(params, inputs):
        out = model.apply({"params": params}, inputs)
        return jnp.asarray(out, jnp.float32).sum(), out

    (loss, out), grads = jax.jit(jax.value_and_grad(loss_fn, has_aux=True))(variables["params"], x)
    loss, out, grads = jax.block_until_ready((loss, out, grads))

    print(f"[jax] output_shape={tuple(out.shape)}")
    print(f"[jax] output_dtype={out.dtype}")
    print(f"[jax] loss={float(jax.device_get(loss)):.6f}")
    print(f"[jax] gradients_finite={bool(jax.device_get(jnp.all(jnp.stack([jnp.all(jnp.isfinite(jnp.asarray(leaf))) for leaf in jax.tree_util.tree_leaves(grads)]))))}")
    for line in _jax_recipe_support_lines():
        print(line)
    print("[jax] smoke=PASS")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--framework",
        choices=("pytorch", "jax", "both"),
        default="both",
        help="Which runtime path to inspect. Default: both.",
    )
    parser.add_argument("--pytorch-batch-size", type=int, default=4)
    parser.add_argument("--pytorch-in-features", type=int, default=16)
    parser.add_argument("--pytorch-out-features", type=int, default=32)
    parser.add_argument("--jax-batch-size", type=int, default=4)
    parser.add_argument("--jax-in-features", type=int, default=16)
    parser.add_argument("--jax-features", type=int, default=32)
    parser.add_argument("--jax-seed", type=int, default=0)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if args.framework in ("pytorch", "both"):
        run_pytorch(args)
    if args.framework in ("jax", "both"):
        run_jax(args)


if __name__ == "__main__":
    main()
