#!/usr/bin/env python3
"""Read-only KAIR dataset layout checker.

The checker inspects common KAIR image, video, meta-info, and LMDB layouts. It
never imports KAIR and never writes data.
"""
from __future__ import annotations

import argparse
import re
from collections import Counter
from pathlib import Path
from typing import Iterable, List, Tuple

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".webp"}


def image_files(root: Path, recursive: bool = False) -> List[Path]:
    pattern = "**/*" if recursive else "*"
    return sorted(p for p in root.glob(pattern) if p.is_file() and p.suffix.lower() in IMAGE_EXTS and not p.name.startswith("."))


def strip_scale_stem(stem: str) -> str:
    return re.sub(r"x[2348]$", "", stem, flags=re.IGNORECASE)


def check_exists(path: Path, kind: str) -> bool:
    if not path.exists():
        print(f"ERROR: {kind} does not exist: {path}")
        return False
    return True


def cmd_image(args: argparse.Namespace) -> int:
    root = args.root
    if not check_exists(root, "image root"):
        return 1
    files = image_files(root, recursive=args.recursive)
    print(f"Image root: {root}")
    print(f"Image files: {len(files)}")
    if files:
        print("First files:")
        for path in files[: args.preview]:
            print(f"  {path.relative_to(root) if path.is_relative_to(root) else path}")
        suffixes = Counter(p.suffix.lower() for p in files)
        print("Extensions: " + ", ".join(f"{k}:{v}" for k, v in sorted(suffixes.items())))
    else:
        print("ERROR: no image files found")
        return 1

    if args.paired_root:
        paired = args.paired_root
        if not check_exists(paired, "paired image root"):
            return 1
        pfiles = image_files(paired, recursive=args.recursive)
        print(f"Paired image files: {len(pfiles)}")
        if args.pair_strategy == "exact":
            left = {p.relative_to(root).with_suffix("").as_posix() for p in files}
            right = {p.relative_to(paired).with_suffix("").as_posix() for p in pfiles}
        elif args.pair_strategy == "stem-loose":
            left = {strip_scale_stem(p.stem) for p in files}
            right = {strip_scale_stem(p.stem) for p in pfiles}
        else:
            left = {p.stem for p in files}
            right = {p.stem for p in pfiles}
        missing_right = sorted(left - right)[: args.preview]
        missing_left = sorted(right - left)[: args.preview]
        if missing_right or missing_left:
            print("WARN: image pairs do not fully align under selected strategy")
            if missing_right:
                print("  present in root but missing in paired root: " + ", ".join(missing_right))
            if missing_left:
                print("  present in paired root but missing in root: " + ", ".join(missing_left))
            return 1 if args.strict else 0
        print("Pair check: OK")
    return 0


def clip_dirs(root: Path) -> List[Path]:
    return sorted(p for p in root.iterdir() if p.is_dir() and not p.name.startswith("."))


def cmd_video(args: argparse.Namespace) -> int:
    root = args.root
    if not check_exists(root, "video root"):
        return 1
    print(f"Video root: {root}")
    if args.layout == "vimeo":
        sequences = sorted(p for p in root.glob("*/*") if p.is_dir())
        print(f"Vimeo-style sequences: {len(sequences)}")
        bad = []
        for seq in sequences[: max(len(sequences), 0)]:
            names = {p.name for p in image_files(seq)}
            missing = [f"im{i}.png" for i in range(1, 8) if f"im{i}.png" not in names]
            if missing:
                bad.append((seq.relative_to(root).as_posix(), missing))
                if len(bad) >= args.preview:
                    break
        if bad:
            print("WARN: some Vimeo sequences do not contain im1.png..im7.png")
            for seq, missing in bad:
                print(f"  {seq}: missing {', '.join(missing)}")
            return 1 if args.strict else 0
        if not sequences:
            print("ERROR: no Vimeo two-level sequence folders found")
            return 1
        print("Vimeo sequence check: OK")
        return 0

    clips = clip_dirs(root)
    print(f"Clip folders: {len(clips)}")
    if not clips:
        print("ERROR: no immediate clip folders found; KAIR video datasets usually expect root/clip/frame.ext")
        return 1
    frame_counts = {}
    for clip in clips:
        frame_counts[clip.name] = len(image_files(clip, recursive=False))
    for name, count in list(frame_counts.items())[: args.preview]:
        print(f"  {name}: {count} frame(s)")
    too_small = {k: v for k, v in frame_counts.items() if v < args.min_frames}
    if too_small:
        print(f"WARN: {len(too_small)} clip(s) have fewer than {args.min_frames} frames")
        if args.strict:
            return 1
    if args.paired_root:
        paired = args.paired_root
        if not check_exists(paired, "paired video root"):
            return 1
        paired_clips = clip_dirs(paired)
        pcounts = {clip.name: len(image_files(clip, recursive=False)) for clip in paired_clips}
        missing_gt = sorted(set(frame_counts) - set(pcounts))
        missing_lq = sorted(set(pcounts) - set(frame_counts))
        mismatched = sorted(k for k in set(frame_counts) & set(pcounts) if frame_counts[k] != pcounts[k])
        if missing_gt or missing_lq or mismatched:
            print("WARN: paired video roots do not align")
            if missing_gt:
                print("  clips in root missing from paired root: " + ", ".join(missing_gt[: args.preview]))
            if missing_lq:
                print("  clips in paired root missing from root: " + ", ".join(missing_lq[: args.preview]))
            if mismatched:
                print("  frame-count mismatches: " + ", ".join(f"{k}({frame_counts[k]} vs {pcounts[k]})" for k in mismatched[: args.preview]))
            return 1 if args.strict else 0
        print("Paired video check: OK")
    return 0


