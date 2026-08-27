#!/usr/bin/env python3
"""Safely report or prune low-shot identity folders for face.evoLVe.

The original face.evoLVe low-shot helper removed folders in place. This bundled
version is dry-run by default and can write a pruned copy with --copy-to.
Classes with fewer than --min-num valid image files are considered low-shot.
"""

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".webp",
    ".gif",
    ".tif",
    ".tiff",
}


def is_hidden(path):
    return path.name.startswith(".")


def is_image_file(path):
    return path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS


def rel(path, root):
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def immediate_class_dirs(root):
    return sorted(
        [p for p in root.iterdir() if p.is_dir() and not is_hidden(p)],
        key=lambda p: p.name,
    )


def scan_hidden_entries(root):
    hidden = []
    for current, dirnames, filenames in os.walk(root):
        current_path = Path(current)
        for name in dirnames:
            candidate = current_path / name
            if is_hidden(candidate):
                hidden.append(candidate)
        for name in filenames:
            candidate = current_path / name
            if is_hidden(candidate):
                hidden.append(candidate)
    return sorted(hidden, key=lambda p: str(p))


def remove_hidden_entries(hidden_paths):
    removed = []
    for path in sorted(hidden_paths, key=lambda p: len(p.parts), reverse=True):
        if not path.exists():
            continue
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()
        removed.append(path)
    return removed


def scan_classes(root, min_num):
    classes = []
    lowshot = []
    for class_dir in immediate_class_dirs(root):
        image_files = sorted(
            [p for p in class_dir.iterdir() if is_image_file(p)],
            key=lambda p: p.name,
        )
        other_files = sorted(
            [p for p in class_dir.iterdir() if p.is_file() and not is_hidden(p) and not is_image_file(p)],
            key=lambda p: p.name,
        )
        nested_dirs = sorted(
            [p for p in class_dir.iterdir() if p.is_dir() and not is_hidden(p)],
            key=lambda p: p.name,
        )
        record = {
            "class_name": class_dir.name,
            "image_count": len(image_files),
            "other_file_count": len(other_files),
            "nested_dir_count": len(nested_dirs),
            "remove": len(image_files) < min_num,
        }
        classes.append(record)
        if record["remove"]:
            lowshot.append(class_dir)
    return classes, lowshot


def maybe_copy_root(source_root, copy_to, apply):
    if copy_to is None:
        return source_root, None
    copy_to = Path(copy_to).expanduser().resolve()
    if copy_to == source_root:
        raise ValueError("--copy-to must be different from --root")
    if not apply:
        return source_root, copy_to
    if copy_to.exists():
        raise ValueError("--copy-to destination already exists; choose a new path")
    shutil.copytree(source_root, copy_to)
    return copy_to, copy_to


def build_summary(args, source_root, target_root, planned_copy_to, hidden_before, hidden_removed, class_records, removed_classes):
    total_images = sum(item["image_count"] for item in class_records)
    kept_records = [item for item in class_records if not item["remove"]]
    lowshot_records = [item for item in class_records if item["remove"]]
    return {
        "source_root": str(source_root),
        "target_root": str(target_root),
        "copy_to": str(planned_copy_to) if planned_copy_to is not None else None,
        "applied": bool(args.apply),
        "mode": "copy-apply" if args.apply and planned_copy_to else ("in-place-apply" if args.apply else "dry-run"),
        "min_num": args.min_num,
        "threshold_rule": "remove classes with image_count < min_num",
        "image_extensions": sorted(IMAGE_EXTENSIONS),
        "class_count_before_prune": len(class_records),
        "image_count_before_prune": total_images,
        "kept_class_count": len(kept_records),
        "lowshot_class_count": len(lowshot_records),
        "hidden_entry_count": len(hidden_before),
        "hidden_removed_count": len(hidden_removed),
        "hidden_entries": [rel(p, target_root) for p in hidden_before],
        "removed_classes": [p.name for p in removed_classes],
        "class_records": class_records,
    }


def print_text(summary):
    print("face.evoLVe low-shot pruning summary")
    print("- mode: {}".format(summary["mode"]))
    print("- source_root: {}".format(summary["source_root"]))
    print("- target_root: {}".format(summary["target_root"]))
    if summary["copy_to"]:
        print("- copy_to: {}".format(summary["copy_to"]))
    print("- min_num: {} ({})".format(summary["min_num"], summary["threshold_rule"]))
    print("- classes before prune: {}".format(summary["class_count_before_prune"]))
    print("- valid images before prune: {}".format(summary["image_count_before_prune"]))
    print("- low-shot classes: {}".format(summary["lowshot_class_count"]))
    print("- kept classes: {}".format(summary["kept_class_count"]))
    print("- hidden entries found: {}".format(summary["hidden_entry_count"]))
    if summary["applied"]:
        print("- hidden entries removed: {}".format(summary["hidden_removed_count"]))
    else:
        print("- dry-run: no files were copied, removed, or modified")
    if summary["removed_classes"]:
        action = "removed" if summary["applied"] else "would remove"
        print("- {} classes:".format(action))
        for class_name in summary["removed_classes"]:
            print("  - {}".format(class_name))
    if summary["hidden_entries"]:
        action = "removed" if summary["applied"] else "would remove hidden entry"
        print("- hidden entries {}:".format(action))
        for path in summary["hidden_entries"]:
            print("  - {}".format(path))


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Dry-run or safely prune low-shot face.evoLVe identity folders.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python remove_lowshot_safe.py --root data/train --min-num 10\n"
            "  python remove_lowshot_safe.py --root data/train --min-num 10 --copy-to data/train_pruned --apply\n"
            "  python remove_lowshot_safe.py --root data/train --min-num 2 --json"
        ),
    )
    parser.add_argument("--root", required=True, help="Identity-folder root to inspect.")
    parser.add_argument(
        "--min-num",
        type=int,
        default=10,
        help="Remove classes with fewer than this many valid image files (default: 10).",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually remove hidden entries and low-shot classes. Without this flag the command is a dry-run.",
    )
    parser.add_argument(
        "--copy-to",
        help="Optional destination for a pruned copy. Only created when --apply is supplied.",
    )
    parser.add_argument("--json", action="store_true", help="Print the summary as JSON.")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv or sys.argv[1:])
    if args.min_num < 0:
        print("error: --min-num must be non-negative", file=sys.stderr)
        return 2

    source_root = Path(args.root).expanduser().resolve()
    if not source_root.exists() or not source_root.is_dir():
        print("error: --root must be an existing directory", file=sys.stderr)
        return 2

    try:
        target_root, planned_copy_to = maybe_copy_root(source_root, args.copy_to, args.apply)
    except (OSError, ValueError) as exc:
        print("error: {}".format(exc), file=sys.stderr)
        return 2

    hidden_before = scan_hidden_entries(target_root)
    hidden_removed = []
    if args.apply:
        hidden_removed = remove_hidden_entries(hidden_before)

    class_records, lowshot_dirs = scan_classes(target_root, args.min_num)
    removed_classes = []
    if args.apply:
        for class_dir in lowshot_dirs:
            if class_dir.exists():
                shutil.rmtree(class_dir)
                removed_classes.append(class_dir)
    else:
        removed_classes = lowshot_dirs

    summary = build_summary(
        args=args,
        source_root=source_root,
        target_root=target_root,
        planned_copy_to=planned_copy_to,
        hidden_before=hidden_before,
        hidden_removed=hidden_removed,
        class_records=class_records,
        removed_classes=removed_classes,
    )
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print_text(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
