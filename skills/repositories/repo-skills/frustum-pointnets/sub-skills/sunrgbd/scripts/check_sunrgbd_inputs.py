#!/usr/bin/env python3
"""Read-only preflight for externally prepared SUN RGB-D assets."""
import argparse
from pathlib import Path
import sys


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--data-root", type=Path, help="reorganized SUN RGB-D root")
    p.add_argument("--train-list", type=Path)
    p.add_argument("--val-list", type=Path)
    p.add_argument("--train-pickle", type=Path)
    p.add_argument("--val-pickle", type=Path)
    p.add_argument("--detector-pickle", type=Path)
    p.add_argument("--result-pickle", type=Path)
    a = p.parse_args()
    errors = []
    if a.data_root is not None:
        training = a.data_root / "training"
        if not training.is_dir():
            errors.append("missing reorganized training directory: %s" % training)
    for label, path in (("train list", a.train_list), ("val list", a.val_list),
                        ("train pickle", a.train_pickle), ("val pickle", a.val_pickle),
                        ("detector pickle", a.detector_pickle), ("result pickle", a.result_pickle)):
        if path is not None and not path.is_file():
            errors.append("missing %s: %s" % (label, path))
    if a.train_list and a.train_list.is_file() and not a.train_list.read_text().strip():
        errors.append("train list is empty")
    if a.val_list and a.val_list.is_file() and not a.val_list.read_text().strip():
        errors.append("val list is empty")
    supplied = [a.data_root, a.train_list, a.val_list, a.train_pickle,
                a.val_pickle, a.detector_pickle, a.result_pickle]
    if not any(item is not None for item in supplied):
        errors.append("supply at least one asset to check")
    if errors:
        for error in errors:
            print("ERROR:", error, file=sys.stderr)
        return 1
    print("SUN RGB-D input paths OK (presence-only preflight)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
