#!/usr/bin/env python3
"""Validate pix2pixHD feature cache files without launching long jobs."""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import List, Sequence

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}


@dataclass
class Finding:
    level: str
    message: str
    remedy: str | None = None


class Report:
    def __init__(self) -> None:
        self.findings: List[Finding] = []

    def ok(self, message: str) -> None:
        self.findings.append(Finding("OK", message))

    def warn(self, message: str, remedy: str | None = None) -> None:
        self.findings.append(Finding("WARN", message, remedy))

    def fail(self, message: str, remedy: str | None = None) -> None:
        self.findings.append(Finding("FAIL", message, remedy))

    def exit_code(self, *, strict: bool = False) -> int:
        if any(item.level == "FAIL" for item in self.findings):
            return 1
        if strict and any(item.level == "WARN" for item in self.findings):
            return 1
        return 0

    def print(self) -> None:
        for item in self.findings:
            print(f"[{item.level}] {item.message}")
            if item.remedy:
                print(f"  remedy: {item.remedy}")


def resolve_path(root: Path, override: str | None, fallback: Path) -> Path:
    if override:
        return root / override
    return root / fallback


def image_files(directory: Path) -> List[Path]:
    if not directory.is_dir():
        return []
    return sorted(p for p in directory.rglob("*") if p.is_file() and p.suffix.lower() in IMAGE_SUFFIXES)


def relative_stem(path: Path, root: Path) -> str:
    return path.relative_to(root).with_suffix("").as_posix()


def comma_list(value: str | None) -> List[str]:
    if not value:
        return []
    return [part.strip() for part in value.split(",") if part.strip()]


def short_list(values: Sequence[str], limit: int = 5) -> str:
    if not values:
        return "none"
    head = list(values[:limit])
    suffix = "" if len(values) <= limit else f" ... (+{len(values) - limit} more)"
    return ", ".join(head) + suffix


def discover_phases(dataroot: Path, requested: Sequence[str]) -> List[str]:
    if requested:
        return sorted(set(requested))
    return sorted(p.name[:-5] for p in dataroot.glob("*_feat") if p.is_dir())


def inspect_feature_folders(report: Report, dataroot: Path, phases: Sequence[str]) -> None:
    if not dataroot.exists():
        report.fail(
            f"dataroot does not exist: {dataroot}",
            "Pass --dataroot explicitly or create the standard pix2pixHD dataset layout first.",
        )
        return

    if not phases:
        report.fail(
            f"no *_feat folders found under {dataroot}",
            "Run precompute_feature_maps.py for load_features training, or use --mode cache when only clustered .npy files are expected.",
        )
        return

    for phase in phases:
        feat_dir = dataroot / f"{phase}_feat"
        label_dir = dataroot / f"{phase}_label"
        inst_dir = dataroot / f"{phase}_inst"
        img_dir = dataroot / f"{phase}_img"

        if not feat_dir.is_dir():
            report.fail(
                f"missing feature folder: {feat_dir}",
                f"Run precompute_feature_maps.py for phase '{phase}', or remove --load_features for workflows that do not consume {phase}_feat/.",
            )
            continue

        feat_files = image_files(feat_dir)
        if not feat_files:
            report.fail(
                f"feature folder is empty: {feat_dir}",
                "Regenerate the feature maps; train.py --load_features expects one image per label map.",
            )
            continue

        if not label_dir.is_dir():
            report.fail(
                f"missing label folder required to align feature maps: {label_dir}",
                "Keep the standard phase_label/phase_feat folder names, because precompute_feature_maps.py rewrites train_label to train_feat.",
            )
            continue

        label_files = image_files(label_dir)
        label_stems = sorted(relative_stem(p, label_dir) for p in label_files)
        feat_stems = sorted(relative_stem(p, feat_dir) for p in feat_files)
        missing = sorted(set(label_stems) - set(feat_stems))
        extra = sorted(set(feat_stems) - set(label_stems))
        if missing or extra or len(label_stems) != len(feat_stems):
            report.fail(
                f"{feat_dir} is not one-to-one aligned with {label_dir}: {len(feat_files)} feature files vs {len(label_files)} labels",
                f"missing feature stems: {short_list(missing)}; extra feature stems: {short_list(extra)}. Regenerate train_feat/ from the matching label folder.",
            )
        else:
            report.ok(f"{feat_dir} has {len(feat_files)} feature maps aligned with {label_dir}")

        for companion_dir, label in [(inst_dir, "instance"), (img_dir, "image")]:
            if not companion_dir.is_dir():
                report.warn(
                    f"{label} companion folder not found for phase '{phase}': {companion_dir}",
                    "This may be acceptable for a narrow cache check, but default instance-feature workflows need paired labels/instances/images.",
                )
                continue
            companion_count = len(image_files(companion_dir))
            if companion_count != len(label_files):
                report.fail(
                    f"{companion_dir} has {companion_count} files but {label_dir} has {len(label_files)} files",
                    "Fix the paired dataset layout before using load_features; the loader relies on sorted lists with matching counts.",
                )
            else:
                report.ok(f"{companion_dir} file count matches {label_dir} ({companion_count})")


