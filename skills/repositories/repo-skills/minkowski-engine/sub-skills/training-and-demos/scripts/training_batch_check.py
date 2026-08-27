#!/usr/bin/env python3
"""Run a synthetic training-batch and tiny forward-pass smoke test.

This helper avoids downloads and long training runs. It checks that sparse
collation, sparse tensor construction, and a tiny classification head can work
on a small synthetic batch.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import torch
from torch.utils.data import DataLoader, Dataset


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, help="Optional local checkout root to add to sys.path.")
    parser.add_argument("--device", choices=("cpu", "cuda", "auto"), default="cpu")
    parser.add_argument("--batch-size", type=int, default=2)
    parser.add_argument("--num-items", type=int, default=4)
    parser.add_argument("--collate", choices=("sparse-collate", "batch-sparse-collate", "sparse-collation"), default="sparse-collate")
    return parser.parse_args()


def add_repo_root(repo_root: Path | None) -> None:
    if repo_root:
        sys.path.insert(0, str(repo_root.resolve()))


class ToySparseDataset(Dataset):
    def __init__(self, n_items: int):
        self.n_items = n_items

    def __len__(self) -> int:
        return self.n_items

    def __getitem__(self, idx: int):
        coords = torch.tensor([[0, 0], [0, 1], [1, 0]], dtype=torch.int32) + (idx % 2)
        feats = torch.tensor([[1.0], [2.0], [3.0]], dtype=torch.float32) + idx
        label = torch.tensor([idx % 3], dtype=torch.long)
        return coords, feats, label


def choose_device(requested: str, me):
    if requested == "cpu":
        return "cpu"
    cuda_ok = torch.cuda.is_available() and me.is_cuda_available()
    if requested == "cuda" and not cuda_ok:
        raise SystemExit("CUDA requested but not available in the current environment")
    return "cuda" if cuda_ok else "cpu"


def make_collate(me, kind: str):
    if kind == "sparse-collate":
        return lambda batch: me.utils.sparse_collate([x[0] for x in batch], [x[1] for x in batch], [x[2] for x in batch])
    if kind == "batch-sparse-collate":
        return me.utils.batch_sparse_collate
    return me.utils.SparseCollation()


def main() -> int:
    args = parse_args()
    add_repo_root(args.repo_root)
    try:
        import MinkowskiEngine as ME
    except Exception as exc:  # noqa: BLE001
        print(f"failed to import MinkowskiEngine: {exc}", file=sys.stderr)
        return 1

    device = choose_device(args.device, ME)
    dataset = ToySparseDataset(args.num_items)
    loader = DataLoader(dataset, batch_size=args.batch_size, shuffle=False, collate_fn=make_collate(ME, args.collate), num_workers=0)

    conv = ME.MinkowskiConvolution(1, 4, kernel_size=3, stride=1, dimension=2)
    bn = ME.MinkowskiBatchNorm(4)
    relu = ME.MinkowskiReLU()
    pool = ME.MinkowskiGlobalMaxPooling()
    head = ME.MinkowskiLinear(4, 3)
    if device == "cuda":
        conv, bn, relu, pool, head = conv.cuda(), bn.cuda(), relu.cuda(), pool.cuda(), head.cuda()

    batch_summaries = []
    for batch in loader:
        if len(batch) == 3:
            coords, feats, labels = batch
        else:
            coords, feats = batch
            labels = torch.zeros(len(feats), dtype=torch.long)
        st = ME.SparseTensor(features=feats, coordinates=coords, device=device)
        with torch.no_grad():
            logits = head(pool(relu(bn(conv(st)))))
        batch_summaries.append({
            "coords": list(coords.shape),
            "feats": list(feats.shape),
            "labels": list(labels.shape),
            "logits": list(logits.F.shape),
        })

    print(json.dumps({"device": device, "batches": batch_summaries}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
