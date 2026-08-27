#!/usr/bin/env python3
"""Post-process HRM ARC evaluation predictions saved by evaluate.py.

This is a compact CLI adaptation of the repository's ARC notebook logic. It
loads `*_all_preds.*` shards, removes padding puzzle identifiers, reverses ARC
augmentation names, groups predictions by original puzzle/input, and reports
whether the correct answer appears in the top-K vote buckets.
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import torch

PAD_PUZZLE_IDENTIFIER = 0
DIHEDRAL_INVERSE = [0, 3, 2, 1, 4, 5, 6, 7]


def dihedral_transform(arr: np.ndarray, tid: int) -> np.ndarray:
    if tid == 0:
        return arr
    if tid == 1:
        return np.rot90(arr, k=1)
    if tid == 2:
        return np.rot90(arr, k=2)
    if tid == 3:
        return np.rot90(arr, k=3)
    if tid == 4:
        return np.fliplr(arr)
    if tid == 5:
        return np.flipud(arr)
    if tid == 6:
        return arr.T
    if tid == 7:
        return np.fliplr(np.rot90(arr, k=1))
    raise ValueError(f"bad dihedral transform id: {tid}")


def inverse_dihedral_transform(arr: np.ndarray, tid: int) -> np.ndarray:
    return dihedral_transform(arr, DIHEDRAL_INVERSE[tid])


def crop_arc_sequence(seq: np.ndarray) -> np.ndarray:
    grid = np.asarray(seq).reshape(30, 30)
    max_area = 0
    max_size = (0, 0)
    nr, nc = grid.shape
    num_c = nc
    for num_r in range(1, nr + 1):
        for c in range(1, num_c + 1):
            value = grid[num_r - 1, c - 1]
            if (value < 2) or (value > 11):
                num_c = c - 1
                break
        area = num_r * num_c
        if area > max_area:
            max_area = area
            max_size = (num_r, num_c)
    return grid[: max_size[0], : max_size[1]] - 2


def inverse_aug(name: str, grid: np.ndarray) -> np.ndarray:
    parts = name.split("_")
    if len(parts) < 3 or not parts[-2].startswith("t"):
        return grid
    trans_id = int(parts[-2][1:])
    inv_perm = np.argsort([int(ch) for ch in parts[-1]])
    return inv_perm[inverse_dihedral_transform(grid, trans_id)]


def grid_hash(grid: np.ndarray) -> str:
    digest = hashlib.sha256()
    digest.update(np.asarray(grid.shape, dtype=np.int32).tobytes())
    digest.update(np.ascontiguousarray(grid).tobytes())
    return digest.hexdigest()


def load_predictions(dataset_path: Path, checkpoint_prefix: str) -> tuple[list[str], dict[str, torch.Tensor]]:
    with (dataset_path / "identifiers.json").open("r", encoding="utf-8") as handle:
        identifier_map = json.load(handle)
    shards = sorted(glob.glob(f"{checkpoint_prefix}_all_preds.*"))
    if not shards:
        raise FileNotFoundError(f"no prediction shards match {checkpoint_prefix}_all_preds.*")
    merged: dict[str, list[torch.Tensor]] = {}
    for filename in shards:
        shard = torch.load(filename, map_location="cpu")
        for key, value in shard.items():
            merged.setdefault(key, []).append(value.cpu())
    all_preds = {key: torch.cat(values, dim=0) for key, values in merged.items()}
    mask = all_preds["puzzle_identifiers"] != PAD_PUZZLE_IDENTIFIER
    all_preds = {key: value[mask] for key, value in all_preds.items()}
    return identifier_map, all_preds


def evaluate_arc(dataset_path: Path, checkpoint_prefix: str, ks: list[int]) -> dict[str, Any]:
    identifier_map, preds = load_predictions(dataset_path, checkpoint_prefix)
    required = {"puzzle_identifiers", "inputs", "labels", "logits", "q_halt_logits"}
    missing = sorted(required - preds.keys())
    if missing:
        raise KeyError(f"prediction shards missing keys: {missing}")

    global_grids: dict[str, np.ndarray] = {}
    puzzle_labels: dict[str, dict[str, str]] = {}
    for identifier, input_seq, label_seq in zip(preds["puzzle_identifiers"], preds["inputs"], preds["labels"]):
        name = identifier_map[int(identifier)]
        if "_" in name:
            continue
        input_grid = crop_arc_sequence(input_seq.numpy())
        label_grid = crop_arc_sequence(label_seq.numpy())
        ih = grid_hash(input_grid)
        lh = grid_hash(label_grid)
        global_grids[ih] = input_grid
        global_grids[lh] = label_grid
        puzzle_labels.setdefault(name, {})[ih] = lh

    argmax_preds = preds["logits"].argmax(-1)
    pred_answers: dict[str, dict[str, list[tuple[str, float]]]] = {}
    for identifier, input_seq, pred_seq, q in zip(
        preds["puzzle_identifiers"], preds["inputs"], argmax_preds, preds["q_halt_logits"].sigmoid()
    ):
        name = identifier_map[int(identifier)]
        original_name = name.split("_")[0]
        input_hash = grid_hash(inverse_aug(name, crop_arc_sequence(input_seq.numpy())))
        pred_grid = inverse_aug(name, crop_arc_sequence(pred_seq.numpy()))
        pred_hash = grid_hash(pred_grid)
        global_grids[pred_hash] = pred_grid
        pred_answers.setdefault(original_name, {}).setdefault(input_hash, []).append((pred_hash, float(q)))

    correct_by_k = {k: 0 for k in ks}
    for name, tests in puzzle_labels.items():
        per_test = {k: 0 for k in ks}
        for input_hash, label_hash in tests.items():
            vote_map: dict[str, list[float]] = {}
            for pred_hash, q_value in pred_answers.get(name, {}).get(input_hash, []):
                stats = vote_map.setdefault(pred_hash, [0.0, 0.0])
                stats[0] += 1
                stats[1] += q_value
            ranked = sorted(vote_map.items(), key=lambda item: (item[1][0], item[1][1] / max(item[1][0], 1)), reverse=True)
            for k in ks:
                per_test[k] += any(pred_hash == label_hash for pred_hash, _ in ranked[:k])
        for k in ks:
            correct_by_k[k] += int(bool(tests) and per_test[k] == len(tests))

    total = len(puzzle_labels)
    return {
        "num_puzzles": total,
        "accuracy_percent": {str(k): (correct_by_k[k] / total * 100.0 if total else 0.0) for k in ks},
        "correct_by_k": {str(k): correct_by_k[k] for k in ks},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Aggregate HRM ARC prediction shards into top-K puzzle accuracy.")
    parser.add_argument("--dataset-path", type=Path, required=True, help="Converted ARC dataset root containing identifiers.json.")
    parser.add_argument("--checkpoint-prefix", required=True, help="Checkpoint path/prefix before `_all_preds.<rank>`.")
    parser.add_argument("--ks", nargs="+", type=int, default=[1, 2, 10, 100, 1000], help="Top-K vote cutoffs.")
    parser.add_argument("--json", action="store_true", help="Print JSON only.")
    args = parser.parse_args()
    try:
        result = evaluate_arc(args.dataset_path, args.checkpoint_prefix, args.ks)
    except Exception as exc:
        if args.json:
            print(json.dumps({"ok": False, "error": str(exc)}, indent=2, sort_keys=True))
        else:
            print(f"ERROR: {exc}")
        return 2
    result["ok"] = True
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"Number of puzzles: {result['num_puzzles']}")
        for k, value in result["accuracy_percent"].items():
            print(f"{k}-shot: {value:.2f}%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