def load_npy_dict(path: Path, report: Report) -> dict | None:
    try:
        import numpy as np
    except Exception as exc:  # pragma: no cover - numpy is expected but keep message precise.
        report.fail(f"numpy import failed while inspecting {path}: {exc}", "Install numpy before inspecting pix2pixHD feature caches.")
        return None

    try:
        obj = np.load(path, allow_pickle=True, encoding="latin1")
        data = obj.item()
    except Exception as exc:
        report.fail(
            f"could not load feature cache {path}: {exc}",
            "The cache should be a dict saved with np.save; regenerate it with encode_features.py if it is corrupt.",
        )
        return None

    if not isinstance(data, dict):
        report.fail(f"feature cache {path} is {type(data).__name__}, not a dict")
        return None
    return data


def validate_feature_dict(report: Report, path: Path, data: dict, *, feat_num: int, clustered: bool) -> None:
    expected_cols = feat_num if clustered else feat_num + 1
    nonempty = 0
    bad: List[str] = []
    for label, value in sorted(data.items(), key=lambda item: str(item[0])):
        shape = getattr(value, "shape", None)
        if shape is None or len(shape) != 2 or shape[1] != expected_cols:
            bad.append(f"label {label}: shape {shape}")
            continue
        if shape[0] > 0:
            nonempty += 1
    kind = "cluster" if clustered else "raw feature"
    if bad:
        report.fail(
            f"{path} has {kind} arrays with unexpected width; expected {expected_cols} columns",
            f"examples: {short_list(bad)}. Rebuild caches with the same --feat_num used by train/test.",
        )
        return
    if nonempty == 0:
        report.warn(
            f"{path} loaded as a dict with {len(data)} labels but no non-empty {kind} arrays",
            "Check whether the dataset is empty or all objects were filtered out before clustering.",
        )
    else:
        report.ok(f"{path} loaded as {kind} dict with {len(data)} labels and {nonempty} non-empty labels")


