#!/usr/bin/env python3
"""Build or augment annotation JSON files for 3D-ResNets-PyTorch.

This script combines self-contained adaptations of the repository utilities:
kinetics_json.py, ucf101_json.py, hmdb51_json.py, mit_json.py, and
add_fps_into_activitynet_json.py. It does not import from the original checkout.
"""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from fractions import Fraction
from pathlib import Path
from typing import Any, Iterable, Optional


def read_rows(path: Path, *, delimiter: str = ",", has_header: bool = False) -> list[Any]:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        if has_header:
            return list(csv.DictReader(f, delimiter=delimiter))
        return list(csv.reader(f, delimiter=delimiter))


def first_existing(directory: Path, names: Iterable[str]) -> Optional[Path]:
    for name in names:
        candidate = directory / name
        if candidate.exists():
            return candidate
    return None


def get_n_frames_jpg(video_path: Path) -> Optional[int]:
    if not video_path.is_dir():
        return None
    return sum(
        1
        for p in video_path.iterdir()
        if p.suffix.lower() == ".jpg" and p.name.startswith("image_") and not p.name.startswith(".")
    )


def get_n_frames_hdf5(video_path: Path) -> Optional[int]:
    if not video_path.is_file():
        return None
    try:
        import h5py  # imported lazily so JPG-only users do not need it
    except ImportError as exc:
        raise RuntimeError("h5py is required to count HDF5 frames") from exc
    with h5py.File(video_path, "r") as h5:
        if "video" not in h5:
            raise KeyError(f"{video_path} has no RGB dataset named 'video'")
        return len(h5["video"])


def load_path_map(path_map: Path | None) -> dict[tuple[str | None, str], Path]:
    if path_map is None:
        return {}
    with path_map.open("r", encoding="utf-8") as f:
        payload = json.load(f)
    items = payload.get("items", payload if isinstance(payload, list) else [])
    mapping: dict[tuple[str | None, str], Path] = {}
    for item in items:
        video_id = item.get("video_id")
        actual_path = item.get("path")
        if not video_id or not actual_path:
            continue
        label = item.get("label")
        mapping[(label, video_id)] = Path(actual_path)
        mapping[(None, video_id)] = Path(actual_path)
    return mapping


def resolve_video_path(
    video_root: Path,
    label: str,
    video_id: str,
    video_type: str,
    path_map: dict[tuple[str | None, str], Path],
) -> Path:
    mapped = path_map.get((label, video_id)) or path_map.get((None, video_id))
    if mapped is not None:
        return mapped
    if video_type == "jpg":
        return video_root / label / video_id
    return video_root / label / f"{video_id}.hdf5"


def add_segment(
    entry: dict,
    *,
    video_root: Path,
    label: str,
    video_id: str,
    video_type: str,
    strict: bool,
    path_map: dict[tuple[str | None, str], Path],
    include_video_paths: bool,
    warnings: list[str],
) -> None:
    video_path = resolve_video_path(video_root, label, video_id, video_type, path_map)
    if video_type == "jpg":
        n_frames = get_n_frames_jpg(video_path)
        segment = [1, n_frames + 1] if n_frames is not None else None
    else:
        n_frames = get_n_frames_hdf5(video_path) if video_path.exists() else None
        segment = [0, n_frames] if n_frames is not None else None

    if segment is None or n_frames is None or n_frames <= 0:
        message = f"missing or empty {video_type} video for id={video_id!r}, label={label!r}: {video_path}"
        if strict:
            raise FileNotFoundError(message)
        warnings.append(message)
        return

    entry.setdefault("annotations", {})["segment"] = segment
    if include_video_paths or (path_map and path_map.get((label, video_id))):
        entry["video_path"] = str(video_path)


