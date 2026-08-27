#!/usr/bin/env python3
"""List the known `python -m experiments` preset commands safely.

This helper does not import the repository's launcher modules, does not start
Tmux, and does not allocate GPUs. It simply prints the static command strings
that the repository launchers describe.

Example:
    python scripts/list_experiment_commands.py --family pretrained --kind test --ids 0,2
"""
from __future__ import annotations

import argparse
import json
from collections import OrderedDict
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class CommandSpec:
    args: tuple[str, ...]
    kvs: tuple[tuple[str, str], ...]

    def render(self, gpu_id: str | None = None, which_epoch: str | None = None, continue_train: bool = False) -> str:
        parts = ["python"]
        parts.extend(self.args)
        for key, value in self.kvs:
            parts.append(f"--{key}")
            parts.append(str(value))
        if gpu_id is not None:
            parts.insert(0, f"CUDA_VISIBLE_DEVICES={gpu_id}")
        if which_epoch is not None:
            parts.extend(["--epoch", str(which_epoch)])
        if continue_train:
            parts.append("--continue_train")
        return " ".join(parts)


def options(*pairs: tuple[str, str]) -> OrderedDict[str, str]:
    return OrderedDict(pairs)


FAMILIES: dict[str, dict[str, list[CommandSpec]]] = {
    "grumpifycat": {
        "train": [
            CommandSpec(args=("train.py",), kvs=(
                ("gpu_ids", "0"),
                ("dataroot", "./datasets/grumpifycat"),
                ("name", "grumpifycat_CUT"),
                ("CUT_mode", "CUT"),
            )),
            CommandSpec(args=("train.py",), kvs=(
                ("gpu_ids", "0"),
                ("dataroot", "./datasets/grumpifycat"),
                ("name", "grumpifycat_FastCUT"),
                ("CUT_mode", "FastCUT"),
            )),
        ],
        "test": [
            CommandSpec(args=("test.py",), kvs=(
                ("gpu_ids", "0"),
                ("dataroot", "./datasets/grumpifycat"),
                ("name", "grumpifycat_CUT"),
                ("CUT_mode", "CUT"),
                ("phase", "train"),
            )),
            CommandSpec(args=("test.py",), kvs=(
                ("gpu_ids", "0"),
                ("dataroot", "./datasets/grumpifycat"),
                ("name", "grumpifycat_FastCUT"),
                ("CUT_mode", "FastCUT"),
                ("phase", "train"),
            )),
        ],
    },
    "pretrained": {
        "train": [
            CommandSpec(args=("train.py",), kvs=(
                ("gpu_ids", "0"),
                ("dataroot", "datasets/cityscapes/cityscapes_val/"),
                ("direction", "BtoA"),
                ("phase", "val"),
                ("name", "cityscapes_cut_pretrained"),
                ("CUT_mode", "CUT"),
            )),
            CommandSpec(args=("train.py",), kvs=(
                ("gpu_ids", "0"),
                ("dataroot", "./datasets/cityscapes_unaligned/cityscapes/"),
                ("direction", "BtoA"),
                ("name", "cityscapes_fastcut_pretrained"),
                ("CUT_mode", "FastCUT"),
            )),
            CommandSpec(args=("train.py",), kvs=(
                ("gpu_ids", "0"),
                ("dataroot", "./datasets/horse2zebra/"),
                ("name", "horse2zebra_cut_pretrained"),
                ("CUT_mode", "CUT"),
            )),
            CommandSpec(args=("train.py",), kvs=(
                ("gpu_ids", "0"),
                ("dataroot", "./datasets/horse2zebra/"),
                ("name", "horse2zebra_fastcut_pretrained"),
                ("CUT_mode", "FastCUT"),
            )),
            CommandSpec(args=("train.py",), kvs=(
                ("gpu_ids", "0"),
                ("dataroot", "./datasets/afhq/cat2dog/"),
                ("name", "cat2dog_cut_pretrained"),
                ("CUT_mode", "CUT"),
            )),
            CommandSpec(args=("train.py",), kvs=(
                ("gpu_ids", "0"),
                ("dataroot", "./datasets/afhq/cat2dog/"),
                ("name", "cat2dog_fastcut_pretrained"),
                ("CUT_mode", "FastCUT"),
            )),
        ],
        "test": [
            CommandSpec(args=("test.py",), kvs=(
                ("gpu_ids", "0"),
                ("dataroot", "datasets/cityscapes/cityscapes_val/"),
                ("direction", "BtoA"),
                ("phase", "val"),
                ("name", "cityscapes_cut_pretrained"),
                ("CUT_mode", "CUT"),
                ("num_test", "500"),
            )),
            CommandSpec(args=("test.py",), kvs=(
                ("gpu_ids", "0"),
                ("dataroot", "./datasets/cityscapes_unaligned/cityscapes/"),
                ("direction", "BtoA"),
                ("name", "cityscapes_fastcut_pretrained"),
                ("CUT_mode", "FastCUT"),
                ("num_test", "500"),
            )),
            CommandSpec(args=("test.py",), kvs=(
                ("gpu_ids", "0"),
                ("dataroot", "./datasets/horse2zebra/"),
                ("name", "horse2zebra_cut_pretrained"),
                ("CUT_mode", "CUT"),
                ("num_test", "500"),
            )),
            CommandSpec(args=("test.py",), kvs=(
                ("gpu_ids", "0"),
                ("dataroot", "./datasets/horse2zebra/"),
                ("name", "horse2zebra_fastcut_pretrained"),
                ("CUT_mode", "FastCUT"),
                ("num_test", "500"),
            )),
            CommandSpec(args=("test.py",), kvs=(
                ("gpu_ids", "0"),
                ("dataroot", "./datasets/afhq/cat2dog/"),
                ("name", "cat2dog_cut_pretrained"),
                ("CUT_mode", "CUT"),
                ("num_test", "500"),
            )),
            CommandSpec(args=("test.py",), kvs=(
                ("gpu_ids", "0"),
                ("dataroot", "./datasets/afhq/cat2dog/"),
                ("name", "cat2dog_fastcut_pretrained"),
                ("CUT_mode", "FastCUT"),
                ("num_test", "500"),
            )),
        ],
    },
    "singleimage": {
        "train": [
            CommandSpec(args=("train.py",), kvs=(
                ("gpu_ids", "0"),
                ("name", "singleimage_monet_etretat"),
                ("dataroot", "./datasets/single_image_monet_etretat"),
                ("model", "sincut"),
            )),
        ],
        "test": [
            CommandSpec(args=("test.py",), kvs=(
                ("gpu_ids", "0"),
                ("name", "singleimage_monet_etretat"),
                ("dataroot", "./datasets/single_image_monet_etretat"),
                ("model", "sincut"),
            )),
        ],
    },
}


