#!/usr/bin/env python3
"""Safe KDA smoke helper for flash-linear-attention.

Default mode imports KDA public APIs and prints signatures. The optional CUDA
smoke runs one tiny chunk_kda forward call; it never launches distributed work.
"""

from __future__ import annotations

import argparse
import inspect
import os
import sys


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import-check KDA APIs and optionally run a tiny CUDA chunk_kda smoke.")
    parser.add_argument(
        "--require-cuda",
        action="store_true",
        help="Require CUDA and run a tiny chunk_kda forward smoke. No distributed process group is launched.",
    )
    parser.add_argument(
        "--dtype",
        choices=("float16", "bfloat16"),
        default="float16",
        help="CUDA smoke dtype. Default: float16.",
    )
    parser.add_argument(
        "--keep-optional-backends",
        action="store_true",
        help="Do not force-disable optional FlashKDA/TileLang/intra-card backend gates for the tiny smoke.",
    )
    return parser.parse_args()


def import_kda_apis():
    try:
        import torch
        from fla.layers.kda import KimiDeltaAttention
        from fla.models.kda import KDAConfig
        from fla.ops.cp import build_cp_context
        from fla.ops.kda import chunk_kda, fused_recurrent_kda
    except Exception as exc:  # pragma: no cover - environment dependent
        print(f"KDA import check failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return None
    return {
        "torch": torch,
        "chunk_kda": chunk_kda,
        "fused_recurrent_kda": fused_recurrent_kda,
        "KimiDeltaAttention": KimiDeltaAttention,
        "KDAConfig": KDAConfig,
        "build_cp_context": build_cp_context,
    }


def print_import_summary(apis: dict) -> None:
    torch = apis["torch"]
    KDAConfig = apis["KDAConfig"]
    KimiDeltaAttention = apis["KimiDeltaAttention"]

    print(f"torch: {torch.__version__}")
    print(f"cuda_available: {torch.cuda.is_available()}")
    print(f"chunk_kda signature: {inspect.signature(apis['chunk_kda'])}")
    print(f"fused_recurrent_kda signature: {inspect.signature(apis['fused_recurrent_kda'])}")
    print(f"build_cp_context signature: {inspect.signature(apis['build_cp_context'])}")

    config = KDAConfig(
        hidden_size=64,
        head_dim=32,
        num_heads=2,
        num_v_heads=2,
        num_hidden_layers=1,
        vocab_size=128,
        use_short_conv=False,
        safe_gate=True,
        lower_bound=-5.0,
    )
    layer = KimiDeltaAttention(
        hidden_size=64,
        head_dim=32,
        num_heads=2,
        num_v_heads=2,
        mode="chunk",
        use_short_conv=False,
        safe_gate=True,
        lower_bound=-5.0,
    )
    print(
        "constructed: "
        f"KDAConfig(model_type={config.model_type!r}, safe_gate={config.safe_gate}, lower_bound={config.lower_bound}); "
        f"KimiDeltaAttention(mode={layer.mode!r}, gate_dim={layer.gate_dim})"
    )


def run_cuda_smoke(apis: dict, dtype_name: str, keep_optional_backends: bool) -> int:
    torch = apis["torch"]
    chunk_kda = apis["chunk_kda"]

    if not torch.cuda.is_available():
        print("CUDA smoke requested but torch.cuda.is_available() is false.", file=sys.stderr)
        return 2

    if not keep_optional_backends:
        # Keep the smoke focused on the default KDA path unless the caller asks
        # to exercise optional dispatch. These env vars are read by backend
        # verifiers when the call is made.
        os.environ.setdefault("FLA_FLASH_KDA", "0")
        os.environ.setdefault("FLA_TILELANG", "0")
        os.environ.setdefault("FLA_INTRACARD_CP", "0")

    device = torch.device("cuda")
    dtype = getattr(torch, dtype_name)
    B, T, H, HV, K, V = 1, 64, 1, 1, 64, 64
    torch.manual_seed(0)

    q = torch.randn(B, T, H, K, device=device, dtype=dtype)
    k = torch.randn(B, T, H, K, device=device, dtype=dtype)
    v = torch.randn(B, T, HV, V, device=device, dtype=dtype)
    g = torch.randn(B, T, HV, K, device=device, dtype=dtype)
    beta = torch.randn(B, T, HV, device=device, dtype=dtype)
    A_log = torch.zeros(HV, device=device, dtype=torch.float32)
    dt_bias = torch.zeros(HV * K, device=device, dtype=torch.float32)

    with torch.inference_mode():
        out, final_state = chunk_kda(
            q=q,
            k=k,
            v=v,
            g=g,
            beta=beta,
            A_log=A_log,
            dt_bias=dt_bias,
            use_qk_l2norm_in_kernel=True,
            use_gate_in_kernel=True,
            use_beta_sigmoid_in_kernel=True,
            safe_gate=True,
            lower_bound=-5.0,
            state_v_first=True,
            chunk_size=32,
        )

    if final_state is not None:
        print(f"unexpected final_state: {tuple(final_state.shape)}", file=sys.stderr)
        return 3
    if out.shape != (B, T, HV, V):
        print(f"unexpected output shape: {tuple(out.shape)}", file=sys.stderr)
        return 4
    if not torch.isfinite(out.float()).all().item():
        print("output contains non-finite values", file=sys.stderr)
        return 5

    print(f"cuda_smoke_ok: output_shape={tuple(out.shape)} dtype={out.dtype} device={out.device}")
    return 0


def main() -> int:
    args = parse_args()
    apis = import_kda_apis()
    if apis is None:
        return 1

    print_import_summary(apis)
    if args.require_cuda:
        return run_cuda_smoke(apis, args.dtype, args.keep_optional_backends)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