def write_json(path: Path, payload: dict, *, pretty: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        if pretty:
            json.dump(payload, f, indent=2, sort_keys=False)
            f.write("\n")
        else:
            json.dump(payload, f)


def ordered_unique(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            out.append(value)
    return out


def kinetics_rows_to_database(csv_path: Path, subset: str) -> dict[str, dict]:
    rows = read_rows(csv_path, has_header=True)
    database: dict[str, dict] = {}
    for row in rows:
        youtube_id = row["youtube_id"]
        time_start = int(float(row["time_start"]))
        time_end = int(float(row["time_end"]))
        key = f"{youtube_id}_{time_start:06d}_{time_end:06d}"
        entry = {"subset": subset, "annotations": {}}
        if subset != "testing":
            entry["annotations"] = {"label": row["label"]}
        database[key] = entry
    return database


def cmd_kinetics(args: argparse.Namespace) -> int:
    train_csv = first_existing(args.annotation_dir, [f"kinetics-{args.n_classes}_train.csv", "kinetics_train.csv"])
    val_csv = first_existing(args.annotation_dir, [f"kinetics-{args.n_classes}_val.csv", "kinetics_val.csv"])
    test_csv = first_existing(args.annotation_dir, [f"kinetics-{args.n_classes}_test.csv", "kinetics_test.csv"])
    if train_csv is None or val_csv is None:
        raise FileNotFoundError("Expected kinetics train/val CSV files in annotation_dir")

    labels = ordered_unique(row["label"] for row in read_rows(train_csv, has_header=True))
    database = {}
    database.update(kinetics_rows_to_database(train_csv, "training"))
    database.update(kinetics_rows_to_database(val_csv, "validation"))
    if test_csv is not None:
        database.update(kinetics_rows_to_database(test_csv, "testing"))

    path_map = load_path_map(args.path_map)
    warnings: list[str] = []
    for video_id, entry in database.items():
        label = entry.get("annotations", {}).get("label", "test")
        add_segment(
            entry,
            video_root=args.video_path,
            label=label,
            video_id=video_id,
            video_type=args.video_type,
            strict=args.strict,
            path_map=path_map,
            include_video_paths=args.include_video_paths,
            warnings=warnings,
        )

    write_json(args.dst_json, {"labels": labels, "database": database}, pretty=args.pretty)
    print(f"wrote {args.dst_json} with {len(database)} videos and {len(labels)} labels")
    for warning in warnings[:20]:
        print(f"warning: {warning}", file=sys.stderr)
    if len(warnings) > 20:
        print(f"warning: {len(warnings) - 20} more missing/empty videos suppressed", file=sys.stderr)
    return 0


def parse_ucf_list(csv_path: Path, subset: str) -> dict[str, dict]:
    rows = read_rows(csv_path, delimiter=" ")
    database: dict[str, dict] = {}
    for row in rows:
        if not row or not row[0]:
            continue
        parts = row[0].split("/")
        if len(parts) != 2:
            raise ValueError(f"Unexpected UCF101 list item {row[0]!r} in {csv_path}")
        class_name = parts[0]
        video_id = Path(parts[1]).stem
        database[video_id] = {"subset": subset, "annotations": {"label": class_name}}
    return database


def ucf_labels(label_csv_path: Path) -> list[str]:
    rows = read_rows(label_csv_path, delimiter=" ")
    return [row[1] for row in rows if len(row) >= 2]


def cmd_ucf101(args: argparse.Namespace) -> int:
    labels = ucf_labels(args.annotation_dir / "classInd.txt")
    path_map = load_path_map(args.path_map)
    args.dst_dir.mkdir(parents=True, exist_ok=True)
    for split_index in range(1, 4):
        train_csv = args.annotation_dir / f"trainlist0{split_index}.txt"
        val_csv = args.annotation_dir / f"testlist0{split_index}.txt"
        database = {}
        database.update(parse_ucf_list(train_csv, "training"))
        database.update(parse_ucf_list(val_csv, "validation"))
        warnings: list[str] = []
        for video_id, entry in database.items():
            label = entry["annotations"]["label"]
            add_segment(
                entry,
                video_root=args.video_path,
                label=label,
                video_id=video_id,
                video_type=args.video_type,
                strict=args.strict,
                path_map=path_map,
                include_video_paths=args.include_video_paths,
                warnings=warnings,
            )
        dst_json = args.dst_dir / f"ucf101_0{split_index}.json"
        write_json(dst_json, {"labels": labels, "database": database}, pretty=args.pretty)
        print(f"wrote {dst_json} with {len(database)} videos")
        for warning in warnings[:10]:
            print(f"warning: {warning}", file=sys.stderr)
        if len(warnings) > 10:
            print(f"warning: {len(warnings) - 10} more missing/empty videos suppressed", file=sys.stderr)
    return 0


def hmdb_label_from_split_file(path: Path) -> str:
    # Example: brush_hair_test_split1.txt -> brush_hair
    return "_".join(path.name.split("_")[:-2])


def hmdb_labels(annotation_dir: Path) -> list[str]:
    return sorted({hmdb_label_from_split_file(p) for p in annotation_dir.iterdir() if "test_split" in p.name})


def hmdb_database(annotation_dir: Path, split_index: int) -> dict[str, dict]:
    database: dict[str, dict] = {}
    for file_path in sorted(annotation_dir.iterdir()):
        if f"split{split_index}" not in file_path.name:
            continue
        label = hmdb_label_from_split_file(file_path)
        rows = read_rows(file_path, delimiter=" ")
        for row in rows:
            if len(row) < 2:
                continue
            flag = int(row[1])
            if flag == 0:
                continue
            subset = "training" if flag == 1 else "validation"
            video_id = Path(row[0]).stem
            database[video_id] = {"subset": subset, "annotations": {"label": label}}
    return database


def cmd_hmdb51(args: argparse.Namespace) -> int:
    labels = hmdb_labels(args.annotation_dir)
    path_map = load_path_map(args.path_map)
    args.dst_dir.mkdir(parents=True, exist_ok=True)
    for split_index in range(1, 4):
        database = hmdb_database(args.annotation_dir, split_index)
        warnings: list[str] = []
        for video_id, entry in database.items():
            label = entry["annotations"]["label"]
            add_segment(
                entry,
                video_root=args.video_path,
                label=label,
                video_id=video_id,
                video_type=args.video_type,
                strict=args.strict,
                path_map=path_map,
                include_video_paths=args.include_video_paths,
                warnings=warnings,
            )
        dst_json = args.dst_dir / f"hmdb51_{split_index}.json"
        write_json(dst_json, {"labels": labels, "database": database}, pretty=args.pretty)
        print(f"wrote {dst_json} with {len(database)} videos")
        for warning in warnings[:10]:
            print(f"warning: {warning}", file=sys.stderr)
        if len(warnings) > 10:
            print(f"warning: {len(warnings) - 10} more missing/empty videos suppressed", file=sys.stderr)
    return 0


def mit_rows_to_database(csv_path: Path, subset: str) -> dict[str, dict]:
    rows = read_rows(csv_path)
    database: dict[str, dict] = {}
    for row in rows:
        if not row:
            continue
        if subset == "testing":
            video_id = Path(row[0]).stem
            database[video_id] = {"subset": subset, "annotations": {}}
        else:
            parts = row[0].split("/")
            if len(parts) != 2:
                raise ValueError(f"Unexpected MIT item {row[0]!r} in {csv_path}")
            video_id = Path(parts[1]).stem
            label = row[1]
            database[video_id] = {"subset": subset, "annotations": {"label": label}}
    return database


def mit_labels(class_file_path: Path) -> list[str]:
    rows = read_rows(class_file_path)
    return [row[0] for row in rows if row]


def cmd_mit(args: argparse.Namespace) -> int:
    class_file_path = args.annotation_dir / "moments_categories.txt"
    train_csv = args.annotation_dir / "trainingSet.csv"
    val_csv = args.annotation_dir / "validationSet.csv"
    test_csv = args.annotation_dir / "testingSet.csv"
    labels = mit_labels(class_file_path)
    database = {}
    database.update(mit_rows_to_database(train_csv, "training"))
    database.update(mit_rows_to_database(val_csv, "validation"))
    if test_csv.exists():
        database.update(mit_rows_to_database(test_csv, "testing"))

    path_map = load_path_map(args.path_map)
    warnings: list[str] = []
    for video_id, entry in database.items():
        label = entry.get("annotations", {}).get("label", "test")
        add_segment(
            entry,
            video_root=args.video_path,
            label=label,
            video_id=video_id,
            video_type=args.video_type,
            strict=args.strict,
            path_map=path_map,
            include_video_paths=args.include_video_paths,
            warnings=warnings,
        )
    write_json(args.dst_json, {"labels": labels, "database": database}, pretty=args.pretty)
    print(f"wrote {args.dst_json} with {len(database)} videos and {len(labels)} labels")
    for warning in warnings[:20]:
        print(f"warning: {warning}", file=sys.stderr)
    if len(warnings) > 20:
        print(f"warning: {len(warnings) - 20} more missing/empty videos suppressed", file=sys.stderr)
    return 0


def parse_rate(rate_text: str | None) -> Optional[float]:
    if not rate_text or rate_text in {"0/0", "N/A"}:
        return None
    try:
        return float(Fraction(rate_text))
    except Exception:
        try:
            return float(rate_text)
        except Exception:
            return None


def ffprobe_fps(video_path: Path) -> float:
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=avg_frame_rate,r_frame_rate",
        "-of",
        "json",
        str(video_path),
    ]
    proc = subprocess.run(cmd, text=True, capture_output=True)
    if proc.returncode != 0:
        raise RuntimeError(f"ffprobe failed for {video_path}: {proc.stderr.strip()}")
    payload = json.loads(proc.stdout or "{}")
    streams = payload.get("streams") or []
    if not streams:
        raise RuntimeError(f"ffprobe found no video stream in {video_path}")
    fps = parse_rate(streams[0].get("avg_frame_rate")) or parse_rate(streams[0].get("r_frame_rate"))
    if not fps:
        raise RuntimeError(f"ffprobe did not report a usable frame rate for {video_path}")
    return fps


def activitynet_key_for_stem(database: dict, stem: str) -> Optional[str]:
    candidates = [stem]
    if stem.startswith("v_"):
        candidates.append(stem[2:])
    for key in candidates:
        if key in database:
            return key
    return None


def cmd_activitynet_add_fps(args: argparse.Namespace) -> int:
    with args.input_json.open("r", encoding="utf-8") as f:
        payload = json.load(f)
    database = payload.get("database")
    if not isinstance(database, dict):
        raise KeyError("ActivityNet JSON must contain a top-level 'database' object")

    updated = 0
    warnings: list[str] = []
    for video_path in sorted(args.video_dir.iterdir()):
        if not video_path.is_file() or video_path.suffix.lower() != ".mp4":
            continue
        key = activitynet_key_for_stem(database, video_path.stem)
        if key is None:
            message = f"no database key for {video_path.name}; expected either {video_path.stem!r} or stripped 'v_' form"
            if args.strict:
                raise KeyError(message)
            warnings.append(message)
            continue
        database[key]["fps"] = ffprobe_fps(video_path)
        updated += 1

    output_json = args.output_json or args.input_json
    write_json(output_json, payload, pretty=args.pretty)
    print(f"wrote {output_json}; added/updated fps for {updated} videos")
    for warning in warnings[:20]:
        print(f"warning: {warning}", file=sys.stderr)
    if len(warnings) > 20:
        print(f"warning: {len(warnings) - 20} more unmatched videos suppressed", file=sys.stderr)
    return 0


def add_common_video_args(parser: argparse.ArgumentParser, *, positional_video_type: bool = False) -> None:
    if positional_video_type:
        parser.add_argument("video_type", choices=["jpg", "hdf5"], help="Prepared video storage type")
    else:
        parser.add_argument("--video-type", choices=["jpg", "hdf5"], default="jpg", help="Prepared video storage type")
    parser.add_argument("--path-map", type=Path, default=None, help="Optional HDF5 manifest from extract_video_hdf5.py")
    parser.add_argument(
        "--include-video-paths",
        action="store_true",
        help="Store explicit per-entry video_path values; useful with HDF5 fallback filenames",
    )
    parser.add_argument("--strict", action="store_true", help="Fail if any listed video has no frame/HDF5 data")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build 3D-ResNets-PyTorch annotation JSON files.")
    sub = parser.add_subparsers(dest="command", required=True)

    kinetics = sub.add_parser("kinetics", help="Build Kinetics JSON from kinetics CSV files")
    kinetics.add_argument("annotation_dir", type=Path, help="Directory containing kinetics CSV files")
    kinetics.add_argument("n_classes", type=int, help="Kinetics class count, e.g. 400, 600, or 700")
    kinetics.add_argument("video_path", type=Path, help="Prepared jpg or hdf5 video root")
    add_common_video_args(kinetics, positional_video_type=True)
    kinetics.add_argument("dst_json", type=Path, help="Output JSON path")
    kinetics.set_defaults(func=cmd_kinetics)

    ucf101 = sub.add_parser("ucf101", help="Build UCF101 split JSON files")
    ucf101.add_argument("annotation_dir", type=Path, help="Directory containing classInd.txt and train/test split files")
    ucf101.add_argument("video_path", type=Path, help="Prepared jpg or hdf5 video root")
    ucf101.add_argument("dst_dir", type=Path, help="Output directory for ucf101_01.json..ucf101_03.json")
    add_common_video_args(ucf101)
    ucf101.set_defaults(func=cmd_ucf101)

    hmdb51 = sub.add_parser("hmdb51", help="Build HMDB51 split JSON files")
    hmdb51.add_argument("annotation_dir", type=Path, help="Directory containing *_test_split*.txt files")
    hmdb51.add_argument("video_path", type=Path, help="Prepared jpg or hdf5 video root")
    hmdb51.add_argument("dst_dir", type=Path, help="Output directory for hmdb51_1.json..hmdb51_3.json")
    add_common_video_args(hmdb51)
    hmdb51.set_defaults(func=cmd_hmdb51)

    mit = sub.add_parser("mit", help="Build Moments in Time JSON")
    mit.add_argument("annotation_dir", type=Path, help="Directory containing moments_categories.txt and MIT CSV files")
    mit.add_argument("video_path", type=Path, help="Prepared jpg or hdf5 video root")
    mit.add_argument("dst_json", type=Path, help="Output JSON path")
    add_common_video_args(mit)
    mit.set_defaults(func=cmd_mit)

    anet = sub.add_parser("activitynet-add-fps", help="Add fps fields to an existing ActivityNet JSON")
    anet.add_argument("video_dir", type=Path, help="Directory containing ActivityNet mp4 files, usually v_<id>.mp4")
    anet.add_argument("input_json", type=Path, help="Existing ActivityNet JSON")
    anet.add_argument("output_json", type=Path, nargs="?", default=None, help="Output JSON path; defaults to in-place")
    anet.add_argument("--strict", action="store_true", help="Fail if any mp4 has no matching database key")
    anet.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    anet.set_defaults(func=cmd_activitynet_add_fps)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