def parse_ids(text: str, count: int) -> list[int]:
    if text == "all":
        return list(range(count))
    ids = []
    for item in text.split(","):
        item = item.strip()
        if not item:
            continue
        ids.append(int(item))
    for idx in ids:
        if idx < 0 or idx >= count:
            raise ValueError(f"id out of range: {idx} not in [0, {count})")
    return ids


def render_rows(family: str, kind: str, ids: Iterable[int], gpu_id: str | None, which_epoch: str | None, continue_train: bool) -> list[dict[str, str]]:
    rows = []
    for idx in ids:
        spec = FAMILIES[family][kind][idx]
        rows.append({
            "family": family,
            "kind": kind,
            "id": str(idx),
            "command": spec.render(gpu_id=gpu_id, which_epoch=which_epoch, continue_train=continue_train),
        })
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Safely list the repository's launcher preset commands.")
    parser.add_argument("--family", required=True, choices=sorted(FAMILIES), help="Launcher family to inspect.")
    parser.add_argument("--kind", default="train", choices=["train", "test", "both"], help="Which command list to print.")
    parser.add_argument("--ids", default="all", help="Comma-separated ids or all.")
    parser.add_argument("--gpu-id", default=None, help="Optional CUDA_VISIBLE_DEVICES prefix to show with the command.")
    parser.add_argument("--which-epoch", default=None, help="Append a native launcher-style --epoch value.")
    parser.add_argument("--continue-train", action="store_true", help="Append --continue_train to the rendered command.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of plain text.")
    args = parser.parse_args(argv)

    selected_kinds = [args.kind] if args.kind != "both" else ["train", "test"]
    payload = []
    for kind in selected_kinds:
        specs = FAMILIES[args.family][kind]
        ids = parse_ids(args.ids, len(specs))
        payload.extend(render_rows(args.family, kind, ids, args.gpu_id, args.which_epoch, args.continue_train))

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        for row in payload:
            print(f"[{row['family']}:{row['kind']}:{row['id']}] {row['command']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
