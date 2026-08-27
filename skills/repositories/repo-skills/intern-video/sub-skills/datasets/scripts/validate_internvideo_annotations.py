#!/usr/bin/env python3
"""Safe annotation validator for InternVideo repo-skill workflows.

The script performs syntax/schema/path-readiness checks only. It does not
import InternVideo, decode media, download data, or contact object storage.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
from pathlib import Path
from typing import Any, Iterable


REMOTE_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*://")
VIDEO_SUFFIXES = {".mp4", ".avi", ".mov", ".webm", ".flv", ".wmv", ".mkv", ".rmvb", ".ts"}
VALID_ROLES = {"system", "developer", "user", "assistant", "pretrain"}


class Report:
    def __init__(self, path: Path, fmt: str):
        self.path = str(path)
        self.format = fmt
        self.records_checked = 0
        self.errors: list[dict[str, str]] = []
        self.warnings: list[dict[str, str]] = []
        self.paths_checked = 0
        self.missing_paths: list[dict[str, str]] = []
        self.remote_paths_skipped = 0
        self.extra: dict[str, Any] = {}

    def error(self, where: str, message: str) -> None:
        self.errors.append({"where": where, "message": message})

    def warn(self, where: str, message: str) -> None:
        self.warnings.append({"where": where, "message": message})

    def missing(self, where: str, path: Path) -> None:
        self.missing_paths.append({"where": where, "path": str(path)})

    def as_dict(self, strict: bool = False) -> dict[str, Any]:
        ok = not self.errors and not self.missing_paths and not (strict and self.warnings)
        return {
            "ok": ok,
            "path": self.path,
            "format": self.format,
            "records_checked": self.records_checked,
            "errors": self.errors,
            "warnings": self.warnings,
            "paths_checked": self.paths_checked,
            "missing_paths": self.missing_paths,
            "remote_paths_skipped": self.remote_paths_skipped,
            "extra": self.extra,
        }


def is_remote_path(value: str) -> bool:
    return bool(REMOTE_RE.match(value)) or value.startswith("p2:s3")


def as_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    return [value]


def load_json(path: Path, report: Report) -> Any | None:
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:  # noqa: BLE001 - validator reports all parse failures
        report.error(str(path), f"failed to parse JSON: {exc}")
        return None


def iter_jsonl(path: Path, report: Report, max_records: int) -> Iterable[tuple[int, Any]]:
    checked = 0
    try:
        with path.open("r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, 1):
                if max_records and checked >= max_records:
                    report.extra["truncated_at_max_records"] = max_records
                    break
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    obj = json.loads(stripped)
                except Exception as exc:  # noqa: BLE001
                    report.error(f"line {line_no}", f"invalid JSONL object: {exc}")
                    continue
                checked += 1
                yield line_no, obj
    except FileNotFoundError:
        report.error(str(path), "file does not exist")
    except Exception as exc:  # noqa: BLE001
        report.error(str(path), f"failed to read JSONL: {exc}")


def numeric(value: Any, *, positive: bool = False) -> bool:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    if not math.isfinite(float(value)):
        return False
    return (float(value) > 0) if positive else True


def int_like(value: Any) -> bool:
    if isinstance(value, bool):
        return False
    try:
        int(str(value))
        return True
    except Exception:  # noqa: BLE001
        return False


def validate_wh(value: Any) -> bool:
    if not isinstance(value, list) or len(value) != 2:
        return False
    return all(numeric(v, positive=True) for v in value)


def validate_caption(value: Any) -> bool:
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, list):
        return bool(value) and all(isinstance(v, str) and v.strip() for v in value)
    if isinstance(value, dict):
        return bool(value) and all(isinstance(v, str) and v.strip() for v in value.values())
    return False


def resolve_candidate(media_path: str, media_root: str | None) -> Path | None:
    if is_remote_path(media_path):
        return None
    p = Path(media_path)
    if p.is_absolute():
        return p
    if media_root:
        root = Path(media_root)
        if is_remote_path(str(root)):
            return None
        return root / p
    return p


def check_media_path(value: Any, media_root: str | None, where: str, report: Report) -> None:
    for item in as_list(value):
        if not isinstance(item, str) or not item:
            report.error(where, f"media path must be a non-empty string, got {type(item).__name__}")
            continue
        candidate = resolve_candidate(item, media_root)
        if candidate is None:
            report.remote_paths_skipped += 1
            continue
        report.paths_checked += 1
        if not candidate.exists():
            report.missing(where, candidate)


def maybe_check_media_path(value: Any, args: argparse.Namespace, where: str, report: Report, media_root: str | None = None) -> None:
    if args.check_paths:
        check_media_path(value, media_root if media_root is not None else args.media_root, where, report)


def detect_format(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".jsonl":
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                obj = json.loads(line)
                if isinstance(obj, dict) and {"search_word_id", "search_word"}.issubset(obj):
                    return "internvid-queries"
                return "internvideo3-jsonl"
        return "internvideo3-jsonl"
    if suffix == ".json":
        with path.open("r", encoding="utf-8") as f:
            obj = json.load(f)
        if isinstance(obj, list):
            return "internvideo2-json"
        if isinstance(obj, dict):
            if "messages" in obj:
                return "internvideo3-jsonl"
            if any(isinstance(v, dict) and "annotation" in v for v in obj.values()):
                return "internvideo3-meta"
            if {"search_word_id", "search_word"}.issubset(obj):
                return "internvid-queries"
            return "internvideo3-meta"
    return "pretrain-list"


def validate_internvid_queries(path: Path, args: argparse.Namespace, report: Report) -> None:
    seen: set[str] = set()
    for line_no, obj in iter_jsonl(path, report, args.max_records):
        where = f"line {line_no}"
        report.records_checked += 1
        if not isinstance(obj, dict):
            report.error(where, "record must be a JSON object")
            continue
        for key in ("search_word_id", "search_word"):
            if not isinstance(obj.get(key), str) or not obj.get(key, "").strip():
                report.error(where, f"missing or empty string key {key!r}")
        sid = obj.get("search_word_id")
        if isinstance(sid, str):
            if sid in seen:
                report.warn(where, f"duplicate search_word_id {sid!r}")
            seen.add(sid)
    report.extra["unique_search_word_ids"] = len(seen)


def validate_internvideo2_json(path: Path, args: argparse.Namespace, report: Report) -> None:
    data = load_json(path, report)
    if data is None:
        return
    if not isinstance(data, list):
        report.error(str(path), f"expected a JSON array, got {type(data).__name__}")
        return
    report.extra["total_records_in_file"] = len(data)
    limit = len(data) if args.max_records == 0 else min(len(data), args.max_records)
    media_counts: dict[str, int] = {"image": 0, "video": 0, "audio": 0, "audio_video": 0, "unknown": 0}
    for idx, obj in enumerate(data[:limit]):
        where = f"record {idx}"
        report.records_checked += 1
        if not isinstance(obj, dict):
            report.error(where, f"record must be an object, got {type(obj).__name__}")
            continue

        caption_keys = [k for k in obj if "caption" in k]
        if "caption" in obj:
            caption_ok = validate_caption(obj["caption"])
        elif "captions" in obj:
            caption_ok = validate_caption(obj["captions"])
        elif caption_keys:
            caption_ok = all(validate_caption(obj[k]) for k in caption_keys)
        else:
            caption_ok = False
        if not caption_ok:
            report.error(where, "missing or invalid caption/captions/caption-like fields")

        expect = args.expect_media_type
        keys = {k for k in ("image", "video", "audio") if k in obj}
        if expect == "auto":
            if "video" in keys and "audio" in keys:
                media_counts["audio_video"] += 1
            elif "video" in keys:
                media_counts["video"] += 1
            elif "image" in keys:
                media_counts["image"] += 1
            elif "audio" in keys:
                media_counts["audio"] += 1
            else:
                media_counts["unknown"] += 1
                report.error(where, "no image/video/audio media key found")
        elif expect == "audio_video":
            if "video" not in keys:
                report.error(where, "expected audio_video record with at least a video key")
            media_counts["audio_video"] += 1
        else:
            if expect not in keys:
                report.error(where, f"expected media key {expect!r}")
            media_counts[expect] += 1

        for key in keys:
            maybe_check_media_path(obj[key], args, f"{where}.{key}", report)

        if "crop_bbox" in obj:
            bbox = obj["crop_bbox"]
            if not isinstance(bbox, list) or len(bbox) != 4 or not all(numeric(v) for v in bbox):
                report.error(where, "crop_bbox must be a list of four numbers")
        if ("video_start_frame" in obj) != ("video_end_frame" in obj):
            report.error(where, "video_start_frame and video_end_frame must appear together")
        if "duration" in obj and not numeric(obj["duration"]):
            report.warn(where, "duration is present but not numeric")
    if limit < len(data):
        report.extra["truncated_at_max_records"] = args.max_records
    report.extra["media_counts"] = media_counts


def validate_text_timestamps(value: Any, expected_count: int, where: str, report: Report) -> None:
    if value is None:
        return
    if expected_count == 0:
        report.warn(where, "conversation_timestamps provided but no <VIDEO_CONTEXT> placeholder is present")
        return
    if isinstance(value, list) and len(value) == 2 and all(numeric(v) for v in value):
        actual_count = 1
    elif isinstance(value, list):
        actual_count = len(value)
        for i, pair in enumerate(value):
            if not (isinstance(pair, list) and len(pair) == 2 and all(numeric(v) for v in pair)):
                report.error(where, f"conversation_timestamps[{i}] must be [start, end] numbers")
    else:
        report.error(where, "conversation_timestamps must be [start, end] or a list of such pairs")
        return
    if actual_count != expected_count:
        report.error(where, f"conversation_timestamps count {actual_count} does not match <VIDEO_CONTEXT> count {expected_count}")


def validate_video_extra(video_url: dict[str, Any], where: str, report: Report) -> None:
    extra_keys = {"origin_video_length", "origin_fps", "processed_video_length", "processed_fps", "frames_timestamp"}
    present = {k for k in extra_keys if k in video_url}
    if present:
        for key in ("origin_video_length", "origin_fps"):
            if key not in video_url:
                report.error(where, f"{key} is required when any video timing metadata is provided")
        if "origin_video_length" in video_url and not numeric(video_url["origin_video_length"], positive=True):
            report.error(where, "origin_video_length must be positive numeric")
        if "origin_fps" in video_url and not numeric(video_url["origin_fps"], positive=True):
            report.error(where, "origin_fps must be positive numeric")
    if ("processed_video_length" in video_url) != ("processed_fps" in video_url):
        report.error(where, "processed_video_length and processed_fps must appear together")
    if "processed_video_length" in video_url and not numeric(video_url["processed_video_length"], positive=True):
        report.error(where, "processed_video_length must be positive numeric")
    if "processed_fps" in video_url and not numeric(video_url["processed_fps"], positive=True):
        report.error(where, "processed_fps must be positive numeric")
    if "frames_timestamp" in video_url:
        ts = video_url["frames_timestamp"]
        if not isinstance(ts, list) or not all(numeric(v) for v in ts):
            report.error(where, "frames_timestamp must be a list of numbers")
        elif "processed_video_length" in video_url and len(ts) != int(video_url["processed_video_length"]):
            report.error(where, "frames_timestamp length must equal processed_video_length")
        elif "processed_video_length" not in video_url:
            report.warn(where, "frames_timestamp is ignored unless processed_video_length/processed_fps are present")


def validate_internvideo3_jsonl(path: Path, args: argparse.Namespace, report: Report, media_root: str | None = None) -> None:
    role_counts: dict[str, int] = {}
    for line_no, obj in iter_jsonl(path, report, args.max_records):
        where = f"{path.name}:line {line_no}"
        report.records_checked += 1
        if not isinstance(obj, dict):
            report.error(where, "record must be a JSON object")
            continue
        messages = obj.get("messages")
        if not isinstance(messages, list) or not messages:
            report.error(where, "missing non-empty messages list")
            continue
        pretrain_roles = [m for m in messages if isinstance(m, dict) and m.get("role") == "pretrain"]
        if pretrain_roles and len(messages) != 1:
            report.error(where, "pretrain role must be the only message in a pretrain record")

        total_images = 0
        total_videos = 0
        total_img_placeholders = 0
        total_video_placeholders = 0

        for msg_idx, msg in enumerate(messages):
            msg_where = f"{where}.messages[{msg_idx}]"
            if not isinstance(msg, dict):
                report.error(msg_where, "message must be an object")
                continue
            role = msg.get("role")
            if role not in VALID_ROLES:
                report.error(msg_where, f"invalid role {role!r}")
            elif isinstance(role, str):
                role_counts[role] = role_counts.get(role, 0) + 1
            content = msg.get("content")
            if isinstance(content, str):
                continue
            if not isinstance(content, list):
                report.error(msg_where, "content must be a string or list")
                continue

            msg_images = 0
            msg_videos = 0
            msg_img_placeholders = 0
            msg_video_placeholders = 0

            for c_idx, item in enumerate(content):
                item_where = f"{msg_where}.content[{c_idx}]"
                if not isinstance(item, dict):
                    report.error(item_where, "content item must be an object")
                    continue
                typ = item.get("type")
                if typ == "text":
                    text = item.get("text")
                    if not isinstance(text, str):
                        report.error(item_where, "text content item must contain string text")
                        continue
                    img_count = text.count("<IMG_CONTEXT>")
                    video_count = text.count("<VIDEO_CONTEXT>")
                    msg_img_placeholders += img_count
                    msg_video_placeholders += video_count
                    validate_text_timestamps(item.get("conversation_timestamps"), video_count, item_where, report)
                elif typ == "image_url":
                    image_url = item.get("image_url")
                    if not isinstance(image_url, dict):
                        report.error(item_where, "image_url content must contain an image_url object")
                        continue
                    url = image_url.get("url")
                    if not isinstance(url, str) or not url:
                        report.error(item_where, "image_url.url must be a non-empty string")
                    else:
                        maybe_check_media_path(url, args, f"{item_where}.image_url.url", report, media_root)
                    if "image_wh" not in image_url:
                        report.warn(item_where, "image_wh is missing; packing/token counting may discard this record")
                    elif not validate_wh(image_url["image_wh"]):
                        report.error(item_where, "image_wh must be [width, height] positive numbers")
                    msg_images += 1
                elif typ == "video_url":
                    video_url = item.get("video_url")
                    if not isinstance(video_url, dict):
                        report.error(item_where, "video_url content must contain a video_url object")
                        continue
                    url = video_url.get("url")
                    if not isinstance(url, str) or not url:
                        report.error(item_where, "video_url.url must be a non-empty string")
                    else:
                        suffix = Path(url).suffix.lower()
                        if suffix and suffix not in VIDEO_SUFFIXES and not url.endswith("/"):
                            report.warn(item_where, f"video suffix {suffix!r} may not be supported by the SFT loader")
                        maybe_check_media_path(url, args, f"{item_where}.video_url.url", report, media_root)
                    if "image_wh" not in video_url:
                        report.warn(item_where, "video image_wh is missing; packing/token counting may discard this record")
                    elif not validate_wh(video_url["image_wh"]):
                        report.error(item_where, "video image_wh must be [width, height] positive numbers")
                    validate_video_extra(video_url, item_where, report)
                    msg_videos += 1
                else:
                    report.error(item_where, f"unsupported content type {typ!r}")

            if role in {"user", "pretrain"}:
                total_images += msg_images
                total_videos += msg_videos
                total_img_placeholders += msg_img_placeholders
                total_video_placeholders += msg_video_placeholders

        if total_images and total_img_placeholders != total_images:
            report.error(where, f"<IMG_CONTEXT> placeholders ({total_img_placeholders}) do not match image items ({total_images})")
        if total_videos and total_video_placeholders != total_videos:
            report.error(where, f"<VIDEO_CONTEXT> placeholders ({total_video_placeholders}) do not match video items ({total_videos})")
    report.extra["role_counts"] = role_counts


def resolve_meta_path(meta_path: Path, value: str) -> Path:
    p = Path(value)
    if p.is_absolute():
        return p
    return meta_path.parent / p


def validate_internvideo3_meta(path: Path, args: argparse.Namespace, report: Report) -> None:
    data = load_json(path, report)
    if data is None:
        return
    if not isinstance(data, dict):
        report.error(str(path), f"expected top-level object, got {type(data).__name__}")
        return
    report.extra["dataset_count"] = len(data)
    followed_files: list[str] = []
    for name, spec in data.items():
        where = f"dataset {name!r}"
        report.records_checked += 1
        if not isinstance(name, str) or not name:
            report.error(where, "dataset name must be a non-empty string")
        if not isinstance(spec, dict):
            report.error(where, "dataset spec must be an object")
            continue
        annotation = spec.get("annotation")
        if not isinstance(annotation, str) or not annotation:
            report.error(where, "missing non-empty annotation path")
            continue
        if "media_root" in spec and not isinstance(spec["media_root"], str):
            report.error(where, "media_root must be a string when present")
        if "sample_ratio" in spec and not numeric(spec["sample_ratio"], positive=True):
            report.error(where, "sample_ratio must be a positive number")
        vmin = spec.get("video_min_frames")
        vmax = spec.get("video_max_frames")
        vrand = spec.get("rand_video_max_frames")
        if all(v is not None for v in (vmin, vmax, vrand)):
            if not (numeric(vmin, positive=True) and numeric(vmax, positive=True) and numeric(vrand, positive=True)):
                report.error(where, "video frame limits must be positive numbers")
            elif not (float(vmin) <= float(vrand) <= float(vmax)):
                report.error(where, "expected video_min_frames <= rand_video_max_frames <= video_max_frames")
        ann_path = resolve_meta_path(path, annotation)
        if args.check_paths:
            report.paths_checked += 1
            if not ann_path.exists():
                report.missing(f"{where}.annotation", ann_path)
        if args.follow_meta and ann_path.exists():
            media_root = spec.get("media_root") or args.media_root
            if media_root and not Path(media_root).is_absolute() and not is_remote_path(media_root):
                media_root = str(path.parent / media_root)
            if ann_path.is_dir():
                jsonl_files = sorted(ann_path.rglob("*.jsonl"))
                if not jsonl_files:
                    report.warn(where, f"annotation directory contains no .jsonl files: {ann_path}")
                for jsonl_path in jsonl_files:
                    followed_files.append(str(jsonl_path))
                    validate_internvideo3_jsonl(jsonl_path, args, report, media_root=media_root)
            else:
                followed_files.append(str(ann_path))
                validate_internvideo3_jsonl(ann_path, args, report, media_root=media_root)
    if followed_files:
        report.extra["followed_annotation_files"] = followed_files


def validate_pretrain_list(path: Path, args: argparse.Namespace, report: Report) -> None:
    counts = {"path_label": 0, "path_duration_label": 0, "source_clip_label": 0, "unknown": 0}
    try:
        with path.open("r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, 1):
                if args.max_records and report.records_checked >= args.max_records:
                    report.extra["truncated_at_max_records"] = args.max_records
                    break
                stripped = line.strip()
                if not stripped or stripped.startswith("#"):
                    continue
                if args.delimiter is None:
                    fields = stripped.split()
                else:
                    fields = [field.strip() for field in stripped.split(args.delimiter)]
                where = f"line {line_no}"
                report.records_checked += 1
                if len(fields) == 2:
                    media_path, label = fields
                    counts["path_label"] += 1
                    if not int_like(label):
                        report.error(where, "label must be an integer")
                    maybe_check_media_path(media_path, args, f"{where}.path", report)
                elif len(fields) == 3:
                    media_path, duration, label = fields
                    counts["path_duration_label"] += 1
                    if not numeric_from_string(duration, positive=True):
                        report.error(where, "duration/frame-count must be a positive number")
                    if not int_like(label):
                        report.error(where, "label must be an integer")
                    maybe_check_media_path(media_path, args, f"{where}.path", report)
                elif len(fields) == 6:
                    source, media_path, total_time, start_time, end_time, label = fields
                    counts["source_clip_label"] += 1
                    if not source:
                        report.error(where, "source must be non-empty")
                    for key, value in (("total_time", total_time), ("start_time", start_time), ("end_time", end_time)):
                        if not numeric_from_string(value):
                            report.error(where, f"{key} must be numeric")
                    if all(numeric_from_string(v) for v in (total_time, start_time, end_time)):
                        t, s, e = map(float, (total_time, start_time, end_time))
                        if not (t == s == e == -1) and (t <= 0 or s < -1 or e < -1 or (s >= 0 and e >= 0 and e <= s)):
                            report.warn(where, "clip timing values look inconsistent")
                    if not int_like(label):
                        report.error(where, "label must be an integer")
                    maybe_check_media_path(media_path, args, f"{where}.path", report)
                else:
                    counts["unknown"] += 1
                    report.error(where, f"unsupported field count {len(fields)}; expected 2, 3, or 6")
    except FileNotFoundError:
        report.error(str(path), "file does not exist")
    except Exception as exc:  # noqa: BLE001
        report.error(str(path), f"failed to read list: {exc}")
    report.extra["line_format_counts"] = counts


def numeric_from_string(value: str, *, positive: bool = False) -> bool:
    try:
        x = float(value)
    except Exception:  # noqa: BLE001
        return False
    if not math.isfinite(x):
        return False
    return x > 0 if positive else True


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate InternVideo annotation/list files without importing the repo or decoding media.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("path", type=Path, help="Annotation/list/meta file to validate.")
    parser.add_argument(
        "--format",
        choices=["auto", "internvid-queries", "internvideo2-json", "internvideo3-meta", "internvideo3-jsonl", "pretrain-list"],
        default="auto",
        help="Expected annotation format.",
    )
    parser.add_argument("--media-root", default="", help="Root/prefix for local media paths when --check-paths is enabled.")
    parser.add_argument("--check-paths", action="store_true", help="Check local file/directory existence for referenced media/annotation paths.")
    parser.add_argument("--follow-meta", action="store_true", help="For InternVideo3 meta JSON, also validate referenced JSONL annotation files.")
    parser.add_argument("--max-records", type=int, default=1000, help="Maximum records to inspect; use 0 for all records.")
    parser.add_argument(
        "--expect-media-type",
        choices=["auto", "image", "video", "audio", "audio_video"],
        default="auto",
        help="Expected media type for InternVideo2 JSON arrays.",
    )
    parser.add_argument("--delimiter", default=None, help="Delimiter for pretrain-list files; default is arbitrary whitespace.")
    parser.add_argument("--strict", action="store_true", help="Exit nonzero when warnings are present.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.max_records < 0:
        parser.error("--max-records must be >= 0")

    fmt = args.format
    detection_error = None
    if fmt == "auto":
        try:
            fmt = detect_format(args.path)
        except Exception as exc:  # noqa: BLE001
            fmt = "pretrain-list"
            detection_error = f"auto-detection failed ({exc}); falling back to pretrain-list"

    report = Report(args.path, fmt)
    if detection_error:
        report.warn(str(args.path), detection_error)

    if fmt == "internvid-queries":
        validate_internvid_queries(args.path, args, report)
    elif fmt == "internvideo2-json":
        validate_internvideo2_json(args.path, args, report)
    elif fmt == "internvideo3-meta":
        validate_internvideo3_meta(args.path, args, report)
    elif fmt == "internvideo3-jsonl":
        validate_internvideo3_jsonl(args.path, args, report)
    elif fmt == "pretrain-list":
        validate_pretrain_list(args.path, args, report)
    else:  # pragma: no cover - argparse prevents this
        report.error(str(args.path), f"unsupported format {fmt}")

    summary = report.as_dict(strict=args.strict)
    print(json.dumps(summary, indent=2, ensure_ascii=False, sort_keys=True))
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
