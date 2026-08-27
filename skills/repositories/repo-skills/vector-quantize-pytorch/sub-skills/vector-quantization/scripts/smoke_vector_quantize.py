#!/usr/bin/env python3
from __future__ import annotations

import argparse

import torch


def check_vector_quantize() -> None:
    from vector_quantize_pytorch import VectorQuantize

    torch.manual_seed(0)
    vq = VectorQuantize(dim=8, codebook_size=16, decay=0.9, commitment_weight=1.0)
    x = torch.randn(2, 5, 8)

    vq.train()
    quantized, indices, loss = vq(x)
    assert quantized.shape == x.shape
    assert indices.shape == (2, 5)
    assert loss.ndim == 0

    vq.eval()
    quantized_eval, indices_eval, loss_eval = vq(x)
    assert quantized_eval.shape == x.shape
    assert indices_eval.shape == (2, 5)
    assert loss_eval.ndim == 0
    assert torch.allclose(quantized_eval, vq.get_output_from_indices(indices_eval), atol=1e-5)


def check_masked_sequence() -> None:
    from vector_quantize_pytorch import VectorQuantize

    torch.manual_seed(1)
    vq = VectorQuantize(
        dim=8,
        codebook_size=16,
        decay=1.0,
        commitment_weight=1.0,
        return_zeros_for_masked_padding=True,
    )
    x = torch.randn(1, 6, 8)
    lens = torch.tensor([4])

    vq.train()
    quantized, indices, loss = vq(x, lens=lens)
    assert quantized.shape == x.shape
    assert indices.shape == (1, 6)
    assert loss.ndim == 0
    assert torch.allclose(quantized[:, 4:], torch.zeros_like(quantized[:, 4:]))
    assert torch.equal(indices[:, 4:], torch.full((1, 2), -1, dtype=indices.dtype))


def check_topk_and_manual_ema() -> None:
    from vector_quantize_pytorch import VectorQuantize

    torch.manual_seed(2)
    vq1 = VectorQuantize(dim=8, codebook_size=16, decay=0.8, commitment_weight=1.0)
    vq2 = VectorQuantize(dim=8, codebook_size=16, decay=0.8, commitment_weight=1.0)
    vq2.load_state_dict(vq1.state_dict())

    x = torch.randn(1, 6, 8)
    mask = torch.tensor([[True, True, True, False, True, False]])

    vq1.train()
    quantized1, indices1, commit_loss1 = vq1(x, mask=mask)

    vq2.train()
    quantized2, indices2, commit_losses = vq2(x, mask=mask, topk=1, ema_update=False)

    assert quantized2.shape == (1, 6, 1, 8)
    assert indices2.shape == (1, 6, 1)
    assert commit_losses.shape == (1, 6, 1)
    assert torch.allclose(commit_loss1, commit_losses.sum() / mask.sum())
    assert torch.equal(indices1, indices2[..., 0])
    assert torch.allclose(quantized1, quantized2[..., 0, :])

    vq2.update_ema_indices(x, indices2[..., 0], mask=mask)


def check_random_projection_quantizer() -> None:
    from vector_quantize_pytorch import RandomProjectionQuantizer

    torch.manual_seed(3)
    rq = RandomProjectionQuantizer(dim=8, codebook_size=16, codebook_dim=4, num_codebooks=2)
    x = torch.randn(2, 5, 8)

    indices = rq(x)
    assert indices.shape == (2, 5, 2)

    loss = rq(x, indices=indices)
    assert loss.ndim == 0
    assert loss.item() >= 0


def check_image_or_volume_shapes() -> None:
    from vector_quantize_pytorch import VectorQuantize

    torch.manual_seed(4)
    vq_img = VectorQuantize(
        dim=8,
        codebook_size=16,
        codebook_dim=4,
        heads=2,
        separate_codebook_per_head=True,
        accept_image_fmap=True,
    )
    img = torch.randn(1, 8, 4, 4)
    quantized_img, indices_img, _ = vq_img(img)
    assert quantized_img.shape == img.shape
    assert indices_img.shape == (1, 4, 4, 2)

    vq_3d = VectorQuantize(dim=8, codebook_size=16, accept_3d_fmap=True)
    vol = torch.randn(1, 8, 2, 2, 2)
    quantized_vol, indices_vol, _ = vq_3d(vol)
    assert quantized_vol.shape == vol.shape
    assert indices_vol.shape == (1, 2, 2, 2)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Tiny CPU smoke checks for vector quantization APIs.")
    parser.add_argument("--skip-mask", action="store_true", help="Skip the masked sequence check.")
    parser.add_argument("--skip-topk", action="store_true", help="Skip the top-k and manual EMA check.")
    parser.add_argument("--include-image", action="store_true", help="Also check image feature-map routing.")
    parser.add_argument("--include-3d", action="store_true", help="Also check 3D feature-map routing.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    checks = [
        ("vector-quantize", check_vector_quantize),
        ("random-projection-quantizer", check_random_projection_quantizer),
    ]

    if not args.skip_mask:
        checks.append(("masked-sequence", check_masked_sequence))

    if not args.skip_topk:
        checks.append(("topk-and-manual-ema", check_topk_and_manual_ema))

    if args.include_image or args.include_3d:
        checks.append(("image-and-3d-shapes", check_image_or_volume_shapes))

    for name, check in checks:
        print(f"[smoke] {name} ...", end=" ")
        check()
        print("ok")

    print("vector quantize smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
