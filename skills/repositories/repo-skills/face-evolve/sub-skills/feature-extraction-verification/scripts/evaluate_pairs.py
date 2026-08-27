#!/usr/bin/env python3
"""Evaluate pair-ordered face.evoLVe embeddings.

This script implements the LFW-style metric semantics distilled from
util/verification.py. It accepts plain .npy files and does not require bcolz or
any original repository utility module.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Tuple

import numpy as np
from scipy import interpolate
from sklearn import preprocessing
from sklearn.decomposition import PCA
from sklearn.model_selection import KFold


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Compute face.evoLVe LFW-style ROC, threshold accuracy, and VAL metrics "
            "from a pair-ordered embeddings .npy and issame .npy."
        )
    )
    parser.add_argument("--embeddings-npy", required=True, help="2-D array with rows [a0,b0,a1,b1,...].")
    parser.add_argument("--issame-npy", required=True, help="Boolean .npy with one same/different label per pair.")
    parser.add_argument(
        "--output-json",
        help="Output JSON path. Default: <embeddings stem>.verification.json",
    )
    parser.add_argument("--nrof-folds", type=int, default=10, help="K-fold count. Must be <= number of pairs.")
    parser.add_argument("--pca", type=int, default=0, help="Optional PCA dimension; 0 disables PCA.")
    parser.add_argument(
        "--far-target",
        type=float,
        default=1e-3,
        help="Target FAR for calculate_val-style VAL reporting.",
    )
    return parser.parse_args()


def calculate_accuracy(threshold: float, dist: np.ndarray, actual_issame: np.ndarray) -> Tuple[float, float, float]:
    predict_issame = np.less(dist, threshold)
    tp = np.sum(np.logical_and(predict_issame, actual_issame))
    fp = np.sum(np.logical_and(predict_issame, np.logical_not(actual_issame)))
    tn = np.sum(np.logical_and(np.logical_not(predict_issame), np.logical_not(actual_issame)))
    fn = np.sum(np.logical_and(np.logical_not(predict_issame), actual_issame))

    tpr = 0.0 if (tp + fn == 0) else float(tp) / float(tp + fn)
    fpr = 0.0 if (fp + tn == 0) else float(fp) / float(fp + tn)
    acc = float(tp + tn) / float(dist.size)
    return tpr, fpr, acc


def calculate_roc(
    thresholds: np.ndarray,
    embeddings1: np.ndarray,
    embeddings2: np.ndarray,
    actual_issame: np.ndarray,
    nrof_folds: int = 10,
    pca: int = 0,
):
    assert embeddings1.shape[0] == embeddings2.shape[0]
    assert embeddings1.shape[1] == embeddings2.shape[1]
    nrof_pairs = min(len(actual_issame), embeddings1.shape[0])
    nrof_thresholds = len(thresholds)
    k_fold = KFold(n_splits=nrof_folds, shuffle=False)

    tprs = np.zeros((nrof_folds, nrof_thresholds))
    fprs = np.zeros((nrof_folds, nrof_thresholds))
    accuracy = np.zeros((nrof_folds))
    best_thresholds = np.zeros((nrof_folds))
    indices = np.arange(nrof_pairs)

    if pca == 0:
        diff = np.subtract(embeddings1, embeddings2)
        dist = np.sum(np.square(diff), axis=1)

    for fold_idx, (train_set, test_set) in enumerate(k_fold.split(indices)):
        if pca > 0:
            embed1_train = embeddings1[train_set]
            embed2_train = embeddings2[train_set]
            embed_train = np.concatenate((embed1_train, embed2_train), axis=0)
            pca_model = PCA(n_components=pca)
            pca_model.fit(embed_train)
            embed1 = preprocessing.normalize(pca_model.transform(embeddings1))
            embed2 = preprocessing.normalize(pca_model.transform(embeddings2))
            diff = np.subtract(embed1, embed2)
            dist = np.sum(np.square(diff), axis=1)

        acc_train = np.zeros((nrof_thresholds))
        for threshold_idx, threshold in enumerate(thresholds):
            _, _, acc_train[threshold_idx] = calculate_accuracy(
                threshold, dist[train_set], actual_issame[train_set]
            )
        best_threshold_index = int(np.argmax(acc_train))
        best_thresholds[fold_idx] = thresholds[best_threshold_index]

        for threshold_idx, threshold in enumerate(thresholds):
            tprs[fold_idx, threshold_idx], fprs[fold_idx, threshold_idx], _ = calculate_accuracy(
                threshold, dist[test_set], actual_issame[test_set]
            )
        _, _, accuracy[fold_idx] = calculate_accuracy(
            thresholds[best_threshold_index], dist[test_set], actual_issame[test_set]
        )

    tpr = np.mean(tprs, axis=0)
    fpr = np.mean(fprs, axis=0)
    return tpr, fpr, accuracy, best_thresholds


def calculate_val_far(threshold: float, dist: np.ndarray, actual_issame: np.ndarray) -> Tuple[float, float]:
    predict_issame = np.less(dist, threshold)
    true_accept = np.sum(np.logical_and(predict_issame, actual_issame))
    false_accept = np.sum(np.logical_and(predict_issame, np.logical_not(actual_issame)))
    n_same = np.sum(actual_issame)
    n_diff = np.sum(np.logical_not(actual_issame))
    val = 0.0 if n_same == 0 else float(true_accept) / float(n_same)
    far = 0.0 if n_diff == 0 else float(false_accept) / float(n_diff)
    return val, far


def interpolate_threshold_at_far(far_train: np.ndarray, thresholds: np.ndarray, far_target: float) -> float:
    if np.max(far_train) < far_target:
        return 0.0
    unique_far, unique_indices = np.unique(far_train, return_index=True)
    unique_thresholds = thresholds[unique_indices]
    if unique_far.size == 1:
        return float(unique_thresholds[0])
    interpolator = interpolate.interp1d(unique_far, unique_thresholds, kind="linear", bounds_error=False)
    return float(interpolator(far_target))


def calculate_val(
    thresholds: np.ndarray,
    embeddings1: np.ndarray,
    embeddings2: np.ndarray,
    actual_issame: np.ndarray,
    far_target: float,
    nrof_folds: int = 10,
):
    assert embeddings1.shape[0] == embeddings2.shape[0]
    assert embeddings1.shape[1] == embeddings2.shape[1]
    nrof_pairs = min(len(actual_issame), embeddings1.shape[0])
    nrof_thresholds = len(thresholds)
    k_fold = KFold(n_splits=nrof_folds, shuffle=False)

    val = np.zeros(nrof_folds)
    far = np.zeros(nrof_folds)

    diff = np.subtract(embeddings1, embeddings2)
    dist = np.sum(np.square(diff), axis=1)
    indices = np.arange(nrof_pairs)

    for fold_idx, (train_set, test_set) in enumerate(k_fold.split(indices)):
        far_train = np.zeros(nrof_thresholds)
        for threshold_idx, threshold in enumerate(thresholds):
            _, far_train[threshold_idx] = calculate_val_far(
                threshold, dist[train_set], actual_issame[train_set]
            )
        threshold = interpolate_threshold_at_far(far_train, thresholds, far_target)
        val[fold_idx], far[fold_idx] = calculate_val_far(
            threshold, dist[test_set], actual_issame[test_set]
        )

    val_mean = np.mean(val)
    far_mean = np.mean(far)
    val_std = np.std(val)
    return val_mean, val_std, far_mean


def evaluate(embeddings: np.ndarray, actual_issame: np.ndarray, nrof_folds: int = 10, pca: int = 0):
    thresholds = np.arange(0, 4, 0.01)
    embeddings1 = embeddings[0::2]
    embeddings2 = embeddings[1::2]
    return calculate_roc(thresholds, embeddings1, embeddings2, np.asarray(actual_issame), nrof_folds, pca)


def validate_inputs(embeddings: np.ndarray, issame: np.ndarray, nrof_folds: int, pca: int) -> np.ndarray:
    if embeddings.ndim != 2:
        raise SystemExit(f"Embeddings must be 2-D [num_rows, embedding_dim], got shape {embeddings.shape}")
    if embeddings.shape[0] == 0:
        raise SystemExit("Embeddings array is empty")
    if embeddings.shape[0] % 2 != 0:
        raise SystemExit(
            f"Embeddings row count must be even because rows are paired, got {embeddings.shape[0]}"
        )
    if embeddings.shape[1] <= 0:
        raise SystemExit("Embedding dimension must be positive")
    if not np.all(np.isfinite(embeddings)):
        raise SystemExit("Embeddings contain NaN or infinite values")

    issame = np.asarray(issame).reshape(-1).astype(bool)
    num_pairs = embeddings.shape[0] // 2
    if issame.shape[0] != num_pairs:
        raise SystemExit(
            f"issame length must equal num_pairs ({num_pairs}), got {issame.shape[0]}"
        )
    if nrof_folds < 2:
        raise SystemExit("--nrof-folds must be at least 2")
    if nrof_folds > num_pairs:
        raise SystemExit(
            f"--nrof-folds ({nrof_folds}) must be <= number of pairs ({num_pairs})"
        )
    if pca < 0:
        raise SystemExit("--pca must be non-negative")
    if pca > 0 and pca > embeddings.shape[1]:
        raise SystemExit(
            f"--pca ({pca}) must be <= embedding dimension ({embeddings.shape[1]})"
        )
    return issame


def default_output_json(embeddings_path: Path) -> Path:
    if embeddings_path.suffix == ".npy":
        return embeddings_path.with_suffix(".verification.json")
    return embeddings_path.with_name(embeddings_path.name + ".verification.json")


def main() -> int:
    args = parse_args()
    embeddings_path = Path(args.embeddings_npy).expanduser().resolve()
    issame_path = Path(args.issame_npy).expanduser().resolve()
    if not embeddings_path.exists():
        raise SystemExit(f"--embeddings-npy does not exist: {embeddings_path}")
    if not issame_path.exists():
        raise SystemExit(f"--issame-npy does not exist: {issame_path}")

    embeddings = np.load(embeddings_path)
    issame = np.load(issame_path, allow_pickle=False)
    issame = validate_inputs(embeddings, issame, args.nrof_folds, args.pca)

    thresholds = np.arange(0, 4, 0.01)
    tpr, fpr, accuracy, best_thresholds = evaluate(
        embeddings, issame, nrof_folds=args.nrof_folds, pca=args.pca
    )
    embeddings1 = embeddings[0::2]
    embeddings2 = embeddings[1::2]
    val_mean, val_std, far_mean = calculate_val(
        thresholds,
        embeddings1,
        embeddings2,
        issame,
        far_target=args.far_target,
        nrof_folds=args.nrof_folds,
    )

    result = {
        "schema": "face-evolve-verification-metrics-v1",
        "inputs": {
            "embeddings_npy": str(embeddings_path),
            "issame_npy": str(issame_path),
        },
        "pair_count": int(embeddings.shape[0] // 2),
        "embedding_dim": int(embeddings.shape[1]),
        "nrof_folds": int(args.nrof_folds),
        "pca": int(args.pca),
        "far_target": float(args.far_target),
        "accuracy_mean": float(np.mean(accuracy)),
        "accuracy_std": float(np.std(accuracy)),
        "best_threshold_mean": float(np.mean(best_thresholds)),
        "fold_accuracy": accuracy.tolist(),
        "fold_best_thresholds": best_thresholds.tolist(),
        "val_mean": float(val_mean),
        "val_std": float(val_std),
        "far_mean": float(far_mean),
        "roc": {
            "thresholds": thresholds.tolist(),
            "tpr": tpr.tolist(),
            "fpr": fpr.tolist(),
        },
    }

    output_path = Path(args.output_json).expanduser().resolve() if args.output_json else default_output_json(embeddings_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")

    print(
        f"Wrote verification metrics to {output_path} | pairs={result['pair_count']} | "
        f"embedding_dim={result['embedding_dim']} | "
        f"accuracy_mean={result['accuracy_mean']:.6f} | "
        f"best_threshold_mean={result['best_threshold_mean']:.4f}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
