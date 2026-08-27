#!/usr/bin/env python3
"""Tiny DALLE.generate_images smoke without checkpoint downloads."""
import argparse


def main():
    p = argparse.ArgumentParser(description="Run a tiny DALLE generation API smoke.")
    p.add_argument("--device", default="cpu")
    args = p.parse_args()
    import torch
    from dalle_pytorch import DiscreteVAE, DALLE

    vae = DiscreteVAE(image_size=8, num_tokens=16, codebook_dim=8, num_layers=1, hidden_dim=8).to(args.device)
    dalle = DALLE(dim=32, vae=vae, num_text_tokens=32, text_seq_len=4, depth=1, heads=2, dim_head=16, rotary_emb=False).to(args.device)
    text = torch.randint(1, 16, (1, 4), device=args.device)
    images = dalle.generate_images(text, filter_thres=0.9)
    assert images.shape == (1, 3, 8, 8), images.shape
    print(f"ok tiny generation: images={tuple(images.shape)} device={args.device}")


if __name__ == "__main__":
    main()
