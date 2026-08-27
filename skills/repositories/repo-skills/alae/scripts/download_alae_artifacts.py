#!/usr/bin/env python3
"""List or explicitly download ALAE pretrained model artifacts.

Default behavior is a dry-run manifest print. Network downloads require both
`--download` and `--yes` so future agents do not accidentally fetch large files.

Examples:
  python scripts/download_alae_artifacts.py --dataset ffhq
  python scripts/download_alae_artifacts.py --dataset ffhq --download --yes --dest-root training_artifacts
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


# Distilled from the repository's training_artifacts/download_all.py.
ARTIFACTS: Dict[str, List[Dict[str, Optional[str]]]] = {
    "ffhq": [
        {"name": "model_submitted.pth", "google_id": "170Qldnn28IwnVm9CQEq1AZhVsK7PJ0Xz", "s3_url": "https://alaeweights.s3.us-east-2.amazonaws.com/ffhq/model_submitted.pth"},
        {"name": "model_194.pth", "google_id": "1QESywJW8N-g3n0Csy0clztuJV99g8pRm", "s3_url": "https://alaeweights.s3.us-east-2.amazonaws.com/ffhq/model_194.pth"},
        {"name": "model_157.pth", "google_id": "18BzFYKS3icFd1DQKKTeje7CKbEKXPVug", "s3_url": "https://alaeweights.s3.us-east-2.amazonaws.com/ffhq/model_157.pth"},
    ],
    "celeba": [
        {"name": "model_final.pth", "google_id": "1T4gkE7-COHpX38qPwjMYO-xU-SrY_aT4", "s3_url": "https://alaeweights.s3.us-east-2.amazonaws.com/celeba/model_final.pth"},
    ],
    "bedroom": [
        {"name": "model_final.pth", "google_id": "1gmYbc6Z8qJHJwICYDsB4aBMxXjnKeXA_", "s3_url": "https://alaeweights.s3.us-east-2.amazonaws.com/bedroom/model_final.pth"},
    ],
    "celeba-hq256": [
        {"name": "model_262r.pth", "google_id": "1ihJvp8iJWcLxTIjkV5cyA7l9TrxlUPkG", "s3_url": "https://alaeweights.s3.us-east-2.amazonaws.com/celeba-hq256/model_262r.pth"},
        {"name": "model_580r.pth", "google_id": "1gFQsGCNKo-frzKmA3aCvx07ShRymRIKZ", "s3_url": "https://alaeweights.s3.us-east-2.amazonaws.com/celeba-hq256/model_580r.pth"},
    ],
}
DEFAULT_LAST_CHECKPOINT = {
    "ffhq": "model_157.pth",
    "celeba": "model_final.pth",
    "bedroom": "model_final.pth",
    "celeba-hq256": "model_580r.pth",
}


def selected_datasets(value: str) -> List[str]:
    if value == "all":
        return list(ARTIFACTS.keys())
    return [value]


def iter_entries(datasets: Iterable[str], dest_root: Path) -> Iterable[Dict[str, Any]]:
    for dataset in datasets:
        for artifact in ARTIFACTS[dataset]:
            target_dir = dest_root / dataset
            target_file = target_dir / str(artifact["name"])
            yield {
                "dataset": dataset,
                "name": artifact["name"],
                "target_dir": str(target_dir),
                "target_file": str(target_file),
                "exists": target_file.is_file(),
                "google_id": artifact.get("google_id"),
                "s3_url": artifact.get("s3_url"),
            }


def print_manifest(entries: List[Dict[str, Any]], as_json: bool) -> None:
    if as_json:
        print(json.dumps(entries, indent=2, sort_keys=True))
        return
    for entry in entries:
        status = "present" if entry["exists"] else "missing"
        print(f"{entry['dataset']:<12} {entry['name']:<24} {status:<8} -> {entry['target_file']}")
        print(f"  google id: {entry['google_id']}")
        print(f"  s3 url:    {entry['s3_url']}")


def require_dlutils():
    try:
        from dlutils import download  # type: ignore
    except Exception as exc:  # pragma: no cover - environment-dependent
        raise RuntimeError("dlutils is required for --download; install/upgrade dlutils first") from exc
    return download


def download_one(entry: Dict[str, Any], prefer: str, fallback: bool) -> None:
    download = require_dlutils()
    target_dir = entry["target_dir"]
    Path(target_dir).mkdir(parents=True, exist_ok=True)
    errors = []
    orders = [prefer]
    if fallback:
        orders.append("s3" if prefer == "google" else "google")
    for method in orders:
        try:
            if method == "google":
                if not entry.get("google_id"):
                    raise RuntimeError("no Google Drive id recorded")
                download.from_google_drive(entry["google_id"], directory=target_dir)
            else:
                if not entry.get("s3_url"):
                    raise RuntimeError("no S3 fallback URL recorded")
                download.from_url(entry["s3_url"], directory=target_dir)
            return
        except Exception as exc:  # pragma: no cover - network-dependent
            errors.append(f"{method}: {type(exc).__name__}: {exc}")
    raise RuntimeError("; ".join(errors))


def write_last_checkpoint(dataset: str, dest_root: Path) -> None:
    name = DEFAULT_LAST_CHECKPOINT.get(dataset)
    if not name:
        return
    dataset_dir = dest_root / dataset
    dataset_dir.mkdir(parents=True, exist_ok=True)
    pointer = dataset_dir / "last_checkpoint"
    pointer.write_text(str(dataset_dir / name))
    print(f"wrote {pointer} -> {dataset_dir / name}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="List or explicitly download ALAE pretrained artifacts with safe dry-run defaults.")
    parser.add_argument("--dataset", choices=["all"] + list(ARTIFACTS.keys()), default="all", help="Dataset/model group to list or download.")
    parser.add_argument("--dest-root", default="training_artifacts", help="Destination root that will contain dataset subdirectories.")
    parser.add_argument("--prefer", choices=["google", "s3"], default="google", help="Preferred download source when --download is used.")
    parser.add_argument("--no-fallback", action="store_true", help="Do not try the other source if the preferred source fails.")
    parser.add_argument("--download", action="store_true", help="Actually download artifacts. Without this, only the manifest is printed.")
    parser.add_argument("--yes", action="store_true", help="Required together with --download to acknowledge network and disk side effects.")
    parser.add_argument("--skip-existing", action="store_true", help="Do not download files that already exist at the target path.")
    parser.add_argument("--write-last-checkpoint", action="store_true", help="After download/list, write default last_checkpoint pointer(s). Mutates files and should be used deliberately.")
    parser.add_argument("--json", action="store_true", help="Print manifest as JSON in dry-run mode.")
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    dest_root = Path(args.dest_root).expanduser()
    datasets = selected_datasets(args.dataset)
    entries = list(iter_entries(datasets, dest_root))
    if not args.download:
        print_manifest(entries, args.json)
        if args.write_last_checkpoint:
            for dataset in datasets:
                write_last_checkpoint(dataset, dest_root)
        return 0
    if not args.yes:
        print("Refusing to download without --yes. Re-run with --download --yes after confirming network/disk side effects.")
        print_manifest(entries, False)
        return 2
    for entry in entries:
        if entry["exists"] and args.skip_existing:
            print(f"skip existing {entry['target_file']}")
            continue
        print(f"download {entry['dataset']} / {entry['name']} -> {entry['target_dir']}")
        download_one(entry, args.prefer, not args.no_fallback)
    if args.write_last_checkpoint:
        for dataset in datasets:
            write_last_checkpoint(dataset, dest_root)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
