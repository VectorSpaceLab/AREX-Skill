#!/usr/bin/env python3
"""Safe CPU environment check for vector-quantize-pytorch.

This helper verifies that the public package imports and that representative
quantizer families run on tiny random tensors. It never downloads data or runs
training loops.

Example:
  python scripts/check_vector_quantize_env.py
"""

from __future__ import annotations

import argparse
import sys


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a tiny vector-quantize-pytorch import and API smoke check.")
    parser.add_argument("--seed", type=int, default=0, help="Torch random seed for deterministic smoke tensors.")
    parser.add_argument("--skip-hierarchical", action="store_true", help="Skip the small HierarchicalVQ check.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        import torch
        from vector_quantize_pytorch import (
            FSQ,
            LFQ,
            LatentQuantize,
            ResidualVQ,
            SimVQ,
            VectorQuantize,
        )
        from vector_quantize_pytorch import HierarchicalVQ
    except Exception as exc:  # pragma: no cover - diagnostic path
        print(f"IMPORT_FAIL: {exc}", file=sys.stderr)
        print("Install the base package with `pip install vector-quantize-pytorch` in this Python environment.", file=sys.stderr)
        return 2

    torch.manual_seed(args.seed)
    print(f"torch={torch.__version__} cuda_available={torch.cuda.is_available()}")

    x = torch.randn(1, 8, 16)
    vq = VectorQuantize(dim=16, codebook_size=8)
    quantized, indices, loss = vq(x)
    assert quantized.shape == x.shape, (quantized.shape, x.shape)
    assert indices.shape == (1, 8), indices.shape
    print("VectorQuantize ok", tuple(quantized.shape), tuple(indices.shape), tuple(loss.shape))

    rvq = ResidualVQ(dim=16, codebook_size=8, num_quantizers=2)
    rvq.eval()
    rq, ridx, rloss = rvq(x)
    rout = rvq.get_output_from_indices(ridx)
    assert rq.shape == x.shape
    assert ridx.shape == (1, 8, 2)
    assert torch.allclose(rq, rout, atol=1e-5)
    print("ResidualVQ ok", tuple(rq.shape), tuple(ridx.shape), tuple(rloss.shape))

    fx = torch.randn(1, 8, 4)
    fsq = FSQ(levels=[4, 4, 4, 4])
    fq, findices = fsq(fx)
    assert fq.shape == fx.shape
    assert torch.equal(fq, fsq.indices_to_codes(findices))
    print("FSQ ok", tuple(fq.shape), tuple(findices.shape))

    lfq = LFQ(codebook_size=16, dim=4)
    lq, lidx, lloss = lfq(fx)
    assert lq.shape == fx.shape
    assert lidx.shape == (1, 8)
    print("LFQ ok", tuple(lq.shape), tuple(lidx.shape), tuple(lloss.shape))

    lat = LatentQuantize(levels=[2, 2], dim=4)
    img = torch.randn(1, 4, 2, 2)
    latq, latidx, latloss = lat(img)
    assert latq.shape == img.shape
    assert latidx.shape == (1, 2, 2)
    print("LatentQuantize ok", tuple(latq.shape), tuple(latidx.shape))

    sim = SimVQ(dim=8, codebook_size=16)
    sx = torch.randn(1, 8, 8)
    sq, sidx, sloss = sim(sx)
    assert sq.shape == sx.shape
    assert torch.allclose(sq, sim.indices_to_codes(sidx), atol=1e-6)
    print("SimVQ ok", tuple(sq.shape), tuple(sidx.shape))

    if not args.skip_hierarchical:
        hq = HierarchicalVQ(
            dim=8,
            codebook_size=16,
            accept_image_fmap=True,
            scales=(1, 2),
            quant_resi=0.5,
            share_quant_resi=1,
        )
        hx = torch.randn(1, 8, 4, 4)
        hq_out, hidx, hloss = hq(hx)
        assert hq_out.shape == hx.shape
        assert len(hidx) == 2
        assert torch.isfinite(hloss).all()
        print("HierarchicalVQ ok", tuple(hq_out.shape), len(hidx))

    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
