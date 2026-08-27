#!/usr/bin/env python3
"""Validate DALLE-pytorch image-text folder pairing rules."""
import argparse
import json
from pathlib import Path

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".bmp"}


def scan(root: Path):
    images = {}
    texts = {}
    unsupported = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        suffix = path.suffix.lower()
        if suffix in IMAGE_EXTS:
            images.setdefault(path.stem, []).append(str(path.relative_to(root)))
        elif suffix == ".txt":
            texts.setdefault(path.stem, []).append(str(path.relative_to(root)))
        elif suffix:
            unsupported.append(str(path.relative_to(root)))
    paired = sorted(set(images) & set(texts))
    missing_text = sorted(set(images) - set(texts))
    missing_image = sorted(set(texts) - set(images))
    empty_texts = []
    multi_image_stems = {k: v for k, v in images.items() if len(v) > 1}
    multi_text_stems = {k: v for k, v in texts.items() if len(v) > 1}
    for stem, rels in texts.items():
        for rel in rels:
            lines = [ln.strip() for ln in (root / rel).read_text(errors="replace").splitlines() if ln.strip()]
            if not lines:
                empty_texts.append(rel)
    return {
        "root": str(root),
        "image_count": sum(len(v) for v in images.values()),
        "text_count": sum(len(v) for v in texts.values()),
        "paired_stem_count": len(paired),
        "paired_stems_sample": paired[:20],
        "missing_text_stems": missing_text[:100],
        "missing_image_stems": missing_image[:100],
        "empty_text_files": empty_texts[:100],
        "duplicate_image_stems": multi_image_stems,
        "duplicate_text_stems": multi_text_stems,
        "unsupported_files_sample": unsupported[:50],
    }


def main():
    p = argparse.ArgumentParser(description="Validate image/text stem pairing for DALLE-pytorch training.")
    p.add_argument("folder", type=Path)
    p.add_argument("--strict", action="store_true", help="Exit non-zero on missing/empty/duplicate issues.")
    p.add_argument("--json", action="store_true")
    args = p.parse_args()
    if not args.folder.exists() or not args.folder.is_dir():
        raise SystemExit(f"not a directory: {args.folder}")
    report = scan(args.folder)
    issues = []
    for key in ("missing_text_stems", "missing_image_stems", "empty_text_files", "duplicate_image_stems", "duplicate_text_stems"):
        if report[key]:
            issues.append(key)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"images={report['image_count']} texts={report['text_count']} paired_stems={report['paired_stem_count']}")
        for key in issues:
            print(f"{key}: {report[key]}")
        if report["unsupported_files_sample"]:
            print(f"unsupported sample: {report['unsupported_files_sample']}")
        print("OK" if not issues else "ISSUES FOUND")
    return 1 if args.strict and issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
