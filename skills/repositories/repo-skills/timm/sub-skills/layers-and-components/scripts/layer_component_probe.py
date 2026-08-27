#!/usr/bin/env python3
"""No-download smoke probe for timm reusable layers and components."""

import argparse

import torch

from timm.layers import ClassifierHead, DropPath, PatchEmbed, SelectAdaptivePool2d


def _shape(tensor: torch.Tensor) -> str:
    return "x".join(str(dim) for dim in tensor.shape)


def run_probe(batch_size: int = 2, image_size: int = 32, patch_size: int = 4, seed: int = 123) -> None:
    torch.manual_seed(seed)

    images = torch.randn(batch_size, 3, image_size, image_size)

    patch_embed = PatchEmbed(
        img_size=image_size,
        patch_size=patch_size,
        in_chans=3,
        embed_dim=64,
    )
    patch_tokens = patch_embed(images)
    expected_grid = image_size // patch_size
    assert patch_tokens.shape == (batch_size, expected_grid * expected_grid, 64)

    feature_map = patch_tokens.transpose(1, 2).reshape(batch_size, 64, expected_grid, expected_grid)

    pool = SelectAdaptivePool2d(pool_type="catavgmax", flatten=True)
    pooled = pool(feature_map)
    assert pooled.shape == (batch_size, 128)

    head = ClassifierHead(in_features=64, num_classes=7, pool_type="avg")
    logits = head(feature_map)
    assert logits.shape == (batch_size, 7)

    drop_path = DropPath(0.5)
    drop_path.eval()
    eval_out = drop_path(feature_map)
    assert torch.equal(eval_out, feature_map)

    print(f"input={_shape(images)}")
    print(f"patch_tokens={_shape(patch_tokens)}")
    print(f"feature_map={_shape(feature_map)}")
    print(f"catavgmax_pooled={_shape(pooled)}")
    print(f"classifier_logits={_shape(logits)}")
    print("drop_path_eval=identity")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch-size", type=int, default=2)
    parser.add_argument("--image-size", type=int, default=32)
    parser.add_argument("--patch-size", type=int, default=4)
    parser.add_argument("--seed", type=int, default=123)
    args = parser.parse_args()

    if args.image_size % args.patch_size != 0:
        raise SystemExit("--image-size must be divisible by --patch-size for this strict PatchEmbed probe")

    run_probe(
        batch_size=args.batch_size,
        image_size=args.image_size,
        patch_size=args.patch_size,
        seed=args.seed,
    )


if __name__ == "__main__":
    main()