def inspect_checkpoint_cache(report: Report, checkpoints_dir: Path, name: str, args: argparse.Namespace) -> None:
    exp_dir = checkpoints_dir / name
    if not exp_dir.is_dir():
        report.fail(
            f"missing checkpoint/cache directory: {exp_dir}",
            "Check --name, --checkpoints-dir, or run the feature training recipe before validating caches.",
        )
        return

    if args.check_generator:
        gen_path = exp_dir / f"{args.which_epoch}_net_G.pth"
        if gen_path.is_file():
            report.ok(f"generator checkpoint found: {gen_path}")
        else:
            report.fail(
                f"missing generator checkpoint: {gen_path}",
                "Feature-conditioned inference needs the generator checkpoint for the selected experiment name.",
            )

    if args.check_encoder:
        enc_path = exp_dir / f"{args.which_epoch}_net_E.pth"
        if enc_path.is_file():
            report.ok(f"feature encoder checkpoint found: {enc_path}")
        else:
            report.fail(
                f"missing feature encoder checkpoint: {enc_path}",
                "Use the source feature checkpoint that actually trained netE; 1024p --load_features target runs may not save an encoder.",
            )

    raw_path = exp_dir / "features.npy"
    if raw_path.is_file():
        data = load_npy_dict(raw_path, report)
        if data is not None:
            validate_feature_dict(report, raw_path, data, feat_num=args.feat_num, clustered=False)
    else:
        report.warn(
            f"raw feature cache not found: {raw_path}",
            "This is not required for test-time sampling if the clustered cache exists, but rerun encode_features.py if you need to rebuild clusters.",
        )

    cluster_name = args.cluster_path or f"features_clustered_{args.n_clusters:03d}.npy"
    cluster_path = exp_dir / cluster_name
    if not cluster_path.is_file():
        report.fail(
            f"missing clustered feature cache: {cluster_path}",
            f"Run encode_features.py --name {name} --n_clusters {args.n_clusters}, or pass --cluster_path to point at the existing clustered file.",
        )
        return

    data = load_npy_dict(cluster_path, report)
    if data is not None:
        validate_feature_dict(report, cluster_path, data, feat_num=args.feat_num, clustered=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate pix2pixHD feature caches and precomputed feature-map folders.")
    parser.add_argument("--repo-root", required=True, help="Pix2pixHD checkout root to inspect.")
    parser.add_argument("--name", required=True, help="Experiment/checkpoint name under checkpoints_dir.")
    parser.add_argument("--mode", choices=["folders", "cache", "full"], default="full", help="Which cache surfaces to validate.")
    parser.add_argument("--dataroot", help="Override dataroot; relative paths are resolved under --repo-root.")
    parser.add_argument("--checkpoints-dir", help="Override checkpoints root; relative paths are resolved under --repo-root.")
    parser.add_argument("--phases", help="Comma-separated phases to inspect, e.g. train,test. Defaults to autodetected *_feat folders.")
    parser.add_argument("--n_clusters", type=int, default=10, help="Expected cluster count used to derive the default cluster filename.")
    parser.add_argument("--cluster_path", help="Cluster filename under checkpoints/<name>/; default is features_clustered_<n_clusters>.npy.")
    parser.add_argument("--feat_num", type=int, default=3, help="Expected feature-vector width.")
    parser.add_argument("--which_epoch", default="latest", help="Checkpoint epoch label to inspect when checkpoint checks are enabled.")
    parser.add_argument("--check-generator", action="store_true", help="Also require <which_epoch>_net_G.pth.")
    parser.add_argument("--check-encoder", action="store_true", help="Also require <which_epoch>_net_E.pth.")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as failures.")
    args = parser.parse_args()

    repo_root = Path(args.repo_root)
    dataroot = resolve_path(repo_root, args.dataroot, Path("datasets") / "cityscapes")
    checkpoints_dir = resolve_path(repo_root, args.checkpoints_dir, Path("checkpoints"))
    phases = discover_phases(dataroot, comma_list(args.phases))

    report = Report()
    report.ok(f"repo root: {repo_root}")
    report.ok(f"dataroot: {dataroot}")
    report.ok(f"checkpoints dir: {checkpoints_dir}")

    if args.mode in {"folders", "full"}:
        inspect_feature_folders(report, dataroot, phases)
    if args.mode in {"cache", "full"}:
        inspect_checkpoint_cache(report, checkpoints_dir, args.name, args)

    report.print()
    return report.exit_code(strict=args.strict)


if __name__ == "__main__":
    raise SystemExit(main())
