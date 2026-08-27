#!/usr/bin/env python3
"""Lightweight import and catalog smoke check for PaddleCV."""
from __future__ import annotations

import importlib.metadata as md

import paddlecv
from ppcv.model_zoo.model_zoo import TASK_DICT, list_model


DISTROS = [
    "paddlecv",
    "numpy",
    "opencv-python",
    "opencv-contrib-python",
    "paddlenlp",
    "paddlespeech",
    "aistudio-sdk",
    "setuptools",
]


def dist_version(name: str) -> str:
    try:
        return md.version(name)
    except md.PackageNotFoundError:
        return "not-installed"


def main() -> int:
    print("PaddleCV import ok:", paddlecv.__version__)
    for name in DISTROS:
        print(f"{name}: {dist_version(name)}")
    print(f"task_count: {len(TASK_DICT)}")
    print(f"task_sample: {list(TASK_DICT)[:5]}")
    print("supported tasks:")
    paddlecv.PaddleCV.list_all_supported_tasks()
    print("filtered model catalog:")
    list_model(["PP-LCNet"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
