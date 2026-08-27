#!/usr/bin/env python3
"""Validate a face.evoLVe ImageFolder-style identity root.

The script checks immediate identity folders, valid image extensions, hidden
files, non-image files, nested folders, empty classes, and a configurable
minimum sample count. It exits nonzero when required checks fail.
"""

import argparse
import json
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


def scan_root(root, min_num):
    root_hidden = []
    root_files = []
    class_dirs = []
    issues = []

    for entry in sorted(root.iterdir(), key=lambda p: p.name):
        if is_hidden(entry):
            root_hidden.append(entry)
        elif entry.is_dir():
            class_dirs.append(entry)
        elif entry.is_file():
            root_files.append(entry)
        else:
            issues.append({"level": "root", "path": rel(entry, root), "issue": "unsupported_root_entry"})

    if root_hidden:
        issues.append({
            "level": "root",
            "path": ".",
            "issue": "hidden_entries_at_root",
            "count": len(root_hidden),
        })
    if root_files:
        issues.append({
            "level": "root",
            "path": ".",
            "issue": "files_at_root_not_classes",
            "count": len(root_files),
        })
    if not class_dirs:
        issues.append({"level": "root", "path": ".", "issue": "no_class_directories"})

    class_records = []
    for class_dir in class_dirs:
        hidden_entries = []
        image_files = []
        other_files = []
        nested_dirs = []
        for entry in sorted(class_dir.iterdir(), key=lambda p: p.name):
            if is_hidden(entry):
                hidden_entries.append(entry)
            elif is_image_file(entry):
                image_files.append(entry)
            elif entry.is_file():
                other_files.append(entry)
            elif entry.is_dir():
                nested_dirs.append(entry)
            else:
                other_files.append(entry)

        record = {
            "class_name": class_dir.name,
            "image_count": len(image_files),
            "hidden_count": len(hidden_entries),
            "non_image_file_count": len(other_files),
            "nested_dir_count": len(nested_dirs),
            "hidden_entries": [rel(p, root) for p in hidden_entries],
            "non_image_files": [rel(p, root) for p in other_files],
            "nested_dirs": [rel(p, root) for p in nested_dirs],
            "failures": [],
        }
        if len(image_files) == 0:
            record["failures"].append("empty_class")
        if min_num > 0 and len(image_files) < min_num:
            record["failures"].append("below_min_num")
        if hidden_entries:
            record["failures"].append("hidden_entries")
        if other_files:
            record["failures"].append("non_image_files")
        if nested_dirs:
            record["failures"].append("nested_dirs")
        class_records.append(record)

    for record in class_records:
        for failure in record["failures"]:
            issues.append({
                "level": "class",
                "class_name": record["class_name"],
                "issue": failure,
            })

    total_images = sum(item["image_count"] for item in class_records)
    summary = {
        "ok": len(issues) == 0,
        "root": str(root),
        "min_num": min_num,
        "image_extensions": sorted(IMAGE_EXTENSIONS),
        "class_count": len(class_records),
        "total_valid_images": total_images,
        "root_hidden_entries": [rel(p, root) for p in root_hidden],
        "root_files": [rel(p, root) for p in root_files],
        "class_records": class_records,
        "issues": issues,
    }
    return summary


def print_text(summary):
    status = "OK" if summary["ok"] else "FAIL"
    print("face.evoLVe ImageFolder check: {}".format(status))
    print("- root: {}".format(summary["root"]))
    print("- min_num: {}".format(summary["min_num"]))
    print("- class_count: {}".format(summary["class_count"]))
    print("- total_valid_images: {}".format(summary["total_valid_images"]))
    if summary["root_hidden_entries"]:
        print("- hidden entries at root:")
        for path in summary["root_hidden_entries"]:
            print("  - {}".format(path))
    if summary["root_files"]:
        print("- root files that are not class directories:")
        for path in summary["root_files"]:
            print("  - {}".format(path))
    print("- classes:")
    for record in summary["class_records"]:
        status = ",".join(record["failures"]) if record["failures"] else "ok"
        print(
            "  - {class_name}: images={image_count}, hidden={hidden_count}, "
            "non_images={non_image_file_count}, nested_dirs={nested_dir_count}, status={status}".format(
                status=status,
                **record
            )
        )
    if summary["issues"]:
        print("- issues:")
        for issue in summary["issues"]:
            if issue.get("class_name"):
                print("  - {class_name}: {issue}".format(**issue))
            else:
                print("  - {path}: {issue}".format(**issue))


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Validate face.evoLVe ImageFolder-style identity folders.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python check_image_folder.py --root data/train\n"
            "  python check_image_folder.py --root data/train --min-num 10\n"
            "  python check_image_folder.py --root data/train --min-num 2 --json"
        ),
    )
    parser.add_argument("--root", required=True, help="Identity-folder root to validate.")
    parser.add_argument(
        "--min-num",
        type=int,
        default=1,
        help="Required minimum valid image files per class; 1 only rejects empty classes (default: 1).",
    )
    parser.add_argument("--json", action="store_true", help="Print JSON instead of text.")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv or sys.argv[1:])
    if args.min_num < 0:
        print("error: --min-num must be non-negative", file=sys.stderr)
        return 2
    root = Path(args.root).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        print("error: --root must be an existing directory", file=sys.stderr)
        return 2
    summary = scan_root(root, args.min_num)
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print_text(summary)
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
