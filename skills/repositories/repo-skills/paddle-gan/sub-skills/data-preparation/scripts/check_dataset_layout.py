#!/usr/bin/env python3
"""Check common PaddleGAN dataset layouts without downloading or training."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:  # pragma: no cover - Pillow is expected in the runtime
    Image = None

IMAGE_SUFFIXES = {
    ".bmp",
    ".gif",
    ".jpeg",
    ".jpg",
    ".png",
    ".tif",
    ".tiff",
    ".webp",
}


def is_image(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES


def list_images(root: Path, recursive: bool = True) -> list[Path]:
    if not root.exists():
        return []
    iterator = root.rglob("*") if recursive else root.iterdir()
    return sorted(path for path in iterator if is_image(path))


def read_image_meta(path: Path):
    if Image is None:
        return None
    try:
        with Image.open(path) as img:
            return img.width, img.height, img.mode
    except Exception as exc:  # pragma: no cover - depends on local image data
        return exc


def describe_image(path: Path) -> str:
    meta = read_image_meta(path)
    if meta is None:
        return path.name
    if isinstance(meta, Exception):
        return f"{path.name} [unreadable: {meta}]"
    width, height, mode = meta
    return f"{path.name} [{width}x{height} {mode}]"


def take(items, limit):
    limit = max(0, int(limit))
    return items[:limit]


def folder_summary(root: Path,
                   label: str,
                   *,
                   recursive: bool = True,
                   sample: int = 3,
                   required: bool = True):
    details: list[str] = []
    issues: list[str] = []
    if not root.is_dir():
        if required:
            issues.append(f"missing {label}: {root}")
        else:
            details.append(f"{label}: absent")
        return details, issues, []

    images = list_images(root, recursive=recursive)
    if not images:
        issues.append(f"no images found under {label}: {root}")
        return details, issues, images

    details.append(f"{label}: {len(images)} images")
    for path in take(images, sample):
        details.append(f"  - {describe_image(path)}")
    return details, issues, images


def report(title: str, details: list[str], issues: list[str]) -> int:
    status = "OK" if not issues else "FAIL"
    print(f"[{status}] {title}")
    for line in details:
        print(f"  {line}")
    for line in issues:
        print(f"  ! {line}")
    return 0 if not issues else 1


def check_cyclegan(args) -> int:
    root = Path(args.root)
    details: list[str] = []
    issues: list[str] = []

    for split in ("trainA", "trainB"):
        split_details, split_issues, _ = folder_summary(
            root / split,
            split,
            recursive=True,
            sample=args.sample,
            required=True,
        )
        details.extend(split_details)
        issues.extend(split_issues)

    test_a = root / "testA"
    test_b = root / "testB"
    test_a_exists = test_a.is_dir()
    test_b_exists = test_b.is_dir()
    if test_a_exists or test_b_exists or args.require_test:
        if not (test_a_exists and test_b_exists):
            issues.append(
                "CycleGAN evaluation expects both testA and testB when test data is present"
            )
        else:
            for split in ("testA", "testB"):
                split_details, split_issues, _ = folder_summary(
                    root / split,
                    split,
                    recursive=True,
                    sample=args.sample,
                    required=True,
                )
                details.extend(split_details)
                issues.extend(split_issues)
    else:
        details.append("testA/testB: absent (training-only layout)")

    return report("CycleGAN layout", details, issues)


def check_pix2pix(args) -> int:
    root = Path(args.root)
    details: list[str] = []
    issues: list[str] = []
    eval_found = False

    train_details, train_issues, train_images = folder_summary(
        root / "train",
        "train",
        recursive=True,
        sample=args.sample,
        required=True,
    )
    details.extend(train_details)
    issues.extend(train_issues)
    for path in take(train_images, args.sample):
        meta = read_image_meta(path)
        if isinstance(meta, tuple) and meta[0] % 2 != 0:
            issues.append(
                f"{path} has odd width {meta[0]}; Pix2Pix paired images should split evenly left/right"
            )

    for split in ("val", "test"):
        split_root = root / split
        if split_root.is_dir():
            eval_found = True
            split_details, split_issues, split_images = folder_summary(
                split_root,
                split,
                recursive=True,
                sample=args.sample,
                required=True,
            )
            details.extend(split_details)
            issues.extend(split_issues)
            for path in take(split_images, args.sample):
                meta = read_image_meta(path)
                if isinstance(meta, tuple) and meta[0] % 2 != 0:
                    issues.append(
                        f"{path} has odd width {meta[0]}; Pix2Pix paired images should split evenly left/right"
                    )
        else:
            details.append(f"{split}: absent")

    if args.require_eval and not eval_found:
        issues.append("Pix2Pix evaluation expects either val/ or test/ to exist")

    return report("Pix2Pix layout", details, issues)


def check_div2k(args) -> int:
    root = Path(args.root)
    scales = args.scales
    details: list[str] = []
    issues: list[str] = []

    raw_dirs: list[tuple[str, Path]] = [("DIV2K_train_HR", root / "DIV2K_train_HR")]
    raw_dirs.extend(
        (f"DIV2K_train_LR_bicubic/X{scale}", root / "DIV2K_train_LR_bicubic" /
         f"X{scale}") for scale in scales)

    raw_counts: list[int] = []
    for label, folder in raw_dirs:
        folder_details, folder_issues, images = folder_summary(
            folder,
            label,
            recursive=False,
            sample=args.sample,
            required=True,
        )
        details.extend(folder_details)
        issues.extend(folder_issues)
        if images:
            raw_counts.append(len(images))

    if raw_counts and len(set(raw_counts)) != 1:
        issues.append(
            f"raw DIV2K folders have different image counts: {raw_counts}"
        )

    processed_dirs: list[tuple[str, Path]] = [("DIV2K_train_HR_sub",
                                               root / "DIV2K_train_HR_sub")]
    processed_dirs.extend(
        (f"DIV2K_train_LR_bicubic/X{scale}_sub",
         root / "DIV2K_train_LR_bicubic" / f"X{scale}_sub")
        for scale in scales)

    processed_present = any(folder.exists() for _, folder in processed_dirs)
    if processed_present or args.require_processed:
        missing = [label for label, folder in processed_dirs if not folder.is_dir()]
        if missing:
            issues.append(
                f"missing processed DIV2K folders: {', '.join(missing)}")
        else:
            name_lists: list[list[str]] = []
            counts: list[int] = []
            for label, folder in processed_dirs:
                folder_details, folder_issues, images = folder_summary(
                    folder,
                    label,
                    recursive=False,
                    sample=args.sample,
                    required=True,
                )
                details.extend(folder_details)
                issues.extend(folder_issues)
                counts.append(len(images))
                name_lists.append([path.name for path in images])
            if counts and len(set(counts)) != 1:
                issues.append(
                    f"processed DIV2K folders have different patch counts: {counts}"
                )
            if name_lists and any(names != name_lists[0] for names in name_lists[1:]):
                issues.append(
                    "processed DIV2K patch filenames differ across HR_sub and X*_sub folders"
                )
    else:
        details.append(
            "processed DIV2K outputs: absent (set --require-processed to enforce them)"
        )

    return report("DIV2K layout", details, issues)


def parse_reds_key(raw: str) -> tuple[str, str]:
    token = raw.split()[0].strip()
    token = token.split(".")[0]
    if "/" not in token:
        raise ValueError(f"invalid REDS key: {raw}")
    clip, frame = token.split("/", 1)
    return clip, frame


def check_reds(args) -> int:
    lq_root = Path(args.lq_root)
    gt_root = Path(args.gt_root)
    ann_file = Path(args.ann_file)
    details: list[str] = []
    issues: list[str] = []

    for label, folder in (("lq-root", lq_root), ("gt-root", gt_root)):
        if not folder.is_dir():
            issues.append(f"missing {label}: {folder}")

    if not ann_file.is_file():
        issues.append(f"missing ann-file: {ann_file}")
        return report("REDS layout", details, issues)

    if args.num_frames is not None and args.num_frames % 2 == 0:
        issues.append("REDS num_frames should be odd")

    if args.partition == "REDS4":
        val_partition = {"000", "011", "015", "020"}
    else:
        val_partition = {f"{value:03d}" for value in range(240, 270)}

    keys: list[str] = []
    seen = set()
    for line in ann_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            clip, frame = parse_reds_key(line)
        except ValueError as exc:
            issues.append(str(exc))
            continue
        key = f"{clip}/{frame}"
        if key not in seen:
            seen.add(key)
            keys.append(key)

    if not keys:
        issues.append(f"no REDS keys found in {ann_file}")
        return report("REDS layout", details, issues)

    details.append(f"ann-file: {ann_file}")
    details.append(f"keys: {len(keys)}")

    for key in take(keys, args.sample):
        clip, frame = key.split("/", 1)
        if args.test_mode and clip not in val_partition:
            issues.append(
                f"{key} is not part of the selected validation partition {args.partition}"
            )
        if not args.test_mode and clip in val_partition:
            issues.append(
                f"{key} belongs to the validation partition {args.partition} but test_mode is off"
            )
        frame_file = frame if frame.lower().endswith(".png") else f"{frame}.png"
        lq_file = lq_root / clip / frame_file
        gt_file = gt_root / clip / frame_file
        if not lq_file.is_file():
            issues.append(f"missing REDS LQ frame: {lq_file}")
        if not gt_file.is_file():
            issues.append(f"missing REDS GT frame: {gt_file}")
        details.append(f"  - {key}")

    return report("REDS layout", details, issues)


def parse_vimeo_key(raw: str) -> str:
    token = raw.split()[0].strip()
    token = token.split(".")[0]
    if "/" not in token:
        raise ValueError(f"invalid Vimeo90K key: {raw}")
    return token


def check_vimeo90k(args) -> int:
    lq_root = Path(args.lq_root)
    gt_root = Path(args.gt_root)
    ann_file = Path(args.ann_file)
    details: list[str] = []
    issues: list[str] = []

    for label, folder in (("lq-root", lq_root), ("gt-root", gt_root)):
        if not folder.is_dir():
            issues.append(f"missing {label}: {folder}")

    if not ann_file.is_file():
        issues.append(f"missing ann-file: {ann_file}")
        return report("Vimeo90K layout", details, issues)

    keys: list[str] = []
    seen = set()
    for line in ann_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            key = parse_vimeo_key(line)
        except ValueError as exc:
            issues.append(str(exc))
            continue
        if key not in seen:
            seen.add(key)
            keys.append(key)

    if not keys:
        issues.append(f"no Vimeo90K keys found in {ann_file}")
        return report("Vimeo90K layout", details, issues)

    details.append(f"ann-file: {ann_file}")
    details.append(f"keys: {len(keys)}")

    for key in take(keys, args.sample):
        lq_seq = lq_root / key
        gt_seq = gt_root / key
        if not lq_seq.is_dir():
            issues.append(f"missing Vimeo90K LQ sequence: {lq_seq}")
            continue
        if not gt_seq.is_dir():
            issues.append(f"missing Vimeo90K GT sequence: {gt_seq}")
            continue
        lq_images = list_images(lq_seq, recursive=False)
        gt_images = list_images(gt_seq, recursive=False)
        if not lq_images:
            issues.append(f"no frames found in Vimeo90K LQ sequence: {lq_seq}")
        if not gt_images:
            issues.append(f"no frames found in Vimeo90K GT sequence: {gt_seq}")
        if len(lq_images) != len(gt_images):
            issues.append(
                f"Vimeo90K frame counts differ for {key}: LQ={len(lq_images)}, GT={len(gt_images)}"
            )
        details.append(f"  - {key}: {len(lq_images)} LQ frames, {len(gt_images)} GT frames")

    return report("Vimeo90K layout", details, issues)


def check_lrs2(args) -> int:
    preprocessed_root = Path(args.preprocessed_root)
    filelists_dir = Path(args.filelists_dir)
    details: list[str] = []
    issues: list[str] = []
    detail_count = 0

    def add_detail(line: str) -> None:
        nonlocal detail_count
        if detail_count < args.detail_limit:
            details.append(line)
            detail_count += 1

    if not preprocessed_root.is_dir():
        issues.append(f"missing preprocessed-root: {preprocessed_root}")
    if not filelists_dir.is_dir():
        issues.append(f"missing filelists-dir: {filelists_dir}")
        return report("LRS2 layout", details, issues)

    for split in args.splits:
        filelist = filelists_dir / f"{split}.txt"
        if not filelist.is_file():
            issues.append(f"missing filelist: {filelist}")
            continue
        lines = [line.strip() for line in filelist.read_text(encoding="utf-8").splitlines() if line.strip()]
        if not lines:
            issues.append(f"empty filelist: {filelist}")
            continue
        add_detail(f"{split}: {len(lines)} entries")
        seen = set()
        for raw in lines:
            rel = raw.split()[0]
            if rel in seen:
                continue
            seen.add(rel)
            clip_root = preprocessed_root / rel
            if not clip_root.is_dir():
                issues.append(f"missing preprocessed clip directory: {clip_root}")
                continue
            frames = list_images(clip_root, recursive=False)
            audio = clip_root / "audio.wav"
            if not frames:
                issues.append(f"no frame images found in {clip_root}")
            if not audio.is_file():
                issues.append(f"missing audio track: {audio}")
            note = " (short clip)" if len(frames) < 16 else ""
            add_detail(f"  - {rel}: {len(frames)} frames, audio.wav present{note}")

    return report("LRS2 layout", details, issues)


def check_realsr(args) -> int:
    hr_root = Path(args.hr_root)
    lr_root = Path(args.lr_root)
    noise_root = Path(args.noise_root) if args.noise_root else None
    kernel_root = Path(args.kernel_root) if args.kernel_root else None
    details: list[str] = []
    issues: list[str] = []

    hr_details, hr_issues, hr_images = folder_summary(
        hr_root,
        "HR",
        recursive=False,
        sample=args.sample,
        required=True,
    )
    lr_details, lr_issues, lr_images = folder_summary(
        lr_root,
        "LR",
        recursive=False,
        sample=args.sample,
        required=True,
    )
    details.extend(hr_details)
    details.extend(lr_details)
    issues.extend(hr_issues)
    issues.extend(lr_issues)

    if hr_images and lr_images:
        if len(hr_images) != len(lr_images):
            issues.append(
                f"RealSR HR/LR counts differ: HR={len(hr_images)}, LR={len(lr_images)}"
            )
        hr_names = [path.name for path in hr_images]
        lr_names = [path.name for path in lr_images]
        if hr_names != lr_names:
            issues.append("RealSR HR/LR filenames differ")

    if noise_root is not None:
        noise_details, noise_issues, _ = folder_summary(
            noise_root,
            "noise-root",
            recursive=False,
            sample=args.sample,
            required=True,
        )
        details.extend(noise_details)
        issues.extend(noise_issues)

    if kernel_root is not None:
        kernel_root = Path(kernel_root)
        if not kernel_root.is_dir():
            issues.append(f"missing kernel-root: {kernel_root}")
        else:
            kernels = sorted(path for path in kernel_root.rglob("*")
                             if path.is_file() and path.suffix.lower() == ".mat")
            if not kernels:
                issues.append(f"no .mat kernels found under {kernel_root}")
            else:
                details.append(f"kernel-root: {len(kernels)} .mat files")
                for path in take(kernels, args.sample):
                    details.append(f"  - {path.name}")

    return report("RealSR layout", details, issues)


def check_generic(args) -> int:
    root = Path(args.root)
    details: list[str] = []
    issues: list[str] = []

    if not root.is_dir():
        issues.append(f"missing root: {root}")
        return report("Generic layout", details, issues)

    images = list_images(root, recursive=args.recursive)
    if not images:
        issues.append(f"no images found under {root}")
        return report("Generic layout", details, issues)

    details.append(f"images: {len(images)}")
    details.append(f"recursive: {args.recursive}")
    for path in take(images, args.sample):
        details.append(f"  - {describe_image(path)}")

    return report("Generic layout", details, issues)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check common PaddleGAN dataset layouts.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    def add_sample_argument(subparser):
        subparser.add_argument(
            "--sample",
            type=int,
            default=3,
            help="Number of example files to print for each checked folder.",
        )

    cyclegan = subparsers.add_parser(
        "cyclegan", help="Check unpaired CycleGAN-style folders.")
    cyclegan.add_argument(
        "--root",
        required=True,
        help="Parent folder that contains trainA/trainB and optionally testA/testB.",
    )
    cyclegan.add_argument(
        "--require-test",
        action="store_true",
        help="Require the testA/testB pair instead of treating it as optional.",
    )
    add_sample_argument(cyclegan)

    pix2pix = subparsers.add_parser(
        "pix2pix", help="Check paired Pix2Pix-style folders.")
    pix2pix.add_argument(
        "--root",
        required=True,
        help="Parent folder that contains train and optional val/test splits.",
    )
    pix2pix.add_argument(
        "--require-eval",
        action="store_true",
        help="Require either val/ or test/ to exist.",
    )
    add_sample_argument(pix2pix)

    div2k = subparsers.add_parser(
        "div2k", help="Check raw and processed DIV2K/SR folders.")
    div2k.add_argument(
        "--root",
        required=True,
        help="DIV2K root that contains DIV2K_train_HR and DIV2K_train_LR_bicubic.",
    )
    div2k.add_argument(
        "--scales",
        nargs="+",
        type=int,
        default=[2, 3, 4],
        help="LR scales to validate.",
    )
    div2k.add_argument(
        "--require-processed",
        action="store_true",
        help="Require the *_sub outputs produced by the bundled DIV2K helper.",
    )
    add_sample_argument(div2k)

    reds = subparsers.add_parser(
        "reds", help="Check REDS frame folders and annotation keys.")
    reds.add_argument("--lq-root", required=True, help="Low-quality frame root.")
    reds.add_argument("--gt-root", required=True, help="Ground-truth frame root.")
    reds.add_argument("--ann-file", required=True, help="Annotation file.")
    reds.add_argument(
        "--partition",
        choices=("REDS4", "official"),
        default="REDS4",
        help="Validation partition used by the dataset class.",
    )
    reds.add_argument(
        "--test-mode",
        action="store_true",
        help="Check that sampled keys belong to the validation partition.",
    )
    reds.add_argument(
        "--num-frames",
        type=int,
        default=None,
        help="Optional num_frames check; REDS dataset classes expect an odd value.",
    )
    add_sample_argument(reds)

    vimeo = subparsers.add_parser(
        "vimeo90k", help="Check Vimeo90K sequence folders and list keys.")
    vimeo.add_argument("--lq-root", required=True, help="Low-quality sequence root.")
    vimeo.add_argument("--gt-root", required=True, help="Ground-truth sequence root.")
    vimeo.add_argument("--ann-file", required=True, help="Split list file.")
    add_sample_argument(vimeo)

    lrs2 = subparsers.add_parser(
        "lrs2", help="Check Wav2Lip/LRS2 preprocessed folders and filelists.")
    lrs2.add_argument(
        "--preprocessed-root",
        required=True,
        help="Root that contains preprocessed clip directories.",
    )
    lrs2.add_argument(
        "--filelists-dir",
        default="filelists",
        help="Directory that contains train/val/test split files.",
    )
    lrs2.add_argument(
        "--splits",
        nargs="+",
        default=["train", "val", "test"],
        help="Split names to validate.",
    )
    lrs2.add_argument(
        "--detail-limit",
        type=int,
        default=30,
        help="Stop printing LRS2 detail lines after this many rows.",
    )
    add_sample_argument(lrs2)

    realsr = subparsers.add_parser(
        "realsr", help="Check explicit RealSR output and auxiliary folders.")
    realsr.add_argument("--hr-root", required=True, help="Generated HR folder.")
    realsr.add_argument("--lr-root", required=True, help="Generated LR folder.")
    realsr.add_argument(
        "--noise-root",
        default=None,
        help="Optional generated noise folder.",
    )
    realsr.add_argument(
        "--kernel-root",
        default=None,
        help="Optional folder that contains KernelGAN .mat files.",
    )
    add_sample_argument(realsr)

    generic = subparsers.add_parser(
        "generic",
        help="Recursively count images in a small fixture or arbitrary tree.")
    generic.add_argument("--root", required=True, help="Folder to inspect.")
    generic.add_argument(
        "--recursive",
        dest="recursive",
        action="store_true",
        default=True,
        help="Scan nested folders recursively.",
    )
    generic.add_argument(
        "--flat",
        dest="recursive",
        action="store_false",
        help="Only inspect files directly under the root folder.",
    )
    add_sample_argument(generic)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    handlers = {
        "cyclegan": check_cyclegan,
        "pix2pix": check_pix2pix,
        "div2k": check_div2k,
        "reds": check_reds,
        "vimeo90k": check_vimeo90k,
        "lrs2": check_lrs2,
        "realsr": check_realsr,
        "generic": check_generic,
    }
    return handlers[args.command](args)


if __name__ == "__main__":
    raise SystemExit(main())