def cmd_meta(args: argparse.Namespace) -> int:
    path = args.meta_info
    if not check_exists(path, "meta-info file"):
        return 1
    lines = [line.strip() for line in path.read_text(encoding="utf-8", errors="replace").splitlines() if line.strip()]
    print(f"Meta-info: {path}")
    print(f"Records: {len(lines)}")
    bad = []
    first_tokens = []
    for idx, line in enumerate(lines, start=1):
        parts = line.split()
        first_tokens.append(parts[0] if parts else "")
        ok = len(parts) in {3, 4} and re.match(r"^\([^)]*\)$", parts[2] if len(parts) >= 3 else "")
        if not ok:
            bad.append((idx, line))
            if len(bad) >= args.preview:
                break
    if lines:
        print("First records:")
        for line in lines[: args.preview]:
            print(f"  {line}")
    if bad:
        print("WARN: records with unexpected format:")
        for idx, line in bad:
            print(f"  line {idx}: {line}")
        if args.strict:
            return 1
    if args.root:
        root = args.root
        if not check_exists(root, "root for first-token check"):
            return 1
        missing = [tok for tok in first_tokens if not (root / tok).exists()]
        if missing:
            print("WARN: first meta-info tokens missing as folders/keys under root sample: " + ", ".join(missing[: args.preview]))
            if args.strict:
                return 1
    return 0


def cmd_lmdb(args: argparse.Namespace) -> int:
    root = args.root
    if not check_exists(root, "LMDB root"):
        return 1
    print(f"LMDB root: {root}")
    expected = [root / "data.mdb", root / "lock.mdb", root / "meta_info.txt"]
    missing = [p.name for p in expected if not p.exists()]
    if missing:
        print("ERROR: missing LMDB files: " + ", ".join(missing))
        return 1
    meta = root / "meta_info.txt"
    lines = [line.strip() for line in meta.read_text(encoding="utf-8", errors="replace").splitlines() if line.strip()]
    print(f"meta_info.txt records: {len(lines)}")
    for line in lines[: args.preview]:
        print(f"  {line}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only KAIR dataset layout checker.")
    parser.add_argument("--preview", type=int, default=5, help="Number of sample paths/records to print.")
    parser.add_argument("--strict", action="store_true", help="Return nonzero on warnings, not only errors.")
    sub = parser.add_subparsers(dest="mode", required=True)

    p = sub.add_parser("image", help="Check an image folder and optional paired folder.")
    p.add_argument("--root", required=True, type=Path)
    p.add_argument("--paired-root", type=Path)
    p.add_argument("--recursive", action="store_true")
    p.add_argument("--pair-strategy", choices=["exact", "stem", "stem-loose"], default="stem")
    p.set_defaults(func=cmd_image)

    p = sub.add_parser("video", help="Check clip-folder or Vimeo-style video data.")
    p.add_argument("--root", required=True, type=Path)
    p.add_argument("--paired-root", type=Path)
    p.add_argument("--layout", choices=["clips", "vimeo"], default="clips")
    p.add_argument("--min-frames", type=int, default=1)
    p.set_defaults(func=cmd_video)

    p = sub.add_parser("meta", help="Check KAIR video meta-info text file format.")
    p.add_argument("--meta-info", required=True, type=Path)
    p.add_argument("--root", type=Path, help="Optional folder root for first-token existence checks.")
    p.set_defaults(func=cmd_meta)

    p = sub.add_parser("lmdb", help="Check KAIR LMDB directory files and meta_info.txt sample.")
    p.add_argument("--root", required=True, type=Path)
    p.set_defaults(func=cmd_lmdb)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
