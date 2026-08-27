#!/usr/bin/env python3
"""Non-interactive VINN k-selection helper.

This is a safe wrapper around the repository's k-selection logic. It avoids the
raw script's IPython breakpoint and exposes explicit arguments for the dataset
and feature files.

Example:
    python scripts/select_k.py --dataset-dir <dataset-dir> --ckpt-dir <out-dir> --feature-repr byol
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path

import h5py
import matplotlib.pyplot as plt
import numpy as np
import torch
import torch.nn.functional as F


def calculate_nearest_neighbors(query_inputs, query_targets, support_inputs, support_targets, max_k):
    with torch.no_grad():
        pairwise_dist = []
        for q_in in query_inputs:
            diff = support_inputs - q_in.unsqueeze(0)
            dist = torch.norm(diff, dim=1)
            pairwise_dist.append(dist)
        pairwise_dist = torch.stack(pairwise_dist)

        sorted_dist, index = torch.sort(pairwise_dist, dim=1)
        permuted_support_targets = support_targets[index]
        errors = []
        for k in range(1, max_k):
            topk_dist = pairwise_dist[:, :k]
            topk_support_targets = permuted_support_targets[:, :k]
            weights = F.softmax(-topk_dist, dim=1)
            weighted_support_targets = weights.unsqueeze(2) * topk_support_targets
            prediction = torch.sum(weighted_support_targets, dim=1)
            error = F.mse_loss(prediction, query_targets)
            errors.append(error)
        return errors


def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


def load_feature_file(dataset_dir: Path, repr_type: str, seed: int, episode_id: int):
    feature_path = dataset_dir / f"{repr_type}_features_seed{seed}_episode_{episode_id}.hdf5"
    if not feature_path.is_file():
        raise FileNotFoundError(f"missing feature file: {feature_path}")

    with h5py.File(feature_path, "r") as root:
        cam_names = list(root["/features"].keys())
        cam_arrays = [root[f"/features/{cam_name}"][()] for cam_name in cam_names]
    return cam_names, np.concatenate(cam_arrays, axis=1)


def main() -> int:
    parser = argparse.ArgumentParser(description="Select k for VINN using cached features.")
    parser.add_argument("--dataset-dir", required=True, help="Directory containing episode_<idx>.hdf5 and cached feature files.")
    parser.add_argument("--ckpt-dir", required=True, help="Directory where the k-selection plot and report will be written.")
    parser.add_argument("--feature-repr", default="byol", choices=["byol", "byol_cotrain"], help="Feature prefix used in the cached HDF5 filenames.")
    parser.add_argument("--seed", type=int, default=0, help="Seed embedded in the cached feature filenames.")
    parser.add_argument("--max-k", type=int, default=400, help="Upper bound on k (exclusive).")
    parser.add_argument("--batch-size", type=int, default=100, help="Batch size for validation evaluation.")
    parser.add_argument("--train-split", type=float, default=0.8, help="Fraction of dense episode ids used for training.")
    args = parser.parse_args()

    dataset_dir = Path(args.dataset_dir).expanduser().resolve()
    ckpt_dir = Path(args.ckpt_dir).expanduser().resolve()
    ckpt_dir.mkdir(parents=True, exist_ok=True)

    episode_idxs = [int(name.split("_")[1].split(".")[0]) for name in os.listdir(dataset_dir) if name.endswith(".hdf5") and "features" not in name]
    episode_idxs.sort()
    if not episode_idxs:
        raise SystemExit(f"no episode_*.hdf5 files found in {dataset_dir}")
    if episode_idxs[-1] + 1 != len(episode_idxs):
        raise SystemExit("episode indices must be dense from 0 with no holes")

    num_episodes = len(episode_idxs)
    val_split = int(num_episodes * args.train_split)
    if val_split <= 0 or val_split >= num_episodes:
        raise SystemExit(
            f"train_split={args.train_split} leaves no usable train/val split for {num_episodes} episodes"
        )
    repr_type = args.feature_repr

    print(f"dataset_dir={dataset_dir}")
    print(f"ckpt_dir={ckpt_dir}")
    print(f"repr_type={repr_type}")
    print(f"seed={args.seed}")
    print(f"num_episodes={num_episodes}")
    print(f"val_split={val_split}")

    train_X = []
    train_Y = []
    camera_names = None
    for episode_id in range(0, val_split):
        episode_path = dataset_dir / f"episode_{episode_id}.hdf5"
        with h5py.File(episode_path, "r") as root:
            action = root["/action"][()]
            camera_names = list(root["/observations/images"].keys())
        cam_names, cam_feature = load_feature_file(dataset_dir, repr_type, args.seed, episode_id)
        if camera_names is None:
            camera_names = cam_names
        train_X.append(cam_feature)
        train_Y.append(action)

    val_X = []
    val_Y = []
    for episode_id in range(val_split, num_episodes):
        episode_path = dataset_dir / f"episode_{episode_id}.hdf5"
        with h5py.File(episode_path, "r") as root:
            action = root["/action"][()]
            camera_names = list(root["/observations/images"].keys())
        _, cam_feature = load_feature_file(dataset_dir, repr_type, args.seed, episode_id)
        val_X.append(cam_feature)
        val_Y.append(action)

    train_inputs = torch.from_numpy(np.concatenate(train_X)).cuda()
    train_targets = torch.from_numpy(np.concatenate(train_Y)).cuda()
    val_inputs = torch.from_numpy(np.concatenate(val_X)).cuda()
    val_targets = torch.from_numpy(np.concatenate(val_Y)).cuda()

    val_losses = []
    for inputs, targets in zip(chunks(val_inputs, args.batch_size), chunks(val_targets, args.batch_size)):
        batch_loss = calculate_nearest_neighbors(inputs, targets, train_inputs, train_targets, args.max_k)
        val_losses.append(torch.stack(batch_loss))
    val_losses = torch.mean(torch.stack(val_losses), dim=0)
    val_loss = val_losses.detach().cpu().numpy()

    best_k = int(np.argmin(val_loss) + 1)
    print(f"best_k={best_k}")
    print(f"min_val_loss={float(np.min(val_loss))}")

    plot_path = ckpt_dir / f"k_select-seed{args.seed}.png"
    plt.plot(np.arange(1, args.max_k), val_loss)
    plt.savefig(plot_path)
    plt.close()
    print(f"saved_plot={plot_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
