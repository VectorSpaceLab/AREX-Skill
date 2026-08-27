#!/usr/bin/env python3
"""Tiny CPU smoke for DALLE-pytorch DiscreteVAE."""
import argparse


def main():
    p = argparse.ArgumentParser(description="Run a tiny DiscreteVAE API smoke without downloads or training loops.")
    p.add_argument("--image-size", type=int, default=8)
    p.add_argument("--num-tokens", type=int, default=16)
    p.add_argument("--device", default="cpu")
    args = p.parse_args()

    import torch
    from dalle_pytorch import DiscreteVAE

    vae = DiscreteVAE(image_size=args.image_size, num_tokens=args.num_tokens, codebook_dim=8, num_layers=1, hidden_dim=8).to(args.device)
    images = torch.randn(2, 3, args.image_size, args.image_size, device=args.device)
    loss, recons = vae(images, return_loss=True, return_recons=True)
    indices = vae.get_codebook_indices(images)
    assert recons.shape == images.shape, (recons.shape, images.shape)
    assert indices.shape[0] == images.shape[0]
    assert torch.isfinite(loss)
    print(f"ok DiscreteVAE smoke: loss={float(loss.detach().cpu()):.6f} recons={tuple(recons.shape)} indices={tuple(indices.shape)} device={args.device}")


if __name__ == "__main__":
    main()
