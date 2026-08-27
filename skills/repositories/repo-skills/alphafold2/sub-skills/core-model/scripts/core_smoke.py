#!/usr/bin/env python3
"""Run a deterministic, tiny Alphafold2 core-model smoke without network or repo files.

The helper is safe to invoke from any working directory after the package is
installed. It defaults to CPU and checks distance-logit shape, optional angle
logit shapes, the no-MSA fallback, and optional template/direct-embedding
routes. It intentionally does not run native repository tests or download
pretrained models.
"""

from __future__ import annotations

import argparse
import sys


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--device",
        default="cpu",
        help="torch device such as cpu or cuda:0 (default: cpu)",
    )
    parser.add_argument(
        "--angles",
        action="store_true",
        help="also construct predict_angles=True and check angle logits",
    )
    parser.add_argument(
        "--templates",
        action="store_true",
        help="also check tiny templates_feats/templates_mask inputs",
    )
    parser.add_argument(
        "--embedding-input",
        action="store_true",
        help="also check seq_embed/msa_embed with token embeddings disabled",
    )
    return parser.parse_args()


def import_runtime():
    try:
        import torch
        from alphafold2_pytorch import Alphafold2
    except Exception as exc:  # import failures need an actionable, short result
        print(
            "core_smoke: alphafold2_pytorch import failed. Install the "
            "alphafold2-pytorch 0.4.32 dependencies (including torch, "
            "PyTorch3D, invariant-point-attention, Biopython, sidechainnet, "
            "and mp-nerf) in the active environment. "
            f"Original error: {type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        raise SystemExit(2)
    return torch, Alphafold2


def assert_core_output(ret, batch: int, length: int, *, angles: bool) -> None:
    expected = (batch, length, length, 37)
    assert tuple(ret.distance.shape) == expected, (
        f"distance shape {tuple(ret.distance.shape)} != {expected}"
    )
    assert bool(ret.distance.isfinite().all()), "distance logits contain non-finite values"
    if angles:
        expected_angles = {
            "theta_logits": (batch, length, length, 25),
            "phi_logits": (batch, length, length, 13),
            "omega_logits": (batch, length, length, 25),
        }
        for name, shape in expected_angles.items():
            value = getattr(ret, name)
            assert tuple(value.shape) == shape, (
                f"{name} shape {tuple(value.shape)} != {shape}"
            )
            assert bool(value.isfinite().all()), f"{name} contains non-finite values"


def make_inputs(torch, device, batch: int = 1, rows: int = 2, length: int = 4):
    seq = torch.arange(batch * length, device=device).reshape(batch, length) % 21
    msa = (
        torch.arange(batch * rows * length, device=device).reshape(batch, rows, length)
        % 21
    )
    mask = torch.ones(batch, length, dtype=torch.bool, device=device)
    msa_mask = torch.ones(batch, rows, length, dtype=torch.bool, device=device)
    return seq, msa, mask, msa_mask


def run(args: argparse.Namespace) -> int:
    torch, Alphafold2 = import_runtime()
    try:
        device = torch.device(args.device)
    except Exception as exc:
        print(f"core_smoke: invalid --device {args.device!r}: {exc}", file=sys.stderr)
        return 2

    if device.type == "cuda" and not torch.cuda.is_available():
        print(
            "core_smoke: CUDA was requested but torch.cuda.is_available() is false; "
            "retry with --device cpu or prepare a CUDA-capable environment.",
            file=sys.stderr,
        )
        return 2

    torch.manual_seed(0)
    batch, rows, length, dim = 1, 2, 4, 16
    try:
        with torch.no_grad():
            seq, msa, mask, msa_mask = make_inputs(
                torch, device, batch=batch, rows=rows, length=length
            )
            model = Alphafold2(dim=dim, depth=1, heads=1, dim_head=dim).to(device).eval()
            ret = model(seq, msa, mask=mask, msa_mask=msa_mask)
            assert_core_output(ret, batch, length, angles=False)
            print(f"base distance={tuple(ret.distance.shape)} device={device}")

            # The source's no-MSA fallback needs mask and creates an M=1 MSA.
            no_msa = Alphafold2(dim=dim, depth=1, heads=1, dim_head=dim).to(device).eval()
            no_msa_ret = no_msa(seq, mask=mask)
            assert_core_output(no_msa_ret, batch, length, angles=False)
            print(f"no_msa distance={tuple(no_msa_ret.distance.shape)}")

            if args.angles:
                angle_model = Alphafold2(
                    dim=dim, depth=1, heads=1, dim_head=dim, predict_angles=True
                ).to(device).eval()
                angle_ret = angle_model(seq, msa, mask=mask, msa_mask=msa_mask)
                assert_core_output(angle_ret, batch, length, angles=True)
                print(
                    "angles distance="
                    f"{tuple(angle_ret.distance.shape)} "
                    f"theta={tuple(angle_ret.theta_logits.shape)} "
                    f"phi={tuple(angle_ret.phi_logits.shape)} "
                    f"omega={tuple(angle_ret.omega_logits.shape)}"
                )

            if args.templates:
                template_model = Alphafold2(
                    dim=dim,
                    depth=1,
                    heads=1,
                    dim_head=dim,
                    templates_dim=32,
                    templates_angles_feats_dim=55,
                    predict_angles=args.angles,
                ).to(device).eval()
                template_count = 2
                templates_feats = torch.arange(
                    batch * template_count * length * length * 32,
                    device=device,
                    dtype=torch.float32,
                ).reshape(batch, template_count, length, length, 32)
                templates_angles = torch.arange(
                    batch * template_count * length * 55,
                    device=device,
                    dtype=torch.float32,
                ).reshape(batch, template_count, length, 55)
                templates_mask = torch.ones(
                    batch, template_count, length, dtype=torch.bool, device=device
                )
                template_ret = template_model(
                    seq,
                    msa,
                    mask=mask,
                    msa_mask=msa_mask,
                    templates_feats=templates_feats,
                    templates_angles=templates_angles,
                    templates_mask=templates_mask,
                )
                assert_core_output(template_ret, batch, length, angles=args.angles)
                print(f"templates distance={tuple(template_ret.distance.shape)}")

            if args.embedding_input:
                embed_model = Alphafold2(
                    dim=dim,
                    depth=1,
                    heads=1,
                    dim_head=dim,
                    disable_token_embed=True,
                ).to(device).eval()
                seq_embed = torch.zeros(batch, length, dim, device=device)
                msa_embed = torch.zeros(batch, rows, length, dim, device=device)
                embed_ret = embed_model(
                    seq,
                    msa,
                    mask=mask,
                    msa_mask=msa_mask,
                    seq_embed=seq_embed,
                    msa_embed=msa_embed,
                )
                assert_core_output(embed_ret, batch, length, angles=False)
                print(f"embedding_input distance={tuple(embed_ret.distance.shape)}")
    except RuntimeError as exc:
        print(
            "core_smoke: model execution failed. Retry with --device cpu and the "
            "default tiny dimensions; a CUDA out-of-memory error means the device "
            "is unavailable for this smoke. "
            f"Original error: {exc}",
            file=sys.stderr,
        )
        return 1
    except AssertionError as exc:
        print(f"core_smoke: shape/finite-output assertion failed: {exc}", file=sys.stderr)
        return 1

    print("core_smoke: PASS")
    return 0


def main() -> None:
    raise SystemExit(run(parse_args()))


if __name__ == "__main__":
    main()
