#!/usr/bin/env python3
"""Check local imgclsmob dataset layouts without framework imports or downloads.

The command is a conservative preflight for the training/evaluation CLIs.  It
checks directory names, required metadata, and the expected ImageNet class
directory count.  It never imports MXNet, PyTorch, torchvision, or any other
framework, and it never invokes a downloader.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Iterable

IMAGE_NET_FOLDER = "ImageNet1K"
IMAGE_NET_RECORD = "ImageNet1K_rec"
CIFAR_DATASETS = ("CIFAR10", "CIFAR100")
SUPPORTED_DATASETS = (
    IMAGE_NET_FOLDER,
    IMAGE_NET_RECORD,
    *CIFAR_DATASETS,
    "SVHN",
    "CUB200_2011",
)
SUPPORTED_BACKENDS = ("auto", "gluon", "pytorch")


def _result(dataset: str, root: Path, status: str, message: str, **extra: Any) -> dict[str, Any]:
    """Build a stable, JSON-serializable result for both humans and scripts."""
    result: dict[str, Any] = {
        "dataset": dataset,
        "data_dir": str(root),
        "status": status,
        "message": message,
        "network": "not_used",
    }
    result.update(extra)
    return result


def _nonempty_file(path: Path) -> bool:
    try:
        return path.is_file() and path.stat().st_size > 0
    except OSError:
        return False


def _directory_entries(path: Path) -> tuple[list[Path] | None, str | None]:
    """Return entries, or an actionable filesystem error without a traceback."""
    try:
        return list(path.iterdir()), None
    except OSError as exc:
        return None, f"cannot inspect {path}: {exc}"


def _class_directories(path: Path) -> tuple[list[Path] | None, str | None]:
    entries, error = _directory_entries(path)
    if error is not None:
        return None, error
    assert entries is not None
    return sorted(entry for entry in entries if entry.is_dir()), None


def _record_names_present(root: Path) -> list[str]:
    names = ("train.rec", "train.idx", "val.rec", "val.idx")
    return [name for name in names if (root / name).exists()]


def _has_folder_split(root: Path) -> bool:
    return (root / "train").is_dir() or (root / "val").is_dir()


def _check_root(dataset: str, root: Path) -> dict[str, Any] | None:
    try:
        if not root.exists():
            return _result(
                dataset,
                root,
                "missing_local_data",
                f"data root does not exist: {root}; create or point --data-dir at the local dataset root",
            )
        if not root.is_dir():
            return _result(
                dataset,
                root,
                "invalid_root",
                f"--data-dir must be a directory, but is a file: {root}",
            )
    except OSError as exc:
        return _result(
            dataset,
            root,
            "inaccessible_root",
            f"cannot inspect --data-dir {root}: {exc}; check permissions and the path",
        )
    return None


def _check_imagenet_folder(dataset: str, root: Path) -> dict[str, Any]:
    record_names = _record_names_present(root)
    train = root / "train"
    val = root / "val"
    if record_names and _has_folder_split(root):
        return _result(
            dataset,
            root,
            "ambiguous_imagenet_layout",
            "both folder splits and record files are present; use a root containing one explicit layout",
            found_record_files=record_names,
            required=["train/", "val/"],
        )
    if not train.is_dir() or not val.is_dir():
        if record_names:
            message = (
                "ImageNet1K is the folder layout and needs train/ and val/ class directories; "
                "record files were found instead. Use ImageNet1K_rec with Gluon when the four "
                "record/index files are complete."
            )
        else:
            message = (
                "ImageNet1K needs train/ and val/ directories directly under --data-dir; "
                "point --data-dir at the dataset root, not at train/ or an extra parent directory"
            )
        return _result(
            dataset,
            root,
            "invalid_imagenet_layout",
            message,
            required=["train/", "val/"],
            found_record_files=record_names,
        )

    train_classes, train_error = _class_directories(train)
    val_classes, val_error = _class_directories(val)
    if train_error or val_error:
        errors = [error for error in (train_error, val_error) if error]
        return _result(
            dataset,
            root,
            "inaccessible_dataset_layout",
            "; ".join(errors) + "; check directory permissions",
        )
    assert train_classes is not None and val_classes is not None
    train_count = len(train_classes)
    val_count = len(val_classes)
    if train_count != 1000 or val_count != 1000:
        return _result(
            dataset,
            root,
            "invalid_imagenet_layout",
            (
                "ImageNet1K needs exactly 1000 class directories in both train/ and val/ "
                f"(found train={train_count}, val={val_count}); repair the split root"
            ),
            train_class_dirs=train_count,
            val_class_dirs=val_count,
            required_class_dirs=1000,
        )
    return _result(
        dataset,
        root,
        "ok",
        "ImageNet1K folder layout has train/ and val/ with 1000 class directories each",
        layout="folder",
        train_class_dirs=train_count,
        val_class_dirs=val_count,
    )


def _check_imagenet_records(dataset: str, root: Path, backend: str) -> dict[str, Any]:
    if backend == "pytorch":
        return _result(
            dataset,
            root,
            "unsupported_backend_layout",
            "ImageNet1K_rec is Gluon-only; use --dataset ImageNet1K with train/ and val/ folders for PyTorch",
        )
    required = ("train.rec", "train.idx", "val.rec", "val.idx")
    missing = [name for name in required if not _nonempty_file(root / name)]
    if missing:
        if _has_folder_split(root):
            message = (
                "ImageNet1K_rec needs non-empty train.rec, train.idx, val.rec, and val.idx files "
                "directly under --data-dir; folder splits were found, so select ImageNet1K instead"
            )
        else:
            message = (
                "ImageNet1K_rec needs four non-empty record/index files directly under --data-dir; "
                f"missing or empty: {', '.join(missing)}"
            )
        return _result(dataset, root, "invalid_imagenet_layout", message, missing=missing, required=list(required))
    return _result(
        dataset,
        root,
        "ok",
        "ImageNet1K_rec has all four non-empty record/index files",
        layout="record",
        files=list(required),
    )


def _check_cub(dataset: str, root: Path) -> dict[str, Any]:
    required_files = ("images.txt", "image_class_labels.txt", "train_test_split.txt")
    missing = [name for name in required_files if not _nonempty_file(root / name)]
    try:
        images_present = (root / "images").is_dir()
    except OSError:
        images_present = False
    if not images_present:
        missing.append("images/")
    if missing:
        return _result(
            dataset,
            root,
            "invalid_dataset_layout",
            (
                "CUB200_2011 needs images.txt, image_class_labels.txt, "
                f"train_test_split.txt, and images/; missing or invalid: {', '.join(missing)}"
            ),
            required=list(required_files) + ["images/"],
            missing=missing,
        )
    return _result(
        dataset,
        root,
        "ok",
        "CUB200_2011 metadata files and images/ directory are present",
        layout="metadata-and-images",
        classes=200,
    )


def _check_native_cache(dataset: str, root: Path) -> dict[str, Any]:
    """Check only local presence; exact cache integrity belongs to the backend."""
    entries, error = _directory_entries(root)
    if error is not None:
        return _result(dataset, root, "inaccessible_dataset_layout", error + "; check directory permissions")
    assert entries is not None
    if not entries:
        return _result(
            dataset,
            root,
            "missing_local_data",
            (
                f"{dataset} root is empty; populate its backend-native local cache before running "
                "offline (this checker will not download it)"
            ),
            layout="native-cache",
        )
    return _result(
        dataset,
        root,
        "indeterminate_native_cache",
        (
            f"{dataset} root exists and is non-empty, but exact native-cache integrity must be "
            "checked by the selected framework with downloads disabled"
        ),
        layout="native-cache",
        entries=len(entries),
        cache_validation="presence-only",
        next_step="run the framework dataset integrity check with download disabled",
    )


def check_layout(dataset: str, data_dir: Path, backend: str = "auto") -> dict[str, Any]:
    """Return a no-network layout result for one supported dataset."""
    root = data_dir.expanduser()
    if dataset not in SUPPORTED_DATASETS:
        return _result(
            dataset,
            root,
            "invalid_dataset",
            f"unsupported dataset {dataset!r}; use one of: {', '.join(SUPPORTED_DATASETS)}",
            supported=list(SUPPORTED_DATASETS),
        )
    if backend not in SUPPORTED_BACKENDS:
        return _result(
            dataset,
            root,
            "invalid_backend",
            f"unsupported backend {backend!r}; use auto, gluon, or pytorch",
            supported=list(SUPPORTED_BACKENDS),
        )

    root_error = _check_root(dataset, root)
    if root_error is not None:
        return root_error
    if dataset == IMAGE_NET_FOLDER:
        return _check_imagenet_folder(dataset, root)
    if dataset == IMAGE_NET_RECORD:
        return _check_imagenet_records(dataset, root, backend)
    if dataset == "CUB200_2011":
        return _check_cub(dataset, root)
    return _check_native_cache(dataset, root)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate imgclsmob dataset roots without framework imports, downloads, or training.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--dataset",
        required=True,
        choices=SUPPORTED_DATASETS,
        help="exact dataset metainfo name",
    )
    parser.add_argument(
        "--data-dir",
        required=True,
        type=Path,
        help="local dataset root to inspect",
    )
    parser.add_argument(
        "--backend",
        choices=SUPPORTED_BACKENDS,
        default="auto",
        help="consumer used for backend-specific layout rules",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit only compact JSON (useful for shell automation)",
    )
    return parser


def _print_result(result: dict[str, Any], as_json: bool) -> None:
    if as_json:
        print(json.dumps(result, sort_keys=True))
        return
    print(f"{result['status']}: {result['message']}")
    print(json.dumps(result, indent=2, sort_keys=True))


def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = check_layout(args.dataset, args.data_dir, args.backend)
    _print_result(result, args.json)
    return 0 if result["status"] == "ok" else 2


if __name__ == "__main__":
    sys.exit(main())
